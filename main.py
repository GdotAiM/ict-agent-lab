"""
ICT Agent Lab -- personal extension of the course customer-support agent
=========================================================================
PERSONAL LAB COPY (not the Udacity submission). Deployed as the separate
AgentCore runtime `ict_agent_lab`; reuses the course KB, Memory and Gateway.

Original description:
Customer Support AI Agent (Amazon Bedrock AgentCore + Strands Agents)
A customer support agent for an Amazon-style store, served by the AgentCore
Runtime (BedrockAgentCoreApp). It uses Amazon Nova 2 Lite via Bedrock and has:

- search_knowledge_base       -- RAG over the product catalog / policies (Bedrock KB)
- calculate_loyalty_discount  -- exact loyalty maths in the AgentCore Code Interpreter
- AgentCore Browser           -- live web lookups
- Gateway (MCP) tools         -- order tracking and refund processing Lambdas
- MemoryHook                  -- AgentCore long-term memory (facts + preferences)
                                 keyed by customer_id

Set GATEWAY_URL, KB_ID, REGION and MEMORY_ID below before running.

Deploy with the Starter Toolkit (from starter/):
    agentcore configure --entrypoint main.py --name <agent-name> --deployment-type direct_code_deploy --runtime PYTHON_3_13 --disable-memory
    agentcore deploy
    uv run setup_permissions.py

Invoke the deployed agent:
    agentcore invoke '{"prompt": "Can you track order ORD-001?", "customer_id": "CUST-123", "session_id": "t1"}'

Local CLI test: swap app.run() for main() at the bottom of this file, then
    uv run main.py '{"prompt": "Hello", "customer_id": "CUST-123", "session_id": "s1"}'
"""

# -- Imports ------------------------------------------------------------------
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from strands.models import BedrockModel
from strands.agent.conversation_manager import SummarizingConversationManager
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamable_http_client
import argparse, json
import os, asyncio, boto3
from strands.hooks import (
    HookProvider, AfterInvocationEvent, HookRegistry, MessageAddedEvent,
)
import logging
import uuid
from typing import Dict
from bedrock_agentcore.tools.code_interpreter_client import code_session
from strands_tools.browser import AgentCoreBrowser

from ict_lab.memory_utils import CONTEXT_HEADER, redact_amounts
from ict_lab.gateway import (
    GatewayError, error_json, parse_gateway_result, resolve_refund_amount,
    resolve_tool_name,
)
from pydantic import ValidationError
from ict_lab.models import (
    LoyaltyDiscountResult, OrderStatus, RefundRequest, RefundResult,
    validate_to_json, validation_error_json,
)
from ict_lab.loyalty import compute_loyalty_discount, normalize_category, normalize_tier
from ict_lab.ict_tools import hypothesis_json, risk_reward_json
from typing import List, Optional


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("ICT_Agent_Lab")


# -- TODO 1 -- App Initialisation ---------------------------------------------
app = BedrockAgentCoreApp()


# Suppress interactive tool-consent prompts (required in headless deployments).
os.environ["BYPASS_TOOL_CONSENT"] = "true"


# -- TODO 2 -- Configuration --------------------------------------------------
GATEWAY_URL = "https://customersupportagent-customersupportgateway-klmzs0vuvz.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
KB_ID       = "APLMUD7GVI"
REGION      = "us-east-1"
MEMORY_ID   = "CustomerSupportAgent_CustomerSupportMemory-jacOiD6KOb"


# -- TODO 3 -- Model and Clients ----------------------------------------------
model_id = "global.amazon.nova-2-lite-v1:0"

model = BedrockModel(model_id=model_id)
memory_client = MemoryClient(region_name=REGION)
_bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)


# -- TODO 4 -- Namespace Helper -----------------------------------------------
def get_namespaces(mem_client: MemoryClient, memory_id: str) -> Dict:
    """Return a dict mapping strategy type to namespace template string."""
    strategies = mem_client.get_memory_strategies(memory_id)
    namespaces = {}
    for s in strategies:
        # Current API field is namespaceTemplates; namespaces is the legacy name.
        ns = s.get("namespaceTemplates") or s.get("namespaces") or []
        strategy_type = (
            s.get("type") or s.get("memoryStrategyType") or s.get("strategyType")
        )
        if not ns or not strategy_type:
            continue
        namespaces[strategy_type] = ns[0]
    return namespaces


