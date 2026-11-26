# Engineering Operations Agent – Concise Health Reporting

## 1. Overview

`agentic_workflow_report_optimized.py` implements a bounded, read-only, agentic workflow for reviewing an application's engineering operations across Platform, Development and FinOps.

The workflow uses LangGraph to plan data collection, execute approved collectors, observe source results, correlate telemetry, run team-specific analysis and synthesize a concise report for management and engineering teams.

The implementation produces two files for each investigation:

- **Management/engineering report (`.md`)** – a short, decision-oriented health report.
- **Diagnostics (`_diagnostics.json`)** – detailed execution trace, source status, specialist outputs, correlations, collector errors and redacted evidence for technical investigation.

The workflow does not perform remediation or write changes to connected systems.

## 2. Workflow

The LangGraph workflow follows this sequence:

1. **Plan** – an LLM selects relevant collectors from a fixed allowlist.
2. **Act** – the selected read-only collector functions retrieve data.
3. **Observe** – the workflow checks source outcomes and whether the investigation should continue.
4. **Re-plan** – if the review is not complete and the round limit has not been reached, the planner selects further collectors.
5. **Correlate** – telemetry records are grouped by shared Application Insights operation IDs.
6. **Specialist review** – Platform, Development and FinOps specialists analyse the available evidence.
7. **Supervisor** – a final LLM synthesis produces the concise report.

The planner is limited to the named collector allowlist and selects no more than five collectors per round. The initial round attempts a baseline set of sources: Application Insights, Azure DevOps builds, ServiceNow incidents, SonarCloud quality gate and Azure cost data.

## 3. Report contents

### Human-readable Markdown report

The generated report contains:

- **Investigation header** – service, environment, lookback period, investigation ID, completion time, data mode and read-only designation.
- **Overall status** – Critical, Attention Required, Healthy or Insufficient Data, with an explanation.
- **Management summary** – up to three material risks or decisions/escalations.
- **Team actions** – concise findings and actions for Platform, Development and FinOps.
- **Priority action list** – up to three prioritised actions with owner and validation criteria.
- **Data confidence and gaps** – unavailable sources and important limitations.
- **Data coverage** – status of each collector that was attempted.
- **Important limitations** – known interpretation constraints.

The supervisor prompt requests a report of no more than 350 words. The three specialist prompts each request fewer than 180 words. These are prompt instructions to the language model, not a hard post-generation word-count enforcement mechanism.

### Diagnostics JSON

The diagnostics file contains:

- Investigation ID and UTC start/completion timestamps
- Planning-round history and selected collectors
- Executed collector names and source statuses
- Telemetry correlations
- Collector error codes
- Specialist reports
- Redacted evidence returned by collectors

Treat diagnostics as operationally sensitive. Redaction is applied through `security.controls.redact`, but the resulting file should still be stored and shared according to your organisation's data-handling policy.

## 4. Data sources and collector mapping

The implementation expects these Python modules and functions in the project:

| Data area | Collector name | Expected module and function |
|---|---|---|
| Application Insights | `appinsights` | `clients.azure_monitor_client.get_real_application_insights_data` |
| Application exceptions | `exceptions` | `clients.azure_monitor_client.get_application_exceptions` |
| Failed requests | `failed_requests` | `clients.azure_monitor_client.get_failed_application_requests` |
| Failed dependencies | `failed_dependencies` | `clients.azure_monitor_client.get_failed_dependencies` |
| Azure activity | `azure_activity` | `clients.azure_monitor_client.get_azure_activity` |
| Azure DevOps builds | `builds` | `clients.azure_devops_client.get_recent_builds` |
| ServiceNow incidents | `servicenow_incidents` | `clients.servicenow_client.search_incidents` |
| SonarCloud quality gate | `sonar_quality_gate` | `clients.sonarcloud_client.quality_gate` |
| SonarCloud measures | `sonar_measures` | `clients.sonarcloud_client.measures` |
| SonarCloud issues | `sonar_issues` | `clients.sonarcloud_client.issues` |
| Azure actual cost | `finops_cost` | `clients.azure_finops_client.get_cost_by_resource` |
| Azure budgets | `finops_budgets` | `clients.azure_finops_client.get_budgets` |

