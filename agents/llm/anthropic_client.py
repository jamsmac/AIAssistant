"""
Anthropic (Claude) API Client
Wrapper for Claude models with error handling and retry logic
"""

import os
import time
from typing import Optional, Dict, Any, List
from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError


class AnthropicClient:
    """Client for Anthropic Claude API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Anthropic client
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.client = Anthropic(api_key=self.api_key)
        
        # Model configurations
        self.models = {
            "haiku": "claude-3-haiku-20240307",
            "sonnet": "claude-3-5-sonnet-20241022",
            "opus": "claude-3-opus-20240229"
        }
        
        # Cost per 1M tokens (as of Nov 2024)
        self.costs = {
            "haiku": {"input": 0.25, "output": 1.25},
            "sonnet": {"input": 3.00, "output": 15.00},
            "opus": {"input": 15.00, "output": 75.00}
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
        Send chat completion request to Claude
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (haiku, sonnet, opus)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            system: System prompt
            **kwargs: Additional parameters
            
        Returns:
            Response dict with content, usage, and cost
            
        Raises:
            ValueError: If model is invalid
            APIError: If API request fails
        """
        if model not in self.models:
            raise ValueError(f"Invalid model: {model}. Choose from: {list(self.models.keys())}")
        
        model_id = self.models[model]
        
        try:
            # Make API request with retry logic
            response = self._make_request_with_retry(
                messages=messages,
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                **kwargs
            )
            
            # Extract response content
            content = response.content[0].text if response.content else ""
            
            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self._calculate_cost(model, input_tokens, output_tokens)
            
            return {
                "content": content,
                "model": model_id,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                },
                "cost": cost,
                "finish_reason": response.stop_reason
            }
        
        except RateLimitError as e:
            raise APIError(f"Rate limit exceeded: {str(e)}")
        except APIConnectionError as e:
            raise APIError(f"Connection error: {str(e)}")
        except Exception as e:
            raise APIError(f"Anthropic API error: {str(e)}")
    
    def _make_request_with_retry(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
        system: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ):
        """Make API request with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                request_params = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages,
                    **kwargs
                }
                
                if system:
                    request_params["system"] = system
                
                return self.client.messages.create(**request_params)
            
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise
                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            
            except APIConnectionError as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                time.sleep(wait_time)
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for API request
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        costs = self.costs[model]
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return round(input_cost + output_cost, 6)
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a model
        
        Args:
            model: Model name
            
        Returns:
            Dict with model info
        """
        if model not in self.models:
            raise ValueError(f"Invalid model: {model}")
        
        return {
            "name": model,
            "id": self.models[model],
            "costs": self.costs[model],
            "max_tokens": 4096 if model == "haiku" else 8192,
            "context_window": 200000  # All Claude 3 models have 200k context
        }
    
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
        Stream chat completion from Claude
        
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
        if model not in self.models:
            raise ValueError(f"Invalid model: {model}")
        
        model_id = self.models[model]
        
        request_params = {
            "model": model_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
            **kwargs
        }
        
        if system:
            request_params["system"] = system
        
        with self.client.messages.stream(**request_params) as stream:
            for text in stream.text_stream:
                yield text


# Convenience functions
def create_message(role: str, content: str) -> Dict[str, str]:
    """Create a message dict"""
    return {"role": role, "content": content}


def create_user_message(content: str) -> Dict[str, str]:
    """Create a user message"""
    return create_message("user", content)


def create_assistant_message(content: str) -> Dict[str, str]:
    """Create an assistant message"""
    return create_message("assistant", content)
