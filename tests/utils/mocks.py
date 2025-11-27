"""
Common mocks for external services in tests.

This module provides reusable mocks for:
- OpenAI API
- Ollama API
- ChromaDB
- Redis
- External HTTP APIs
"""
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, Optional, List
import json
from datetime import datetime


class MockOpenAIClient:
    """Mock OpenAI API client."""
    
    def __init__(self):
        self.chat = Mock()
        self.chat.completions = Mock()
        self.chat.completions.create = AsyncMock(
            return_value=self._create_mock_response()
        )
        self.models = Mock()
        self.models.list = AsyncMock(return_value=Mock(data=[]))
    
    def _create_mock_response(self, content: str = "Mocked analysis response"):
        """Create a mock chat completion response."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = content
        mock_response.usage = Mock(total_tokens=100, prompt_tokens=50, completion_tokens=50)
        mock_response.id = "mock-response-id"
        mock_response.model = "gpt-4"
        mock_response.created = int(datetime.now().timestamp())
        return mock_response
    
    def set_response(self, content: str):
        """Set a custom response content."""
        self.chat.completions.create = AsyncMock(
            return_value=self._create_mock_response(content)
        )


class MockOllamaClient:
    """Mock Ollama API client."""
    
    def __init__(self):
        self.initialize = Mock(return_value=True)
        self.analyze_medical_data = AsyncMock(
            return_value={
                "risk_score": 7.5,
                "symptom_patterns": ["fever", "cough", "headache"],
                "geographic_clusters": ["Mumbai", "Delhi"],
                "recommended_actions": [
                    "Monitor closely",
                    "Increase testing capacity",
                    "Implement contact tracing"
                ],
                "confidence": 0.85
            }
        )
        self.generate_response = AsyncMock(
            return_value="Mocked agentic analysis response"
        )
        self.generate_analysis = AsyncMock(
            return_value="Comprehensive epidemic analysis report"
        )
    
    def set_analysis_response(self, response: Dict[str, Any]):
        """Set custom analysis response."""
        self.analyze_medical_data = AsyncMock(return_value=response)


class MockChromaDBClient:
    """Mock ChromaDB client."""
    
    def __init__(self):
        self.initialize = Mock(return_value=True)
        self.collection_name = "test_collection"
        self.documents = {}
        
        # Mock methods
        self.add_documents = AsyncMock(return_value=["doc_id_1", "doc_id_2"])
        self.query = AsyncMock(return_value={
            "ids": [["doc_id_1"]],
            "documents": [["Sample document about epidemic"]],
            "distances": [[0.5]],
            "metadatas": [[{"source": "test"}]]
        })
        self.delete = AsyncMock(return_value=True)
        self.update = AsyncMock(return_value=True)
        self.get = AsyncMock(return_value={
            "ids": ["doc_id_1"],
            "documents": ["Sample document"],
            "metadatas": [{"source": "test"}]
        })
    
    def set_query_result(self, result: Dict[str, Any]):
        """Set custom query result."""
        self.query = AsyncMock(return_value=result)


class MockRedisClient:
    """Mock Redis client with in-memory storage."""
    
    def __init__(self):
        self._storage: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        
        # Mock async methods
        self.get = AsyncMock(side_effect=self._get)
        self.set = AsyncMock(side_effect=self._set)
        self.delete = AsyncMock(side_effect=self._delete)
        self.exists = AsyncMock(side_effect=self._exists)
        self.expire = AsyncMock(side_effect=self._expire)
        self.ttl = AsyncMock(side_effect=self._ttl)
        self.ping = AsyncMock(return_value=True)
        self.flushall = AsyncMock(side_effect=self._flushall)
        
        # JSON operations
        self.json_set = AsyncMock(side_effect=self._json_set)
        self.json_get = AsyncMock(side_effect=self._json_get)
        
        # Hash operations
        self.hset = AsyncMock(side_effect=self._hset)
        self.hget = AsyncMock(side_effect=self._hget)
        self.hgetall = AsyncMock(side_effect=self._hgetall)
        
        # List operations
        self.lpush = AsyncMock(side_effect=self._lpush)
        self.rpush = AsyncMock(side_effect=self._rpush)
        self.lrange = AsyncMock(side_effect=self._lrange)
        
        # Set operations
        self.sadd = AsyncMock(side_effect=self._sadd)
        self.smembers = AsyncMock(side_effect=self._smembers)
    
    async def _get(self, key: str) -> Optional[str]:
        """Get value from storage."""
        if key in self._expiry and self._expiry[key] < datetime.now().timestamp():
            del self._storage[key]
            del self._expiry[key]
            return None
        return self._storage.get(key)
    
    async def _set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set value in storage."""
        self._storage[key] = str(value)
        if ex:
            self._expiry[key] = datetime.now().timestamp() + ex
        return True
    
    async def _delete(self, *keys: str) -> int:
        """Delete keys from storage."""
        count = 0
        for key in keys:
            if key in self._storage:
                del self._storage[key]
                if key in self._expiry:
                    del self._expiry[key]
                count += 1
        return count
    
    async def _exists(self, *keys: str) -> int:
        """Check if keys exist."""
        return sum(1 for key in keys if key in self._storage)
    
    async def _expire(self, key: str, time: int) -> bool:
        """Set expiry for key."""
        if key in self._storage:
            self._expiry[key] = datetime.now().timestamp() + time
            return True
        return False
    
    async def _ttl(self, key: str) -> int:
        """Get time to live for key."""
        if key not in self._storage:
            return -2
        if key in self._expiry:
            ttl = int(self._expiry[key] - datetime.now().timestamp())
            return max(0, ttl) if ttl > 0 else -1
        return -1
    
    async def _flushall(self) -> bool:
        """Clear all data."""
        self._storage.clear()
        self._expiry.clear()
        return True
    
    async def _json_set(self, key: str, path: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set JSON value."""
        return await self._set(key, json.dumps(value), ex=ex)
    
    async def _json_get(self, key: str, path: str = "$") -> Optional[Any]:
        """Get JSON value."""
        value = await self._get(key)
        if value:
            return json.loads(value)
        return None
    
    async def _hset(self, name: str, key: str, value: str) -> int:
        """Set hash field."""
        if name not in self._storage:
            self._storage[name] = {}
        hash_data = json.loads(self._storage.get(name, "{}")) if isinstance(self._storage.get(name), str) else self._storage.get(name, {})
        hash_data[key] = value
        self._storage[name] = json.dumps(hash_data)
        return 1
    
    async def _hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field."""
        hash_data = self._storage.get(name, "{}")
        if isinstance(hash_data, str):
            hash_data = json.loads(hash_data)
        return hash_data.get(key)
    
    async def _hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields."""
        hash_data = self._storage.get(name, "{}")
        if isinstance(hash_data, str):
            hash_data = json.loads(hash_data)
        return hash_data
    
    async def _lpush(self, name: str, *values: str) -> int:
        """Push values to left of list."""
        if name not in self._storage:
            self._storage[name] = json.dumps([])
        list_data = json.loads(self._storage[name])
        list_data = list(values) + list_data
        self._storage[name] = json.dumps(list_data)
        return len(values)
    
    async def _rpush(self, name: str, *values: str) -> int:
        """Push values to right of list."""
        if name not in self._storage:
            self._storage[name] = json.dumps([])
        list_data = json.loads(self._storage[name])
        list_data.extend(values)
        self._storage[name] = json.dumps(list_data)
        return len(values)
    
    async def _lrange(self, name: str, start: int, end: int) -> List[str]:
        """Get range of list."""
        list_data = self._storage.get(name, "[]")
        if isinstance(list_data, str):
            list_data = json.loads(list_data)
        return list_data[start:end+1] if end >= 0 else list_data[start:]
    
    async def _sadd(self, name: str, *values: str) -> int:
        """Add members to set."""
        if name not in self._storage:
            self._storage[name] = json.dumps(set())
        set_data = set(json.loads(self._storage[name]))
        added = sum(1 for v in values if v not in set_data)
        set_data.update(values)
        self._storage[name] = json.dumps(list(set_data))
        return added
    
    async def _smembers(self, name: str) -> set:
        """Get all members of set."""
        set_data = self._storage.get(name, "[]")
        if isinstance(set_data, str):
            set_data = json.loads(set_data)
        return set(set_data)


class MockHTTPClient:
    """Mock HTTP client for external API calls."""
    
    def __init__(self):
        self.get = AsyncMock(return_value=Mock(status_code=200, json=AsyncMock(return_value={})))
        self.post = AsyncMock(return_value=Mock(status_code=200, json=AsyncMock(return_value={})))
        self.put = AsyncMock(return_value=Mock(status_code=200, json=AsyncMock(return_value={})))
        self.delete = AsyncMock(return_value=Mock(status_code=200, json=AsyncMock(return_value={})))
    
    def set_response(self, method: str, status_code: int, data: Dict[str, Any]):
        """Set a custom response for a method."""
        mock_response = Mock(status_code=status_code, json=AsyncMock(return_value=data))
        getattr(self, method.lower()).return_value = mock_response


def create_mock_session_manager():
    """Create a mock session manager."""
    mock_manager = Mock()
    mock_manager.get_session = AsyncMock(return_value="mock_session_id")
    mock_manager.validate_session = AsyncMock(return_value=True)
    mock_manager.destroy_session = AsyncMock(return_value=True)
    return mock_manager


def create_mock_rate_limiter():
    """Create a mock rate limiter."""
    mock_limiter = Mock()
    mock_limiter.check_rate_limit = AsyncMock(return_value=(True, 100, 100))
    mock_limiter.increment = AsyncMock(return_value=1)
    mock_limiter.reset = AsyncMock(return_value=True)
    return mock_limiter

