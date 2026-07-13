from src.config import CREDENTIALS, CUSTOMER_PROFILES, LANGUAGES, LLM_MODEL, get_system_prompt_template


def test_core_configurations():
    # Assertion
    assert "101" in CUSTOMER_PROFILES.keys(), "Missing required customer profile"
    assert "102" in CUSTOMER_PROFILES.keys(), "Missing required customer profile"

    assert "rahul" in CREDENTIALS.keys(), "Missing rahul mock credentials"

    assert "English" in LANGUAGES, "Missing English language support"
    assert "Hindi" in LANGUAGES, "Missing Hindi language support"

    assert isinstance(LLM_MODEL, str) and LLM_MODEL != "", "LLM model must be defined"

    template = get_system_prompt_template()
    assert "{language}" in template, "System prompt missing language format parameter"
    assert "{c360_json}" in template, "System prompt missing c360_json format parameter"
