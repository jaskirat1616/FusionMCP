"""
Context Manager for FusionMCP

This module handles both short-term (session) and long-term (persistent) context
management for the FusionMCP system. It includes functionality for summarizing
old context to save tokens and managing memory efficiently.
"""

import json
import os
import pickle
import time
from datetime import datetime
from typing import Any, Dict, List, Optional


class SessionContext:
    """Manages short-term (session) context for the current interaction."""
    
    def __init__(self):
        self.creation_time = time.time()
        self.interactions = []
        self.current_state = {}
        self.max_interactions = 50  # Limit to prevent memory bloat
    
    def add_interaction(self, user_input: str, ai_response: str, execution_result: Optional[Dict] = None):
        """Add a new interaction to the session context."""
        interaction = {
            'timestamp': time.time(),
            'user_input': user_input,
            'ai_response': ai_response,
            'execution_result': execution_result
        }
        self.interactions.append(interaction)
        
        # Limit the number of interactions stored
        if len(self.interactions) > self.max_interactions:
            self.interactions = self.interactions[-self.max_interactions:]
    
    def get_recent_context(self, count: int = 5) -> List[Dict]:
        """Get the most recent interactions."""
        return self.interactions[-count:]
    
    def update_state(self, key: str, value: Any):
        """Update a value in the current session state."""
        self.current_state[key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a value from the current session state."""
        return self.current_state.get(key, default)


class PersistentContext:
    """Manages long-term (persistent) context stored on disk."""
    
    def __init__(self, storage_path: str = "persistent_context.json"):
        self.storage_path = storage_path
        self.context_data = self._load_context()
    
    def _load_context(self) -> Dict:
        """Load context data from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_context(self):
        """Save context data to storage."""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as file:
                json.dump(self.context_data, file, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving context: {e}")
    
    def store_data(self, key: str, value: Any):
        """Store data in persistent context."""
        self.context_data[key] = {
            'value': value,
            'timestamp': time.time(),
            'last_accessed': time.time()
        }
        self._save_context()
    
    def retrieve_data(self, key: str, default: Any = None) -> Any:
        """Retrieve data from persistent context."""
        item = self.context_data.get(key)
        if item:
            item['last_accessed'] = time.time()  # Update last accessed time
            self._save_context()
            return item['value']
        return default
    
    def summarize_old_context(self, max_age_hours: int = 24):
        """Summarize old context to save space and tokens."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        for key, value in self.context_data.items():
            if value.get('timestamp', 0) < cutoff_time:
                # For now, we'll just keep track of old items to potentially summarize
                # In a more advanced implementation, this would trigger an AI summarization
                print(f"Context item '{key}' is old and could be summarized")


class ContextManager:
    """Main context manager that combines session and persistent context."""
    
    def __init__(self, persistent_storage_path: str = "persistent_context.json"):
        self.session_context = SessionContext()
        self.persistent_context = PersistentContext(persistent_storage_path)
        self.summary_threshold = 100  # Number of interactions before summarization
    
    def add_interaction(self, user_input: str, ai_response: str, execution_result: Optional[Dict] = None):
        """Add an interaction to both session and persistent contexts."""
        self.session_context.add_interaction(user_input, ai_response, execution_result)
        
        # Store interactions in persistent context as well for long-term memory
        interaction_key = f"interaction_{int(time.time())}_{len(self.session_context.interactions)}"
        self.persistent_context.store_data(interaction_key, {
            'user_input': user_input,
            'ai_response': ai_response,
            'execution_result': execution_result,
            'timestamp': time.time()
        })
        
        # Trigger summarization if needed
        self._maybe_summarize()
    
    def _maybe_summarize(self):
        """Check if it's time to summarize old context."""
        total_interactions = len(self.session_context.interactions)
        if total_interactions > self.summary_threshold:
            # In a real implementation, this would trigger AI summarization of old context
            # For now, just clean up the oldest entries beyond the threshold
            excess_count = total_interactions - self.summary_threshold
            self.session_context.interactions = self.session_context.interactions[excess_count:]
    
    def get_recent_context(self, count: int = 5) -> List[Dict]:
        """Get recent context from session."""
        return self.session_context.get_recent_context(count)
    
    def update_session_state(self, key: str, value: Any):
        """Update a value in the session state."""
        self.session_context.update_state(key, value)
    
    def get_session_state(self, key: str, default: Any = None) -> Any:
        """Get a value from the session state."""
        return self.session_context.get_state(key, default)
    
    def store_persistent_data(self, key: str, value: Any):
        """Store data in persistent context."""
        self.persistent_context.store_data(key, value)
    
    def retrieve_persistent_data(self, key: str, default: Any = None) -> Any:
        """Retrieve data from persistent context."""
        return self.persistent_context.retrieve_data(key, default)
    
    def get_long_term_context(self, since_time: Optional[float] = None) -> Dict:
        """Get relevant long-term context since a specific time."""
        result = {}
        for key, value in self.persistent_context.context_data.items():
            if since_time is None or value.get('timestamp', 0) >= since_time:
                result[key] = value
        return result


# Example usage
if __name__ == "__main__":
    # Initialize context manager
    ctx_manager = ContextManager()
    
    # Add some interactions
    ctx_manager.add_interaction("Create a cube", "Creating a cube with dimensions 10x10x10", {"status": "success", "object_id": "cube_001"})
    ctx_manager.add_interaction("Rotate the cube", "Rotating cube 45 degrees around Z-axis", {"status": "success", "object_id": "cube_001"})
    
    # Check recent context
    recent_context = ctx_manager.get_recent_context(2)
    print("Recent context:", recent_context)
    
    # Store and retrieve persistent data
    ctx_manager.store_persistent_data("project_name", "Test Project")
    project_name = ctx_manager.retrieve_persistent_data("project_name")
    print("Project name:", project_name)