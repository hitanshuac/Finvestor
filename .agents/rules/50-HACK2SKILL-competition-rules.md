---
trigger: inactive
---

# Hack2Skill Challenge Rules & Instructions

This master rule document governs the entire repository.

## 1. Important Rules
- The repository size MUST be less than 10 MB.
- The GitHub repository MUST be public.
- The repository MUST exclusively contain a single branch (`main`).

## 2. Challenge Expectations
Your solution MUST demonstrate:
- Ability to build a smart, dynamic assistant.
- Logical decision making based on user context.
- Practical and real-world usability.
- Clean and maintainable code.

## 3. Score Multiplier Guidelines
- The earlier you submit, the higher your final score (Time-Dependent Decay).
- The multiplier active at the exact timestamp of your submission applies to that specific attempt.

## 4. What to Submit
Your submission MUST include:
- A public GitHub repository link.
- Complete project code.
- A README explaining your chosen vertical, approach, logic, and assumptions.

# Hack2Skill PromptWars: Strict Agent Constraints

## 1. Git & Version Control (The Single-Branch Rule)
* **CRITICAL:** You MUST exclusively use and commit to the `main` branch. 
* You MUST maintain a strictly linear Git history.

## 2. Storage & Asset Management (< 10MB Limit)
* The entire repository MUST stay under 10 MB.
* You MUST explicitly add all database files (`.duckdb`), raw telemetry, and large datasets to `.gitignore`.

## 3. The README.md Contract (Submission Requirements)
When asked to update the `README.md`, you MUST include these exact sections prominently:
1. **Vertical/Persona:** "Sustainability / Enterprise ESG" built for an "Enterprise Sustainability Officer".
2. **Approach & Logic:** Explain the Bronze -> Silver -> Gold DuckDB pipeline.
3. **Assumptions Made:** List technical or business assumptions.

## 4. Evaluation Criteria (Code Standards)
* You MUST exclusively rely on vectorized operations (PyArrow/DuckDB) over standard Python loops.
* You MUST explicitly include semantic tags, ARIA labels, and proper contrast in UI components.
