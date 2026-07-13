"""
Tests for the PII Redaction Middleware (Microsoft Presidio).

Validates that Indian financial PII (Aadhaar, PAN, IFSC, phone numbers)
is correctly detected and masked, while financial terms are NOT falsely redacted.
"""

from src.pii_redactor import redact_pii


class TestAadhaarRedaction:
    """Tests for Aadhaar number detection and masking."""

    def test_aadhaar_with_spaces(self):
        text = "My aadhaar number is 1234 5678 9012"
        redacted, found = redact_pii(text)
        assert found is True
        assert "1234 5678 9012" not in redacted

    def test_aadhaar_without_spaces(self):
        text = "My aadhaar is 123456789012"
        redacted, found = redact_pii(text)
        assert found is True
        assert "123456789012" not in redacted


class TestPANRedaction:
    """Tests for PAN card number detection and masking."""

    def test_pan_card(self):
        text = "My PAN card number is ABCDE1234F"
        redacted, found = redact_pii(text)
        assert found is True
        assert "ABCDE1234F" not in redacted

    def test_pan_lowercase_context(self):
        text = "pan number: ZYXWV9876A"
        redacted, found = redact_pii(text)
        assert found is True
        assert "ZYXWV9876A" not in redacted


class TestPhoneRedaction:
    """Tests for Indian phone number detection and masking."""

    def test_indian_mobile(self):
        text = "Call me on my mobile 9876543210"
        redacted, found = redact_pii(text)
        assert found is True
        assert "9876543210" not in redacted

    def test_indian_mobile_with_country_code(self):
        text = "My phone is +91-9876543210"
        redacted, found = redact_pii(text)
        assert found is True
        assert "9876543210" not in redacted


class TestNegativeCases:
    """Tests that financial terms are NOT incorrectly redacted."""

    def test_sip_not_redacted(self):
        text = "I want to start a SIP of ₹5000 per month"
        redacted, _found = redact_pii(text)
        assert "SIP" in redacted

    def test_fd_not_redacted(self):
        text = "What is the current FD interest rate?"
        redacted, _found = redact_pii(text)
        assert "FD" in redacted

    def test_plain_financial_query(self):
        text = "What are my top expenses and how can I cut back?"
        redacted, found = redact_pii(text)
        assert found is False
        assert redacted == text

    def test_rupee_amounts_not_redacted(self):
        text = "My balance is ₹1,50,000"
        redacted, _found = redact_pii(text)
        assert "1,50,000" in redacted
