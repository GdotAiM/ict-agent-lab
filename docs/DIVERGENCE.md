# Where the lab and the submission diverge

This guide compares my graded Udacity submission (`GdotAiM/cd14763-project-starter`, code under `starter/`) with this personal lab. The lab started as a copy of the submission and was then changed to fix two test results and to add research tooling. The aim is to show, area by area, what each repo does and why the behaviour differs, so I can understand each difference and write my own fix in the submission.

The guide describes behaviour and ideas in prose on purpose. It points to file paths, function names and rough line numbers so both repos are easy to find your way around, but it does not contain fix code or diffs. Line numbers for the submission refer to `starter/main.py` at commit `7a997de` and are approximate.

Two test results are the reason most of the differences exist:

- **Test 2 (refund).** The submission approves the refund but reports "Refund Amount: $0". The lab reports $139.99.
- **Test 5 (loyalty discount, customer `CUST-123`).** The submission answers $95.00. The lab answers $99.00, which is what the discount tool actually calculates.

## Mapping table

| Submission area | Submission location | Lab location | Diverges? |
|---|---|---|---|
| App set-up, configuration, model and clients | `starter/main.py`, about lines 51–71 | `main.py`, about lines 72–92 | no |
| System prompt | `starter/main.py`, `SYSTEM_PROMPT`, about lines 329–342 | `main.py`, `SYSTEM_PROMPT`, about lines 473–524 | yes |
| Order tracking tool | Raw Gateway tool `get_order`, loaded in `invoke()` about lines 371–377; Lambda `starter/lambda/order_tracker.py` | `track_order` wrapper inside `invoke()` in `main.py` (about lines 573–592); `ict_lab/gateway.py`; `OrderStatus` in `ict_lab/models.py`; Lambda `lambda/order_tracker.py` (unchanged) | yes (agent side only; the Lambda is identical) |
| Refund tool | Raw Gateway tool `initiate_refund`; `starter/lambda/refund_processor.py`; `starter/lambda/lambda_schema` | `process_refund` wrapper inside `invoke()` in `main.py` (about lines 594–629); `resolve_refund_amount` in `ict_lab/gateway.py`; `RefundRequest` / `RefundResult` in `ict_lab/models.py`; course Lambda and schema unchanged in `lambda/`; an undeployed variant in `lambda/lab/` | yes |
| Loyalty / discount tool | `calculate_loyalty_discount`, about lines 214–325 | `calculate_loyalty_discount` in `main.py` (about lines 239–346); `ict_lab/loyalty.py`; `LoyaltyDiscountResult` in `ict_lab/models.py` | yes (same sandbox formula; input checks, output validation and fallback differ) |
| Knowledge Base search tool | `search_knowledge_base`, about lines 184–210 | `search_knowledge_base` in `main.py`, about lines 209–235 | no |
| Browser tool | `AgentCoreBrowser` created in `invoke()`, about line 367 | Same in `invoke()` in `main.py`, about line 549 | no |
| Memory hook / long-term memory | `get_namespaces` and `MemoryHook`, about lines 74–180 | `MemoryHook` in `main.py` (about lines 113–205); `ict_lab/memory_utils.py` | yes |
| Conversation management | Not configured (Strands default), `Agent(...)` about lines 379–385 | `SummarizingConversationManager` passed to `Agent(...)` in `main.py`, about lines 631–644 | yes |
| Input/output contracts | None; tools return raw JSON strings | Pydantic v2 models in `ict_lab/models.py`, helpers `validate_to_json` and `validation_error_json` | yes |
| Gateway / KB / Memory set-up and permissions | Resource IDs as literals in `starter/main.py` about lines 59–63; `starter/setup_permissions.py`; resources created in the AWS console | Same resources reused read-only; same literals in `main.py`; `setup_permissions.py` identical | no (the lab reuses the course resources and changes none of them) |
| Deployment scripts | Manual `agentcore configure` / `deploy` commands in `starter/README.md` and the top-level `README.md` | `scripts/deploy_lab.sh`, `scripts/cleanup_lab.sh`, separate runtime `ict_agent_lab` | yes (packaging only; not a behaviour change) |
| Tests / scenarios | Six manual `agentcore invoke` runs in `starter/SUBMISSION_CHECKLIST.md`; outputs in `starter/test_outputs/`; no unit tests | `scripts/run_scenarios.sh` (six course scenarios plus a stale-memory Test 5b and four lab tests); pytest suite in `tests/`; outputs in `tests/outputs/` | yes |
| Product catalog (KB source), `pyproject.toml` | `starter/product_catalog.txt`, `starter/pyproject.toml` | `product_catalog.txt` (identical); `pyproject.toml` adds Pydantic and pytest | catalog no; dependencies yes (lab only) |

