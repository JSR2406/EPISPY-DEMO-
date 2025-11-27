"""
Session management using Redis for user sessions and agent state.

This module provides session storage for:
- User session management
- Agent conversation state persistence
- Temporary data storage for multi-step workflows
- Session expiration and cleanup

Example usage:
    from src.cache.session_manager import SessionManager
    
    # Create session manager
    session_manager = SessionManager()
    
    # Store user session
    await session_manager.create_session(
        session_id="sess123",
        user_id="user456",
        data={"name": "John", "role": "admin"}
    )
    
    # Get session
    session = await session_manager.get_session("sess123")
    
    # Store agent conversation state
    await session_manager.store_agent_state(
        agent_id="agent789",
        conversation_id="conv123",
        state={"messages": [...], "context": {...}}
    )
"""
import json
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .redis_client import get_redis_client, RedisClient
from ..utils.logger import api_logger


class SessionManager:
    """
    Session manager for user sessions and agent state.
    
    Features:
    - User session storage with expiration
    - Agent conversation state persistence
    - Temporary data storage for workflows
    - Session cleanup and management
    
    Attributes:
        redis: Redis client instance
        session_prefix: Prefix for session keys
        default_ttl: Default session TTL in seconds
    """
    
    def __init__(
        self,
        session_prefix: str = "epispy:sessions",
        default_ttl: int = 3600,  # 1 hour default
    ):
        """
        Initialize session manager.
        
        Args:
            session_prefix: Prefix for session keys
            default_ttl: Default session TTL in seconds
        """
        self.session_prefix = session_prefix
        self.default_ttl = default_ttl
        self._redis: Optional[RedisClient] = None
    
    async def _get_redis(self) -> RedisClient:
        """Get Redis client (lazy initialization)."""
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis
    
    def _make_session_key(self, session_id: str) -> str:
        """Generate session key."""
        return f"{self.session_prefix}:{session_id}"
    
    def _make_user_sessions_key(self, user_id: str) -> str:
        """Generate key for user's session list."""
        return f"{self.session_prefix}:user:{user_id}"
    
    def _make_agent_state_key(self, agent_id: str, conversation_id: str) -> str:
        """Generate key for agent conversation state."""
        return f"{self.session_prefix}:agent:{agent_id}:{conversation_id}"
    
    def _make_workflow_key(self, workflow_id: str) -> str:
        """Generate key for workflow temporary data."""
        return f"{self.session_prefix}:workflow:{workflow_id}"
    
    # User Session Management
    async def create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> str:
        """
        Create a new user session.
        
        Args:
            session_id: Optional session ID (generated if not provided)
            user_id: User ID associated with session
            data: Session data to store
            ttl: Time to live in seconds (defaults to instance default)
            
        Returns:
            Session ID
            
        Example:
            session_id = await session_manager.create_session(
                user_id="user123",
                data={"name": "John", "role": "admin"},
                ttl=7200  # 2 hours
            )
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        redis = await self._get_redis()
        session_key = self._make_session_key(session_id)
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "data": data or {},
        }
        
        ttl = ttl or self.default_ttl
        
        # Store session
        await redis.json_set(session_key, "$", session_data, ex=ttl)
        
        # Add to user's session list if user_id provided
        if user_id:
            user_sessions_key = self._make_user_sessions_key(user_id)
            await redis.sadd(user_sessions_key, session_id)
            await redis.expire(user_sessions_key, ttl)
        
        api_logger.info(f"Created session: {session_id} for user: {user_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
            
        Example:
            session = await session_manager.get_session("sess123")
            if session:
                print(f"User: {session['user_id']}")
        """
        redis = await self._get_redis()
        session_key = self._make_session_key(session_id)
        
        session_data = await redis.json_get(session_key, "$")
        
        if session_data:
            # Update last accessed time
            await self.update_session_access(session_id)
            return session_data
        
        return None
    
    async def update_session(
        self,
        session_id: str,
        data: Optional[Dict[str, Any]] = None,
        extend_ttl: bool = True,
    ) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session ID
            data: Data to update (merged with existing)
            extend_ttl: Whether to extend session TTL
            
        Returns:
            True if successful
        """
        redis = await self._get_redis()
        session_key = self._make_session_key(session_id)
        
        # Get existing session
        existing = await redis.json_get(session_key, "$")
        
        if not existing:
            return False
        
        # Merge data
        if data:
            if isinstance(existing, dict) and "data" in existing:
                existing["data"].update(data)
            else:
                existing["data"] = data
        
        existing["last_accessed"] = datetime.now().isoformat()
        
        # Update session
        ttl = None
        if extend_ttl:
            current_ttl = await redis.ttl(session_key)
            if current_ttl > 0:
                ttl = current_ttl
            else:
                ttl = self.default_ttl
        
        await redis.json_set(session_key, "$", existing, ex=ttl)
        
        return True
    
    async def update_session_access(self, session_id: str) -> bool:
        """Update last accessed time for session."""
        redis = await self._get_redis()
        session_key = self._make_session_key(session_id)
        
        try:
            # Get current session
            session = await redis.json_get(session_key, "$")
            if session:
                session["last_accessed"] = datetime.now().isoformat()
                current_ttl = await redis.ttl(session_key)
                await redis.json_set(
                    session_key, "$", session, ex=current_ttl if current_ttl > 0 else self.default_ttl
                )
                return True
        except Exception as e:
            api_logger.error(f"Failed to update session access: {str(e)}")
        
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted
        """
        redis = await self._get_redis()
        session_key = self._make_session_key(session_id)
        
        # Get session to find user_id
        session = await redis.json_get(session_key, "$")
        
        # Delete session
        deleted = await redis.delete(session_key)
        
        # Remove from user's session list
        if session and isinstance(session, dict) and "user_id" in session:
            user_sessions_key = self._make_user_sessions_key(session["user_id"])
            await redis.srem(user_sessions_key, session_id)
        
        if deleted:
            api_logger.info(f"Deleted session: {session_id}")
        
        return deleted > 0
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """
        Get all session IDs for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of session IDs
        """
        redis = await self._get_redis()
        user_sessions_key = self._make_user_sessions_key(user_id)
        
        sessions = await redis.smembers(user_sessions_key)
        return list(sessions) if sessions else []
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions deleted
        """
        session_ids = await self.get_user_sessions(user_id)
        deleted_count = 0
        
        for session_id in session_ids:
            if await self.delete_session(session_id):
                deleted_count += 1
        
        return deleted_count
    
    # Agent State Management
    async def store_agent_state(
        self,
        agent_id: str,
        conversation_id: str,
        state: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store agent conversation state.
        
        Args:
            agent_id: Agent ID
            conversation_id: Conversation ID
            state: State data to store
            ttl: Time to live in seconds
            
        Returns:
            True if successful
            
        Example:
            await session_manager.store_agent_state(
                agent_id="epidemic_analyzer",
                conversation_id="conv123",
                state={
                    "messages": [...],
                    "context": {...},
                    "step": "analyzing"
                },
                ttl=7200  # 2 hours
            )
        """
        redis = await self._get_redis()
        state_key = self._make_agent_state_key(agent_id, conversation_id)
        
        state_data = {
            "agent_id": agent_id,
            "conversation_id": conversation_id,
            "state": state,
            "updated_at": datetime.now().isoformat(),
        }
        
        ttl = ttl or (self.default_ttl * 2)  # Agent state lasts longer
        
        await redis.json_set(state_key, "$", state_data, ex=ttl)
        
        api_logger.debug(
            f"Stored agent state: {agent_id}:{conversation_id}"
        )
        return True
    
    async def get_agent_state(
        self,
        agent_id: str,
        conversation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get agent conversation state.
        
        Args:
            agent_id: Agent ID
            conversation_id: Conversation ID
            
        Returns:
            State data or None
        """
        redis = await self._get_redis()
        state_key = self._make_agent_state_key(agent_id, conversation_id)
        
        state_data = await redis.json_get(state_key, "$")
        return state_data
    
    async def update_agent_state(
        self,
        agent_id: str,
        conversation_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update agent state (merge updates).
        
        Args:
            agent_id: Agent ID
            conversation_id: Conversation ID
            updates: Updates to merge into state
            
        Returns:
            True if successful
        """
        current_state = await self.get_agent_state(agent_id, conversation_id)
        
        if not current_state:
            return False
        
        # Merge updates
        if "state" in current_state and isinstance(current_state["state"], dict):
            current_state["state"].update(updates)
        else:
            current_state["state"] = updates
        
        current_state["updated_at"] = datetime.now().isoformat()
        
        # Store updated state
        redis = await self._get_redis()
        state_key = self._make_agent_state_key(agent_id, conversation_id)
        
        current_ttl = await redis.ttl(state_key)
        ttl = current_ttl if current_ttl > 0 else (self.default_ttl * 2)
        
        await redis.json_set(state_key, "$", current_state, ex=ttl)
        
        return True
    
    async def delete_agent_state(
        self,
        agent_id: str,
        conversation_id: str,
    ) -> bool:
        """Delete agent conversation state."""
        redis = await self._get_redis()
        state_key = self._make_agent_state_key(agent_id, conversation_id)
        
        deleted = await redis.delete(state_key)
        return deleted > 0
    
    # Workflow Temporary Data
    async def store_workflow_data(
        self,
        workflow_id: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store temporary data for multi-step workflow.
        
        Args:
            workflow_id: Workflow ID
            data: Data to store
            ttl: Time to live in seconds
            
        Returns:
            True if successful
            
        Example:
            await session_manager.store_workflow_data(
                workflow_id="workflow123",
                data={
                    "step": 2,
                    "intermediate_results": {...},
                    "next_action": "analyze"
                },
                ttl=1800  # 30 minutes
            )
        """
        redis = await self._get_redis()
        workflow_key = self._make_workflow_key(workflow_id)
        
        workflow_data = {
            "workflow_id": workflow_id,
            "data": data,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        ttl = ttl or self.default_ttl
        
        await redis.json_set(workflow_key, "$", workflow_data, ex=ttl)
        return True
    
    async def get_workflow_data(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow temporary data."""
        redis = await self._get_redis()
        workflow_key = self._make_workflow_key(workflow_id)
        
        data = await redis.json_get(workflow_key, "$")
        return data
    
    async def update_workflow_data(
        self,
        workflow_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update workflow data (merge updates)."""
        current_data = await self.get_workflow_data(workflow_id)
        
        if not current_data:
            return False
        
        if "data" in current_data and isinstance(current_data["data"], dict):
            current_data["data"].update(updates)
        else:
            current_data["data"] = updates
        
        current_data["updated_at"] = datetime.now().isoformat()
        
        redis = await self._get_redis()
        workflow_key = self._make_workflow_key(workflow_id)
        
        current_ttl = await redis.ttl(workflow_key)
        ttl = current_ttl if current_ttl > 0 else self.default_ttl
        
        await redis.json_set(workflow_key, "$", current_data, ex=ttl)
        return True
    
    async def delete_workflow_data(self, workflow_id: str) -> bool:
        """Delete workflow temporary data."""
        redis = await self._get_redis()
        workflow_key = self._make_workflow_key(workflow_id)
        
        deleted = await redis.delete(workflow_key)
        return deleted > 0
    
    # Cleanup and Management
    async def cleanup_expired_sessions(self) -> int:
        """
        Cleanup expired sessions (Redis handles expiration automatically,
        but this can clean up user session lists).
        
        Returns:
            Number of sessions cleaned up
        """
        # Redis automatically expires keys, but we can clean up user session lists
        # This is a simplified version - in production, you might want a more
        # sophisticated cleanup strategy
        
        api_logger.info("Session cleanup completed (Redis handles expiration)")
        return 0
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics.
        
        Returns:
            Dictionary with session statistics
        """
        # This would require scanning keys, which is expensive
        # In production, maintain counters separately
        
        return {
            "note": "Statistics require key scanning - implement counters for production",
        }


# Global session manager instance
_session_manager: Optional[SessionManager] = None


async def get_session_manager() -> SessionManager:
    """Get or create global session manager instance."""
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager()
    
    return _session_manager

