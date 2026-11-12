"""
Redis memory — in-memory fallback when Redis is not available.
"""
import json
from typing import Optional, Any

# In-memory store for local dev
_store: dict = {}
_conv_store: dict = {}


async def set_agent_state(session_id: str, state: dict, ttl_seconds: int = 3600) -> None:
    _store[f"agent_state:{session_id}"] = state


async def get_agent_state(session_id: str) -> Optional[dict]:
    return _store.get(f"agent_state:{session_id}")


async def append_conversation(student_id: str, role: str, content: str, max_turns: int = 20) -> None:
    key = f"conv:{student_id}"
    if key not in _conv_store:
        _conv_store[key] = []
    _conv_store[key].append({"role": role, "content": content})
    if len(_conv_store[key]) > max_turns * 2:
        _conv_store[key] = _conv_store[key][-max_turns * 2:]


async def get_conversation_history(student_id: str) -> list[dict]:
    return _conv_store.get(f"conv:{student_id}", [])


async def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    _store[f"cache:{key}"] = value


async def cache_get(key: str) -> Optional[Any]:
    return _store.get(f"cache:{key}")
