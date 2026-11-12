"""
Token budget enforcement — in-memory fallback when Redis is not available.
"""
import json
from datetime import date
from app.config import get_settings

settings = get_settings()

# In-memory budget store (resets on restart — OK for local dev)
_memory_store: dict = {}


async def record_usage(user_id: str, cost_usd: float) -> None:
    key = f"{user_id}:{date.today().isoformat()}"
    _memory_store[key] = _memory_store.get(key, 0.0) + cost_usd


async def get_daily_spend(user_id: str) -> float:
    key = f"{user_id}:{date.today().isoformat()}"
    return _memory_store.get(key, 0.0)


async def check_budget(user_id: str) -> tuple[bool, float]:
    """Returns (within_budget, current_spend)."""
    spend = await get_daily_spend(user_id)
    return spend < settings.daily_token_budget_usd, spend
