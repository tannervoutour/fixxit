"""Conversation manager for maintaining context and history."""

import re
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json

from config import config


@dataclass
class ConversationEntity:
    """Represents an entity mentioned in conversation."""
    entity_type: str  # 'machine', 'ticket', 'technician', 'part', 'fault_code'
    entity_id: Optional[int] = None
    name: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    mentioned_turn: int = 0
    last_used_turn: int = 0


@dataclass
class ConversationContext:
    """Maintains conversation context and state."""
    current_focus: Optional[str] = None  # What we're currently discussing
    user_intent: Optional[str] = None   # troubleshooting, maintenance, etc.
    location_context: Optional[str] = None  # Building A, Floor 1, etc.
    priority_filter: Optional[str] = None  # urgent, high, etc.
    entities: Dict[str, ConversationEntity] = field(default_factory=dict)
    last_results: Dict[str, Any] = field(default_factory=dict)
    turn_count: int = 0


class ConversationManager:
    """Manages conversation history, context, and entity tracking."""
    
    def __init__(self):
        """Initialize conversation manager."""
        self.messages: List[Dict[str, Any]] = []
        self.context = ConversationContext()
        self.max_history = config.MAX_CONVERSATION_HISTORY
        self.context_retention = config.CONTEXT_RETENTION_TURNS
        
    def add_user_message(self, content: str):
        """Add a user message to the conversation."""
        self.context.turn_count += 1
        
        message = {
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "turn": self.context.turn_count
        }
        
        self.messages.append(message)
        self._analyze_user_input(content)
        self._trim_history()
    
    def add_assistant_message(self, content: str, function_calls: Optional[List[Dict]] = None):
        """Add an assistant message to the conversation."""
        message = {
            "role": "assistant", 
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "turn": self.context.turn_count
        }
        
        if function_calls:
            message["function_calls"] = function_calls
        
        self.messages.append(message)
        self._trim_history()
    
    def add_function_call(self, function_name: str, parameters: Dict[str, Any], result: Dict[str, Any]):
        """Add a function call and its result to the conversation."""
        # Add function call message
        call_message = {
            "role": "function",
            "name": function_name,
            "content": json.dumps(parameters),
            "timestamp": datetime.now().isoformat(),
            "turn": self.context.turn_count
        }
        self.messages.append(call_message)
        
        # Store results in context
        self.context.last_results[function_name] = result
        
        # Extract entities from results
        self._extract_entities_from_result(function_name, result)
        
        self._trim_history()
    
    def _analyze_user_input(self, content: str):
        """Analyze user input to understand intent and extract context."""
        content_lower = content.lower()
        
        # Detect user intent
        if any(word in content_lower for word in ['broken', 'down', 'error', 'fault', 'problem', 'issue', 'trouble']):
            self.context.user_intent = 'troubleshooting'
        elif any(word in content_lower for word in ['maintenance', 'service', 'repair', 'fix', 'history']):
            self.context.user_intent = 'maintenance'
        elif any(word in content_lower for word in ['parts', 'inventory', 'stock', 'order']):
            self.context.user_intent = 'parts_management'
        elif any(word in content_lower for word in ['technician', 'who', 'expert', 'assign']):
            self.context.user_intent = 'technician_lookup'
        
        # Extract location context
        location_patterns = [
            r'building ([a-z])',
            r'floor (\d+)', 
            r'(shipping|receiving|assembly|utilities)',
            r'in ([a-z][a-z0-9\s-]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content_lower)
            if match:
                self.context.location_context = match.group(1)
                break
        
        # Extract priority context
        if any(word in content_lower for word in ['urgent', 'emergency', 'critical']):
            self.context.priority_filter = 'urgent'
        elif any(word in content_lower for word in ['high priority', 'important']):
            self.context.priority_filter = 'high'
        
        # Handle references to previous entities
        self._resolve_references(content_lower)
    
    def _resolve_references(self, content_lower: str):
        """Resolve pronouns and references to previous entities."""
        reference_patterns = {
            'machine': ['it', 'that machine', 'the machine', 'this equipment'],
            'ticket': ['that ticket', 'the ticket', 'this issue', 'that problem'],
            'technician': ['that technician', 'the technician', 'they', 'them'],
            'part': ['that part', 'the part', 'those parts']
        }
        
        for entity_type, patterns in reference_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    # Find the most recent entity of this type
                    recent_entity = self._get_most_recent_entity(entity_type)
                    if recent_entity:
                        recent_entity.last_used_turn = self.context.turn_count
                        self.context.current_focus = f"{entity_type}_{recent_entity.entity_id}"
    
    def _extract_entities_from_result(self, function_name: str, result: Dict[str, Any]):
        """Extract entities from function call results."""
        if not result.get('success') or 'result' not in result:
            return
        
        data = result['result']
        
        # Extract machines
        if 'machines' in data:
            for machine in data['machines']:
                self._add_entity('machine', machine.get('id'), 
                               machine.get('serial_number', ''), machine)
        
        # Extract tickets
        if 'tickets' in data:
            for ticket in data['tickets']:
                self._add_entity('ticket', ticket.get('id'),
                               f"Ticket #{ticket.get('id')}", ticket)
        
        # Extract technicians
        if 'technicians' in data:
            for tech in data['technicians']:
                self._add_entity('technician', tech.get('id'),
                               tech.get('name', ''), tech)
        
        # Extract parts
        if 'parts' in data:
            for part in data['parts']:
                self._add_entity('part', part.get('part_number'),
                               part.get('name', ''), part)
        
        # Extract fault codes
        if 'fault_codes' in data:
            for code in data['fault_codes']:
                self._add_entity('fault_code', code.get('code'),
                               code.get('code', ''), code)
    
    def _add_entity(self, entity_type: str, entity_id: Any, name: str, details: Dict[str, Any]):
        """Add or update an entity in the context."""
        key = f"{entity_type}_{entity_id}"
        
        if key in self.context.entities:
            # Update existing entity
            entity = self.context.entities[key]
            entity.last_used_turn = self.context.turn_count
            entity.details.update(details)
        else:
            # Add new entity
            entity = ConversationEntity(
                entity_type=entity_type,
                entity_id=entity_id,
                name=name,
                details=details,
                mentioned_turn=self.context.turn_count,
                last_used_turn=self.context.turn_count
            )
            self.context.entities[key] = entity
    
    def _get_most_recent_entity(self, entity_type: str) -> Optional[ConversationEntity]:
        """Get the most recently mentioned entity of a given type."""
        recent_entities = [
            entity for entity in self.context.entities.values()
            if entity.entity_type == entity_type
        ]
        
        if not recent_entities:
            return None
        
        # Sort by last used turn, then by mentioned turn
        recent_entities.sort(key=lambda e: (e.last_used_turn, e.mentioned_turn), reverse=True)
        return recent_entities[0]
    
    def get_context_for_function_call(self, function_name: str) -> Dict[str, Any]:
        """Get relevant context for a function call."""
        context_hints = {}
        
        # Add location context if relevant
        if self.context.location_context and function_name in ['search_equipment', 'get_maintenance_tickets']:
            context_hints['suggested_location'] = self.context.location_context
        
        # Add priority context
        if self.context.priority_filter and function_name == 'get_maintenance_tickets':
            context_hints['suggested_priority'] = self.context.priority_filter
        
        # Add entity context
        if self.context.current_focus:
            entity_key = self.context.current_focus
            if entity_key in self.context.entities:
                entity = self.context.entities[entity_key]
                context_hints['focused_entity'] = {
                    'type': entity.entity_type,
                    'id': entity.entity_id,
                    'name': entity.name
                }
        
        # Add recent relevant entities
        recent_entities = {}
        for entity in self.context.entities.values():
            if (self.context.turn_count - entity.last_used_turn) <= self.context_retention:
                if entity.entity_type not in recent_entities:
                    recent_entities[entity.entity_type] = []
                recent_entities[entity.entity_type].append({
                    'id': entity.entity_id,
                    'name': entity.name,
                    'last_used': entity.last_used_turn
                })
        
        if recent_entities:
            context_hints['recent_entities'] = recent_entities
        
        return context_hints
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation context."""
        summary_parts = []
        
        if self.context.user_intent:
            summary_parts.append(f"Intent: {self.context.user_intent}")
        
        if self.context.location_context:
            summary_parts.append(f"Location: {self.context.location_context}")
        
        if self.context.priority_filter:
            summary_parts.append(f"Priority: {self.context.priority_filter}")
        
        # Recent entities
        recent_entities = []
        for entity in self.context.entities.values():
            if (self.context.turn_count - entity.last_used_turn) <= 2:  # Very recent
                recent_entities.append(f"{entity.entity_type}: {entity.name}")
        
        if recent_entities:
            summary_parts.append(f"Recent entities: {', '.join(recent_entities)}")
        
        return " | ".join(summary_parts) if summary_parts else "No active context"
    
    def _trim_history(self):
        """Trim conversation history to stay within limits."""
        if len(self.messages) > self.max_history:
            # Keep the most recent messages
            self.messages = self.messages[-self.max_history:]
        
        # Clean up old entities
        cutoff_turn = self.context.turn_count - (self.context_retention * 2)
        expired_entities = [
            key for key, entity in self.context.entities.items()
            if entity.last_used_turn < cutoff_turn
        ]
        
        for key in expired_entities:
            del self.context.entities[key]
    
    def get_messages_for_openai(self) -> List[Dict[str, Any]]:
        """Get messages formatted for OpenAI API."""
        # Filter out function messages and format for OpenAI
        openai_messages = []
        
        for msg in self.messages:
            if msg["role"] in ["user", "assistant"]:
                openai_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        return openai_messages
    
    def reset_context(self):
        """Reset the conversation context but keep history."""
        self.context = ConversationContext()
        self.context.turn_count = len(self.messages)


# Global conversation manager instance
conversation_manager = ConversationManager()