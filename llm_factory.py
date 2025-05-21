"""
LLM Factory for generating responses with different models.
Can be used as an alternative to direct calls to generate_llm_response.
"""

import os
import json
from typing import Dict, Any, Optional, List, Union
from config import LLM_CONFIG
from llm_interface import (
    _call_claude_api, 
    _call_chatgpt_api, 
    _call_ollama_api,
    _call_groq_api
)

class LLMFactory:
    """Factory class for creating and using different LLM providers."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the LLM factory.
        
        Args:
            config: Optional configuration override (defaults to LLM_CONFIG)
        """
        self.config = config or LLM_CONFIG
        self.default_provider = self.config.get("provider", "ollama")
    
    def get_response(
        self, 
        prompt: str, 
        provider: str = None, 
        model: str = None, 
        max_tokens: int = None
    ) -> str:
        """
        Get a response from the specified LLM provider.
        
        Args:
            prompt: The prompt to send to the LLM
            provider: Optional provider override (claude, chatgpt, ollama)
            model: Optional model override
            max_tokens: Optional max tokens override
            
        Returns:
            The response text from the LLM
        """
        # Use defaults if not specified
        provider = provider or self.default_provider
        
        if provider.lower() == "claude":
            return self._get_claude_response(prompt, model, max_tokens)
        elif provider.lower() == "chatgpt":
            return self._get_chatgpt_response(prompt, model, max_tokens)
        elif provider.lower() == "ollama":
            return self._get_ollama_response(prompt, model, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _get_claude_response(self, prompt: str, model: str = None, max_tokens: int = None) -> str:
        """Get a response from Claude API."""
        config = self.config.get("claude", {})
        if model:
            config["model"] = model
        if max_tokens:
            config["max_tokens"] = max_tokens
        
        # Store original config
        orig_config = dict(self.config.get("claude", {}))
        
        # Update config temporarily
        self.config["claude"] = config
        
        # Get response
        response = _call_claude_api(prompt)
        
        # Restore original config
        self.config["claude"] = orig_config
        
        return response
    
    def _get_chatgpt_response(self, prompt: str, model: str = None, max_tokens: int = None) -> str:
        """Get a response from ChatGPT API."""
        config = self.config.get("chatgpt", {})
        if model:
            config["model"] = model
        if max_tokens:
            config["max_tokens"] = max_tokens
        
        # Store original config
        orig_config = dict(self.config.get("chatgpt", {}))
        
        # Update config temporarily
        self.config["chatgpt"] = config
        
        # Get response
        response = _call_chatgpt_api(prompt)
        
        # Restore original config
        self.config["chatgpt"] = orig_config
        
        return response
    
    def _get_ollama_response(self, prompt: str, model: str = None, max_tokens: int = None) -> str:
        """Get a response from Ollama API."""
        config = self.config.get("ollama", {})
        if model:
            config["model"] = model
        if max_tokens:
            config["max_tokens"] = max_tokens
        
        # Store original config
        orig_config = dict(self.config.get("ollama", {}))
        
        # Update config temporarily
        self.config["ollama"] = config
        
        # Get response
        response = _call_ollama_api(prompt)
        
        # Restore original config
        self.config["ollama"] = orig_config
        
        return response
    
    def _get_groq_response(self, prompt: str, model: str = None, max_tokens: int = None) -> str:
        """Get a response from Groq API."""
        config = self.config.get("groq", {})
        if model:
            config["model"] = model
        if max_tokens:
            config["max_tokens"] = max_tokens
        
        # Store original config
        orig_config = dict(self.config.get("groq", {}))
        
        # Update config temporarily
        self.config["groq"] = config
        
        # Get response
        response = _call_groq_api(prompt)
        
        # Restore original config
        self.config["groq"] = orig_config
        
        return response
    
    def set_default_provider(self, provider: str) -> None:
        """
        Set the default LLM provider.
        
        Args:
            provider: The provider to set as default ("claude", "chatgpt", "ollama", or "groq")
        """
        if provider not in ["claude", "chatgpt", "ollama", "groq"]:
            raise ValueError(f"Invalid provider: {provider}. Choose from: claude, chatgpt, ollama, groq")
        
        self.default_provider = provider
    
    def get_available_models(self, provider: str = None) -> List[str]:
        """
        Get a list of available models for the specified provider.
        
        Args:
            provider: Optional provider (defaults to default_provider)
            
        Returns:
            List of available model names
        """
        provider = provider or self.default_provider
        
        if provider == "ollama":
            # For ollama, we need to call the API to get available models
            try:
                import requests
                base_url = self.config.get("ollama", {}).get("base_url", "http://localhost:11434")
                response = requests.get(f"{base_url}/api/tags")
                
                if response.status_code == 200:
                    models = [model.get("name") for model in response.json().get("models", [])]
                    return models
                return ["llama3", "mistral", "phi"]  # Default fallback
            except:
                return ["llama3", "mistral", "phi"]  # Default fallback
        
        elif provider == "claude":
            return ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
        
        elif provider == "chatgpt":
            return ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        
        elif provider == "groq":
            return ["llama3-70b-8192"]
        
        return []

# Example usage
if __name__ == "__main__":
    llm = LLMFactory()
    print(f"Default provider: {llm.default_provider}")
    
    # Test with default provider
    response = llm.get_response("What is ontology in computer science?")
    print(f"Response: {response[:100]}...")
    
    # Test with specific provider
    response = llm.get_response("What is ontology in computer science?", provider="ollama")
    print(f"Ollama response: {response[:100]}...")