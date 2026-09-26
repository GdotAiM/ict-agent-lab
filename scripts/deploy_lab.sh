#!/usr/bin/env bash
# Deploy the lab agent as its OWN AgentCore runtime (ict_agent_lab).
# Run from the repo root with AWS credentials for us-east-1 in the environment.
# This repo has its own .bedrock_agentcore.yaml (gitignored), so the course
# runtime `customer_support_agent` is never touched.
set -euo pipefail
cd "$(dirname "$0")/.."
AGENT=ict_agent_lab

uv run agentcore configure --entrypoint main.py --name "$AGENT" \
  --deployment-type direct_code_deploy --runtime PYTHON_3_13 \
  --disable-memory --region us-east-1 --non-interactive
uv run agentcore deploy --agent "$AGENT" --auto-update-on-conflict
# Grant the new runtime role access to the reused KB, Memory and Browser.
uv run setup_permissions.py --agent "$AGENT"
