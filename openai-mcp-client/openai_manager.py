"""OpenAI API manager for handling GPT-4o communication."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import openai
from openai import AsyncOpenAI

from config import config
from function_definitions import FunctionDefinitions
from conversation_manager import conversation_manager
from mcp_bridge import mcp_bridge
from utils.formatters import formatter
from utils.validators import validator


class OpenAIManager:
    """Manages communication with OpenAI GPT-4o API."""
    
    def __init__(self):
        """Initialize OpenAI manager."""
        self.client: Optional[AsyncOpenAI] = None
        self.logger = logging.getLogger(__name__)
        self.function_definitions = None  # Will be loaded dynamically
        
    async def initialize(self) -> bool:
        """Initialize the OpenAI client and MCP bridge."""
        try:
            # Validate configuration
            if not config.validate_config():
                return False
            
            # Initialize OpenAI client
            api_key = config.get_openai_api_key()
            self.client = AsyncOpenAI(api_key=api_key)
            
            # Load dynamic function definitions
            self.function_definitions = FunctionDefinitions.get_all_functions()
            enabled_count = len(self.function_definitions)
            self.logger.info(f"✅ OpenAI client initialized with {enabled_count} tools")
            self.logger.info(f"🔧 Max tool iterations per query: {config.MAX_TOOL_ITERATIONS}")
            
            # Connect to MCP bridge
            if not await mcp_bridge.connect():
                self.logger.error("❌ Failed to connect to MCP server")
                return False
            
            self.logger.info("🚀 OpenAI MCP client ready!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def process_user_message(self, user_input: str) -> str:
        """
        Process a user message using cumulative context loop.
        
        Args:
            user_input: User's message
            
        Returns:
            Assistant's response
        """
        if not self.client:
            return "❌ OpenAI client not initialized"
        
        try:
            # Validate user input
            is_valid, error = validator.validate_user_input(user_input)
            if not is_valid:
                return f"❌ Invalid input: {error}"
            
            # Initialize context with user query
            context = [{
                "role": "user",
                "content": user_input
            }]
            
            self.logger.info(f"💬 Processing: {user_input[:100]}...")
            
            # Iterative tool calling loop
            return await self._iterative_tool_loop(context)
            
        except Exception as e:
            self.logger.error(f"❌ Error processing message: {e}")
            return f"❌ Sorry, I encountered an error: {str(e)}"
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for cumulative context approach."""
        return f"{config.SYSTEM_PROMPT}\\n\\nYou have access to maintenance database tools. You can either:\\n1. Call a tool to gather more information\\n2. Call 'answer_user_query' to provide the final answer\\n\\nBase your decision on whether you have enough information to answer the user's question. If you need more specific data, call appropriate tools first."
    
    async def _iterative_tool_loop(self, context: List[Dict[str, Any]]) -> str:
        """Run iterative tool calling loop until AI provides final answer."""
        max_iterations = config.MAX_TOOL_ITERATIONS  # Prevent infinite loops - configurable
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Prepare messages with system prompt and accumulated context
            messages = [
                {"role": "system", "content": self._build_system_prompt()}
            ]
            messages.extend(context)
            
            # Call OpenAI with all accumulated context
            response = await self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages,
                tools=self.function_definitions,
                tool_choice="auto",
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE
            )
            
            message = response.choices[0].message
            
            # Check if AI wants to call a tool
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    
                    # Check if this is the final answer
                    if function_name == "answer_user_query":
                        arguments = json.loads(tool_call.function.arguments)
                        final_answer = arguments.get("answer", "No answer provided")
                        
                        # Add to conversation history
                        conversation_manager.add_user_message(context[0]["content"])
                        conversation_manager.add_assistant_message(final_answer)
                        
                        return final_answer
                    
                    # Handle regular tool call
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        self.logger.info(f"🔧 Tool call {iteration}: {function_name}({arguments})")
                        
                        # Validate and call MCP function
                        is_valid, error = validator.validate_function_parameters(function_name, arguments)
                        if not is_valid:
                            tool_result = f"Error: {error}"
                        else:
                            result = await mcp_bridge.call_function(function_name, arguments)
                            if result.get('success', False):
                                # Get raw data without formatting
                                tool_result = json.dumps(result.get('data', result), indent=2)
                            else:
                                tool_result = f"Error: {result.get('error', 'Unknown error')}"
                        
                        # Add tool result to context
                        context.append({
                            "role": "assistant",
                            "content": f"I called {function_name} and got: {tool_result}"
                        })
                        
                    except Exception as e:
                        context.append({
                            "role": "assistant",
                            "content": f"Error calling {function_name}: {str(e)}"
                        })
            
            else:
                # AI provided text response without tool call - treat as final answer
                final_answer = message.content
                
                # Add to conversation history
                conversation_manager.add_user_message(context[0]["content"])
                conversation_manager.add_assistant_message(final_answer)
                
                return final_answer
        
        # If we hit max iterations, return what we have
        return "❌ Maximum tool calls reached. Please refine your question."
    
    async def _handle_tool_calls(self, tool_calls) -> str:
        """Handle tool calls from OpenAI (new format)."""
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            
            try:
                # Parse function arguments
                arguments_str = tool_call.function.arguments
                arguments = json.loads(arguments_str)
                
                self.logger.info(f"🔧 Tool call: {function_name}({arguments})")
                
                # Validate function parameters
                is_valid, error = validator.validate_function_parameters(function_name, arguments)
                if not is_valid:
                    error_msg = f"❌ Invalid parameters for {function_name}: {error}"
                    results.append(error_msg)
                    continue
                
                # Call the MCP function
                result = await mcp_bridge.call_function(function_name, arguments)
                
                # Record the function call
                conversation_manager.add_function_call(function_name, arguments, result)
                
                # Check if function call was successful
                if not result.get('success', False):
                    error_msg = result.get('error', 'Unknown error')
                    results.append(f"❌ {function_name} failed: {error_msg}")
                    continue
                
                # Format the result for user display
                formatted_result = formatter.format_function_result(function_name, result)
                results.append(formatted_result)
                
            except json.JSONDecodeError as e:
                error_msg = f"❌ Invalid arguments for {function_name}: {e}"
                results.append(error_msg)
            except Exception as e:
                error_msg = f"❌ {function_name} failed: {str(e)}"
                self.logger.error(f"Tool call error: {e}")
                results.append(error_msg)
        
        # Combine all results
        combined_result = "\\n\\n".join(results)
        
        # Get additional context if needed
        context_hints = conversation_manager.get_context_for_function_call("general")
        
        # Create a follow-up prompt to OpenAI to interpret the results
        interpretation = await self._interpret_function_result(
            "multiple_tools", {}, combined_result, context_hints
        )
        
        conversation_manager.add_assistant_message(interpretation)
        return interpretation
    
    async def _interpret_function_result(
        self, 
        function_name: str, 
        arguments: Dict[str, Any], 
        formatted_result: str,
        context_hints: Dict[str, Any]
    ) -> str:
        """Ask OpenAI to interpret and contextualize function results."""
        try:
            interpretation_prompt = f"""
The user asked a question and I called the function '{function_name}' with arguments: {json.dumps(arguments)}

Here are the results:
{formatted_result}

Context from our conversation: {json.dumps(context_hints)}

Please provide a helpful, conversational response that:
1. Directly answers the user's question based on these results
2. Highlights any important or urgent items
3. Suggests logical next steps if appropriate
4. Uses the conversation context to be more specific and relevant

Be conversational and helpful, not just a data dump. If there are urgent issues, prioritize those.
"""
            
            response = await self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are interpreting database results for a maintenance technician. Be helpful and highlight important information."},
                    {"role": "user", "content": interpretation_prompt}
                ],
                max_tokens=config.MAX_TOKENS // 2,  # Use less tokens for interpretation
                temperature=config.TEMPERATURE
            )
            
            interpretation = response.choices[0].message.content
            
            # Combine formatted results with interpretation
            return f"{formatted_result}\\n\\n{interpretation}"
            
        except Exception as e:
            self.logger.error(f"Error interpreting results: {e}")
            # Fall back to just the formatted results
            return formatted_result
    
    async def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the current conversation history."""
        return conversation_manager.messages
    
    async def reset_conversation(self):
        """Reset the conversation context."""
        conversation_manager.reset_context()
        self.logger.info("🔄 Conversation context reset")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get status of all system components."""
        status = {
            "openai_client": self.client is not None,
            "mcp_bridge": mcp_bridge.is_connected,
            "conversation_turns": conversation_manager.context.turn_count,
            "active_entities": len(conversation_manager.context.entities),
            "current_focus": conversation_manager.context.current_focus,
            "user_intent": conversation_manager.context.user_intent
        }
        
        # Get MCP server status
        if mcp_bridge.is_connected:
            tools = await mcp_bridge.get_available_tools()
            status["available_tools"] = len(tools) if tools else 0
        
        return status
    
    async def reload_tools(self) -> bool:
        """Reload tool configuration without restarting the system."""
        try:
            self.logger.info("🔄 Reloading tool configuration...")
            
            # Reload tool configuration
            if FunctionDefinitions.reload_tools():
                # Update function definitions
                self.function_definitions = FunctionDefinitions.get_all_functions()
                enabled_count = len(self.function_definitions)
                self.logger.info(f"✅ Tools reloaded - {enabled_count} tools now available")
                return True
            else:
                self.logger.error("❌ Failed to reload tool configuration")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error reloading tools: {e}")
            return False
    
    async def shutdown(self):
        """Cleanup and shutdown."""
        try:
            await mcp_bridge.disconnect()
            self.logger.info("🔌 OpenAI manager shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Global OpenAI manager instance
openai_manager = OpenAIManager()