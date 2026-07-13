import json

from src.avatar_ai import build_system_prompt


def test_build_system_prompt_injection():
    # Setup
    c360 = {"customer_id": "TEST-ID", "age": 28, "total_inflow_90d": 1000.0, "total_outflow_90d": 500.0}
    language = "Marathi"

    # Action
    prompt = build_system_prompt(c360, language)

    # Assertion
    assert language in prompt, "Language was not injected into the prompt"
    assert json.dumps(c360, indent=2, default=str) in prompt, "Customer_360 JSON was not injected into the prompt"
    assert "You are **Finvestor**" in prompt, "Core system instruction missing from prompt"
