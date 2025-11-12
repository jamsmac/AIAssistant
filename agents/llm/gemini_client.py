"""
Google Gemini API Client
Wrapper for Gemini models with error handling and retry logic
"""

import os
import time
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from google.api_core import exceptions


class GeminiClient:
    """Client for Google Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        genai.configure(api_key=self.api_key)
        
        # Model configurations
        self.models = {
            "gemini-pro": "gemini-1.5-pro-latest",
            "gemini-flash": "gemini-1.5-flash-latest"
        }
        
        # Cost per 1M tokens (as of Nov 2024)
        self.costs = {
            "gemini-pro": {"input": 1.25, "output": 5.00},
            "gemini-flash": {"input": 0.075, "output": 0.30}
        }
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gemini-flash",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to Gemini
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (gemini-pro, gemini-flash)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            **kwargs: Additional parameters
            
        Returns:
            Response dict with content, usage, and cost
            
        Raises:
            ValueError: If model is invalid
            Exception: If API request fails
        """
        if model not in self.models:
            raise ValueError(f"Invalid model: {model}. Choose from: {list(self.models.keys())}")
        
        model_id = self.models[model]
        
        try:
            # Initialize model
            gemini_model = genai.GenerativeModel(model_id)
            
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages(messages)
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            # Make API request with retry logic
            response = self._make_request_with_retry(
                model=gemini_model,
                messages=gemini_messages,
                generation_config=generation_config
            )
            
            # Extract response content
            content = response.text if response.text else ""
            
            # Estimate tokens (Gemini doesn't provide exact counts)
            input_tokens = self._estimate_tokens(gemini_messages)
            output_tokens = self._estimate_tokens(content)
            
            # Calculate cost
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
                "finish_reason": "stop"
            }
        
        except exceptions.ResourceExhausted as e:
            raise Exception(f"Rate limit exceeded: {str(e)}")
        except exceptions.GoogleAPIError as e:
            raise Exception(f"Gemini API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Gemini error: {str(e)}")
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert OpenAI-style messages to Gemini format
        
        Args:
            messages: List of message dicts
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _make_request_with_retry(
        self,
        model,
        messages: str,
        generation_config,
        max_retries: int = 3
    ):
        """Make API request with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return model.generate_content(
                    messages,
                    generation_config=generation_config
                )
            
            except exceptions.ResourceExhausted as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            
            except exceptions.GoogleAPIError as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                time.sleep(wait_time)
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation)
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
    
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
            "gemini-pro": 1000000,  # 1M tokens
            "gemini-flash": 1000000  # 1M tokens
        }
        
        return {
            "name": model,
            "id": self.models[model],
            "costs": self.costs[model],
            "max_tokens": 8192,
            "context_window": context_windows[model]
        }
    
    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gemini-flash",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Stream chat completion from Gemini
        
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
        gemini_model = genai.GenerativeModel(model_id)
        
        gemini_messages = self._convert_messages(messages)
        
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        response = gemini_model.generate_content(
            gemini_messages,
            generation_config=generation_config,
            stream=True
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text


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
