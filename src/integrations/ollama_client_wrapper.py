"""Ollama client wrapper for async operations."""
import os
from typing import Optional, Dict, Any
from ollama import Client, ResponseError, RequestError
import asyncio
from functools import partial

from ..utils.config import settings
from ..utils.logger import api_logger


class OllamaClient:
    """Wrapper for Ollama client with async support."""
    
    def __init__(self, host: Optional[str] = None):
        self.host = host or settings.ollama_host
        self.client: Optional[Client] = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize Ollama client connection."""
        try:
            if not self.host:
                api_logger.warning("OLLAMA_HOST not configured")
                return False
            
            # Replace localhost with 127.0.0.1 for consistency
            host = self.host.replace('localhost', '127.0.0.1')
            self.client = Client(host=host)
            
            # Test connection
            try:
                self.client.list()  # List available models
                self._initialized = True
                api_logger.info(f"Ollama client initialized: {host}")
                return True
            except Exception as e:
                api_logger.warning(f"Ollama connection test failed: {str(e)}")
                return False
                
        except Exception as e:
            api_logger.error(f"Failed to initialize Ollama client: {str(e)}")
            return False
    
    async def analyze_medical_data(self, data_summary: str, model: str = "mistral") -> Dict[str, Any]:
        """
        Analyze medical data using Ollama.
        
        Args:
            data_summary: Summary of medical data to analyze
            model: Model name to use
            
        Returns:
            Analysis results dictionary
        """
        if not self._initialized or not self.client:
            return self._fallback_analysis()
        
        system_prompt = (
            "You are a specialized Epidemiological Decision Support Agent. "
            "Analyze the following patient data and provide: "
            "1. Risk score (0-10), 2. Symptom patterns, 3. Geographic clusters, "
            "4. Recommended actions, 5. Confidence level (0-1). "
            "Respond in JSON format."
        )
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self.client.chat,
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"DATA:\n{data_summary}"}
                    ],
                    options={"temperature": 0.1, "num_ctx": 4096}
                )
            )
            
            content = response.get('message', {}).get('content', '')
            
            # Try to parse JSON from response
            import json
            try:
                # Extract JSON from response if wrapped in text
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = content[start:end]
                    parsed = json.loads(json_str)
                    return parsed
            except:
                pass
            
            # Fallback: parse text response
            return {
                "risk_score": 5.0,
                "symptom_patterns": ["Pattern analysis from LLM"],
                "geographic_clusters": ["Multiple locations identified"],
                "recommended_actions": ["Continue monitoring", "Collect more data"],
                "confidence": 0.7,
                "raw_response": content
            }
            
        except ResponseError as e:
            api_logger.error(f"Ollama response error: {str(e)}")
            return self._fallback_analysis()
        except RequestError as e:
            api_logger.error(f"Ollama request error: {str(e)}")
            return self._fallback_analysis()
        except Exception as e:
            api_logger.error(f"Ollama analysis error: {str(e)}")
            return self._fallback_analysis()
    
    async def _generate_async(self, model: str, prompt: str) -> str:
        """Async wrapper for Ollama generate."""
        if not self._initialized or not self.client:
            return "Ollama not available"
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self.client.generate,
                    model=model,
                    prompt=prompt
                )
            )
            return response.get('response', '')
        except Exception as e:
            api_logger.error(f"Ollama generate error: {str(e)}")
            return f"Error: {str(e)}"
    
    def _fallback_analysis(self) -> Dict[str, Any]:
        """Fallback analysis when Ollama is unavailable."""
        return {
            "risk_score": 5.0,
            "symptom_patterns": ["Pattern analysis unavailable"],
            "geographic_clusters": ["Multiple locations"],
            "recommended_actions": ["Continue monitoring", "Collect more data"],
            "confidence": 0.5
        }

