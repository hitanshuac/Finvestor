import pytest

from src.rate_limiter import get_lockout_info


@pytest.fixture(autouse=True)
def check_rate_limit_lockout(request):
    """
    Automatically check if the API is globally locked out due to rate limits before every test.
    If it is, skip the test gracefully rather than executing it and failing.
    """
    locked, remaining_time = get_lockout_info()
    if locked:
        pytest.skip(f"Groq API globally locked out. Try again in {remaining_time}")
