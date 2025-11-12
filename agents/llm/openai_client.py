"""
OpenAI API Client
Wrapper for GPT models with error handling and retry logic
"""

import os
import time
from typing import Optional, Dict, Any, List
from openai import OpenAI, APIError, RateLimitError, APIConnectionError


class OpenAIClient:
    """Client for OpenAI GPT API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Model configurations
        self.models = {
            "gpt-4": "gpt-4-0125-preview",
            "gpt-4-turbo": "gpt-4-turbo-preview",
            "gpt-3.5-turbo": "gpt-3.5-turbo-0125"
        }
        
        # Cost per 1M tokens (as of Nov 2024)
        self.costs = {
            "gpt-4": {"input": 10.00, "output": 30.00},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50}
        }
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4-turbo",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to GPT
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (gpt-4, gpt-4-turbo, gpt-3.5-turbo)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
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
                **kwargs
            )
            
            # Extract response content
            content = response.choices[0].message.content if response.choices else ""
            
            # Calculate cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self._calculate_cost(model, input_tokens, output_tokens)
            
            return {
                "content": content,
                "model": model_id,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "cost": cost,
                "finish_reason": response.choices[0].finish_reason
            }
        
        except RateLimitError as e:
            raise APIError(f"Rate limit exceeded: {str(e)}")
        except APIConnectionError as e:
            raise APIError(f"Connection error: {str(e)}")
        except Exception as e:
            raise APIError(f"OpenAI API error: {str(e)}")
    
    def _make_request_with_retry(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
        max_retries: int = 3,
        **kwargs
    ):
        """Make API request with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
            
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise
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
        
        context_windows = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 16385
        }
        
        return {
            "name": model,
            "id": self.models[model],
            "costs": self.costs[model],
            "max_tokens": 4096,
            "context_window": context_windows[model]
        }
    
    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4-turbo",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Stream chat completion from GPT
        
        Args:
            messages: List of message dicts
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Yields:
            Content chunks as they arrive
        """
        if model not in self.models:
            raise ValueError(f"Invalid model: {model}")
        
        model_id = self.models[model]
        
        stream = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            **kwargs
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


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


def create_system_message(content: str) -> Dict[str, str]:
    """Create a system message"""
    return create_message("system", content)