Each live collector is called using the function signature shown by the workflow. Ensure your client implementations accept those arguments and return data in a dictionary-compatible structure. The workflow wraps the returned data with a source status and timestamps.

For `DATA_MODE=mock`, the implementation imports `clients.mock_data` and expects that module to expose the collector function names above. The mock module therefore needs to provide all functions that may be selected during a run.

## 5. Prerequisites

- Python 3.10 or later (use the Python version supported by your dependency set).
- A locally accessible Ollama service.
- An Ollama model available locally, such as the default `qwen3:8b`.
- LangGraph and LangChain's Ollama integration.
- The project-specific `clients` package and its collector modules.
- The project-specific `security.controls` module with a `redact` function.
- Credentials and permissions required by the enabled data-source clients.

The workflow file does not define or install the client integrations, authentication, Azure Monitor queries, ServiceNow API configuration or SonarCloud client configuration. Those must be implemented and configured in the surrounding project.

## 6. Installation

Create and activate a virtual environment.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install the Python packages used directly by this workflow:

```bash
pip install langgraph langchain-ollama python-dotenv
```

Install the dependencies required by your individual collector clients separately. For example, Azure, Azure DevOps, ServiceNow and SonarCloud clients may have their own SDK or HTTP-client requirements.

Place `agentic_workflow_report_optimized.py` in your project and ensure it can import:

```text
clients/
    __init__.py
    azure_monitor_client.py
    azure_devops_client.py
    servicenow_client.py
    sonarcloud_client.py
    azure_finops_client.py
    mock_data.py              # required when DATA_MODE=mock
security/
    __init__.py
    controls.py
```

The exact internal structure of each client is project-specific.

## 7. Configuration

Create a `.env` file in the working directory from which the application is launched.

```dotenv
# Local Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b

# Data collection mode: live or mock
DATA_MODE=live

# Report output directory
REPORT_DIR=reports

# Allowed environment values, comma-separated
ALLOWED_ENVIRONMENTS=dev,qa,uat,production

# Application Insights role name; if empty, service argument is used
APPINSIGHTS_ROLE_NAME=

# SonarCloud project key
SONARCLOUD_PROJECT_KEY=

# Azure subscription ID used by FinOps collectors
AZURE_SUBSCRIPTION_ID=
```

Notes:

- `OLLAMA_MODEL` defaults to `qwen3:8b`.
- `OLLAMA_BASE_URL` defaults to `http://localhost:11434`.
- `DATA_MODE` defaults to `live`. Use `mock` only when the mock collector module is implemented and populated.
- `REPORT_DIR` defaults to `reports`.
- `ALLOWED_ENVIRONMENTS` defaults to `dev,qa,uat,production`.
- `SONARCLOUD_PROJECT_KEY` is required when a SonarCloud collector is invoked in live mode.
- `AZURE_SUBSCRIPTION_ID` is required when a FinOps collector is invoked in live mode.
- The workflow uses `APPINSIGHTS_ROLE_NAME` if set; otherwise it uses the supplied service name.
- Authentication settings for the individual clients are not specified by this workflow. Configure them using the authentication approach implemented by each client.

Do not commit secrets or credentials to source control. Add `.env`, virtual environments and generated reports/diagnostics to `.gitignore` as appropriate for your organisation.

## 8. Running an investigation

The workflow exposes the function:

```python
run_agentic_review(
    service: str,
    environment: str,
    lookback_hours: int = 24,
    max_rounds: int = 3,
) -> dict
```

Example invocation from a Python script:

```python
from agentic_workflow_report_optimized import run_agentic_review

result = run_agentic_review(
    service="policy-api",
    environment="production",
    lookback_hours=24,
    max_rounds=3,
)

print("Investigation:", result["investigation_id"])
print("Report:", result["report_path"])
print("Diagnostics:", result["diagnostics_path"])
print(result["report"])
```

