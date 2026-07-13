# Technical Architecture Document (TAD)

## 1. System Architecture
**Architecture Style:** Split-Plane Monolithic Streamlit Dashboard with Layered Decoupling.
- **Control Plane:** `.agents/` directory handles strict SRE governance, skills, and workflows.
- **Data Plane:** `data/` directory handles local state and quarantine logs.
- **Execution Plane:** `src/` modules orchestrated by `main.py`.

## 2. Technology Stack
- **Frontend/Orchestration:** Streamlit (`main.py`)
- **Database/Analytics:** DuckDB (In-memory SQL analytics)
- **Data Manipulation:** Pandas
- **Language Models:** OpenAI API (`gpt-4o-mini` or `llama-3.1` proxy)
- **Python:** 3.11+

## 3. Module Breakdown
1. **`main.py`:** Thin UI layer. Manages Streamlit session state and component rendering.
2. **`src/data_engine.py`:** Contains `@st.cache_data` mock generators and `try/except` wrapped DuckDB pipelines.
3. **`src/avatar_ai.py`:** Contains LLM instantiation, prompt formatting, and generator functions for streaming outputs.
4. **`src/config.py`:** State configuration for Customer Profiles, LLM rules, and Hybrid RM Handoff protocols.
5. **`src/utils.py`:** CSS injection for IDBI premium branding.

## 4. Data Flow
1. User selects a Profile in `main.py`.
2. `data_engine.py` generates the 90-day Pandas DataFrame.
3. `data_engine.py` registers the DataFrame to DuckDB and extracts the Customer_360 dictionary.
4. User types a chat message.
5. `avatar_ai.py` injects the Customer_360 dictionary into the System Prompt.
6. OpenAI API streams the response chunks back to `main.py` via Python generator (`yield`).