## System prompt

**What the submission does.** The prompt (about lines 329–342) describes the agent's job and lists its tools and capabilities, including "persistent memory across sessions to remember customer preferences". It ends by asking the agent to be helpful, accurate and professional. It says nothing about which source to trust when two sources disagree, and it gives no rules for refunds.

**What the lab does differently.** The lab keeps the original opening and adds several rule blocks. The ones that matter for the rubric are:

- A *source-of-truth* block. It says that prices, totals, discounts, points, refund amounts and order status must come from a tool call made in the current conversation. Memory is only for identity and preferences. If memory and a tool disagree, the agent uses the tool's number and does not mention the old one. If the agent needs a number it has not fetched yet, it must call the tool first.
- A *refund* block. It tells the agent to look up the order first, pass an explicit amount when it starts a refund (the order total for a full refund), never refund zero, and report the amount exactly as the tool returns it.
- The capability line about memory now says "identity and preferences" instead of just "preferences", and the tool list names the lab's wrapper tools instead of the raw Gateway tools.

The lab also adds FTN rules and ICT research rules, which are covered in the lab-only section.

**Why.** Nova 2 Lite treats everything in its context as roughly equally trustworthy. If a remembered total and a fresh tool result are both in the prompt and nothing says which one wins, the model can pick either. In the same way, the model will not pass an optional refund amount unless something tells it to.

**Which test it affects.** Test 5 (the stale $95) and Test 2 (the $0 refund). The prompt is only one layer of each fix. The memory hook and the refund wrapper are the others, and neither of the prompt rules would be reliable on its own.

## Order tracking tool

**What the submission does.** The agent uses the Gateway's `get_order` tool directly. In `invoke()` (about lines 371–377) every tool that `list_tools_sync()` returns is added to the agent as-is. The API Gateway target returns the order JSON, and the model reads it and writes the answer.

**What the lab does differently.** The order-tracker Lambda is byte-for-byte identical. The difference is on the agent side. Inside `invoke()` the lab finds the full Gateway name of `get_order` (Gateway names carry a `target___` prefix, which `resolve_tool_name` in `ict_lab/gateway.py` handles). It then hides the raw tool from the model and exposes a local tool called `track_order` instead. `track_order` calls the same Gateway tool through the MCP client, unwraps the result with `parse_gateway_result` (which copes with both a plain JSON body and a Lambda-proxy `statusCode`/`body` envelope, and turns non-2xx statuses into a clear error), and validates it against the `OrderStatus` model. The model receives either a validated order or a small error object.

**Why.** Mainly so that the refund wrapper has a reliable way to get the order total, and so that a malformed or failed lookup becomes an explicit error instead of something the model has to interpret. Hiding the raw tool also means there is only one way for the model to look up an order.

**Which test it affects.** Test 1 passes in both repos. The lab's first Test 1 attempt returned a 500 straight after deployment, which looked like a cold start or IAM propagation delay and has nothing to do with the code. It passed on re-run. The wrapper matters most as the first step of the Test 2 fix.

## Refund tool

**What the submission does.** The agent calls the Gateway's `initiate_refund` tool directly. In `starter/lambda/lambda_schema` only `order_id` and `reason` are required, and `amount` is optional. In `starter/lambda/refund_processor.py` the `initiate_refund` branch (about lines 64–75) echoes `amount` back and falls back to zero when it is missing. In the Test 2 run the model never passed an amount, so the Lambda approved a refund of $0, and the model then described that $0 as a "full refund".

**What the lab does differently.** The course Lambda and schema are unchanged, and the lab still points at the course Gateway. The fix is in the agent:

- The raw `initiate_refund` tool is hidden, and the model sees `process_refund` instead. Unlike the Gateway schema, `process_refund` has `amount` as a *required* argument, so the model cannot leave it out.
- Before it calls the Gateway, `process_refund` fetches the order again to get the real total. `resolve_refund_amount` then rejects an amount that is zero, negative or larger than the order total.
- The request is built as a `RefundRequest` (which requires an amount above zero), and the Lambda's reply is validated as a `RefundResult` (which also requires an amount above zero). If the Lambda ever echoed $0, the model would get a "validation failed; do not use these numbers" error instead of a success message.
- The system prompt's refund rules tell the model to look up the order first and to report the amount exactly.

