import asyncio
import os
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

# Adjust imports based on the actual LiteLLM or Langchain models configured in the project
# For this example, we assume ChatOpenAI or ChatGroq is available via langchain
try:
    from langchain_groq import ChatGroq

    # Initialize the model using the config from the core app
    model = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.7)
except ImportError:
    # Fallback to a mock model if the specific provider isn't installed
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel

    model = FakeMessagesListChatModel(responses=["Mock response"])

import sys

sys.path.append(os.path.dirname(__file__))
from council_schemas import AdvisorTake, CouncilState, GoalFeedback, GoalProposal, PeerReview

# ── Advisor Personas ──────────────────────────────────────────────────

ADVISORS = {
    "Contrarian": "Actively looks for what's wrong, what's missing, what will fail. Assumes the idea has a fatal flaw and tries to find it.",
    "First Principles": "Ignores the surface-level question and asks 'what are we actually trying to solve here?' Strips away assumptions.",
    "Expansionist": "Looks for upside everyone else is missing. What could be bigger? What adjacent opportunity is hiding?",
    "Outsider": "Has zero context about you, your field, or your history. Responds purely to what's in front of them.",
    "Executor": "Only cares about one thing: can this actually be done, and what's the fastest path to doing it?",
}

MAX_ITERATIONS = 3


# ── Graph Nodes ────────────────────────────────────────────────────────


async def generate_advisors(state: CouncilState) -> dict:
    """Spawn 5 parallel LLM calls to generate independent takes."""
    print("[Council] Generating parallel advisor takes...")

    async def get_take(name: str, persona: str) -> tuple[str, str]:
        prompt = f"""You are {name} on an LLM Council.
Your thinking style: {persona}

Context:
{state.get('context', 'No additional context provided.')}

Question:
{state['query']}

Respond from your perspective. Be direct and specific. Do not hedge."""

        # Use structured output for typed contract enforcement
        structured_llm = model.with_structured_output(AdvisorTake)
        try:
            result = await structured_llm.ainvoke([HumanMessage(content=prompt)])
            return name, result.analysis
        except Exception as e:
            # Hard-fail delegation rule
            print(f"❌ [{name}] Failed to validate schema: {e}")
            return name, f"ERROR: Failed to generate response - {e}"

    # Run all 5 advisors concurrently
    tasks = [get_take(name, persona) for name, persona in ADVISORS.items()]
    results = await asyncio.gather(*tasks)

    return {"advisor_takes": dict(results)}


async def generate_peer_reviews(state: CouncilState) -> dict:
    """Spawn 5 parallel LLM calls to critique the anonymized takes."""
    print("[Council] Conducting anonymous peer reviews...")

    # Anonymize takes for review
    anonymized_takes = "\n\n".join(
        f"**Response {chr(65+i)}:**\n{take}" for i, take in enumerate(state["advisor_takes"].values())
    )

    async def get_review(name: str) -> tuple[str, str]:
        prompt = f"""You are {name}, reviewing the outputs of an LLM Council.
Question: {state['query']}

Anonymized Responses:
{anonymized_takes}

Evaluate these responses objectively based on your persona."""

        structured_llm = model.with_structured_output(PeerReview)
        try:
            result = await structured_llm.ainvoke([HumanMessage(content=prompt)])
            # Format the output as a string for state storage
            review_text = (
                f"Strongest: {result.strongest_response}\n"
                f"Blind Spot: {result.biggest_blind_spot}\n"
                f"Universal Miss: {result.universal_miss}"
            )
            return name, review_text
        except Exception as e:
            return name, f"ERROR: Failed to review - {e}"

    tasks = [get_review(name) for name in ADVISORS.keys()]
    results = await asyncio.gather(*tasks)

    return {"peer_reviews": dict(results)}


async def synthesize_and_propose_goal(state: CouncilState) -> dict:
    """The Chairman reads reviews and proposes a specific goal."""
    print(f"[Council] Chairman synthesizing (Loop {state.get('loop_count', 0) + 1})...")

    takes_str = "\n".join(f"{name}: {take}" for name, take in state["advisor_takes"].items())
    reviews_str = "\n".join(f"{name}: {rev}" for name, rev in state["peer_reviews"].items())

    feedback_str = ""
    if state.get("goal_feedback"):
        feedback_str = "\n\nPREVIOUS GOAL FEEDBACK (Address these in your new proposal):\n"
        feedback_str += "\n".join(f"{name}: {fb}" for name, fb in state["goal_feedback"].items())

    prompt = f"""You are the Chairman of the LLM Council.
Question: {state['query']}

ADVISOR TAKES:
{takes_str}

PEER REVIEWS:
{reviews_str}
{feedback_str}

Propose a deterministic, actionable goal that satisfies the council's insights.
"""
    structured_llm = model.with_structured_output(GoalProposal)
    result = await structured_llm.ainvoke([HumanMessage(content=prompt)])

    # Format the final verdict document
    verdict = (
        f"## Where the Council Agrees\n{result.agreements}\n\n"
        f"## Where the Council Clashes\n{result.clashes}\n\n"
        f"## Blind Spots Caught\n{result.blind_spots}\n\n"
        f"## Recommendation\n{result.recommendation}\n\n"
        f"## Proposed Goal\n{result.proposed_goal}"
    )

    current_loop = state.get("loop_count", 0) + 1
    return {"proposed_goal": result.proposed_goal, "final_verdict": verdict, "loop_count": current_loop}