# -- TODO 5 -- Memory Hook ----------------------------------------------------
class MemoryHook(HookProvider):
    """Long-term memory hook for the customer support agent."""

    def __init__(
        self,
        actor_id: str,
        session_id: str,
        memory_client: MemoryClient,
        memory_id: str,
    ):
        self.actor_id = actor_id
        self.session_id = session_id
        self.memory_client = memory_client
        self.memory_id = memory_id
        self.namespaces = get_namespaces(self.memory_client, self.memory_id)

    def retrieve_customer_context(self, event: MessageAddedEvent):
        """Retrieve relevant memories and prepend them to the user message."""
        messages = event.agent.messages
        if (
            not messages
            or messages[-1]["role"] != "user"
            or "toolResult" in messages[-1]["content"][0]
        ):
            return

        user_query = messages[-1]["content"][0]["text"]
        try:
            all_context = []
            for strategy_type, namespace in self.namespaces.items():
                resolved_namespace = namespace.format(actorId=self.actor_id)
                memories = self.memory_client.retrieve_memories(
                    memory_id=self.memory_id,
                    namespace=resolved_namespace,
                    query=user_query,
                    top_k=5,
                )
                for memory in memories:
                    if isinstance(memory, dict):
                        text = memory.get("content", {}).get("text", "").strip()
                        if text:
                            all_context.append(f"[{strategy_type}] {text}")
            if all_context:
                context_block = "\n".join(all_context)
                original_text = messages[-1]["content"][0]["text"]
                messages[-1]["content"][0]["text"] = (
                    f"{CONTEXT_HEADER}\n{context_block}\n\n{original_text}"
                )
        except Exception as exc:
            logger.error("Failed to retrieve customer context: %s", exc)

    def save_support_interaction(self, event: AfterInvocationEvent):
        """Save the completed turn to memory after the agent responds."""
        try:
            messages = event.agent.messages
            user_text = agent_text = None

            for msg in reversed(messages):
                if msg["role"] == "assistant" and not agent_text:
                    content = msg["content"]
                    if isinstance(content, list):
                        agent_text = content[0].get("text", "")
                    else:
                        agent_text = str(content)
                elif (
                    msg["role"] == "user"
                    and not user_text
                    and "toolResult" not in msg["content"][0]
                ):
                    user_text = msg["content"][0]["text"]
                    break

            if user_text and agent_text:
                # Memory is for identity/preferences only: strip calculated or
                # looked-up money amounts so stale totals are never recalled.
                user_text = redact_amounts(user_text)
                agent_text = redact_amounts(agent_text)
                self.memory_client.create_event(
                    memory_id=self.memory_id,
                    actor_id=self.actor_id,
                    session_id=self.session_id,
                    messages=[
                        (user_text, "USER"),
                        (agent_text, "ASSISTANT"),
                    ],
                )
        except Exception as exc:
            logger.error("Failed to save support interaction: %s", exc)

    def register_hooks(self, registry: HookRegistry) -> None:
        """Register both memory callbacks."""
        registry.add_callback(MessageAddedEvent, self.retrieve_customer_context)
        registry.add_callback(AfterInvocationEvent, self.save_support_interaction)