The lab also contains a variant of the refund Lambda and schema in `lambda/lab/` that make the amount mandatory on the server side. It is **not deployed**, and the passing lab run did not use it.

**Why.** The underlying problem is an optional field with a silent default of zero. There are three places where it can be closed: the tool contract the model sees (make the amount required), the value that is sent (derive it from the real order total and check its range), and the result that comes back (refuse to report a zero refund as a success). The submission's README already names two of these ideas under Known Issues.

**Which test it affects.** Test 2. The submission reports $0. The lab reports $139.99 for ORD-002 (see `tests/outputs/test2_refund.txt`).

## Loyalty / discount tool

**What the submission does.** `calculate_loyalty_discount` (about lines 214–325) inserts the arguments into a Python snippet, runs it in the AgentCore Code Interpreter and returns the JSON the snippet prints. The formula is correct. Points are redeemed in 500-point blocks, capped at half the order total, and the tier discount applies to the subtotal after points. For Gold, 4,250 points and a $150 order, that gives 4,000 points ($40), a $110 subtotal, an $11 tier discount and a **$99.00** final total. The `tier` and `product_category` strings go into the snippet without being checked. If the Code Interpreter fails, the fallback (about lines 305–325) applies only the tier discount to the full order and redeems no points, so it gives a different answer from the main path.

**What the lab does differently.** The snippet and its formula are the same. Around it, the lab:

- normalises and checks the inputs first (a known tier, a known category, a positive order total and a non-negative points balance) and returns an error object if they are invalid. This also keeps arbitrary strings out of the code that runs in the sandbox.
- validates the sandbox output against `LoyaltyDiscountResult`. That model checks that the numbers agree with each other: whole 500-point blocks, points value equal to points divided by 100, the 50% cap, the tier discount equal to the tier percentage of the post-points subtotal, and final total plus savings equal to the original total. A result such as the submission's $95 answer, with $15 of tier discount on the full order, would fail that check.
- replaces the fallback with `compute_loyalty_discount` in `ict_lab/loyalty.py`. It applies the same rules in plain Python, and its result is validated too, so both paths give the same answer.

**Why.** The tool was never the source of the wrong $95. It returns $99 for this input in both repos, and a fresh customer gets $99 from the submission as well. The changes make the tool's output something the model can treat as authoritative, and they remove a fallback that would have produced a third, different answer.

**Which test it affects.** Test 5. On its own, this tool change does not fix the $95. That fix comes from the memory and prompt changes described below. The validation stops a wrong breakdown from being passed off as a tool result.

## Knowledge Base search tool

**What the submission does.** `search_knowledge_base` (about lines 184–210) calls the Bedrock `retrieve` API on the course Knowledge Base and joins the returned chunks.

**What the lab does differently.** Nothing. The function is identical, it queries the same Knowledge Base, and `product_catalog.txt` is byte-for-byte the same. (The lab has an optional `docs/ict_glossary.md`, but it is not ingested into the Knowledge Base.)

**Why.** No change was needed.

**Which test it affects.** Test 3 passes in both repos with the same Platinum benefits.

## Browser tool

**What the submission does.** `invoke()` creates an `AgentCoreBrowser` for the region on every request and passes its `browser` tool to the agent (about line 367).

**What the lab does differently.** Nothing. The set-up and the tool are identical.

**Why.** No change was needed.

**Which test it affects.** Test 6 passes in both repos with the same Udacity page title.

## Memory hook / long-term memory

**What the submission does.** `MemoryHook` (about lines 92–180) has two callbacks:

- `retrieve_customer_context` (about lines 108–141) runs when a user message is added. It searches each memory namespace for the customer and puts the matches in front of the user's message under a plain `Customer Context:` label. That label says nothing about what the context is for or how far to trust it.
- `save_support_interaction` (about lines 143–175) runs after the agent responds. It saves the latest user message and the assistant's reply to AgentCore Memory as an event, word for word, including every dollar figure the agent quoted.

Because `CUST-123` had been used in earlier runs, its long-term memory already held an old discount answer from one of them. On the graded Test 5 run that old figure came back in the Customer Context, and the model repeated a $95 breakdown instead of using the tool's $99.

**What the lab does differently.** The class structure, the namespace lookup and the callbacks are the same. Two things change:

