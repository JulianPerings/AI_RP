"""LLM client for OpenAI integration."""

from typing import List, Dict, Optional
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.core.logging import log


class LLMClient:
    """Async OpenAI client with retry logic and error handling."""

    def __init__(self):
        """Initialize the OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Additional OpenAI API parameters
            
        Returns:
            Generated text response
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs
            )
            
            content = response.choices[0].message.content
            
            # Log token usage
            if response.usage:
                log.info(
                    f"LLM tokens used - Prompt: {response.usage.prompt_tokens}, "
                    f"Completion: {response.usage.completion_tokens}, "
                    f"Total: {response.usage.total_tokens}"
                )
            
            return content
            
        except Exception as e:
            log.error(f"LLM completion error: {str(e)}")
            raise

    async def generate_with_system_prompt(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs
    ) -> str:
        """
        Generate completion with system and user messages.
        
        Args:
            system_prompt: System instruction
            user_message: User's message
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        return await self.chat_completion(messages, **kwargs)

    async def continue_conversation(
        self,
        conversation_history: List[Dict[str, str]],
        new_message: str,
        **kwargs
    ) -> str:
        """
        Continue an existing conversation.
        
        Args:
            conversation_history: Previous messages
            new_message: New user message
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        messages = conversation_history + [
            {"role": "user", "content": new_message}
        ]
        
        return await self.chat_completion(messages, **kwargs)


# Global LLM client instance
llm_client = LLMClient()