Input validation:

- `service` must contain 1–64 characters and match letters, digits, period, underscore or hyphen.
- `environment` must be present in `ALLOWED_ENVIRONMENTS`.
- `lookback_hours` must be between 1 and 96.
- `max_rounds` must be between 1 and 5.

The function returns a dictionary containing the investigation ID, report path, diagnostics path, report text and planning execution trace.

## 9. Output files

By default, output is written to the `reports/` directory.

```text
reports/
    <investigation-id>.md
    <investigation-id>_diagnostics.json
```

The Markdown file is intended for management and team review. The JSON file is intended for engineering troubleshooting and audit support.

## 10. How to interpret the results

- **Critical** – the available evidence indicates a critical issue requiring urgent review.
- **Attention Required** – the evidence indicates material concerns that need action or investigation.
- **Healthy** – no material issue was evidenced in the available data. This is not a guarantee that the service has no problems.
- **Insufficient Data** – the available evidence is too incomplete to support a meaningful health assessment.

Always review the data coverage and limitations before making operational decisions. In particular:

1. Azure Monitor environment attribution is not fully verified by this implementation.
2. Azure DevOps records are build runs, not confirmed deployments.
3. Cost and budget data alone do not establish idle resources, waste, safe right-sizing or achievable savings.
4. Missing or unavailable sources must not be interpreted as evidence of a healthy service.
5. Shared Application Insights operation IDs show telemetry correlation; they do not independently prove root cause.
6. Recommendations are analysis outputs. They are not automatically executed.

## 11. Security and operational considerations

- The workflow is designed for read-only data collection; it does not execute remediation.
- The LLM selects from fixed collector names. It does not supply executable code or arbitrary collector URLs.
- Collector evidence is passed through the project's `redact` function before being included in analysis and diagnostics.
- Logs, incidents, telemetry and other retrieved content are treated as untrusted evidence in specialist prompts.
- Apply least-privilege access to every connected service.
- Restrict access and retention for generated diagnostics, which may contain operational details even after redaction.
- Review AI-generated findings and recommendations with the responsible engineering owner before acting.

## 12. Troubleshooting

| Symptom | Checks |
|---|---|
| Ollama connection error | Confirm Ollama is running, the base URL is reachable and the configured model is available. |
| Model not found | Pull the configured model into Ollama or update `OLLAMA_MODEL`. |
| `ModuleNotFoundError` for `clients` or `security` | Run from the project root and verify the expected packages and `__init__.py` files exist. |
| Collector unavailable | Check the relevant client module, credentials, permissions, network access and required environment variables. |
| SonarCloud collector reports missing configuration | Set `SONARCLOUD_PROJECT_KEY` and verify the SonarCloud client configuration. |
| FinOps collector reports missing configuration | Set `AZURE_SUBSCRIPTION_ID` and verify the Azure Cost Management permissions and client configuration. |
| Report says Insufficient Data | Inspect the report's Data coverage section and the matching diagnostics JSON for unavailable sources and collector errors. |
| Diagnostics file is missing | Check the process output for file-system permissions and verify `REPORT_DIR` is writable. |

The workflow logs collector and agent failures through the Python logger named `engineering_ops.agentic`. Configure logging in the calling application to control log level and destinations.

## 13. Current scope and future enhancements

This implementation provides bounded, evidence-based analysis and concise reporting. It does not currently provide:

- Verified deployment-to-incident correlation.
- Fully verified environment filtering for all Azure Monitor queries.
- Resource utilisation analysis or automated rightsizing recommendations based on utilisation.
- Cost forecasting or verified savings calculations.
- Automated incident creation, remediation or infrastructure changes.
- A guaranteed numeric health score.

These capabilities require additional source integrations, validated data mappings and explicit business rules.

---

**Important:** This README describes the interfaces and behaviour visible in `agentic_workflow_report_optimized.py`. Confirm the actual collector implementations, authentication requirements, Python version and dependency versions in your repository before deploying to a production environment.