- **What it saves.** Before it creates the event, the lab runs both texts through `redact_amounts` in `ict_lab/memory_utils.py`. That function replaces money amounts in forms such as "$95.00", "USD 12" or "12 USD" with a neutral placeholder. Names and preferences are kept. The effect is that calculated or looked-up totals are never written into long-term memory, so there is nothing to go stale.
- **How it labels what it retrieves.** The label in front of retrieved memories is replaced with a longer header, `CONTEXT_HEADER` in `ict_lab/memory_utils.py`. The header says the context is for identity and preferences only, may be out of date, and must not be used for prices, totals, discounts, refund amounts or order status. This matches the source-of-truth rules in the system prompt.

**Why.** Long-term memory is meant for durable facts about a person, such as their name, tier or preferred tone. Transaction results change every time and are cheap to recalculate. Keeping them out of memory deals with the cause, and the header and prompt rules deal with anything already stored (the redaction does not remove old records). The submission's README lists both ideas as possible fixes.

**Which test it affects.** Test 5 with `CUST-123`. The lab added a Test 5b that repeats the prompt for `CUST-123` on purpose, with the old memory still in place, and it returns $99.00 without mentioning the $95 (`tests/outputs/test5_discount_cust123_stale_memory.txt`). One side effect is still there: in both the fresh and the stale-memory lab runs, the model still *labels* the Gold discount as "$15.00" even though the validated tool output says $11.00. The final total is right, but the explanation has not fully caught up. A fix in the submission should check the explanation lines as well as the final number. Tests 4a and 4b are not affected by the redaction because they involve a name and a preference, not money.

## Conversation management

**What the submission does.** No conversation manager is passed to `Agent(...)` (about lines 379–385), so Strands uses its default.

**What the lab does differently.** The lab passes a `SummarizingConversationManager` with a summary ratio of 0.3 and the 10 most recent messages kept. If the context window overflows, the oldest part of the conversation is summarised instead of being dropped. The constructor arguments were checked against the installed strands-agents version.

**Why.** The lab's research and FTN tools return long JSON payloads, and multi-step tool turns can fill the context quickly. The course scenarios are all single-turn requests that never come near that limit.

**Which test it affects.** None of the six course tests. It is covered by an offline unit test that checks the manager is attached. Treat it as a lab feature, not a rubric fix.

## Input/output contracts

**What the submission does.** Tools return whatever their back end produces. The Knowledge Base tool returns text. The loyalty tool re-emits the sandbox JSON after checking only that it parses. The Gateway tools return the Lambda payloads unchanged. Nothing checks that the values make sense before the model sees them.

**What the lab does differently.** `ict_lab/models.py` defines Pydantic v2 models for every structured tool output: `OrderStatus` (with `OrderItem`), `RefundRequest`, `RefundResult` and `LoyaltyDiscountResult` for the support tools, plus `RiskReward`, `MeasurementWindow` and `ResearchHypothesis` for the research tools. The models keep any extra keys the tools return, so nothing the rubric looks for is lost. `validate_to_json` returns either the validated JSON or a compact error object that lists each failing field and tells the model not to use the numbers.

