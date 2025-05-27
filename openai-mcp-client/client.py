"""Main OpenAI MCP client application."""

import asyncio
import logging
import signal
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from config import config
from openai_manager import openai_manager


class MaintenanceAssistant:
    """Main application class for the maintenance AI assistant."""
    
    def __init__(self):
        """Initialize the maintenance assistant."""
        self.console = Console() if RICH_AVAILABLE else None
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('maintenance_assistant.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def initialize(self) -> bool:
        """Initialize the assistant and all components."""
        try:
            self._print_header()
            
            # Initialize OpenAI manager (which also connects MCP bridge)
            success = await openai_manager.initialize()
            if not success:
                self._print_error("Failed to initialize. Please check your configuration.")
                return False
            
            self._print_success("Maintenance Assistant ready!")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            self._print_error(f"Initialization failed: {e}")
            return False
    
    def _print_header(self):
        """Print application header."""
        if self.console:
            self.console.print(Panel.fit(
                f"[bold blue]{config.CLIENT_NAME}[/bold blue]\\n"
                f"[dim]Version {config.CLIENT_VERSION}[/dim]\\n"
                f"[dim]{config.CLIENT_DESCRIPTION}[/dim]",
                title="🔧 AI Maintenance Assistant",
                style="blue"
            ))
        else:
            print(f"=== {config.CLIENT_NAME} ===")
            print(f"Version {config.CLIENT_VERSION}")
            print(f"{config.CLIENT_DESCRIPTION}")
            print("=" * 50)
    
    def _print_success(self, message: str):
        """Print success message."""
        if self.console:
            self.console.print(f"✅ {message}", style="green")
        else:
            print(f"✅ {message}")
    
    def _print_error(self, message: str):
        """Print error message."""
        if self.console:
            self.console.print(f"❌ {message}", style="red")
        else:
            print(f"❌ {message}")
    
    def _print_info(self, message: str):
        """Print info message."""
        if self.console:
            self.console.print(f"ℹ️ {message}", style="blue")
        else:
            print(f"ℹ️ {message}")
    
    def _print_assistant_response(self, response: str):
        """Print assistant response with formatting."""
        if self.console:
            # Rich can handle markdown-like formatting
            self.console.print(Panel(
                response,
                title="🤖 Assistant",
                style="green",
                padding=(1, 2)
            ))
        else:
            print("\\n🤖 Assistant:")
            print("-" * 40)
            print(response)
            print("-" * 40)
    
    async def run_interactive(self):
        """Run the interactive chat interface."""
        self.running = True
        
        # Print usage instructions
        self._print_usage_instructions()
        
        while self.running:
            try:
                # Get user input
                if self.console:
                    user_input = Prompt.ask("\\n[bold blue]You[/bold blue]")
                else:
                    user_input = input("\\nYou: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['/quit', '/exit', '/q']:
                    break
                elif user_input.lower() in ['/help', '/h']:
                    self._print_help()
                    continue
                elif user_input.lower() in ['/status', '/s']:
                    await self._print_status()
                    continue
                elif user_input.lower() in ['/reset', '/r']:
                    await openai_manager.reset_conversation()
                    self._print_success("Conversation reset")
                    continue
                elif user_input.lower() in ['/history']:
                    await self._print_history()
                    continue
                
                # Process user message
                response = await openai_manager.process_user_message(user_input)
                self._print_assistant_response(response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in interactive loop: {e}")
                self._print_error(f"An error occurred: {e}")
        
        await self.shutdown()
    
    def _print_usage_instructions(self):
        """Print usage instructions."""
        instructions = """
🔧 **Welcome to the AI Maintenance Assistant!**

Ask me about:
• **Machine status**: "Show me all machines that are down"
• **Trouble tickets**: "What urgent tickets do we have?"
• **Maintenance history**: "When was the CNC machine last serviced?"
• **Parts inventory**: "Do we have belts for the conveyor?"
• **Troubleshooting**: "How do I fix fault code E001?"
• **Technician info**: "Who can repair hydraulic systems?"

**Special commands:**
• `/help` or `/h` - Show this help
• `/status` or `/s` - Show system status  
• `/reset` or `/r` - Reset conversation
• `/history` - Show conversation history
• `/quit` or `/q` - Exit

**Examples:**
• "Find all machines in Building A"
• "Show me urgent tickets for the welding robot"
• "Who should I assign for electrical issues?"
• "Check stock levels for CNC parts"
"""
        
        if self.console:
            self.console.print(Panel(
                instructions,
                title="📖 How to Use",
                style="cyan"
            ))
        else:
            print(instructions)
    
    def _print_help(self):
        """Print help information."""
        help_text = """
**Available Commands:**
• `/help` - Show this help
• `/status` - Show system status
• `/reset` - Reset conversation context
• `/history` - Show conversation history  
• `/quit` - Exit the application

**Example Questions:**
• "What machines are currently down?"
• "Show me high priority tickets"
• "Find maintenance records for machine SN001234"
• "Check if we have hydraulic fluid in stock"
• "How do I troubleshoot error code H001?"
• "Which technician is best for welding repairs?"

**Tips:**
• I remember context from our conversation
• You can refer to "that machine" or "the urgent ticket"
• I can help with follow-up questions
• Ask for specific details or explanations
"""
        
        if self.console:
            self.console.print(Panel(
                help_text,
                title="📚 Help",
                style="yellow"
            ))
        else:
            print(help_text)
    
    async def _print_status(self):
        """Print system status."""
        try:
            status = await openai_manager.get_system_status()
            
            status_text = f"""
**System Status:**
• OpenAI Client: {'✅ Connected' if status['openai_client'] else '❌ Disconnected'}
• MCP Bridge: {'✅ Connected' if status['mcp_bridge'] else '❌ Disconnected'}
• Available Tools: {status.get('available_tools', 'Unknown')}

**Conversation:**
• Turn Count: {status['conversation_turns']}
• Active Entities: {status['active_entities']}
• Current Focus: {status['current_focus'] or 'None'}
• User Intent: {status['user_intent'] or 'None'}
"""
            
            if self.console:
                style = "green" if status['openai_client'] and status['mcp_bridge'] else "yellow"
                self.console.print(Panel(
                    status_text,
                    title="📊 System Status",
                    style=style
                ))
            else:
                print(status_text)
                
        except Exception as e:
            self._print_error(f"Failed to get status: {e}")
    
    async def _print_history(self):
        """Print conversation history."""
        try:
            history = await openai_manager.get_conversation_history()
            
            if not history:
                self._print_info("No conversation history yet.")
                return
            
            history_text = ""
            for msg in history[-10:]:  # Show last 10 messages
                role = msg['role'].title()
                content = msg['content']
                if len(content) > 100:
                    content = content[:100] + "..."
                
                timestamp = msg.get('timestamp', '')
                if timestamp:
                    timestamp = timestamp.split('T')[1][:8]  # Just time part
                
                history_text += f"**{role}** ({timestamp}): {content}\\n\\n"
            
            if self.console:
                self.console.print(Panel(
                    history_text,
                    title="📜 Recent History",
                    style="dim"
                ))
            else:
                print("Recent History:")
                print(history_text)
                
        except Exception as e:
            self._print_error(f"Failed to get history: {e}")
    
    async def process_single_query(self, query: str) -> str:
        """Process a single query (for programmatic use)."""
        try:
            if not await self.initialize():
                return "Failed to initialize assistant"
            
            response = await openai_manager.process_user_message(query)
            await self.shutdown()
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return f"Error: {e}"
    
    async def shutdown(self):
        """Shutdown the assistant gracefully."""
        try:
            self._print_info("Shutting down...")
            await openai_manager.shutdown()
            self._print_success("Goodbye!")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


async def main():
    """Main entry point."""
    assistant = MaintenanceAssistant()
    
    # Check if running with a single query argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        response = await assistant.process_single_query(query)
        print(response)
    else:
        # Run interactive mode
        if await assistant.initialize():
            await assistant.run_interactive()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)