# -- TODO 6 -- Knowledge Base Tool --------------------------------------------
@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the Amazon product catalog and support knowledge base.
    Use this for product specifications, return policies, warranty
    information, loyalty program details, and order status definitions.

    Args:
        query: The question or topic to search for

    Returns:
        Relevant information retrieved from the knowledge base
    """
    if not KB_ID:
        return "Knowledge base not configured."

    resp = _bedrock_runtime.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": query},
    )
    results = resp.get("retrievalResults", [])
    if not results:
        return f"No information found for: {query}"

    chunks = [r["content"]["text"] for r in results]
    return "\n---\n".join(chunks)



# -- TODO 7 -- Loyalty Discount Tool (Code Interpreter) -----------------------
@tool
def calculate_loyalty_discount(
    loyalty_points: int,
    tier: str,
    order_total: float,
    product_category: str = "standard",
) -> str:
    """
    Calculate the loyalty discount for a customer order using the
    AgentCore Code Interpreter. Runs exact arithmetic in a secure sandbox.

    Args:
        loyalty_points: Customer's current points balance
        tier: Customer tier -- Silver, Gold, or Platinum
        order_total: Order total in USD
        product_category: standard, device, or fresh

    Returns:
        Full discount breakdown and final price (validated LoyaltyDiscountResult JSON)
    """
    # Validate/normalise inputs first (also keeps arbitrary strings out of the sandbox code).
    try:
        tier = normalize_tier(tier)
        product_category = normalize_category(product_category)
        loyalty_points = int(loyalty_points)
        order_total = float(order_total)
        if order_total <= 0 or loyalty_points < 0:
            raise ValueError("order_total must be > 0 and loyalty_points >= 0")
    except (TypeError, ValueError) as exc:
        return json.dumps({"error": f"Invalid loyalty input: {exc}"})

    code = f"""
import json, math

loyalty_points = {loyalty_points}
tier = "{tier}"
order_total = {order_total}
product_category = "{product_category}"

earn_rates = {{"standard": 1, "device": 2, "fresh": 5}}
tier_rates = {{"Silver": 0.00, "Gold": 0.10, "Platinum": 0.15}}

