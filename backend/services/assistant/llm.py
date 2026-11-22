"""Optional LLM writing layer for the Admission Assistant.

The grounded engine decides *what* to say; this layer only rewrites that text
so it reads like a natural reply to the user's exact question. It never sees
the database, it is told to add nothing, and its output is checked: if it
introduces a number that is not in the grounded facts, or the call fails or is
refused, the grounded text is returned unchanged.

Configuration (backend/.env or environment):
  ASSISTANT_LLM    auto (default) | on | off
                   auto = enabled when the anthropic package is installed and an
                   ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN is set.
  ASSISTANT_MODEL  Claude model id (default claude-opus-5-5)
"""
from __future__ import annotations

import logging
import os
import re

from services.assistant.engine import Reply

log = logging.getLogger("assistant.llm")

DEFAULT_MODEL = "claude-opus-5-5"
# Only answers built from real data or the knowledge base are rewritten.
POLISHABLE = {"faq", "lead_summary", "lead_explain", "lead_followup", "student_enquiries", "stats"}

SYSTEM_PROMPT = """You are the writing layer of the Decision-Intel Admission Assistant, a chatbot inside a college admission marketing platform.

You receive a user's question and a FACTS block that the platform produced from its own database, trained model and knowledge base. Rewrite FACTS as a clear, friendly answer to the question.

Rules:
- Use only information that is in FACTS. Do not add facts, numbers, programme names, fees, dates, policies, people or advice that FACTS does not contain.
- Keep every number exactly as it appears in FACTS.
- Keep the meaning of every caution in FACTS, such as SHAP factors not being causes or suggestions being rule-based.
- A lead's conversion probability is a marketing estimate. Never describe it as admission eligibility, merit or an admission decision.
- If FACTS says information is not available, say so plainly and keep its suggested next step.
- Write plain text: short paragraphs, and lines starting with "- " for lists. No headings, bold or tables.
- Stay under 170 words. Do not mention FACTS, these rules or that you are rewriting anything."""

NUMBER = re.compile(r"\d+(?:[.,]\d+)*")

_client = None


def enabled() -> bool:
    mode = os.getenv("ASSISTANT_LLM", "auto").strip().lower()
    if mode == "off":
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    if mode == "on":
        return True
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


def _get_client():
    global _client
    if _client is None:
        import anthropic
        # Short timeout and one retry: the grounded answer is always a fallback.
        _client = anthropic.Anthropic(timeout=20.0, max_retries=1)
    return _client


def _numbers(text: str) -> set[str]:
    return {n.replace(",", "") for n in NUMBER.findall(text)}


def grounded_numbers_only(output: str, facts: str) -> bool:
    """True when every number in the rewrite already appears in the facts.

    Small whole numbers (list counts such as "three factors") are allowed.
    """
    allowed = _numbers(facts)
    for number in _numbers(output):
        if number in allowed:
            continue
        if number.isdigit() and int(number) <= 10:
            continue
        return False
    return True


def facts_text(reply: Reply) -> str:
    parts = [reply.text]
    if reply.notice:
        parts.append(f"Caution: {reply.notice}")
    return "\n\n".join(parts)


def polish(question: str, reply: Reply) -> Reply:
    """Return the reply with a rewritten text, or unchanged on any problem."""
    if reply.kind not in POLISHABLE or not enabled():
        return reply
    facts = facts_text(reply)
    try:
        import anthropic
        response = _get_client().beta.messages.create(
            model=os.getenv("ASSISTANT_MODEL", DEFAULT_MODEL),
            max_tokens=4000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Question: {question}\n\nFACTS:\n{facts}"}],
        )
    except anthropic.AuthenticationError:
        log.warning("Assistant LLM disabled for this request: authentication failed")
        return reply
    except anthropic.RateLimitError:
        log.warning("Assistant LLM rate limited; using grounded answer")
        return reply
    except anthropic.APIStatusError as error:
        log.warning("Assistant LLM API error %s; using grounded answer", error.status_code)
        return reply
    except anthropic.APIConnectionError:
        log.warning("Assistant LLM unreachable; using grounded answer")
        return reply

    if response.stop_reason in ("refusal", "max_tokens"):
        log.info("Assistant LLM stop_reason=%s; using grounded answer", response.stop_reason)
        return reply
    text = "\n".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        return reply
    if not grounded_numbers_only(text, facts):
        log.warning("Assistant LLM introduced numbers not in the facts; using grounded answer")
        return reply
    reply.text = text
    reply.engine = "llm"
    return reply
