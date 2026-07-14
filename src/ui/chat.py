"""
Chat UI components.
"""
import json
import logging
from typing import Any

import streamlit as st

from src.domain.context_builder import build_dashboard_context
from src.services.backend_client import get_llm_response_http

logger = logging.getLogger(__name__)

def render_widget(data: dict) -> None:
    """Check for and render a Generative UI widget if requested by the LLM."""
    widget_type = data.get("widget_type")
    widget_data = data.get("widget_data")
    if not widget_type or not widget_data:
        return

    from src.widgets import WIDGET_REGISTRY

    render_fn = WIDGET_REGISTRY.get(widget_type)
    if render_fn:
        try:
            fig = render_fn(widget_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        except (KeyError, TypeError, ValueError) as exc:
            logger.error("Widget rendering failed for type=%s: %s", widget_type, exc)
            st.error(f"Failed to render chart: {exc}")

def render_chat(c360: dict[str, Any], language: str, customer_id: str) -> None:
    """Render the conversational AI chat interface."""
    st.subheader("💬 Chat with Aria")

    history_key = f"messages_{customer_id}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    messages: list[dict[str, str]] = st.session_state[history_key]
    user_input = None

    for i, msg in enumerate(messages):
        avatar = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(msg["role"], avatar=avatar):
            if msg["role"] == "assistant":
                try:
                    data = json.loads(msg["content"])
                    conv_resp = data.get("conversational_response", "")
                    if conv_resp:
                        st.write(conv_resp)
                    else:
                        st.write(data.get("response", data))

                    render_widget(data)

                    follow_up = data.get("follow_up_question", "")
                    if follow_up:
                        st.markdown(f"**{follow_up}**")

                    tips = data.get("recommended_tips", [])
                    for j, tip in enumerate(tips):
                        if st.button(tip, key=f"tip_{i}_{j}"):
                            user_input = tip
                except json.JSONDecodeError:
                    st.markdown(msg["content"])
            else:
                st.markdown(msg["content"])

    st.markdown("**Suggested Actions:**")
    col1, col2, col3 = st.columns(3)
    surplus = c360.get("investable_surplus", 0.0)

    if col1.button("📊 Analyze spending"):
        user_input = "What are my top expenses and how can I cut back to invest?"
    if col2.button("📈 What-If Simulator"):
        user_input = (
            f"I have ₹{surplus:,.0f} investable surplus per month. "
            "What if I invest 70% of it in a SIP? Show me a 10-year projection chart."
        )
    if col3.button("🤝 Connect with RM"):
        user_input = (
            "I am interested in complex market-linked insurance products. "
            "Please connect me to a Relationship Manager."
        )

    if prompt := st.chat_input("Ask Aria anything about your finances..."):
        user_input = prompt

    if user_input:
        dashboard_context = build_dashboard_context(c360)
        contextual_message = f"{dashboard_context}\n\nUser question: {user_input}"

        messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="user"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="assistant"):
            sliced_messages = messages[-5:-1] if len(messages) > 4 else messages[:-1]
            context_messages = [*sliced_messages, {"role": "user", "content": contextual_message}]

            raw_response = get_llm_response_http(context_messages, customer_id, language)

            try:
                cleaned_str = raw_response.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned_str)
                conv_resp = data.get("conversational_response", "")
                if conv_resp:
                    st.write(conv_resp)
                else:
                    st.write(data.get("response", data))

                render_widget(data)

                follow_up = data.get("follow_up_question", "")
                if follow_up:
                    st.markdown(f"**{follow_up}**")

                tips = data.get("recommended_tips", [])
                for j, tip in enumerate(tips):
                    st.button(tip, key=f"tip_{len(messages)}_{j}")

                messages.append({"role": "assistant", "content": json.dumps(data)})
            except json.JSONDecodeError:
                import re
                match = re.search(
                    r'"conversational_response"\s*:\s*"(.*?)"\s*(?:,\s*"follow_up_question"|$)',
                    raw_response,
                    re.IGNORECASE | re.DOTALL,
                )
                if match:
                    clean_text = match.group(1).replace("\\n", "\n").replace('\\"', '"')
                else:
                    clean_text = (
                        raw_response.replace("```json", "").replace("```", "").replace("{", "").replace("}", "").strip()
                    )
                st.write(clean_text)
                messages.append({"role": "assistant", "content": clean_text})