async def debate_goal(state: CouncilState) -> dict:
    """The loop engineering node: Advisors critique the Chairman's goal."""
    print("[Council] Advisors debating the proposed goal...")

    async def evaluate_goal(name: str, persona: str) -> tuple[str, bool, str]:
        prompt = f"""You are {name}.
Your thinking style: {persona}

The Chairman has proposed this goal:
{state['proposed_goal']}

Is this goal deterministic, actionable, and optimal from your perspective?
Critique it ruthlessly if it is vague or flawed."""

        structured_llm = model.with_structured_output(GoalFeedback)
        try:
            result = await structured_llm.ainvoke([HumanMessage(content=prompt)])
            return name, result.is_optimal, result.critique
        except Exception as e:
            return name, False, str(e)

    tasks = [evaluate_goal(name, persona) for name, persona in ADVISORS.items()]
    results = await asyncio.gather(*tasks)

    # Store feedback in a way that check_consensus can evaluate
    feedback_dict = {res[0]: f"{'✅ OPTIMAL' if res[1] else '❌ FLAWED'} - {res[2]}" for res in results}

    # Also calculate how many thought it was optimal
    sum(1 for res in results if res[1])
    # We pass optimal_count through a temporary state key or just evaluate it in the router

    return {"goal_feedback": feedback_dict}


def check_consensus(state: CouncilState) -> Literal["synthesize_and_propose_goal", "human_approval"]:
    """Conditional router: loop back or proceed to human approval."""
    feedback = state.get("goal_feedback", {})

    # Count how many advisors marked it as optimal
    optimal_count = sum(1 for f in feedback.values() if "✅ OPTIMAL" in f)

    print(f"[Council] Consensus Check: {optimal_count}/5 agree.")

    # Break loop if max iterations reached or supermajority (4/5) agree
    if optimal_count >= 4 or state.get("loop_count", 0) >= MAX_ITERATIONS:
        return "human_approval"

    print("[Council] Goal rejected. Looping back to Chairman for refinement...")
    return "synthesize_and_propose_goal"


def human_approval(state: CouncilState) -> dict:
    """Hit-in-the-loop interruption node before taking action."""
    print("[Council] Workflow paused for human approval.")

    # In LangGraph, interrupt raises a special exception that pauses the graph
    response = interrupt(
        {
            "proposed_goal": state["proposed_goal"],
            "verdict": state["final_verdict"],
            "message": "Council loop completed. Do you want to execute the proposed goal?",
        }
    )

    if response.get("approved"):
        print("[Council] Human approved execution.")
        return {"final_verdict": state["final_verdict"] + "\n\n**STATUS: APPROVED BY HUMAN**"}

    print("[Council] Human rejected execution.")
    return {"final_verdict": state["final_verdict"] + "\n\n**STATUS: REJECTED BY HUMAN**"}


# ── Build the Graph ────────────────────────────────────────────────────

workflow = StateGraph(CouncilState)

workflow.add_node("generate_advisors", generate_advisors)
workflow.add_node("generate_peer_reviews", generate_peer_reviews)
workflow.add_node("synthesize_and_propose_goal", synthesize_and_propose_goal)
workflow.add_node("debate_goal", debate_goal)
workflow.add_node("human_approval", human_approval)

# Define the flow
workflow.set_entry_point("generate_advisors")
workflow.add_edge("generate_advisors", "generate_peer_reviews")
workflow.add_edge("generate_peer_reviews", "synthesize_and_propose_goal")
workflow.add_edge("synthesize_and_propose_goal", "debate_goal")

# Loop routing
workflow.add_conditional_edges("debate_goal", check_consensus)

# After human approval, we end
workflow.add_edge("human_approval", END)

# Compile with a simple memory checkpointer for state persistence
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# ── Execution Helper ───────────────────────────────────────────────────


async def run_council(query: str, context: str = "", thread_id: str = "1"):
    """Helper to run the graph and print the verdict."""
    config = {"configurable": {"thread_id": thread_id}}

    # Initialize state
    initial_state = {"query": query, "context": context, "loop_count": 0}

    # Run the graph until it hits the interrupt
    async for _event in app.astream(initial_state, config, stream_mode="values"):
        # Just iterating to drive the async generator
        pass

    # Fetch the state at the interrupt
    state = app.get_state(config)
    print("\n" + "=" * 50)
    print("COUNCIL VERDICT READY")
    print("=" * 50)
    print(state.values.get("final_verdict"))
    print("=" * 50)

    # You would normally resume this by passing the approval dict:
    # app.stream(Command(resume={"approved": True}), config)

    return state.values
