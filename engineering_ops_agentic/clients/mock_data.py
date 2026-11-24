"""Deterministic, fictional fixtures for local development and integration testing.

All records are synthetic. No real customer, subscription, ticket, project or secret data.
"""
from datetime import datetime, timedelta, timezone

SERVICE = "policy-api"
ENV = "production"
NOW = datetime.now(timezone.utc)

def ts(minutes_ago=0):
    return (NOW - timedelta(minutes=minutes_ago)).isoformat()

def _ok(source, **kwargs):
    return {"status": "success", "source": source, "retrieved_at": ts(), **kwargs}

# Azure Monitor / Application Insights

def get_real_application_insights_data(lookback_hours=24, app_role_name=None):
    role = app_role_name or SERVICE
    return {
        "requests": _ok("ApplicationInsights.requests", row_count=4, rows=[
            {"TimeGenerated": ts(8), "Name": "POST /api/policies", "AppRoleName": role, "AppVersion": "2.8.4", "Success": False, "ResultCode": "500", "DurationMs": 4200, "OperationId": "op-9001", "Properties": {"environment": ENV}},
            {"TimeGenerated": ts(12), "Name": "GET /api/policies/{id}", "AppRoleName": role, "AppVersion": "2.8.4", "Success": False, "ResultCode": "503", "DurationMs": 5100, "OperationId": "op-9002", "Properties": {"environment": ENV}},
            {"TimeGenerated": ts(25), "Name": "POST /api/policies", "AppRoleName": role, "AppVersion": "2.8.4", "Success": True, "ResultCode": "200", "DurationMs": 380, "OperationId": "op-9003", "Properties": {"environment": ENV}},
            {"TimeGenerated": ts(35), "Name": "GET /health", "AppRoleName": role, "AppVersion": "2.8.4", "Success": True, "ResultCode": "200", "DurationMs": 42, "OperationId": "op-9004", "Properties": {"environment": ENV}},
        ]),
        "exceptions": _ok("ApplicationInsights.exceptions", row_count=2, rows=[
            {"TimeGenerated": ts(9), "AppRoleName": role, "ExceptionType": "SqlException", "ProblemId": "SqlConnectionTimeout", "OuterMessage": "Database connection pool timeout", "OperationId": "op-9001"},
            {"TimeGenerated": ts(13), "AppRoleName": role, "ExceptionType": "HttpRequestException", "ProblemId": "PolicyStoreUnavailable", "OuterMessage": "Policy store returned 503", "OperationId": "op-9002"},
        ]),
        "dependencies": _ok("ApplicationInsights.dependencies", row_count=3, rows=[
            {"TimeGenerated": ts(9), "AppRoleName": role, "Name": "PolicyDb", "DependencyType": "SQL", "Target": "policy-sql.database.windows.net", "Success": False, "ResultCode": "-2", "DurationMs": 4000, "OperationId": "op-9001"},
            {"TimeGenerated": ts(13), "AppRoleName": role, "Name": "PolicyDb", "DependencyType": "SQL", "Target": "policy-sql.database.windows.net", "Success": False, "ResultCode": "-2", "DurationMs": 4900, "OperationId": "op-9002"},
            {"TimeGenerated": ts(35), "AppRoleName": role, "Name": "RedisCache", "DependencyType": "Azure Cache", "Target": "policy-cache", "Success": True, "ResultCode": "0", "DurationMs": 12, "OperationId": "op-9004"},
        ]),
        "traces": _ok("ApplicationInsights.traces", row_count=2, rows=[
            {"TimeGenerated": ts(10), "AppRoleName": role, "Message": "Retrying database connection", "SeverityLevel": 3, "OperationId": "op-9001"},
            {"TimeGenerated": ts(14), "AppRoleName": role, "Message": "Policy store request failed", "SeverityLevel": 3, "OperationId": "op-9002"},
        ]),
    }

def get_application_exceptions(lookback_hours=1):
    return _ok("LogAnalyticsExceptions", row_count=2, rows=[
        {"TimeGenerated": ts(9), "AppRoleName": SERVICE, "ProblemId": "SqlConnectionTimeout", "ExceptionType": "SqlException", "Message": "Database connection pool timeout", "OperationId": "op-9001"},
        {"TimeGenerated": ts(13), "AppRoleName": SERVICE, "ProblemId": "PolicyStoreUnavailable", "ExceptionType": "HttpRequestException", "Message": "Policy store returned 503", "OperationId": "op-9002"},
    ])

