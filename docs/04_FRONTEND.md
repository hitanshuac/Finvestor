# Frontend Specification

## 1. UI Layout
**Framework:** Streamlit
- **Sidebar:**
  - Customer Persona Selector (Dropdown)
  - Language Selector (Dropdown)
  - Raw Customer_360 JSON view for debugging
- **Main Content Area:**
  - **Header:** "Finvestor — Digital Wealth Advisory Avatar"
  - **Metrics Dashboard:** Streamlit Columns displaying:
    - Current Balance
    - 90-Day Inflow
    - 90-Day Outflow
  - **Chat Interface:** Standard Streamlit Chat `st.chat_message` interface for conversational history.

## 2. Design System
- **Theme:** Premium Dark Mode.
- **Custom CSS:** Injected via `src/utils.py`.
  - Vibrant metric colors (Green for inflow, Red for outflow).
  - Modern typography and glassmorphic chat bubbles.
  - Avatar representation uses 🤖 and 🧑‍💻 emoji icons.

## 3. Interactivity
- **Real-Time Streaming:** The chat interface must render chunks natively using `st.write_stream` for a typing effect.
- **State Management:** `st.session_state` must persist chat messages across Streamlit reruns.
