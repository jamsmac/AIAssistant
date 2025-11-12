"""
LLM Manager
Unified interface for all LLM providers with intelligent routing
"""

from typing import Optional, Dict, Any, List, Literal
from enum import Enum

from .anthropic_client import AnthropicClient
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient


class Provider(str, Enum):
    """LLM Providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


class LLMManager:
    """
    Unified LLM Manager
    Provides a single interface to all LLM providers
    """
    
    def __init__(
        self,
        anthropic_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        gemini_key: Optional[str] = None
    ):
        """
        Initialize LLM Manager
        
        Args:
            anthropic_key: Anthropic API key
            openai_key: OpenAI API key
            gemini_key: Gemini API key
        """
        self.clients = {}
        
        # Initialize available clients
        try:
            self.clients[Provider.ANTHROPIC] = AnthropicClient(anthropic_key)
        except ValueError:
            pass
        
        try:
            self.clients[Provider.OPENAI] = OpenAIClient(openai_key)
        except ValueError:
            pass
        
        try:
            self.clients[Provider.GEMINI] = GeminiClient(gemini_key)
        except ValueError:
            pass
        
        if not self.clients:
            raise ValueError("At least one LLM provider API key must be set")
        
        # Model mapping to providers
        self.model_providers = {
            # Anthropic models
            "haiku": Provider.ANTHROPIC,
            "sonnet": Provider.ANTHROPIC,
            "opus": Provider.ANTHROPIC,
            
            # OpenAI models
            "gpt-4": Provider.OPENAI,
            "gpt-4-turbo": Provider.OPENAI,
            "gpt-3.5-turbo": Provider.OPENAI,
            
            # Gemini models
            "gemini-pro": Provider.GEMINI,
            "gemini-flash": Provider.GEMINI
        }
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "sonnet",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to appropriate provider
        
        Args:
            messages: List of message dicts
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system: System prompt (for Anthropic)
            **kwargs: Additional parameters
            
        Returns:
            Response dict with content, usage, and cost
            
        Raises:
            ValueError: If model is invalid or provider not available
        """
        provider = self._get_provider_for_model(model)
        client = self.clients.get(provider)
        
        if not client:
            raise ValueError(f"Provider {provider} not available. Check API key.")
        
        # Add system message to messages for OpenAI/Gemini
        if system and provider != Provider.ANTHROPIC:
            messages = [{"role": "system", "content": system}] + messages
        
        # Make request
        if provider == Provider.ANTHROPIC:
            return client.chat(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                **kwargs
            )
        else:
            return client.chat(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
    
    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "sonnet",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs
    ):
        """
        Stream chat completion from appropriate provider
        
        Args:
            messages: List of message dicts
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system: System prompt
            **kwargs: Additional parameters
            
        Yields:
            Content chunks as they arrive
        """
        provider = self._get_provider_for_model(model)
        client = self.clients.get(provider)
        
        if not client:
            raise ValueError(f"Provider {provider} not available")
        
        # Add system message for OpenAI/Gemini
        if system and provider != Provider.ANTHROPIC:
            messages = [{"role": "system", "content": system}] + messages
        
        # Stream request
        if provider == Provider.ANTHROPIC:
            yield from client.stream_chat(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                **kwargs
            )
        else:
            yield from client.stream_chat(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a model
        
        Args:
            model: Model name
            
        Returns:
            Dict with model info including provider
        """
        provider = self._get_provider_for_model(model)
        client = self.clients.get(provider)
        
        if not client:
            raise ValueError(f"Provider {provider} not available")
        
        info = client.get_model_info(model)
        info["provider"] = provider.value
        return info
    
    def list_available_models(self) -> List[str]:
        """
        List all available models
        
        Returns:
            List of model names
        """
        available = []
        
        for model, provider in self.model_providers.items():
            if provider in self.clients:
                available.append(model)
        
        return sorted(available)
    
    def get_cheapest_model(self) -> str:
        """
        Get the cheapest available model
        
        Returns:
            Model name of cheapest model
        """
        available = self.list_available_models()
        
        if not available:
            raise ValueError("No models available")
        
        # Priority: gemini-flash > haiku > gpt-3.5-turbo
        for model in ["gemini-flash", "haiku", "gpt-3.5-turbo"]:
            if model in available:
                return model
        
        return available[0]
    
    def get_best_model(self) -> str:
        """
        Get the best available model (highest quality)
        
        Returns:
            Model name of best model
        """
        available = self.list_available_models()
        
        if not available:
            raise ValueError("No models available")
        
        # Priority: opus > gpt-4 > sonnet > gpt-4-turbo
        for model in ["opus", "gpt-4", "sonnet", "gpt-4-turbo"]:
            if model in available:
                return model
        
        return available[0]
    
    def _get_provider_for_model(self, model: str) -> Provider:
        """Get provider for a model"""
        provider = self.model_providers.get(model)
        
        if not provider:
            raise ValueError(
                f"Invalid model: {model}. "
                f"Available: {list(self.model_providers.keys())}"
            )
        
        return provider
    
    def calculate_total_cost(self, responses: List[Dict[str, Any]]) -> float:
        """
        Calculate total cost from multiple responses
        
        Args:
            responses: List of response dicts from chat()
            
        Returns:
            Total cost in USD
        """
        return sum(r.get("cost", 0) for r in responses)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about available providers and models
        
        Returns:
            Dict with statistics
        """
        return {
            "providers": [p.value for p in self.clients.keys()],
            "total_models": len(self.list_available_models()),
            "available_models": self.list_available_models(),
            "cheapest_model": self.get_cheapest_model(),
            "best_model": self.get_best_model()
        }


# Convenience function
def create_llm_manager(**kwargs) -> LLMManager:
    """Create LLM Manager with API keys from environment"""
    return LLMManager(**kwargs)
