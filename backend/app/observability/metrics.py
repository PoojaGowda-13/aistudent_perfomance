"""
Prometheus metrics — tracks agent calls, latency, token usage, and errors.
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Counters
agent_calls_total = Counter(
    "agent_calls_total",
    "Total number of agent calls",
    ["agent_type", "status"],
)

llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["provider", "model"],
)

tokens_used_total = Counter(
    "tokens_used_total",
    "Total tokens used",
    ["provider", "direction"],  # direction: input/output
)

cost_usd_total = Counter(
    "cost_usd_total",
    "Total LLM cost in USD",
    ["provider"],
)

# Histograms
agent_latency_seconds = Histogram(
    "agent_latency_seconds",
    "Agent execution latency in seconds",
    ["agent_type"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

llm_latency_seconds = Histogram(
    "llm_latency_seconds",
    "LLM API call latency in seconds",
    ["provider"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# Gauges
active_sessions = Gauge("active_sessions", "Currently active user sessions")
hitl_pending = Gauge("hitl_pending_reviews", "HITL items pending human review")


def record_agent_call(agent_type: str, status: str, latency_s: float):
    agent_calls_total.labels(agent_type=agent_type, status=status).inc()
    agent_latency_seconds.labels(agent_type=agent_type).observe(latency_s)


def record_llm_call(provider: str, model: str, input_tokens: int, output_tokens: int, cost: float, latency_s: float):
    llm_requests_total.labels(provider=provider, model=model).inc()
    tokens_used_total.labels(provider=provider, direction="input").inc(input_tokens)
    tokens_used_total.labels(provider=provider, direction="output").inc(output_tokens)
    cost_usd_total.labels(provider=provider).inc(cost)
    llm_latency_seconds.labels(provider=provider).observe(latency_s)


async def metrics_endpoint():
    """FastAPI endpoint handler for Prometheus scraping."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
