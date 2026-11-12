"""
LangSmith tracing — wraps agent calls with observability.
"""
import os
import functools
from typing import Callable, Any
from app.config import get_settings

settings = get_settings()

# Set LangSmith environment variables
os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project


async def trace_agent_call(func: Callable, data: dict, agent_name: str = "agent") -> Any:
    """
    Wraps an async agent function call with LangSmith tracing when available.
    Falls back to a direct call if LangSmith is not configured.
    """
    if not settings.langchain_api_key:
        # No tracing configured — call directly
        return await func(data)

    try:
        from langsmith import traceable

        @traceable(name=agent_name, run_type="chain")
        async def traced_call(input_data: dict) -> Any:
            return await func(input_data)

        return await traced_call(data)
    except ImportError:
        return await func(data)
    except Exception:
        # Never fail the actual agent call due to tracing issues
        return await func(data)
