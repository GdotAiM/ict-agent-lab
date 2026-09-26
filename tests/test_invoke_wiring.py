"""Offline wiring test for invoke(): fake Gateway + fake Agent, no AWS calls."""
import asyncio
import json
from types import SimpleNamespace

import pytest

main = pytest.importorskip("main")

ORDER = {"order_id": "ORD-002", "customer_id": "CUST-123", "status": "DELIVERED",
         "items": [{"name": "Kindle Paperwhite", "qty": 1, "price": 139.99}], "total": 139.99}


class FakeClient:
    def __init__(self, *_a, **_k):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def list_tools_sync(self):
        return [SimpleNamespace(tool_name=n) for n in (
            "order_tracker___get_order", "order_tracker___get_customer",
            "refund_processor___initiate_refund", "refund_processor___check_refund_status")]

    def call_tool_sync(self, tool_use_id, name, arguments):
        self.calls.append((name, arguments))
        if name.endswith("get_order"):
            body = ORDER
        else:
            body = {"refund_id": "REF-TEST1234", "order_id": arguments["order_id"],
                    "status": "APPROVED", "amount": arguments.get("amount", 0)}
        return {"status": "success", "content": [
            {"text": json.dumps({"statusCode": 200, "body": json.dumps(body)})}]}


class FakeAgent:
    last = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        FakeAgent.last = self

    def __call__(self, prompt):
        return "ok"


@pytest.fixture
def wired(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(main, "MCPClient", lambda *_a, **_k: client)
    monkeypatch.setattr(main, "Agent", FakeAgent)
    monkeypatch.setattr(main, "MemoryHook", lambda **_k: object())
    monkeypatch.setattr(main, "AgentCoreBrowser", lambda **_k: SimpleNamespace(browser="browser"))
    asyncio.run(main.invoke({"prompt": "hi", "customer_id": "C", "session_id": "s"}))
    tools = {getattr(t, "tool_name", t): t for t in FakeAgent.last.kwargs["tools"]}
    return client, tools, FakeAgent.last.kwargs


def test_tools_and_conversation_manager(wired):
    _, tools, kwargs = wired
    assert {"track_order", "process_refund", "calculate_risk_reward",
            "build_research_hypothesis"} <= set(tools)
    assert "order_tracker___get_order" not in tools
    assert "refund_processor___initiate_refund" not in tools
    assert "order_tracker___get_customer" in tools
    assert type(kwargs["conversation_manager"]).__name__ == "SummarizingConversationManager"


def test_process_refund_passes_order_total(wired):
    client, tools, _ = wired
    out = json.loads(tools["process_refund"](order_id="ORD-002", reason="return", amount=139.99))
    assert out["amount"] == 139.99
    assert client.calls[-1] == ("refund_processor___initiate_refund",
                                {"order_id": "ORD-002", "reason": "return", "amount": 139.99})


@pytest.mark.parametrize("amount", [0, -5, 500])
def test_process_refund_rejects_bad_amount(wired, amount):
    client, tools, _ = wired
    out = json.loads(tools["process_refund"](order_id="ORD-002", reason="return", amount=amount))
    assert "error" in out
    assert not any(n.endswith("initiate_refund") for n, _ in client.calls)


def test_track_order_validated(wired):
    _, tools, _ = wired
    out = json.loads(tools["track_order"](order_id="ORD-002"))
    assert out["total"] == 139.99 and out["status"] == "DELIVERED"
