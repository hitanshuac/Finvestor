import os

from litellm import Router

from src.config import FALLBACK_MODEL, LLM_MODEL


def _get_router() -> Router:
    """Initialize and return a configured LiteLLM Router."""
    model_list = []

    primary_key = os.environ.get("GROQ_API_KEY")
    fallback_key = os.environ.get("OPENROUTER_API_KEY")

    if primary_key and primary_key.strip():
        model_list.append(
            {
                "model_name": LLM_MODEL,
                "litellm_params": {
                    "model": LLM_MODEL,
                    "api_key": primary_key,
                    "rpm": 1000,
                    "tpm": 12000,
                },
            }
        )

    if fallback_key and fallback_key.strip():
        model_list.append(
            {
                "model_name": LLM_MODEL,
                "litellm_params": {
                    "model": FALLBACK_MODEL,
                    "api_key": fallback_key,
                    "rpm": 1000,
                    "tpm": 12000,
                },
            }
        )

    if not model_list:
        # Provide a dummy key so the Router can initialize without crashing.
        model_list.append(
            {
                "model_name": LLM_MODEL,
                "litellm_params": {
                    "model": LLM_MODEL,
                    "api_key": "dummy-key-for-initialization",
                },
            }
        )

    # Initialize the Router with automatic fallback/retry logic
    return Router(
        model_list=model_list,
        num_retries=2,  # Retries per request
        timeout=30,  # Request timeout
        # Removed "simple-shuffle" to enforce strict sequential fallback
        # Order: Llama (Primary) -> Llama (Fallback) -> Qwen (Primary)
    )


# Singleton router instance for the application
llm_router = _get_router()


def robust_completion(*args, **kwargs):
    """
    Wrapper for llm_router.completion that natively respects the global rate limit lockout file.
    If the system is locked out due to a 429 TPD limit, it raises a RateLimitLockoutError instantly
    without attempting to hit the API, saving execution time and preventing spam.
    """
    import litellm

    from src.rate_limiter import RateLimitLockoutError, get_lockout_info, set_lockout

    locked, remaining_time = get_lockout_info()
    if locked:
        raise RateLimitLockoutError(
            f"API is globally locked out. Please wait {remaining_time} before trying again.", unlock_time=0.0
        )

    try:
        return llm_router.completion(*args, **kwargs)
    except litellm.RateLimitError as exc:
        # If the router exhausts all keys and raises RateLimitError, parse the cooldown and lock the system
        set_lockout(str(exc))
        raise
