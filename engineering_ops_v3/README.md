# Engineering Operations Agent – v3 starter

This is an evidence-first implementation starter based on the uploaded `AI.zip`. It preserves the Ollama/Qwen3 approach and the existing Azure Monitor, Azure DevOps, ServiceNow and SonarCloud clients. It adds specialist Platform/Development/FinOps analyses, a supervisor synthesis, structured source-health reporting, redaction and a read-only Azure Cost Management client.

## Important scope and limitations

- The supplied Azure DevOps client retrieves **build runs**. This package labels them as builds and does not claim they are deployments.
- The supplied Azure Monitor KQL functions do not consistently apply environment filters. This package records that limitation; do not use it as proof that all returned telemetry belongs to the requested environment. Add trusted resource/role-to-environment mappings and KQL filters before production use.
- The FinOps client retrieves Azure Cost Management actual cost and subscription budgets. It does **not** infer idle resources, utilization, safe right-sizing, or savings. Add Azure Monitor metrics/Advisor/Resource Graph collectors before making those recommendations.
- The uploaded archive does not include the referenced technology-intelligence module or dummy-data modules. They are not required by this v3 runner.
- The code is a starter, not a production security certification. Validate API permissions, data classification, retention, network egress, audit destination and enterprise identity configuration with your security team.

## Layout

- `agent_v3.py`: collection -> three specialist analyses -> supervisor synthesis -> Markdown report.
- `evidence.py`: isolated source collectors; unavailable sources remain explicitly unavailable.
- `security/controls.py`: recursive secret/email/JWT redaction before evidence is passed to the model.
- `clients/`: the four supplied clients plus `azure_finops_client.py`.

## Setup

1. Create a virtual environment and install `requirements.txt`.
2. Copy `.env.example` to `.env`; populate only the integrations you intend to enable.
3. Ensure these files are importable as packages (empty `__init__.py` files are included).
4. Run `az login` for local testing, or use a managed identity in Azure with least-privilege access.
5. Start Ollama and pull the configured model.
6. Run `python agent_v3.py`.

Missing or misconfigured integrations are reported as unavailable rather than being interpreted as healthy. Do not put credentials in source control.

## Security deployment checklist

- Replace local Azure CLI authentication with a managed identity in hosted environments.
- Grant only Log Analytics query, required Azure DevOps read, ServiceNow read, SonarCloud project-scoped read and subscription cost-read permissions.
- Use OAuth for ServiceNow if enabled by your instance; the supplied legacy client uses Basic authentication and must be upgraded to your enterprise-approved method.
- Use a secret manager for tokens; never commit `.env`.
- Put Ollama behind private networking and authenticated workload access; restrict outbound network access.
- Apply environment/service authorization before collection. The sample CLI runner is an operator utility, not an authenticated multi-user API.
- Review redaction against your actual telemetry schema. Redaction is defense-in-depth, not a substitute for field allowlists and data minimization.
- Keep all actions read-only. No automatic remediation, incident creation, deployment or resource modification is exposed.
- Encrypt reports, restrict report access, and define retention/deletion policies.

## Report outputs

Each run writes one Markdown report containing the consolidated supervisor summary, Platform/Development/FinOps specialist sections, source availability and a redacted evidence bundle. LLM conclusions are advisory and must be reviewed by an engineer.

## Dummy data / offline demonstration

The project includes `clients/mock_data.py`, a set of entirely fictional fixtures for:

- Azure Monitor / Application Insights: requests, exceptions, dependencies, traces and Azure Activity.
- Azure DevOps: build runs (not deployments).
- ServiceNow: historical incident records and resolution notes.
- SonarCloud: quality gate, measures and sample issues.
- Azure Cost Management: resource-level cost rows and a sample budget.

To run without connecting to the external services, set this in `.env`:

```dotenv
DATA_MODE=mock
SERVICE_NAME=policy-api
ENVIRONMENT=production
SONARCLOUD_PROJECT_KEY=demo-policy-api
AZURE_SUBSCRIPTION_ID=00000000-0000-0000-0000-000000000001
```

Then run `python agent_v3.py` as usual. Ollama must still be running for LLM-generated reports. The fixtures are time-relative so the sample events remain recent when rerun. They are intentionally synthetic and must never be mixed with production evidence or represented as real customer/operational findings.

To return to real integrations, set `DATA_MODE=live` and configure the real credentials and permissions. The mock mode is an application-level fixture selector, not a substitute for access control or production authentication.
