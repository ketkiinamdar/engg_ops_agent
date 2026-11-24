import os
from agentic_workflow import TOOL_CATALOG, TEAM_TOOL_SCOPE, _json_from_llm


def test_planner_json_parser():
    assert _json_from_llm('```json\n{"tools":["builds"],"done":false}\n```')["tools"] == ["builds"]
    assert _json_from_llm("not json") == {}


def test_tool_allowlist_and_scopes():
    assert "finops_cost" in TOOL_CATALOG
    assert "sonar_issues" in TEAM_TOOL_SCOPE["Development"]
    assert "finops_cost" not in TEAM_TOOL_SCOPE["Development"]


def test_mock_collectors_are_available():
    os.environ["DATA_MODE"] = "mock"
    from agentic_workflow import _invoke_collector
    state = {"service": "policy-api", "environment": "production", "lookback_hours": 24}
    assert _invoke_collector("builds", state)["build_count"] == 3
    assert _invoke_collector("servicenow_incidents", state)["records"]
    assert _invoke_collector("sonar_quality_gate", state)["projectStatus"]["status"] == "ERROR"
    assert _invoke_collector("finops_cost", state)["row_count"] > 0


def test_operation_id_correlation():
    from agentic_workflow import _correlate_evidence
    evidence = {
        "requests": {"data": {"rows": [{"OperationId": "op-1", "ResultCode": "500"}]}},
        "exceptions": {"data": {"rows": [{"OperationId": "op-1", "ExceptionType": "SqlException"}]}},
    }
    result = _correlate_evidence(evidence)
    assert result["shared_operation_id_groups"][0]["operation_id"] == "op-1"
