"""
PII Redaction Middleware using Microsoft Presidio.

Detects and anonymizes Personally Identifiable Information (PII) in text
before it is sent to external LLM providers. Includes custom recognizers
for Indian financial PII (Aadhaar, PAN, IFSC).
"""

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine


def _build_indian_recognizers() -> list[PatternRecognizer]:
    """Build custom Presidio recognizers for Indian financial PII.

    Returns:
        list[PatternRecognizer]: Custom recognizers for Aadhaar, PAN, and IFSC.
    """
    aadhaar_recognizer = PatternRecognizer(
        supported_entity="IN_AADHAAR",
        name="Indian Aadhaar Recognizer",
        patterns=[
            Pattern(
                name="aadhaar_pattern",
                regex=r"\b\d{4}\s?\d{4}\s?\d{4}\b",
                score=0.85,
            )
        ],
        context=["aadhaar", "aadhar", "uid", "आधार"],
    )

    pan_recognizer = PatternRecognizer(
        supported_entity="IN_PAN",
        name="Indian PAN Card Recognizer",
        patterns=[
            Pattern(
                name="pan_pattern",
                regex=r"\b[A-Z]{5}\d{4}[A-Z]\b",
                score=0.9,
            )
        ],
        context=["pan", "pan card", "permanent account number", "पैन"],
    )

    ifsc_recognizer = PatternRecognizer(
        supported_entity="IN_IFSC",
        name="Indian IFSC Code Recognizer",
        patterns=[
            Pattern(
                name="ifsc_pattern",
                regex=r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
                score=0.85,
            )
        ],
        context=["ifsc", "bank branch", "neft", "rtgs", "imps"],
    )

    indian_phone_recognizer = PatternRecognizer(
        supported_entity="IN_PHONE",
        name="Indian Phone Number Recognizer",
        patterns=[
            Pattern(
                name="indian_mobile",
                regex=r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b",
                score=0.8,
            )
        ],
        context=["phone", "mobile", "contact", "call", "फोन", "मोबाइल"],
    )

    account_number_recognizer = PatternRecognizer(
        supported_entity="IN_BANK_ACCOUNT",
        name="Indian Bank Account Number Recognizer",
        patterns=[
            Pattern(
                name="account_number",
                regex=r"\b\d{9,18}\b",
                score=0.4,  # Low base score — needs context to fire
            )
        ],
        context=["account", "a/c", "account number", "bank account", "खाता"],
    )

    return [
        aadhaar_recognizer,
        pan_recognizer,
        ifsc_recognizer,
        indian_phone_recognizer,
        account_number_recognizer,
    ]


# Configure Presidio to use the small SpaCy model to prevent Render OOM (512MB RAM limit)
_configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}
_provider = NlpEngineProvider(nlp_configuration=_configuration)
_nlp_engine = _provider.create_engine()

# Module-level singletons (initialized once, reused across requests)
_analyzer = AnalyzerEngine(nlp_engine=_nlp_engine, supported_languages=["en"])
_anonymizer = AnonymizerEngine()

# Register custom Indian recognizers
for recognizer in _build_indian_recognizers():
    _analyzer.registry.add_recognizer(recognizer)


def redact_pii(text: str, language: str = "en") -> tuple[str, bool]:
    """Detect and redact PII from text using Presidio.

    Args:
        text: The raw text to scan for PII.
        language: The language code for analysis (default: "en").

    Returns:
        A tuple of (redacted_text, was_pii_found).
    """
    results = _analyzer.analyze(
        text=text,
        language=language,
        entities=[
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "CREDIT_CARD",
            "IN_AADHAAR",
            "IN_PAN",
            "IN_IFSC",
            "IN_PHONE",
            "IN_BANK_ACCOUNT",
        ],
        score_threshold=0.5,
    )

    if not results:
        return text, False

    anonymized = _anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text, True
