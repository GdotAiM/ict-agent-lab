#!/usr/bin/env bash
# Remove ONLY the lab runtime. Never run `agentcore destroy` in the course repo.
set -euo pipefail
cd "$(dirname "$0")/.."
uv run agentcore destroy --agent ict_agent_lab
# If you deployed the optional lab Lambda / gateway target, delete them too, e.g.:
#   aws lambda delete-function --function-name refund-processor-lab --region us-east-1
