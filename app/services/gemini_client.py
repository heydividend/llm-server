"""
Shared Gemini Client Service for Harvey AI
Provides unified interface to Google's Gemini 2.5 Pro API with rate limiting,
caching, error handling, and comprehensive logging.
"""

import os
import time
import hashlib
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger("gemini_client")

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig, HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("google-generativeai not installed - Gemini features disabled")
    GEMINI_AVAILABLE = False
    genai = None
    GenerationConfig = None
    HarmCategory = None
    HarmBlockThreshold = None


class RateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds (default 60 for 1 minute)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        
    def can_proceed(self) -> bool:
        """Check if request can proceed without hitting rate limit."""
        now = time.time()
        
        # Remove requests outside the time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        return len(self.requests) < self.max_requests
    
    def add_request(self):
        """Record a new request."""
        self.requests.append(time.time())
    
    def wait_time(self) -> float:
        """Calculate seconds to wait before next request."""
        if self.can_proceed():
            return 0.0
        
        # Time until oldest request expires
        oldest = self.requests[0]
        wait_until = oldest + self.time_window
        return max(0.0, wait_until - time.time())


class ResponseCache:
    """Simple in-memory cache for API responses."""
    
    def __init__(self, max_age_seconds: int = 3600):
        """
        Initialize response cache.
        
        Args:
            max_age_seconds: Maximum age of cached responses (default 1 hour)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_age = max_age_seconds
    
    def _generate_key(self, prompt: str, config: Dict[str, Any]) -> str:
        """Generate cache key from prompt and config."""
        key_data = f"{prompt}:{json.dumps(config, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get(self, prompt: str, config: Dict[str, Any]) -> Optional[str]:
        """Retrieve cached response if available and not expired."""
        key = self._generate_key(prompt, config)
        
        if key in self.cache:
            cached = self.cache[key]
            age = time.time() - cached['timestamp']
            
            if age < self.max_age:
                logger.debug(f"Cache hit (age: {age:.1f}s)")
                return cached['response']
            else:
                # Expired, remove from cache
                del self.cache[key]
                logger.debug("Cache expired, removed")
        
        return None
    
    def set(self, prompt: str, config: Dict[str, Any], response: str):
        """Store response in cache."""
        key = self._generate_key(prompt, config)
        self.cache[key] = {
            'response': response,
            'timestamp': time.time()
        }
        logger.debug(f"Cached response (total cached: {len(self.cache)})")
    
    def clear(self):
        """Clear all cached responses."""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared {count} cached responses")


class GeminiClient:
    """
    Unified client for Google Gemini 2.5 Pro API.
    
    Features:
    - Rate limiting (60 requests/minute default)
    - Response caching
    - Exponential backoff retry logic
    - Comprehensive error handling
    - Detailed logging of all API calls
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash-exp",
        max_requests_per_minute: int = 60,
        cache_enabled: bool = True,
        cache_max_age: int = 3600
    ):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model_name: Model to use (default: gemini-2.0-flash-exp)
            max_requests_per_minute: Rate limit (default: 60)
            cache_enabled: Enable response caching (default: True)
            cache_max_age: Cache TTL in seconds (default: 3600)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai>=0.8.0"
            )
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        
        # Rate limiting and caching
        self.rate_limiter = RateLimiter(max_requests_per_minute, 60)
        self.cache = ResponseCache(cache_max_age) if cache_enabled else None
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'rate_limit_waits': 0,
            'errors': 0,
            'retries': 0
        }
        
        logger.info(f"Gemini client initialized (model: {model_name}, rate limit: {max_requests_per_minute}/min)")
    
    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.95,
        top_k: int = 40,
        use_cache: bool = True,
        retry_attempts: int = 3,
        retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generate text using Gemini API with retry logic.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling parameter
            use_cache: Use cached response if available
            retry_attempts: Number of retry attempts on failure
            retry_delay: Initial delay between retries (exponential backoff)
        
        Returns:
            Dict with:
                - text: Generated text
                - cached: Whether response was cached
                - model: Model used
                - finish_reason: Reason generation finished
                - usage: Token usage statistics
                - latency_ms: Request latency in milliseconds
        """
        config = {
            'temperature': temperature,
            'max_tokens': max_tokens,
            'top_p': top_p,
            'top_k': top_k
        }
        
        # Check cache first
        if use_cache and self.cache:
            cached_response = self.cache.get(prompt, config)
            if cached_response:
                self.stats['cache_hits'] += 1
                return {
                    'text': cached_response,
                    'cached': True,
                    'model': self.model_name,
                    'finish_reason': 'CACHED',
                    'usage': {},
                    'latency_ms': 0
                }
            self.stats['cache_misses'] += 1
        
        # Rate limiting
        wait_time = self.rate_limiter.wait_time()
        if wait_time > 0:
            logger.warning(f"Rate limit reached, waiting {wait_time:.2f}s")
            self.stats['rate_limit_waits'] += 1
            time.sleep(wait_time)
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(retry_attempts):
            try:
                # Record request
                self.rate_limiter.add_request()
                self.stats['total_requests'] += 1
                
                start_time = time.time()
                
                # Configure generation
                generation_config = GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=top_p,
                    top_k=top_k
                )
                
                # Safety settings - allow most content for financial analysis
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
                
                # Generate response
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Extract text
                if not response.candidates:
                    raise ValueError("No candidates in response")
                
                text = response.text
                finish_reason = str(response.candidates[0].finish_reason) if response.candidates else "UNKNOWN"
                
                # Usage stats
                usage = {}
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    usage = {
                        'prompt_tokens': response.usage_metadata.prompt_token_count,
                        'completion_tokens': response.usage_metadata.candidates_token_count,
                        'total_tokens': response.usage_metadata.total_token_count
                    }
                
                # Cache successful response
                if use_cache and self.cache:
                    self.cache.set(prompt, config, text)
                
                logger.info(f"Generated {len(text)} chars in {latency_ms}ms (tokens: {usage.get('total_tokens', 'N/A')})")
                
                return {
                    'text': text,
                    'cached': False,
                    'model': self.model_name,
                    'finish_reason': finish_reason,
                    'usage': usage,
                    'latency_ms': latency_ms
                }
                
            except Exception as e:
                last_error = e
                self.stats['errors'] += 1
                
                if attempt < retry_attempts - 1:
                    self.stats['retries'] += 1
                    delay = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {retry_attempts} attempts failed: {e}")
        
        # All retries failed
        raise Exception(f"Failed to generate text after {retry_attempts} attempts: {last_error}")
    
    def generate_batch(
        self,
        prompts: List[str],
        batch_size: int = 5,
        delay_between_batches: float = 1.0,
        **generation_kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generate text for multiple prompts in batches.
        
        Args:
            prompts: List of prompts
            batch_size: Number of concurrent requests per batch
            delay_between_batches: Delay between batches in seconds
            **generation_kwargs: Passed to generate_text()
        
        Returns:
            List of generation results
        """
        results = []
        total_batches = (len(prompts) + batch_size - 1) // batch_size
        
        logger.info(f"Generating {len(prompts)} responses in {total_batches} batches")
        
        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} prompts)")
            
            for prompt in batch:
                try:
                    result = self.generate_text(prompt, **generation_kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to generate for prompt: {e}")
                    results.append({
                        'text': '',
                        'error': str(e),
                        'cached': False,
                        'model': self.model_name
                    })
            
            # Delay between batches to avoid rate limits
            if i + batch_size < len(prompts):
                time.sleep(delay_between_batches)
        
        logger.info(f"Batch generation complete: {len(results)} responses")
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get client usage statistics."""
        return {
            **self.stats,
            'cache_size': len(self.cache.cache) if self.cache else 0,
            'cache_hit_rate': (
                self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])
                if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0
                else 0.0
            )
        }
    
    def reset_statistics(self):
        """Reset usage statistics."""
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'rate_limit_waits': 0,
            'errors': 0,
            'retries': 0
        }
        logger.info("Statistics reset")
    
    def clear_cache(self):
        """Clear response cache."""
        if self.cache:
            self.cache.clear()


# Global shared instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create the global Gemini client instance."""
    global _gemini_client
    
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    
    return _gemini_client
