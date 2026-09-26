"""Render tests/outputs/*.txt as terminal-style PNGs in screenshots/.

Same look as the course submission's screenshots (DejaVu Sans Mono 15px, dark
background, green command lines). The toolkit's deprecation banner and the
session/ARN/log box are trimmed; 12-digit numbers are masked again as a guard.
"""
import os
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tests" / "outputs"
SHOTS = ROOT / "screenshots"

# png name -> (source txt, title, note shown when the raw file has no command line)
TESTS = {
    "test1_order_tracking": ("rerun_t1.txt", "Test 1 - Order tracking (re-run)",
                             'prompt: "Can you track order ORD-001?"  customer_id: CUST-123'),
    "test2_refund": ("test2_refund.txt", "Test 2 - Refund processing", None),
    "test3_kb_loyalty": ("test3_kb_loyalty.txt", "Test 3 - Knowledge Base (RAG)", None),
    "test4a_memory_store": ("rerun_t4a.txt", "Test 4a - Memory store (re-run, session A)",
                            'prompt: "Hi, I am Jane. I prefer concise responses."  (fresh customer id)'),
    "test4b_memory_recall": ("rerun_t4b.txt", "Test 4b - Memory recall (re-run, new session B, ~150 s later)",
                             'prompt: "Do you remember my name and communication preference?"  (same fresh customer id)'),
    "test5_discount_fresh": ("test5_discount_fresh.txt", "Test 5 - Loyalty discount, fresh customer", None),
    "test5_discount_cust123": ("test5_discount_cust123_stale_memory.txt",
                               "Test 5b - Loyalty discount, CUST-123 (stale memory)", None),
    "test6_browser": ("test6_browser.txt", "Test 6 - Browser", None),
    "test7_risk_reward": ("test7_risk_reward.txt", "Test 7 - Risk/reward (ICT tool)", None),
    "test8_hypothesis": ("test8_hypothesis.txt", "Test 8 - Research hypothesis (ICT tool)", None),
    "test9_ftn_workflow": ("test9_ftn_workflow.txt", "Test 9 - FTN workflow, sample_eurusd (PAPER)", None),
    "test10_ftn_briefing": ("test10_ftn_briefing.txt", "Test 10 - FTN Month-9 briefing (PAPER)", None),
}

_FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"]


def clean(text: str) -> tuple[list[str], str]:
    """Drop the deprecation banner and the log box; return (lines, session)."""
    out, session, in_box, in_banner = [], "", False, False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("⚠️ Recommendation"):
            in_banner = True
            continue
        if in_banner:
            if s.startswith("Set AGENTCORE_SUPPRESS_RECOMMENDATION"):
                in_banner = False
            continue
        if s.startswith("╭"):
            in_box = True
            continue
        if in_box:
            m = re.search(r"Session:\s*(\S+)", line)
            if m:
                session = m.group(1)
            if s.startswith("╰"):
                in_box = False
                out.append(f"[ict_agent_lab | session {session} | ARN/log box trimmed]")
            continue
        out.append(line)
    # collapse leading/duplicate blank lines
    lines, prev_blank = [], True
    for line in out:
        blank = not line.strip()
        if blank and prev_blank:
            continue
        lines.append(line)
        prev_blank = blank
    while lines and not lines[-1].strip():
        lines.pop()
    return lines, session


def render(name: str, src: str, title: str, note: str | None, font) -> Path:
    raw = (OUT_DIR / src).read_text(encoding="utf-8")
    raw = re.sub(r"\d{12}", "XXXXXXXXXXXX", raw)  # guard: account id already masked
    lines, _ = clean(raw)
    header = [f"# {title}"]
    if note and not any(l.startswith("$ ") for l in lines):
        header.append(f"# {note}")
        header.append("# (re-run output saved without the command line)")
    header.append("")
    wrapped = []
    for l in header + lines:
        wrapped += textwrap.wrap(l, 110, replace_whitespace=False, drop_whitespace=False) or [""]
    bb = font.getbbox("M")
    cw, lh = bb[2], bb[3] + 6
    W, H = cw * 112 + 40, lh * len(wrapped) + 40
    im = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(im)
    cont = False
    for i, l in enumerate(wrapped):
        if l.startswith("# "):
            col = (140, 170, 255)
        elif l.startswith("$ ") or cont:
            col = (120, 220, 120)
        elif l.startswith("[ict_agent_lab"):
            col = (150, 150, 150)
        else:
            col = (230, 230, 230)
        # command lines wrap: keep the continuation green until the box marker
        cont = (l.startswith("$ ") or cont) and not l.startswith("[")
        if l.startswith("[ict_agent_lab") or not l.strip():
            cont = False
        d.text((20, 20 + i * lh), l, font=font, fill=col)
    SHOTS.mkdir(exist_ok=True)
    path = SHOTS / f"{name}.png"
    im.save(path)
    return path


def main() -> None:
    fp = [p for p in _FONTS if os.path.exists(p)]
    font = ImageFont.truetype(fp[0], 15) if fp else ImageFont.load_default()
    for name, (src, title, note) in TESTS.items():
        print(render(name, src, title, note, font).relative_to(ROOT))


if __name__ == "__main__":
    main()