**Why.** A contract turns a silent bad value (a $0 refund, a discount that doesn't add up, an order without a total) into an explicit error that the model has to handle. It also gives unit tests something precise to check without calling AWS.

**Which test it affects.** Test 2 (a zero refund amount is rejected on the way out and on the way back) and Test 5 (an inconsistent discount breakdown is rejected). Tests 1, 3, 4 and 6 are not affected.

## Gateway / KB / Memory set-up

**What the submission does.** The Gateway (with an `order_tracker` API Gateway target and a `refund_processor` Lambda target), the Knowledge Base and the Memory resource (with `customer_facts` and `customer_preferences` strategies) were created for the course. `starter/main.py` holds their identifiers as literals (about lines 59–63), and `starter/setup_permissions.py` reads those literals to grant the runtime role access to the Knowledge Base, Memory and Browser.

**What the lab does differently.** Nothing on the resource side. The lab reuses the same Gateway, Knowledge Base and Memory without changing them, and `setup_permissions.py` is identical. No Gateway target, Lambda or memory strategy was changed. The server-side refund variant in `lambda/lab/` would need its own Lambda and a separate Gateway target, and it has not been deployed. Because both agents write to the same Memory resource, lab runs for `CUST-123` add to the same customer history the submission reads. From now on the lab only saves those turns with money amounts removed.

**Why.** Keeping the shared resources untouched means the graded agent's behaviour can only change through my own edits to the submission.

**Which test it affects.** None directly. Keep in mind the shared-memory point above when you re-run Test 5 in the submission for `CUST-123`.

## Deployment scripts

**What the submission does.** It is deployed by hand with `agentcore configure`, `agentcore deploy` and `uv run setup_permissions.py` from `starter/`, as documented in the READMEs. The runtime is `customer_support_agent`.

**What the lab does differently.** `scripts/deploy_lab.sh` runs the same three steps non-interactively for a separate runtime called `ict_agent_lab`, using the lab's own gitignored toolkit configuration. `scripts/cleanup_lab.sh` destroys only that runtime. The lab never configures, redeploys or destroys the graded runtime.

**Why.** It gives the lab repeatable deploys and keeps the two runtimes completely separate.

**Which test it affects.** None. It changes how the code is packaged, not how the agent behaves.

## Tests / scenarios

**What the submission does.** It has the six `agentcore invoke` commands in `starter/SUBMISSION_CHECKLIST.md`, run by hand, with raw outputs in `starter/test_outputs/`. All of them use `CUST-123`, including both halves of the memory test, and the checklist asks for at least a 30-second wait between Test 4a and 4b. There are no unit tests. The README records five passes, Test 2 passing with the $0 caveat, and Test 5 as a known issue.

**What the lab does differently.**

- `scripts/run_scenarios.sh` runs the six course prompts plus Test 5b (the Test 5 prompt for `CUST-123`, to prove the stale-memory fix) and four lab tests. It uses a new customer ID for each run for the memory and discount tests, and it masks 12-digit numbers in the saved outputs.
- The memory recall test needed a longer wait than the script's 60 seconds. The first Test 4b attempt failed and passed on re-run after about 150 seconds. The README's follow-ups suggest waiting at least two minutes.
- `tests/` holds an offline pytest suite (89 tests at the last run) covering model validation, loyalty maths, refund amount rules, Gateway result parsing, memory redaction, a fake-Gateway wiring test of `invoke()` and the lab-only tools. No AWS access is needed.

**Why.** Using a new customer ID separates the fix itself from memory left over by earlier runs. The stale-memory variant proves the fix works when that old memory is present. Unit tests make the contracts and the refund rules checkable without a deployment.

**Which test it affects.** It makes Test 2 and Test 5 checkable in the lab, and it explains the Test 4 timing. One thing to remember for the submission: because the graded scenarios all run as `CUST-123`, any earlier run for that customer can affect later runs through long-term memory.

## Lab-only additions (not relevant to the rubric)

These exist only in the lab, are not part of the course project, and have nothing to do with how the submission is graded.

- **ICT research tools.** `calculate_risk_reward` (in `main.py`, with its logic in `ict_lab/ict_tools.py`) works out risk, reward and the R multiple for a trade idea, infers the direction from the stop, and rejects stops or targets on the wrong side. `build_research_hypothesis` turns a trading research question into a validated `ResearchHypothesis` with an instrument, observable and invalidation conditions, a measurement window in a named IANA timezone, and the evidence needed. It defines how to test an idea and does not claim the idea is true. Both have their own rules in the lab's system prompt.
- **FTN tools, paper only.** `ftn_run_workflow`, `ftn_briefing` and `ftn_list_fixtures` expose my FTN package, vendored unchanged under `vendor/ftn-agent/`, through `ict_lab/ftn_bridge.py` and the Pydantic models in `ict_lab/ftn_models.py`. The glue refuses to run unless FTN's config is in paper mode with live trading disabled. It never loads broker adapters, only allows fixtures from FTN's own folder, and sends every file FTN writes to a temporary directory. The system prompt adds FTN charter rules (paper only, tickets are research artefacts, report the tool's output as-is, never propose raising risk caps).
- **Supporting files.** `docs/ict_glossary.md`, the extension scenarios (Tests 7–10) in `scripts/run_scenarios.sh`, `scripts/render_screenshots.py` and the FTN integration tests.

None of this touches the customer-support tools, the memory hook or the shared AWS resources.

## Summary

The two graded failures come from two different gaps, and in the lab each is closed at more than one layer.

- **Test 2 ($0 refund).** The amount was optional and defaulted to zero silently. The lab makes it required in the tool the model sees, takes it from the real order total, checks its range, and refuses to report a zero refund as a success. The prompt backs this up.
- **Test 5 ($95 instead of $99).** A calculated total had been saved into long-term memory, and nothing told the model that a fresh tool result outranks memory. The lab stops saving money amounts, labels retrieved memory as identity and preferences only, and states the source-of-truth rule in the system prompt. Output validation on the discount tool is an extra safeguard. It is not the main fix.

Everything else that diverges (conversation summarisation, contracts for the research tools, deployment scripts and the ICT/FTN tools) is lab infrastructure or new features, and none of it is needed for the rubric.
