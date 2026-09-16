from typing import Optional

import requests
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("DevRescue Observability")

LOKI_URL = "http://localhost:3100"
PROMETHEUS_URL = "http://localhost:9090"


@mcp.tool()
def get_service_health() -> dict:
    """Return the current health status of the payment service."""

    return {
        "service": "payment-service",
        "status": "healthy",
    }


@mcp.tool()
def search_logs(
    query: str,
    service: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """
    Search application logs in Loki.

    Args:
        query: Text to search for in log messages.
        service: Optional service name to restrict the search.
        limit: Maximum number of log records to return.
    """

    if limit <= 0:
        return {
            "query": query,
            "service": service,
            "results": [],
            "error": "limit must be greater than zero",
        }

    if limit > 200:
        limit = 200

    logql = '{service_name="payment-service"}'

    if service:
        logql = f'{{service_name="{service}"}}'

    if query:
        escaped_query = query.replace("\\", "\\\\").replace('"', '\\"')
        logql += f' |= "{escaped_query}"'

    try:
        response = requests.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params={
                "query": logql,
                "limit": limit,
                "direction": "backward",
            },
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as exc:
        return {
            "query": query,
            "service": service,
            "results": [],
            "error": f"Loki request failed: {exc}",
        }

    results = []

    for stream in data.get("data", {}).get("result", []):
        labels = stream.get("stream", {})

        for timestamp, message in stream.get("values", []):
            results.append(
                {
                    "timestamp": timestamp,
                    "service": labels.get("service_name"),
                    "level": labels.get("severity_text"),
                    "message": message,
                    "trace_id": labels.get("trace_id"),
                    "span_id": labels.get("span_id"),
                    "request_id": _extract_request_id(message),
                }
            )

    return {
        "query": query,
        "service": service or "payment-service",
        "count": len(results),
        "results": results,
    }


@mcp.tool()
def query_metrics(
    query: str,
    time: Optional[str] = None,
) -> dict:
    """
    Query application metrics from Prometheus.

    Args:
        query: PromQL query to execute.
        time: Optional Prometheus evaluation timestamp.
    """

    if not query.strip():
        return {
            "query": query,
            "result": [],
            "error": "query must not be empty",
        }

    params = {
        "query": query,
    }

    if time:
        params["time"] = time

    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params=params,
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as exc:
        return {
            "query": query,
            "result": [],
            "error": f"Prometheus request failed: {exc}",
        }

    if data.get("status") != "success":
        return {
            "query": query,
            "result": [],
            "error": data.get("error", "Prometheus query failed"),
        }

    results = []

    for item in data.get("data", {}).get("result", []):
        results.append(
            {
                "metric": item.get("metric", {}),
                "value": item.get("value"),
            }
        )

    return {
        "query": query,
        "result_type": data.get("data", {}).get("resultType"),
        "count": len(results),
        "results": results,
    }
@mcp.tool()
def find_traces(
    service: str = "payment-service",
    trace_id: Optional[str] = None,
    limit: int = 10,
) -> dict:
    """
    Find traces from Jaeger.

    Args:
        service: Service name to search for.
        trace_id: Optional exact trace ID.
        limit: Maximum number of traces to return.
    """

    if limit <= 0:
        return {
            "service": service,
            "trace_id": trace_id,
            "count": 0,
            "results": [],
            "error": "limit must be greater than zero",
        }

    if limit > 50:
        limit = 50

    params = {
        "service": service,
        "limit": limit,
    }

    if trace_id:
        params["traceID"] = trace_id

    try:
        response = requests.get(
            "http://localhost:16686/api/traces",
            params=params,
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as exc:
        return {
            "service": service,
            "trace_id": trace_id,
            "count": 0,
            "results": [],
            "error": f"Jaeger request failed: {exc}",
        }

    results = []

    for trace in data.get("data", []):
        trace_result = {
            "trace_id": trace.get("traceID"),
            "spans": [],
        }

        for span in trace.get("spans", []):
            span_result = {
                "span_id": span.get("spanID"),
                "operation": span.get("operationName"),
                "start_time": span.get("startTime"),
                "duration": span.get("duration"),
                "tags": {
                    tag.get("key"): tag.get("value")
                    for tag in span.get("tags", [])
                },
                "logs": [],
            }

            for log in span.get("logs", []):
                span_result["logs"].append(
                    {
                        "timestamp": log.get("timestamp"),
                        "fields": {
                            field.get("key"): field.get("value")
                            for field in log.get("fields", [])
                        },
                    }
                )

            trace_result["spans"].append(span_result)

        results.append(trace_result)

    return {
        "service": service,
        "trace_id": trace_id,
        "count": len(results),
        "results": results,
    }

def _extract_request_id(message: str) -> Optional[str]:
    """Extract request_id from a structured application log message."""

    marker = "request_id="

    if marker not in message:
        return None

    value = message.split(marker, 1)[1].split()[0]

    return value


if __name__ == "__main__":
    mcp.run()