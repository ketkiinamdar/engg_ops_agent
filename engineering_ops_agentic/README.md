# Agentic Engineering Operations Agent

This version uses a **LangGraph state machine** to implement a bounded agentic loop:

1. **Plan:** Qwen3 chooses from a fixed allowlist of read-only data collectors and explains why.
2. **Act:** The orchestrator executes only approved Python collector functions. It never executes model-generated code, shell commands, URLs or arbitrary queries.
3. **Observe:** Collector outcomes, missing sources and evidence status are inspected deterministically.
4. **Re-plan:** The planner can request additional allowlisted evidence. The loop is bounded by `AGENT_MAX_ROUNDS` (1–5).
5. **Correlate:** Deterministically group telemetry sharing the same Application Insights operation ID; temporal association is never treated as proof of causation.
6. **Specialists:** Platform, Development and FinOps agents analyze the collected evidence independently.
7. **Supervisor:** A final agent synthesizes cross-team risks and an action register.
8. **Trace:** The report records plan decisions, executed collectors, source status and collection errors.

This is an agentic workflow, not merely three independent prompts: the LLM makes bounded tool-selection decisions, the graph executes validated actions, observes results and loops back to planning before specialist analysis.

## Run

```bash
python -m venv .venv
# activate the environment
pip install -r requirements.txt
cp .env.example .env
ollama pull qwen3:8b
ollama serve
python agent_v3.py
```

For synthetic local data, set `DATA_MODE=mock` and configure `SERVICE_NAME`, `ENVIRONMENT`, `SONARCLOUD_PROJECT_KEY` and `AZURE_SUBSCRIPTION_ID`. Ollama is still required for planning and analysis. `DATA_MODE=mock` selects fictional fixture data; it does not authenticate or authorize access to live systems.

## What is genuinely agentic here?

- Model-driven evidence planning using a constrained tool catalogue.
- Bounded plan/act/observe/re-plan loop.
- Tool selection based on evidence already collected and remaining sources.
- Independent team-specialist reasoning.
- Supervisor synthesis after specialist results.
- Execution trace for auditability and troubleshooting.

## Important current boundaries

- All tools are read-only. There is no autonomous ticket creation, deployment, Terraform apply, resource modification or remediation.
- The planner chooses from fixed function names only. Tool arguments are assembled by trusted Python code, not accepted from the model.
- The current Azure DevOps client returns **build runs**, not deployment records.
- The current Azure Monitor KQL queries do not consistently filter by environment. The requested environment is recorded in report scope but is not proof that every returned record belongs to it. Add trusted resource/role-to-environment mappings and enforce KQL filters before production use.
- FinOps currently includes actual cost and budgets only. It does not prove utilization, idleness, safe right-sizing or savings. Add metrics, Resource Graph and Azure Advisor evidence before those recommendations.
- Existing ServiceNow client uses Basic authentication. Upgrade to approved OAuth before production.
- The project has no production-ready multi-user Entra authorization/API boundary, durable checkpoint store, notification service or report-access control yet. Add these before hosting for multiple users.
- LLM conclusions are advisory. Validate evidence and recommendations with accountable engineers.

## Security

- The model can select only allowlisted read-only collectors.
- The model cannot generate executable code or choose arbitrary endpoints/query strings.
- Source evidence is redacted before analysis; redaction is defense-in-depth, not a substitute for schema allowlists and data minimization.
- Keep credentials in Key Vault or an approved secret manager, not `.env` in deployed environments.
- Use managed identity for Azure hosted workloads and least-privilege roles for each source.
- Restrict Ollama to private authenticated network access; control egress.
- Add Entra ID authentication, service/environment RBAC, audit persistence, encryption and retention before production deployment.

## Testing

```bash
pytest -q
python -m compileall -q .
```

The included tests validate the constrained planner parser, team tool scopes and mock collectors. They do not validate live API credentials or live integrations.
