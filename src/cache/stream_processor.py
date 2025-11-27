"""
Redis Streams processor for real-time event processing.

This module provides real-time event streaming using Redis Streams for:
- Publishing outbreak events
- Publishing risk alerts
- Publishing agent task completions
- Consumer groups for parallel processing
- Event filtering and routing

Example usage:
    from src.cache.stream_processor import StreamProcessor, publish_outbreak_event
    
    # Publish an event
    await publish_outbreak_event(
        location_id="loc123",
        event_data={"cases": 100, "deaths": 5}
    )
    
    # Process events with consumer group
    processor = StreamProcessor()
    await processor.consume_outbreak_events(
        consumer_group="alert_processors",
        consumer_name="worker1"
    )
"""
import json
import asyncio
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from datetime import datetime

from .redis_client import get_redis_client, RedisClient
from ..utils.logger import api_logger


class StreamProcessor:
    """
    Redis Streams processor for real-time event handling.
    
    Features:
    - Publish events to streams
    - Consumer groups for parallel processing
    - Automatic acknowledgment
    - Error handling and retries
    - Event filtering
    
    Attributes:
        redis: Redis client instance
        stream_prefix: Prefix for all stream names
    """
    
    # Stream names
    STREAM_OUTBREAK_EVENTS = "outbreak_events"
    STREAM_RISK_ALERTS = "risk_alerts"
    STREAM_AGENT_COMPLETIONS = "agent_completions"
    STREAM_PREDICTIONS = "predictions"
    STREAM_SYSTEM_EVENTS = "system_events"
    
    def __init__(self, stream_prefix: str = "epispy:streams"):
        """
        Initialize stream processor.
        
        Args:
            stream_prefix: Prefix for all stream names
        """
        self.stream_prefix = stream_prefix
        self._redis: Optional[RedisClient] = None
    
    async def _get_redis(self) -> RedisClient:
        """Get Redis client (lazy initialization)."""
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis
    
    def _make_stream_name(self, stream: str) -> str:
        """Generate namespaced stream name."""
        return f"{self.stream_prefix}:{stream}"
    
    async def publish(
        self,
        stream: str,
        data: Dict[str, Any],
        max_length: Optional[int] = 10000,
    ) -> str:
        """
        Publish event to stream.
        
        Args:
            stream: Stream name
            data: Event data (will be JSON serialized)
            max_length: Maximum stream length (truncate if exceeded)
            
        Returns:
            Message ID
            
        Example:
            msg_id = await processor.publish(
                "outbreak_events",
                {"location_id": "loc123", "cases": 100}
            )
        """
        try:
            redis = await self._get_redis()
            stream_name = self._make_stream_name(stream)
            
            # Add timestamp to data
            event_data = {
                **data,
                "timestamp": datetime.now().isoformat(),
                "published_at": datetime.now().isoformat(),
            }
            
            # Convert to JSON string for Redis
            fields = {
                "data": json.dumps(event_data),
                "event_type": data.get("event_type", "unknown"),
            }
            
            # Publish to stream
            message_id = await redis._execute_with_retry(
                redis.client.xadd,
                stream_name,
                fields,
                maxlen=max_length,
                approximate=True,  # Approximate trimming for performance
            )
            
            api_logger.info(
                f"Published event to {stream_name}: {message_id} (type: {fields['event_type']})"
            )
            
            return message_id
            
        except Exception as e:
            api_logger.error(f"Failed to publish event to {stream}: {str(e)}")
            raise
    
    async def create_consumer_group(
        self,
        stream: str,
        group_name: str,
        start_id: str = "0",
    ) -> bool:
        """
        Create consumer group for stream.
        
        Args:
            stream: Stream name
            group_name: Consumer group name
            start_id: Starting message ID ("0" for all, "$" for new messages)
            
        Returns:
            True if created, False if already exists
            
        Example:
            await processor.create_consumer_group(
                "outbreak_events",
                "alert_processors"
            )
        """
        try:
            redis = await self._get_redis()
            stream_name = self._make_stream_name(stream)
            
            # Try to create consumer group
            await redis._execute_with_retry(
                redis.client.xgroup_create,
                stream_name,
                group_name,
                id=start_id,
                mkstream=True,  # Create stream if it doesn't exist
            )
            
            api_logger.info(
                f"Created consumer group {group_name} for stream {stream_name}"
            )
            return True
            
        except Exception as e:
            # Group might already exist
            if "BUSYGROUP" in str(e):
                api_logger.debug(
                    f"Consumer group {group_name} already exists for {stream_name}"
                )
                return False
            api_logger.error(
                f"Failed to create consumer group {group_name}: {str(e)}"
            )
            raise
    
    async def read_group(
        self,
        stream: str,
        group_name: str,
        consumer_name: str,
        count: int = 10,
        block: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Read messages from consumer group.
        
        Args:
            stream: Stream name
            group_name: Consumer group name
            consumer_name: Consumer name (unique per worker)
            count: Maximum number of messages to read
            block: Block time in milliseconds (0 for non-blocking)
            
        Returns:
            List of messages with parsed data
            
        Example:
            messages = await processor.read_group(
                "outbreak_events",
                "alert_processors",
                "worker1",
                count=5
            )
        """
        try:
            redis = await self._get_redis()
            stream_name = self._make_stream_name(stream)
            
            # Ensure consumer group exists
            await self.create_consumer_group(stream, group_name)
            
            # Read from consumer group
            messages = await redis._execute_with_retry(
                redis.client.xreadgroup,
                group_name,
                consumer_name,
                {stream_name: ">"},  # ">" means new messages
                count=count,
                block=block,
            )
            
            if not messages:
                return []
            
            # Parse messages
            parsed_messages = []
            for stream_data in messages:
                stream_key, stream_messages = stream_data
                
                for msg_id, fields in stream_messages:
                    # Parse JSON data
                    data_str = fields.get("data", "{}")
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        data = {"raw": data_str}
                    
                    parsed_messages.append({
                        "id": msg_id,
                        "stream": stream_key.decode() if isinstance(stream_key, bytes) else stream_key,
                        "data": data,
                        "event_type": fields.get("event_type", "unknown"),
                        "fields": fields,
                    })
            
            return parsed_messages
            
        except Exception as e:
            api_logger.error(f"Failed to read from consumer group: {str(e)}")
            return []
    
    async def acknowledge(
        self,
        stream: str,
        group_name: str,
        message_ids: List[str],
    ) -> int:
        """
        Acknowledge processed messages.
        
        Args:
            stream: Stream name
            group_name: Consumer group name
            message_ids: List of message IDs to acknowledge
            
        Returns:
            Number of acknowledged messages
            
        Example:
            count = await processor.acknowledge(
                "outbreak_events",
                "alert_processors",
                ["1234567890-0"]
            )
        """
        try:
            redis = await self._get_redis()
            stream_name = self._make_stream_name(stream)
            
            result = await redis._execute_with_retry(
                redis.client.xack,
                stream_name,
                group_name,
                *message_ids,
            )
            
            api_logger.debug(
                f"Acknowledged {result} messages in {group_name} for {stream_name}"
            )
            
            return result
            
        except Exception as e:
            api_logger.error(f"Failed to acknowledge messages: {str(e)}")
            return 0
    
    async def consume_events(
        self,
        stream: str,
        group_name: str,
        consumer_name: str,
        handler: Callable[[Dict[str, Any]], Any],
        batch_size: int = 10,
        block_time: int = 1000,
        auto_ack: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Continuously consume and process events.
        
        Args:
            stream: Stream name
            group_name: Consumer group name
            consumer_name: Consumer name
            handler: Async function to handle each message
            batch_size: Number of messages to read per batch
            block_time: Block time in milliseconds
            auto_ack: Automatically acknowledge after processing
            
        Yields:
            Processed messages
            
        Example:
            async for message in processor.consume_events(
                "outbreak_events",
                "alert_processors",
                "worker1",
                handler=process_outbreak_event
            ):
                print(f"Processed: {message['id']}")
        """
        api_logger.info(
            f"Starting event consumer: {consumer_name} in group {group_name} for {stream}"
        )
        
        while True:
            try:
                # Read messages
                messages = await self.read_group(
                    stream,
                    group_name,
                    consumer_name,
                    count=batch_size,
                    block=block_time,
                )
                
                if not messages:
                    continue
                
                # Process each message
                for message in messages:
                    try:
                        # Call handler
                        await handler(message["data"])
                        
                        # Acknowledge if auto_ack enabled
                        if auto_ack:
                            await self.acknowledge(
                                stream,
                                group_name,
                                [message["id"]],
                            )
                        
                        yield message
                        
                    except Exception as e:
                        api_logger.error(
                            f"Error processing message {message['id']}: {str(e)}"
                        )
                        # Don't acknowledge failed messages
                        # They will be retried or moved to dead letter queue
                
            except asyncio.CancelledError:
                api_logger.info(f"Consumer {consumer_name} cancelled")
                break
            except Exception as e:
                api_logger.error(f"Consumer error: {str(e)}")
                await asyncio.sleep(1)  # Brief pause before retry
    
    # Specific publish methods
    async def publish_outbreak_event(
        self,
        location_id: str,
        event_data: Dict[str, Any],
    ) -> str:
        """
        Publish outbreak event.
        
        Args:
            location_id: Location ID
            event_data: Event data (cases, deaths, etc.)
            
        Returns:
            Message ID
        """
        return await self.publish(
            self.STREAM_OUTBREAK_EVENTS,
            {
                "event_type": "outbreak_event",
                "location_id": location_id,
                **event_data,
            },
        )
    
    async def publish_risk_alert(
        self,
        location_id: str,
        risk_level: str,
        risk_score: float,
        alert_data: Dict[str, Any],
    ) -> str:
        """
        Publish risk alert.
        
        Args:
            location_id: Location ID
            risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
            risk_score: Risk score (0-10)
            alert_data: Additional alert data
            
        Returns:
            Message ID
        """
        return await self.publish(
            self.STREAM_RISK_ALERTS,
            {
                "event_type": "risk_alert",
                "location_id": location_id,
                "risk_level": risk_level,
                "risk_score": risk_score,
                **alert_data,
            },
        )
    
    async def publish_agent_completion(
        self,
        agent_id: str,
        task_id: str,
        status: str,
        result: Dict[str, Any],
    ) -> str:
        """
        Publish agent task completion.
        
        Args:
            agent_id: Agent ID
            task_id: Task ID
            status: Status (COMPLETED, FAILED, etc.)
            result: Task result data
            
        Returns:
            Message ID
        """
        return await self.publish(
            self.STREAM_AGENT_COMPLETIONS,
            {
                "event_type": "agent_completion",
                "agent_id": agent_id,
                "task_id": task_id,
                "status": status,
                "result": result,
            },
        )
    
    async def publish_prediction(
        self,
        location_id: str,
        prediction_data: Dict[str, Any],
    ) -> str:
        """
        Publish prediction update.
        
        Args:
            location_id: Location ID
            prediction_data: Prediction data
            
        Returns:
            Message ID
        """
        return await self.publish(
            self.STREAM_PREDICTIONS,
            {
                "event_type": "prediction_update",
                "location_id": location_id,
                **prediction_data,
            },
        )
    
    # Consumer group methods for specific streams
    async def consume_outbreak_events(
        self,
        consumer_group: str,
        consumer_name: str,
        handler: Optional[Callable] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Consume outbreak events.
        
        Args:
            consumer_group: Consumer group name
            consumer_name: Consumer name
            handler: Optional handler function
            
        Yields:
            Outbreak event messages
        """
        if handler:
            async for message in self.consume_events(
                self.STREAM_OUTBREAK_EVENTS,
                consumer_group,
                consumer_name,
                handler,
            ):
                yield message
        else:
            while True:
                messages = await self.read_group(
                    self.STREAM_OUTBREAK_EVENTS,
                    consumer_group,
                    consumer_name,
                )
                for message in messages:
                    yield message
                await asyncio.sleep(1)
    
    async def consume_risk_alerts(
        self,
        consumer_group: str,
        consumer_name: str,
        handler: Optional[Callable] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Consume risk alerts."""
        if handler:
            async for message in self.consume_events(
                self.STREAM_RISK_ALERTS,
                consumer_group,
                consumer_name,
                handler,
            ):
                yield message
        else:
            while True:
                messages = await self.read_group(
                    self.STREAM_RISK_ALERTS,
                    consumer_group,
                    consumer_name,
                )
                for message in messages:
                    yield message
                await asyncio.sleep(1)
    
    async def get_stream_info(self, stream: str) -> Dict[str, Any]:
        """
        Get stream information.
        
        Args:
            stream: Stream name
            
        Returns:
            Stream information (length, groups, etc.)
        """
        try:
            redis = await self._get_redis()
            stream_name = self._make_stream_name(stream)
            
            info = await redis._execute_with_retry(
                redis.client.xinfo_stream,
                stream_name,
            )
            
            return {
                "length": info.get("length", 0),
                "groups": info.get("groups", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry"),
            }
        except Exception as e:
            api_logger.error(f"Failed to get stream info: {str(e)}")
            return {}


# Global stream processor instance
_stream_processor: Optional[StreamProcessor] = None


async def get_stream_processor() -> StreamProcessor:
    """Get or create global stream processor instance."""
    global _stream_processor
    
    if _stream_processor is None:
        _stream_processor = StreamProcessor()
    
    return _stream_processor


# Convenience functions
async def publish_outbreak_event(
    location_id: str,
    event_data: Dict[str, Any],
) -> str:
    """Publish outbreak event (convenience function)."""
    processor = await get_stream_processor()
    return await processor.publish_outbreak_event(location_id, event_data)


async def publish_risk_alert(
    location_id: str,
    risk_level: str,
    risk_score: float,
    alert_data: Dict[str, Any],
) -> str:
    """Publish risk alert (convenience function)."""
    processor = await get_stream_processor()
    return await processor.publish_risk_alert(
        location_id, risk_level, risk_score, alert_data
    )


async def publish_agent_completion(
    agent_id: str,
    task_id: str,
    status: str,
    result: Dict[str, Any],
) -> str:
    """Publish agent completion (convenience function)."""
    processor = await get_stream_processor()
    return await processor.publish_agent_completion(
        agent_id, task_id, status, result
    )

