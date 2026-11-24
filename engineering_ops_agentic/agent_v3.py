"""CLI entry point for the LangGraph-based agentic Engineering Operations solution."""
import os
from dotenv import load_dotenv
from agentic_workflow import run_agentic_review

load_dotenv()

if __name__ == "__main__":
    result = run_agentic_review(
        service=os.getenv("SERVICE_NAME", "policy-api"),
        environment=os.getenv("ENVIRONMENT", "production"),
        lookback_hours=int(os.getenv("LOOKBACK_HOURS", "24")),
        max_rounds=int(os.getenv("AGENT_MAX_ROUNDS", "3")),
    )
    print(result["report"])
    print(f"\nSaved report: {result['report_path']}")
