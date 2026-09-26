import json

import pytest

from ict_lab.gateway import (
    GatewayError, parse_gateway_result, resolve_refund_amount, resolve_tool_name,
)
from ict_lab.memory_utils import REDACTED, redact_amounts


def _mcp(text, status="success"):
    return {"status": status, "toolUseId": "t", "content": [{"text": text}]}


def test_resolve_tool_name():
    names = ["order_tracker___get_order", "refund_processor___initiate_refund"]
    assert resolve_tool_name(names, "get_order") == "order_tracker___get_order"
    assert resolve_tool_name(names, "initiate_refund") == "refund_processor___initiate_refund"
    assert resolve_tool_name(names, "missing") is None


def test_parse_lambda_proxy_payload():
    body = {"refund_id": "REF-ABC12345", "order_id": "ORD-002", "status": "APPROVED", "amount": 139.99}
    res = _mcp(json.dumps({"statusCode": 200, "body": json.dumps(body)}))
    assert parse_gateway_result(res) == body


def test_parse_plain_json_and_structured():
    assert parse_gateway_result(_mcp('{"order_id": "ORD-001", "total": 89.99}'))["total"] == 89.99
    res = {"status": "success", "content": [], "structuredContent": {"order_id": "ORD-1", "total": 1}}
    assert parse_gateway_result(res)["order_id"] == "ORD-1"


@pytest.mark.parametrize("res", [
    _mcp("boom", status="error"),
    _mcp(json.dumps({"statusCode": 400, "body": json.dumps({"error": "Unknown tool"})})),
    _mcp("plain text, not json"),
    _mcp(json.dumps({"error": "Order not found"})),
    "not a dict",
])
def test_parse_errors(res):
    with pytest.raises(GatewayError):
        parse_gateway_result(res)


def test_resolve_refund_amount():
    assert resolve_refund_amount(139.99, None) == 139.99
    assert resolve_refund_amount(139.99, 50) == 50
    for bad in (0, -10, 200):
        with pytest.raises(ValueError):
            resolve_refund_amount(139.99, bad)
    with pytest.raises(ValueError):
        resolve_refund_amount(None, 10)


def test_redact_amounts_keeps_identity():
    text = "Hi Jane! Your final total is $95.00 (saved $1,055.50, or 12.50 USD). You prefer concise replies."
    out = redact_amounts(text)
    assert "$95" not in out and "1,055" not in out and "12.50" not in out
    assert out.count(REDACTED) == 3 and "Jane" in out and "concise" in out
    assert redact_amounts("") == ""
