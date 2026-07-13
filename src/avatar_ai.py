"""
AI orchestration logic, prompt templates, and LiteLLM integration.

Uses LiteLLM for multi-provider routing with automatic fallback.
Langfuse callbacks are enabled when LANGFUSE_PUBLIC_KEY is set.
"""

import json
import logging
import os
from typing import Any

import litellm
from langsmith import traceable

from src.config import LLM_MODEL, get_system_prompt_template

logger: logging.Logger = logging.getLogger(__name__)

# ── Phase 4: Observability ─────────────────────────────────────────
# LiteLLM has native Langfuse support. If keys are present, enable tracing.
if os.environ.get("LANGFUSE_PUBLIC_KEY"):
    litellm.success_callback = ["langfuse"]
    litellm.failure_callback = ["langfuse"]

# Suppress verbose LiteLLM logging in production
litellm.set_verbose = False


def build_system_prompt(c360: dict[str, Any], language: str) -> str:
    """Construct the LLM system prompt with injected Customer_360 context.

    Args:
        c360 (Dict[str, Any]): The Customer 360 profile dictionary.
        language (str): The requested language.

    Returns:
        str: The fully formatted system prompt.
    """
    # Create a shallow copy and truncate raw transaction arrays to prevent LLM context bloat (TPM limits)
    c360_llm = c360.copy()
    if "balance_history" in c360_llm and isinstance(c360_llm["balance_history"], list):
        # Truncate to the 10 most recent transactions to save tokens while keeping context
        c360_llm["balance_history"] = c360_llm["balance_history"][-10:]
    # Note: expense_breakdown is aggregated (small) so we keep it to allow the LLM to analyze spending
    c360_json = json.dumps(c360_llm, indent=2, default=str)

    # Get dynamic allowed widgets list from registry
    from src.config import ALLOWED_WIDGET_TYPES

    allowed_widgets = ", ".join(sorted(ALLOWED_WIDGET_TYPES))

    # Pre-computed investable surplus from real transaction data
    investable_surplus = c360.get("investable_surplus", 0.0)

    template = get_system_prompt_template()
    return template.format(
        language=language,
        c360_json=c360_json,
        allowed_widgets=allowed_widgets,
        investable_surplus=investable_surplus,
    )


@traceable(run_type="chain", name="avatar_llm_response")
def get_llm_response(messages: list[dict[str, str]], c360: dict[str, Any], language: str) -> str:
    """Call the LLM via LiteLLM with automatic fallback and return a JSON string response.

    Args:
        messages (List[Dict[str, str]]): List of previous chat messages (already truncated if needed).
        c360 (Dict[str, Any]): The customer 360 profile dict.
        language (str): The language requested by the user.

    Returns:
        str: The full JSON response from the LLM completion.
    """
    system_prompt = build_system_prompt(c360, language)

    api_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]

    if not os.environ.get("GROQ_API_KEY") and not os.environ.get("OPENROUTER_API_KEY"):
        return (
            "**API keys not configured.**\n\n"
            "Add `GROQ_API_KEY` or `OPENROUTER_API_KEY` to `.env` "
            "or set them as environment variables to enable the "
            "AI advisor."
        )

    try:
        from src.llm_client import robust_completion
        from src.rate_limiter import RateLimitLockoutError

        response = robust_completion(
            model=LLM_MODEL,
            messages=api_messages,
            temperature=0.6,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or "{}"
    except (litellm.RateLimitError, RateLimitLockoutError) as exc:
        logger.warning("Rate limit hit across all available keys (or system locked): %s", exc)
        return (
            '{"conversational_response": "**Rate Limit Exceeded.** The AI has reached '
            'its token limit. Please wait until the cooldown expires.", '
            '"follow_up_question": "", "recommended_tips": []}'
        )
    except litellm.APIConnectionError as exc:
        logger.error("LLM API connection error: %s", exc)
        return (
            '{"conversational_response": "Unable to connect to the AI service. '
            'Please check your network and try again.", '
            '"follow_up_question": "", "recommended_tips": []}'
        )
    except litellm.AuthenticationError as exc:
        logger.error("LLM authentication error: %s", exc)
        return (
            '{"conversational_response": "API authentication failed. '
            'Please verify your API keys.", '
            '"follow_up_question": "", "recommended_tips": []}'
        )
    except Exception as exc:
        logger.error("Unexpected error in LLM call: %s", exc)
        return (
            '{"conversational_response": "I encountered an unexpected error '
            'processing your request. Please try again.", '
            '"follow_up_question": "", "recommended_tips": []}'
        )