# 100 points = $1; redeem in 500-point blocks (500 minimum),
# capped so the points value never exceeds 50% of the order total.
POINTS_PER_DOLLAR = 100
REDEEM_BLOCK = 500
max_redeemable_points = int(order_total * 0.5 * POINTS_PER_DOLLAR) // REDEEM_BLOCK * REDEEM_BLOCK
points_redeemed = (loyalty_points // REDEEM_BLOCK) * REDEEM_BLOCK
points_redeemed = min(points_redeemed, max_redeemable_points)
points_value = points_redeemed / POINTS_PER_DOLLAR

subtotal_after_points = order_total - points_value
tier_discount_rate = tier_rates.get(tier, 0.00)
tier_discount = subtotal_after_points * tier_discount_rate

final_total = subtotal_after_points - tier_discount
total_savings = order_total - final_total
points_earned = int(order_total * earn_rates.get(product_category, 1))
remaining_points = loyalty_points - points_redeemed + points_earned

result = {{
    "points_redeemed": points_redeemed,
    "points_value": round(points_value, 2),
    "tier": tier,
    "tier_discount_pct": round(tier_discount_rate * 100, 2),
    "tier_discount": round(tier_discount, 2),
    "original_total": order_total,
    "final_total": round(final_total, 2),
    "total_savings": round(total_savings, 2),
    "points_earned": points_earned,
    "remaining_points": remaining_points,
}}

print(json.dumps(result, indent=2))
"""

    try:
        with code_session(REGION) as code_client:
            response = code_client.invoke("executeCode", {
                "code": code,
                "language": "python",
                "clearContext": True,
            })

            for event in response["stream"]:
                result = event.get("result", {})
                if result.get("isError"):
                    raise RuntimeError(f"Code Interpreter error: {result}")
                # Prefer the sandbox's stdout; fall back to the text content blocks.
                stdout = (result.get("structuredContent") or {}).get("stdout")
                if not stdout:
                    stdout = "".join(
                        c.get("text", "")
                        for c in result.get("content", [])
                        if c.get("type") == "text"
                    )
                # Validate the sandbox JSON with Pydantic before returning it.
                return validate_to_json(LoyaltyDiscountResult, stdout)

            raise RuntimeError("Code Interpreter returned no result")

    except Exception as e:
        logger.warning("Code Interpreter unavailable, using fallback: %s", e)
        # Fallback: same rules computed locally in pure Python, still validated.
        fallback = compute_loyalty_discount(loyalty_points, tier, order_total, product_category)
        fallback["note"] = "Code Interpreter unavailable; computed locally with the same rules."
        return validate_to_json(LoyaltyDiscountResult, fallback)


# -- LAB -- ICT research tools ------------------------------------------------
@tool
def calculate_risk_reward(
    entry: float,
    stop_loss: float,
    target: float,
    direction: Optional[str] = None,
) -> str:
    """
    Calculate risk, reward and R multiple for a trade idea (price points per unit).
    Validates that the stop and target are on the correct side for the direction.

    Args:
        entry: Entry price
        stop_loss: Stop-loss price
        target: Target (take-profit) price
        direction: "long" or "short"; inferred from the stop if omitted

    Returns:
        RiskReward JSON (direction, entry, stop_loss, target, risk, reward, r_multiple)
        or an {"error": ...} JSON
    """
    return risk_reward_json(entry, stop_loss, target, direction)


@tool
def build_research_hypothesis(
    question: str,
    hypothesis: Optional[str] = None,
    instrument: Optional[str] = None,
    observable_condition: Optional[str] = None,
    invalidation_condition: Optional[str] = None,
    window_start: Optional[str] = None,
    window_end: Optional[str] = None,
    timezone: Optional[str] = None,
    required_evidence: Optional[List[str]] = None,
) -> str:
    """
    Turn a trading research question into a structured, testable ResearchHypothesis.
    Pass the user's question; instrument, time window (HH:MM 24h) and timezone are
    parsed from it when possible. Optional arguments override the parsed/default text.
    This does NOT answer the question -- it defines how to test it.

    Args:
        question: The research question, verbatim
        hypothesis: Optional one-sentence falsifiable hypothesis
        instrument: Optional instrument symbol, e.g. NQ
        observable_condition: Optional condition that can be measured in data
        invalidation_condition: Optional result that would reject the hypothesis
        window_start: Optional window start, HH:MM 24h
        window_end: Optional window end, HH:MM 24h
        timezone: Optional IANA timezone, e.g. America/New_York
        required_evidence: Optional list of data/evidence needed

    Returns:
        ResearchHypothesis JSON or an {"error": ...} JSON
    """
    overrides = {
        k: v for k, v in dict(
            hypothesis=hypothesis, instrument=instrument,
            observable_condition=observable_condition,
            invalidation_condition=invalidation_condition,
            window_start=window_start, window_end=window_end,
            timezone=timezone, required_evidence=required_evidence,
        ).items() if v
    }
    return hypothesis_json(question, **overrides)


# -- TODO 8 -- Agent Entrypoint -----------------------------------------------
SYSTEM_PROMPT = """You are a customer support agent for an Amazon store, running in a personal
lab build that is also being extended into an ICT trading research assistant. You help customers with:
- Product questions and specifications
- Order tracking and status updates
- Refund and return processing
- Loyalty program information and discount calculations
- General support inquiries
You have access to:
- A knowledge base with product catalog, return policies, and loyalty program details
- track_order / process_refund (validated wrappers around the AgentCore Gateway order and refund tools)
- Other Gateway tools (customer lookup, refund status, return labels)
- A code interpreter for precise loyalty discount calculations
- A browser for looking up live web information
- Persistent memory across sessions to remember customer identity and preferences
- ICT research tools: calculate_risk_reward (risk, reward, R multiple) and
  build_research_hypothesis (structured, testable research hypothesis)

ICT RESEARCH RULES:
- For trade risk/reward questions always call calculate_risk_reward and report its
  risk, reward and r_multiple exactly. If it returns an error, explain the error.
- For research questions call build_research_hypothesis and present the hypothesis,
  instrument, observable condition, invalidation condition, measurement window (with
  timezone) and required evidence. Do not claim the hypothesis is true or false;
  you have no market data. This is research tooling, not financial advice.

SOURCE-OF-TRUTH RULES (always follow):
1. Current tool results win. Prices, order totals, discounts, final totals, points,
   refund amounts and order status must come from a tool call made in THIS conversation.
2. Memory ("Customer Context") is only for identity (name, customer details the user
   stated) and preferences (tone, format). Never quote a price, total, discount, refund
   amount or order status from memory.
3. If memory and a tool result disagree, use the tool's number and do not mention the
   stale value.
4. If you need a number and have no tool result for it yet, call the tool first.

REFUND RULES:
- Before refunding, look up the order with track_order to get its total.
- Call process_refund with order_id, reason and amount (the order total for a full
  refund, or the smaller amount the customer asked for). Never refund $0.
- Report the refund amount exactly as returned by process_refund.

Always be helpful, accurate, and professional. Use the tools available to you
to provide the best possible support experience."""



@app.entrypoint
async def invoke(payload, context=None):
    """
    Main handler called by AgentCore for every incoming request.

    Expected payload keys:
    prompt (str, required) -- the customer's message
    customer_id (str, optional) -- unique customer identifier
    session_id (str, optional) -- session identifier; generated if absent
    """
    user_input = payload.get("prompt", "Hello!")
    actor_id = payload.get("customer_id", "anonymous")
    session_id = payload.get("session_id", str(uuid.uuid4()))

    memory_hook = MemoryHook(
        actor_id=actor_id,
        session_id=session_id,
        memory_client=memory_client,
        memory_id=MEMORY_ID,
    )

    agent_core_browser = AgentCoreBrowser(region=REGION)

    tools = [
        search_knowledge_base, calculate_loyalty_discount, agent_core_browser.browser,
        calculate_risk_reward, build_research_hypothesis,
    ]

    client = MCPClient(
        lambda: streamable_http_client(url=GATEWAY_URL)
    )

    with client:
        gateway_tools = client.list_tools_sync()
        names = [t.tool_name for t in gateway_tools]
        order_tool = resolve_tool_name(names, "get_order")
        refund_tool = resolve_tool_name(names, "initiate_refund")

        def call_gateway(name: str, arguments: dict) -> dict:
            result = client.call_tool_sync(
                tool_use_id=f"lab-{uuid.uuid4()}", name=name, arguments=arguments,
            )
            return parse_gateway_result(result)

        @tool
        def track_order(order_id: str) -> str:
            """
            Look up an order (status, items, total, tracking). Use this for any
            question about an order and before any refund.

            Args:
                order_id: Order ID, e.g. ORD-001

            Returns:
                Order details as JSON, or an {"error": ...} JSON
            """
            if not order_tool:
                return error_json("Order lookup tool is not available on the gateway.")
            try:
                return validate_to_json(
                    OrderStatus, call_gateway(order_tool, {"order_id": order_id})
                )
            except GatewayError as exc:
                return error_json(str(exc), order_id=order_id)

        @tool
        def process_refund(order_id: str, reason: str, amount: float) -> str:
            """
            Initiate a refund. Always look up the order total with track_order first
            and pass it as amount (or a smaller partial amount). amount must be > 0.

            Args:
                order_id: Order ID to refund, e.g. ORD-002
                reason: Reason for the refund
                amount: Refund amount in USD (> 0, <= order total)

            Returns:
                Refund confirmation as JSON, or an {"error": ...} JSON
            """
            if not (order_tool and refund_tool):
                return error_json("Order/refund tools are not available on the gateway.")
            try:
                order = OrderStatus.model_validate(
                    call_gateway(order_tool, {"order_id": order_id})
                )
                request = RefundRequest(
                    order_id=order.order_id,
                    reason=reason,
                    amount=resolve_refund_amount(order.total, amount),
                )
                refund = call_gateway(refund_tool, request.model_dump(include={"order_id", "reason", "amount"}))
                return validate_to_json(RefundResult, refund)
            except ValidationError as exc:
                return validation_error_json(exc.title, exc)
            except (GatewayError, ValueError) as exc:
                return error_json(str(exc), order_id=order_id)

        # Replace the raw get_order / initiate_refund tools with the wrappers.
        hidden = {order_tool, refund_tool}
        tools.extend(t for t in gateway_tools if t.tool_name not in hidden)
        tools.extend([track_order, process_refund])

        agent = Agent(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
            state={"actor_id": actor_id, "session_id": session_id},
            hooks=[memory_hook],
            # Summarise the oldest ~30% of messages on context overflow while keeping
            # the 10 most recent (tool-heavy research turns can get long).
            # Args checked against strands-agents 1.57.1 source.
            conversation_manager=SummarizingConversationManager(
                summary_ratio=0.3,
                preserve_recent_messages=10,
            ),
        )

        response = agent(user_input)
        return response


# -- CLI entry point (do not modify) -----------------------------------------
def main():
    """Run one invocation from the command line for local testing."""
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=str)
    args = parser.parse_args()
    response = asyncio.run(invoke(json.loads(args.payload)))
    print(response)


if __name__ == "__main__":
    app.run()
# Uncomment the line below and comment app.run() for local CLI testing:
# main()
