"""
AI Interface for FusionMCP

This module provides an interface to multiple LLM backends (Gemini, Ollama, OpenAI)
for processing natural language requests and generating Fusion 360 commands.
It handles API calls, error management, and authentication.
"""

import json
import os
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from .config import load_config


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Generate a response from the AI model."""
        pass


class GeminiProvider(AIProvider):
    """Google Gemini API provider."""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Generate a response using the Gemini API."""
        import google.generativeai as genai
        
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            
            # Prepare the prompt with context if provided
            full_prompt = prompt
            if context:
                context_str = json.dumps(context, indent=2)
                full_prompt = f"Context: {context_str}\n\nUser Request: {prompt}"
            
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return f"Error: {str(e)}"


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Generate a response using the OpenAI API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Prepare messages for the chat API
        messages = [{"role": "system", "content": "You are an expert in Fusion 360 CAD operations. Generate Python code for Fusion 360 API."}]
        
        if context:
            context_str = json.dumps(context, indent=2)
            messages.append({"role": "user", "content": f"Context: {context_str}"})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return f"Error: {str(e)}"


class OllamaProvider(AIProvider):
    """Ollama local model provider."""
    
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434/api/generate"):
        self.model = model
        self.base_url = base_url
    
    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Generate a response using a local Ollama model."""
        # Prepare the prompt with context if provided
        full_prompt = prompt
        if context:
            context_str = json.dumps(context, indent=2)
            full_prompt = f"Context: {context_str}\n\nUser Request: {prompt}"
        
        try:
            # Check if this is a generate endpoint (for Ollama) or a chat endpoint
            if "api/generate" in self.base_url:
                response = requests.post(
                    self.base_url,
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False
                    },
                    timeout=120
                )
            elif "api/chat" in self.base_url:
                # For LM Studio which uses OpenAI-compatible API
                response = requests.post(
                    self.base_url,
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are an AI assistant specialized in generating Fusion 360 Python scripts. Always respond with properly formatted Python code when asked to generate scripts."},
                            {"role": "user", "content": full_prompt}
                        ],
                        "stream": False
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=120
                )
            else:
                # Default to generate endpoint
                response = requests.post(
                    self.base_url,
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False
                    },
                    timeout=120
                )
            
            response.raise_for_status()
            
            result = response.json()
            
            # Handle both Ollama and LM Studio response formats
            if "api/generate" in self.base_url:
                return result.get('response', 'No response generated')
            elif "api/chat" in self.base_url:
                choices = result.get('choices', [])
                if choices:
                    return choices[0].get('message', {}).get('content', 'No response generated')
                else:
                    return 'No response generated'
            else:
                # Default to Ollama format
                return result.get('response', 'No response generated')
                
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to local LLM server. Please ensure Ollama or LM Studio is running."
        except requests.exceptions.Timeout:
            return "Error: Request to local LLM server timed out. Please check your model and try again."
        except Exception as e:
            print(f"Error calling local LLM API: {e}")
            return f"Error: {str(e)}"


class LMStudioProvider(AIProvider):
    """LM Studio local model provider (OpenAI-compatible API)."""
    
    def __init__(self, model: str = "default", base_url: str = "http://localhost:1234/v1/chat/completions"):
        self.model = model
        self.base_url = base_url
    
    def generate_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Generate a response using a local LM Studio model."""
        # Prepare the prompt with context if provided
        full_prompt = prompt
        if context:
            context_str = json.dumps(context, indent=2)
            full_prompt = f"Context: {context_str}\n\nUser Request: {prompt}"
        
        try:
            response = requests.post(
                self.base_url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an AI assistant specialized in generating Fusion 360 Python scripts. Always respond with properly formatted Python code when asked to generate scripts. Only return the Python code without any additional explanation or markdown formatting."},
                        {"role": "user", "content": full_prompt}
                    ],
                    "temperature": 0.3
                },
                headers={
                    "Content-Type": "application/json"
                },
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            choices = result.get('choices', [])
            if choices:
                return choices[0].get('message', {}).get('content', 'No response generated')
            else:
                return 'No response generated'
                
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to LM Studio server. Please ensure LM Studio is running with API enabled."
        except requests.exceptions.Timeout:
            return "Error: Request to LM Studio server timed out. Please check your model and try again."
        except Exception as e:
            print(f"Error calling LM Studio API: {e}")
            return f"Error: {str(e)}"


class AIInterface:
    """Main interface for interacting with different AI providers."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)
        self.provider = self._initialize_provider()
    
    def _initialize_provider(self) -> AIProvider:
        """Initialize the appropriate AI provider based on config."""
        provider_type = self.config.get('ai_provider', 'openai').lower()
        
        if provider_type == 'gemini':
            api_key = self.config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("Gemini API key not found in config or environment")
            model = self.config.get('gemini_model', 'gemini-pro')
            return GeminiProvider(api_key, model)
        
        elif provider_type == 'openai':
            api_key = self.config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not found in config or environment")
            model = self.config.get('openai_model', 'gpt-3.5-turbo')
            return OpenAIProvider(api_key, model)
        
        elif provider_type == 'ollama':
            model = self.config.get('ollama_model', 'llama2')
            base_url = self.config.get('ollama_url', 'http://localhost:11434/api/generate')
            return OllamaProvider(model, base_url)
        
        elif provider_type == 'lm_studio':
            model = self.config.get('lm_studio_model', 'default')
            base_url = self.config.get('lm_studio_url', 'http://localhost:1234/v1/chat/completions')
            return LMStudioProvider(model, base_url)
        
        else:
            raise ValueError(f"Unsupported AI provider: {provider_type}")
    
    def generate_fusion_script(self, user_request: str, context: Optional[Dict] = None) -> str:
        """Generate a Fusion 360 script based on user request."""
        # Create a specific prompt for Fusion 360 script generation
        prompt = f"""
        Convert the following user request into a Fusion 360 Python script using the Fusion 360 API.
        The script should be complete, safe, and executable.
        
        User Request: {user_request}
        
        Provide only the Python code without additional explanation.
        """
        
        return self.provider.generate_response(prompt, context)
    
    def explain_fusion_operation(self, operation_description: str) -> str:
        """Generate an explanation of a Fusion 360 operation."""
        prompt = f"""
        Explain the following Fusion 360 operation in simple terms:
        
        {operation_description}
        """
        
        return self.provider.generate_response(prompt)
    
    def validate_and_fix_script(self, script: str, error: str) -> str:
        """Request the AI to fix a Fusion 360 script based on an error."""
        prompt = f"""
        The following Fusion 360 script produced an error. Please fix the script:
        
        Script:
        {script}
        
        Error:
        {error}
        """
        
        return self.provider.generate_response(prompt)


# Example usage
if __name__ == "__main__":
    # Initialize the AI interface
    ai_interface = AIInterface()
    
    # Example request
    user_request = "Create a cylinder with radius 5mm and height 10mm"
    script = ai_interface.generate_fusion_script(user_request)
    print("Generated script:")
    print(script)