def get_failed_application_requests(lookback_hours=1):
    return _ok("LogAnalyticsRequests", row_count=2, rows=[
        {"TimeGenerated": ts(8), "AppRoleName": SERVICE, "Name": "POST /api/policies", "Url": "https://policy-api.example.invalid/api/policies", "ResultCode": "500", "DurationMs": 4200, "OperationId": "op-9001"},
        {"TimeGenerated": ts(12), "AppRoleName": SERVICE, "Name": "GET /api/policies/{id}", "Url": "https://policy-api.example.invalid/api/policies/123", "ResultCode": "503", "DurationMs": 5100, "OperationId": "op-9002"},
    ])

def get_failed_dependencies(lookback_hours=1):
    return _ok("LogAnalyticsDependencies", row_count=2, rows=[
        {"TimeGenerated": ts(9), "AppRoleName": SERVICE, "Name": "PolicyDb", "Target": "policy-sql.database.windows.net", "DependencyType": "SQL", "ResultCode": "-2", "DurationMs": 4000, "OperationId": "op-9001"},
        {"TimeGenerated": ts(13), "AppRoleName": SERVICE, "Name": "PolicyDb", "Target": "policy-sql.database.windows.net", "DependencyType": "SQL", "ResultCode": "-2", "DurationMs": 4900, "OperationId": "op-9002"},
    ])

