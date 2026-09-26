"""Helpers for calling AgentCore Gateway (MCP) tools from thin wrapper tools.

The Gateway exposes Lambda tools as ``<TargetName>___<toolName>``. Lambda
targets return the Lambda payload verbatim, which for these Lambdas is an
API-Gateway style ``{"statusCode": 200, "body": "<json string>"}``; the
API Gateway target returns the parsed body. ``parse_gateway_result`` handles
both shapes.
"""
from __future__ import annotations

import json
from typing import Any, Iterable


class GatewayError(Exception):
    """Raised when a gateway tool result cannot be used."""


def resolve_tool_name(available: Iterable[str], bare_name: str) -> str | None:
    """Return the full gateway tool name for ``bare_name`` (exact or ``*___bare``)."""
    names = list(available)
    if bare_name in names:
        return bare_name
    for name in names:
        if name.endswith("___" + bare_name):
            return name
    return None


def _maybe_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return value
    return value


def parse_gateway_result(result: Any) -> dict:
    """Turn an MCP tool result (strands ``MCPToolResult`` dict) into a payload dict.

    Raises GatewayError on tool errors, non-2xx status codes or non-JSON output.
    """
    if not isinstance(result, dict):
        raise GatewayError(f"Unexpected tool result type: {type(result).__name__}")

    if result.get("status") == "error" or result.get("isError"):
        text = " ".join(c.get("text", "") for c in result.get("content", []) if isinstance(c, dict))
        raise GatewayError(f"Gateway tool error: {text.strip() or 'unknown error'}")

    payload: Any = result.get("structuredContent")
    if not payload:
        text = "".join(c.get("text", "") for c in result.get("content", []) if isinstance(c, dict))
        payload = _maybe_json(text)

    # Unwrap {"statusCode": ..., "body": "..."} (Lambda proxy style).
    if isinstance(payload, dict) and "statusCode" in payload and "body" in payload:
        status = payload.get("statusCode")
        body = _maybe_json(payload.get("body"))
        if not isinstance(status, int) or not 200 <= status < 300:
            raise GatewayError(f"Tool returned status {status}: {body}")
        payload = body

    if not isinstance(payload, dict):
        raise GatewayError(f"Tool did not return a JSON object: {str(payload)[:200]}")
    if "error" in payload and len(payload) <= 2:
        raise GatewayError(f"Tool reported an error: {payload['error']}")
    return payload


def resolve_refund_amount(order_total: float, requested: float | None) -> float:
    """Decide the refund amount from the order total and an optional request.

    - No amount requested -> full order total.
    - Requested amount must be > 0 and must not exceed the order total.
    """
    if order_total is None or order_total <= 0:
        raise ValueError("Order total is missing or not positive; cannot compute a refund amount.")
    if requested is None:
        return round(float(order_total), 2)
    if requested <= 0:
        raise ValueError("Refund amount must be greater than 0.")
    if requested - order_total > 0.005:
        raise ValueError(
            f"Refund amount {requested:.2f} exceeds the order total {order_total:.2f}."
        )
    return round(float(requested), 2)


def error_json(message: str, **extra: Any) -> str:
    """Uniform error payload returned to the agent."""
    return json.dumps({"error": message, **extra})
