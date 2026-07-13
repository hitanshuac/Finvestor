from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# ── Agent State ────────────────────────────────────────────────────────


class CouncilState(TypedDict):
    """The State for the LLM Council Loop Engineering Graph."""

    query: str
    context: str

    # Parallel advisor responses (e.g. 'contrarian': 'response text')
    advisor_takes: dict[str, str]

    # Parallel peer reviews (e.g. 'contrarian': 'review text')
    peer_reviews: dict[str, str]

    # The deterministic goal proposed by the Chairman
    proposed_goal: str

    # Feedback from advisors on the proposed goal (used in debate loop)
    goal_feedback: dict[str, str]

    # Number of debate loops
    loop_count: int

    # Final verdict document
    final_verdict: str


# ── Pydantic Models for Structured Handoffs ─────────────────────────────


class AdvisorTake(BaseModel):
    """An advisor's initial response to the user's query."""

    advisor_name: str = Field(..., description="The name of the advisor (e.g., Contrarian, Expansionist).")
    analysis: str = Field(..., description="The analysis from this specific perspective. Be direct and specific.")


class PeerReview(BaseModel):
    """A peer review of the anonymized advisor takes."""

    reviewer_name: str = Field(..., description="The name of the reviewing advisor.")
    strongest_response: str = Field(..., description="Which response is strongest and why.")
    biggest_blind_spot: str = Field(..., description="Which response has the biggest blind spot and what is it.")
    universal_miss: str = Field(..., description="What did ALL responses miss that the council should consider.")


class GoalProposal(BaseModel):
    """The deterministic goal proposed by the Chairman."""

    agreements: str = Field(..., description="Where the council agrees.")
    clashes: str = Field(..., description="Where the council clashes.")
    blind_spots: str = Field(..., description="Blind spots the council caught.")
    recommendation: str = Field(..., description="A clear, direct recommendation.")
    proposed_goal: str = Field(..., description="The single concrete deterministic next step or goal.")


class GoalFeedback(BaseModel):
    """Feedback from an advisor on the Chairman's proposed goal."""

    advisor_name: str = Field(..., description="The name of the advisor giving feedback.")
    is_optimal: bool = Field(
        ..., description="True if the goal is deterministic, actionable, and safe. False otherwise."
    )
    critique: str = Field(..., description="If not optimal, what needs to change. If optimal, brief validation.")
