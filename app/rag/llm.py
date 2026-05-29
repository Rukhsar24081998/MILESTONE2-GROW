"""Phase 3+ — Groq LLM integration for response generation.

Uses Groq API for ultra-fast LLM inference with open-source models.
Supports: llama-3.1-8b-instant, mixtral-8x7b-32768, llama-3.3-70b-versatile
"""

from __future__ import annotations

import os
from typing import Optional

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

from app.config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS


# System prompt for facts-only mutual fund Q&A
SYSTEM_PROMPT = """You are a factual mutual fund information assistant. You ONLY provide factual information from the provided context.

CRITICAL RULES:
1. Answer ONLY using information from the context provided below
2. DO NOT add any information, explanations, or details that are NOT in the context
3. Extract specific values, dates, and details directly from the context
4. Use the exact values from the context - do not modify or paraphrase numbers
5. If the answer is not in the context, say "I don't have that information in the available documents"
6. Never provide investment advice or recommendations
7. Never compare funds or suggest which is better
8. Never predict future returns or performance
9. Never add definitions or explanations unless they appear in the context

When answering:
- Include the fund name and specific value asked for
- If multiple related details are in the context about the same topic, you can mention them
- Keep answers to 1-3 sentences maximum
- Be direct and factual

GOOD answer format:
- "The expense ratio of HDFC Mid Cap Fund is 0.73%."
- "The NAV of HDFC Mid Cap Fund as of 25 May 2026 is ₹222.38."
- "The minimum SIP amount for HDFC Mid Cap Fund is ₹100."
- "The HDFC Mid Cap Fund Direct Growth is rated Very High risk."

BAD (DO NOT DO):
- Adding explanations not in context: "This is the annual fee..." ❌
- Adding definitions: "NAV (Net Asset Value) represents..." ❌
- Investment advice: "You should invest..." ❌
- Opinions: "This is a good fund" ❌
"""


class GroqLLM:
    """Groq LLM client for response generation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """Initialize Groq LLM client.
        
        Args:
            api_key: Groq API key (default: from config)
            model: Model name (default: from config)
            temperature: Sampling temperature (default: from config)
            max_tokens: Maximum tokens in response (default: from config)
        """
        if not HAS_GROQ:
            raise ImportError(
                "groq package not installed. Install with: pip install groq"
            )
        
        self.api_key = api_key or GROQ_API_KEY
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not set. Get your API key from https://console.groq.com"
            )
        
        self.model = model or LLM_MODEL
        self.temperature = temperature if temperature is not None else LLM_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens is not None else LLM_MAX_TOKENS
        
        self.client = Groq(api_key=self.api_key)
    
    def generate(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a response using Groq LLM.
        
        Args:
            query: User query
            context: Retrieved context from corpus
            system_prompt: Override default system prompt
            
        Returns:
            Generated response text
        """
        prompt = system_prompt or SYSTEM_PROMPT
        
        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}"
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            # Extract response text
            response_text = response.choices[0].message.content.strip()
            return response_text
            
        except Exception as e:
            # Fallback to error message
            return f"Error generating response: {str(e)}"
    
    def generate_with_retry(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 2,
    ) -> str:
        """Generate response with retry logic.
        
        Args:
            query: User query
            context: Retrieved context from corpus
            system_prompt: Override default system prompt
            max_retries: Maximum number of retries
            
        Returns:
            Generated response text
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return self.generate(query, context, system_prompt)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    import time
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        return f"Error generating response after {max_retries + 1} attempts: {str(last_error)}"


def get_llm() -> GroqLLM:
    """Get Groq LLM instance (singleton pattern)."""
    return GroqLLM()


def generate_answer_with_llm(
    query: str,
    context: str,
    citation_url: str,
    footer_date: str,
) -> dict:
    """Generate answer using Groq LLM.
    
    This replaces the template-based generate_answer in Phase 3.
    Use this when Groq API is available.
    
    Args:
        query: User query
        context: Retrieved context from corpus
        citation_url: Source URL for citation
        footer_date: Footer date string
        
    Returns:
        Answer response dict
    """
    llm = get_llm()
    answer_text = llm.generate_with_retry(query, context)
    
    return {
        "type": "answer",
        "text": answer_text,
        "citation_url": citation_url,
        "footer": footer_date,
        "refused": False,
    }
