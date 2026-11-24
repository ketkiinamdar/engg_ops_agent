"""Read-only Azure Cost Management and Budget REST collectors.
Requires an Azure identity with cost visibility at the subscription scope.
"""
import os
import requests
from datetime import datetime, timedelta, timezone
from azure.identity import DefaultAzureCredential

ARM = "https://management.azure.com"
API_VERSION = "2023-03-01"


def _headers():
    token = DefaultAzureCredential().get_token("https://management.azure.com/.default").token
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get_cost_by_resource(subscription_id: str, lookback_days: int = 30) -> dict:
    if not subscription_id or not (1 <= int(lookback_days) <= 90):
        raise ValueError("Valid subscription_id and lookback_days (1-90) are required")
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=int(lookback_days))
    url = f"{ARM}/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query"
    body = {
        "type": "ActualCost", "timeframe": "Custom",
        "timePeriod": {"from": start.isoformat(), "to": end.isoformat()},
        "dataset": {
            "granularity": "Daily",
            "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
            "grouping": [
                {"type": "Dimension", "name": "ResourceId"},
                {"type": "Dimension", "name": "ResourceGroupName"},
                {"type": "Dimension", "name": "ServiceName"},
            ],
        },
    }
    response = requests.post(url, params={"api-version": API_VERSION}, json=body,
                             headers=_headers(), timeout=60)
    response.raise_for_status()
    payload = response.json()
    props = payload.get("properties", {})
    columns = [c.get("name") for c in props.get("columns", [])]
    rows = [dict(zip(columns, row)) for row in props.get("rows", [])]
    return {"status": "success", "currency_and_units": columns,
            "period": {"from": start.isoformat(), "to": end.isoformat()},
            "row_count": len(rows), "rows": rows,
            "note": "Actual cost data; validate billing scope, currency and amortization policy before comparing."}


def get_budgets(subscription_id: str) -> dict:
    url = f"{ARM}/subscriptions/{subscription_id}/providers/Microsoft.Consumption/budgets"
    response = requests.get(url, params={"api-version": "2023-05-01"},
                            headers=_headers(), timeout=45)
    response.raise_for_status()
    values = response.json().get("value", [])
    budgets = []
    for item in values:
        p = item.get("properties", {})
        budgets.append({"name": item.get("name"), "amount": p.get("amount"),
                        "time_grain": p.get("timeGrain"), "time_period": p.get("timePeriod"),
                        "current_spend": p.get("currentSpend"),
                        "notifications": p.get("notifications")})
    return {"status": "success", "count": len(budgets), "budgets": budgets}