def get_azure_activity(lookback_hours=24):
    return _ok("AzureActivity", row_count=2, rows=[
        {"TimeGenerated": ts(18), "OperationNameValue": "Microsoft.Sql/servers/databases/write", "ActivityStatusValue": "Succeeded", "ResourceGroup": "rg-policy-prod", "ResourceId": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg-policy-prod/providers/Microsoft.Sql/servers/policy-sql/databases/policydb", "Caller": "platform-automation"},
        {"TimeGenerated": ts(50), "OperationNameValue": "Microsoft.Compute/virtualMachines/restart/action", "ActivityStatusValue": "Succeeded", "ResourceGroup": "rg-policy-prod", "ResourceId": "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/rg-policy-prod/providers/Microsoft.Compute/virtualMachines/policy-worker-01", "Caller": "ops-operator"},
    ])

# Azure DevOps: deliberately named build runs, not deployments.
def get_recent_builds(lookback_hours=24):
    return _ok("AZURE_DEVOPS_REST_API", organization="demo-org", project="PolicyPlatform", lookback_hours=lookback_hours, build_count=3, builds=[
        {"build_id": 8421, "build_number": "20261124.4", "pipeline_name": "policy-api-ci", "status": "completed", "result": "succeeded", "source_branch": "refs/heads/main", "source_version": "a1b2c3d4e5f6", "requested_by": "Synthetic Build User", "start_time": ts(70), "finish_time": ts(64), "url": "https://dev.azure.com/demo-org/PolicyPlatform/_build/results?buildId=8421"},
        {"build_id": 8419, "build_number": "20261124.2", "pipeline_name": "policy-api-ci", "status": "completed", "result": "failed", "source_branch": "refs/heads/feature/db-retry", "source_version": "b2c3d4e5f6a1", "requested_by": "Synthetic Build User", "start_time": ts(110), "finish_time": ts(103), "url": "https://dev.azure.com/demo-org/PolicyPlatform/_build/results?buildId=8419"},
        {"build_id": 8415, "build_number": "20261123.7", "pipeline_name": "policy-worker-ci", "status": "completed", "result": "succeeded", "source_branch": "refs/heads/main", "source_version": "c3d4e5f6a1b2", "requested_by": "Synthetic Build User", "start_time": ts(900), "finish_time": ts(894), "url": "https://dev.azure.com/demo-org/PolicyPlatform/_build/results?buildId=8415"},
    ])

# ServiceNow incident history.
def search_incidents(text="", days=90, limit=100):
    records = [
        {"number": "INC1002451", "short_description": "Policy API intermittent database connection timeout", "description": "Production policy-api experienced intermittent SQL connection timeouts and elevated HTTP 5xx responses.", "priority": "2", "state": "Resolved", "assignment_group": "Platform Engineering", "opened_at": ts(24 * 5), "closed_at": ts(24 * 5 - 3), "close_code": "Solved (Work Around)", "close_notes": "Temporarily increased connection pool and recycled application instances. Permanent capacity review recommended.", "cmdb_ci": "policy-api", "sys_created_on": ts(24 * 5)},
        {"number": "INC1002388", "short_description": "Policy database connection pool saturation", "description": "Connection pool reached configured limit during peak policy submissions.", "priority": "2", "state": "Resolved", "assignment_group": "Database Operations", "opened_at": ts(24 * 12), "closed_at": ts(24 * 12 - 2), "close_code": "Solved (Permanently)", "close_notes": "Adjusted pool settings after load test and verified connection utilization.", "cmdb_ci": "policy-sql", "sys_created_on": ts(24 * 12)},
        {"number": "INC1002190", "short_description": "Policy API response latency elevated", "description": "P95 latency exceeded service objective during peak usage.", "priority": "3", "state": "Closed", "assignment_group": "Application Support", "opened_at": ts(24 * 28), "closed_at": ts(24 * 28 - 5), "close_code": "Solved (Work Around)", "close_notes": "Restarted affected worker and opened follow-up capacity investigation.", "cmdb_ci": "policy-api", "sys_created_on": ts(24 * 28)},
    ]
    if text:
        records = [r for r in records if text.lower() in r["short_description"].lower()]
    return records[:limit]

# SonarCloud.
def quality_gate(project):
    return {"projectStatus": {"status": "ERROR", "conditions": [
        {"metricKey": "new_vulnerabilities", "status": "ERROR", "actualValue": "1", "errorThreshold": "0"},
        {"metricKey": "new_coverage", "status": "WARN", "actualValue": "71.2", "warningThreshold": "80"},
    ], "ignoredConditions": False}, "projectKey": project}

def measures(project):
    return {"component": {"key": project, "name": "Policy API", "measures": [
        {"metric": "alert_status", "value": "ERROR"}, {"metric": "bugs", "value": "4"},
        {"metric": "vulnerabilities", "value": "2"}, {"metric": "security_hotspots", "value": "5"},
        {"metric": "code_smells", "value": "38"}, {"metric": "coverage", "value": "71.2"},
        {"metric": "duplicated_lines_density", "value": "3.8"}, {"metric": "sqale_index", "value": "540"},
    ]}}

def issues(project):
    return {"total": 3, "p": 1, "ps": 100, "issues": [
        {"key": "SYNTH-SEC-001", "rule": "python:S5131", "severity": "CRITICAL", "type": "VULNERABILITY", "component": project + ":src/api.py", "message": "Review untrusted input handling in policy submission endpoint.", "status": "OPEN", "creationDate": ts(90)},
        {"key": "SYNTH-BUG-002", "rule": "python:S####", "severity": "MAJOR", "type": "BUG", "component": project + ":src/db.py", "message": "Potential connection cleanup issue on exception path.", "status": "OPEN", "creationDate": ts(180)},
        {"key": "SYNTH-CODE-003", "rule": "python:S####", "severity": "MINOR", "type": "CODE_SMELL", "component": project + ":src/utils.py", "message": "Simplify duplicated validation logic.", "status": "OPEN", "creationDate": ts(300)},
    ]}

# Azure Cost Management / budgets.
def get_cost_by_resource(subscription_id, lookback_days=30):
    return _ok("AzureCostManagement-MOCK", currency_and_units=["Cost", "ResourceId", "ResourceGroupName", "ServiceName", "UsageDate"], period={"from": (NOW.date() - timedelta(days=lookback_days)).isoformat(), "to": NOW.date().isoformat()}, row_count=4, rows=[
        {"Cost": 1840.50, "ResourceId": "/subscriptions/demo/resourceGroups/rg-policy-prod/providers/Microsoft.Sql/servers/policy-sql", "ResourceGroupName": "rg-policy-prod", "ServiceName": "Azure SQL Database", "UsageDate": ts(24).split("T")[0]},
        {"Cost": 1260.00, "ResourceId": "/subscriptions/demo/resourceGroups/rg-policy-prod/providers/Microsoft.Compute/virtualMachines/policy-worker-01", "ResourceGroupName": "rg-policy-prod", "ServiceName": "Virtual Machines", "UsageDate": ts(24).split("T")[0]},
        {"Cost": 640.25, "ResourceId": "/subscriptions/demo/resourceGroups/rg-policy-prod/providers/Microsoft.Storage/storageAccounts/policystorage", "ResourceGroupName": "rg-policy-prod", "ServiceName": "Storage", "UsageDate": ts(24).split("T")[0]},
        {"Cost": 390.75, "ResourceId": "/subscriptions/demo/resourceGroups/rg-shared-prod/providers/Microsoft.Network/applicationGateways/policy-agw", "ResourceGroupName": "rg-shared-prod", "ServiceName": "Application Gateway", "UsageDate": ts(24).split("T")[0]},
    ], note="SYNTHETIC DEMO DATA. Currency is illustrative USD; not a real Azure bill.")

def get_budgets(subscription_id):
    return _ok("AzureBudgets-MOCK", count=1, budgets=[
        {"name": "policy-platform-monthly", "amount": 6000, "time_grain": "Monthly", "time_period": {"startDate": NOW.date().replace(day=1).isoformat()}, "current_spend": {"amount": 4131.50, "unit": "USD"}, "notifications": {"Actual80": {"enabled": True, "threshold": 80}}}
    ], note="SYNTHETIC DEMO DATA. Illustrative USD budget only.")
