import json
import sys
from pathlib import Path


sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
    )
)


from agent.investigator import InvestigationAgent

from mcp_servers.observability.server import (
    find_traces,
    get_service_health,
    query_metrics,
    search_logs,
)


def main():

    tools = {
        "get_service_health":
            get_service_health,

        "search_logs":
            search_logs,

        "query_metrics":
            query_metrics,

        "find_traces":
            find_traces,
    }

    agent = InvestigationAgent(
        tools=tools,
        max_iterations=8,
    )

    result = agent.investigate(
        incident=(
            "payment-service is experiencing failures"
        ),
        service="payment-service",
    )

    print(
        json.dumps(
            result.to_dict(),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()