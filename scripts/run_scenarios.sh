#!/usr/bin/env bash
# Run the six course scenarios + lab scenarios against ict_agent_lab and save
# raw outputs (12-digit AWS account IDs redacted) to tests/outputs/.
set -uo pipefail
cd "$(dirname "$0")/.."
AGENT=ict_agent_lab
OUT=tests/outputs
FRESH="CUST-LAB-$(date +%Y%m%d%H%M)"   # fresh customer id: no prior memory
mkdir -p "$OUT"

run() {  # run <file> <json-payload>
  local file="$1" payload="$2"
  local sid; sid="lab-$(basename "$file" .txt)-$(date +%s)-$(printf '%020d' 0)"
  {
    echo "\$ agentcore invoke --agent $AGENT '$payload' --session-id $sid"
    uv run agentcore invoke --agent "$AGENT" "$payload" --session-id "$sid" 2>&1
    echo "[exit code: $?]"
  } | sed -E 's/[0-9]{12}/XXXXXXXXXXXX/g' > "$OUT/$file"
  echo "saved $OUT/$file"
}

run test1_order_tracking.txt '{"prompt": "Can you track order ORD-001?", "customer_id": "CUST-123", "session_id": "t1"}'
run test2_refund.txt '{"prompt": "I want to return my Kindle Paperwhite (ORD-002). Please initiate a refund.", "customer_id": "CUST-123", "session_id": "t2"}'
run test3_kb_loyalty.txt '{"prompt": "What are the benefits of the Platinum loyalty tier?", "customer_id": "CUST-123", "session_id": "t3"}'
run test4a_memory_store.txt "{\"prompt\": \"Hi, I am Jane. I prefer concise responses.\", \"customer_id\": \"$FRESH\", \"session_id\": \"s-A\"}"
sleep 60   # let long-term memory extraction finish
run test4b_memory_recall.txt "{\"prompt\": \"Do you remember my name and communication preference?\", \"customer_id\": \"$FRESH\", \"session_id\": \"s-B\"}"
run test5_discount_fresh.txt "{\"prompt\": \"I am a Gold member with 4250 points. Calculate my discount on a \$150 standard order.\", \"customer_id\": \"$FRESH\", \"session_id\": \"t5\"}"
run test5_discount_cust123_stale_memory.txt '{"prompt": "I am a Gold member with 4250 points. Calculate my discount on a $150 standard order.", "customer_id": "CUST-123", "session_id": "t5b"}'
run test6_browser.txt '{"prompt": "Go to https://www.udacity.com and tell me the page title.", "customer_id": "CUST-123", "session_id": "t6"}'
run test7_risk_reward.txt "{\"prompt\": \"Long NQ: entry 18000, stop 17980, target 18060. What is my risk, reward and R multiple?\", \"customer_id\": \"$FRESH\", \"session_id\": \"t7\"}"
run test8_hypothesis.txt "{\"prompt\": \"Does NQ retrace to the NY midnight open during the 10-11am NY Silver Bullet window?\", \"customer_id\": \"$FRESH\", \"session_id\": \"t8\"}"
run test9_ftn_workflow.txt "{\"prompt\": \"Run the FTN workflow on the sample_eurusd fixture. Give me the chosen family, the four levels, PD-array confluence, NO-TRADE reasons and the paper ticket kind.\", \"customer_id\": \"$FRESH\", \"session_id\": \"t9\"}"
run test10_ftn_briefing.txt "{\"prompt\": \"Give me the FTN Month-9 briefing for the integration_m1_m9_eurusd fixture and list each candidate module with its state and reason.\", \"customer_id\": \"$FRESH\", \"session_id\": \"t10\"}"
echo "fresh customer id: $FRESH"
