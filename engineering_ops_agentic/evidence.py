"""Evidence collection, provenance and safe failure handling."""
from datetime import datetime, timezone
from importlib import import_module
import os
from typing import Callable, Any
from security.controls import redact


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(module: str, function: str) -> Callable:
    return getattr(import_module(module), function)


def _invoke(source: str, module: str, function: str, *args, **kwargs) -> dict:
    started = utc_now()
    try:
        # Mock mode is explicit and local-only; it never falls back silently.
        if os.getenv("DATA_MODE", "live").strip().lower() == "mock":
            module = "clients.mock_data"
        fn = _load(module, function)
        data = fn(*args, **kwargs)
        status = "success"
        if isinstance(data, dict) and data.get("status") in {"error", "partial", "unavailable"}:
            status = data["status"]
        return {
            "source": source, "status": status,
            "retrieved_at": utc_now(), "started_at": started,
            "data": redact(data),
        }
    except Exception as exc:
        # Detailed exception remains in server logs; do not disclose response bodies/secrets to the LLM.
        return {
            "source": source, "status": "unavailable",
            "retrieved_at": utc_now(), "started_at": started,
            "error_code": type(exc).__name__, "data": None,
        }


def collect_all(lookback_hours: int, app_role_name: str | None, sonar_project: str | None) -> dict:
    """Run independent collectors. Missing integrations never masquerade as healthy."""
    evidence = {
        "application_insights": _invoke(
            "ApplicationInsights", "clients.azure_monitor_client",
            "get_real_application_insights_data",
            lookback_hours=lookback_hours, app_role_name=app_role_name,
        ),
        "exceptions": _invoke("LogAnalyticsExceptions", "clients.azure_monitor_client",
                              "get_application_exceptions", lookback_hours),
        "failed_requests": _invoke("LogAnalyticsRequests", "clients.azure_monitor_client",
                                   "get_failed_application_requests", lookback_hours),
        "failed_dependencies": _invoke("LogAnalyticsDependencies", "clients.azure_monitor_client",
                                       "get_failed_dependencies", lookback_hours),
        "azure_activity": _invoke("AzureActivity", "clients.azure_monitor_client",
                                  "get_azure_activity", lookback_hours),
        "builds": _invoke("AzureDevOpsBuilds", "clients.azure_devops_client",
                          "get_recent_builds", lookback_hours),
        "incidents": _invoke("ServiceNowIncidents", "clients.servicenow_client",
                             "search_incidents", days=90, limit=50),
    }
    if sonar_project:
        # Three calls are isolated so one SonarCloud endpoint failure does not hide the others.
        evidence["sonarcloud"] = {
            "quality_gate": _invoke("SonarCloudQualityGate", "clients.sonarcloud_client", "quality_gate", sonar_project),
            "measures": _invoke("SonarCloudMeasures", "clients.sonarcloud_client", "measures", sonar_project),
            "issues": _invoke("SonarCloudIssues", "clients.sonarcloud_client", "issues", sonar_project),
        }
    else:
        evidence["sonarcloud"] = {"status": "not_configured", "reason": "SONARCLOUD_PROJECT_KEY is not set"}

    sub_id = __import__("os").getenv("AZURE_SUBSCRIPTION_ID")
    if sub_id:
        evidence["finops_cost"] = _invoke("AzureCostManagement", "clients.azure_finops_client",
                                          "get_cost_by_resource", sub_id, lookback_days=30)
        evidence["finops_budgets"] = _invoke("AzureBudgets", "clients.azure_finops_client",
                                             "get_budgets", sub_id)
    else:
        evidence["finops_cost"] = {"status": "not_configured", "reason": "AZURE_SUBSCRIPTION_ID is not set"}
        evidence["finops_budgets"] = {"status": "not_configured", "reason": "AZURE_SUBSCRIPTION_ID is not set"}
    return {"collected_at": utc_now(), "lookback_hours": lookback_hours, "sources": evidence}
