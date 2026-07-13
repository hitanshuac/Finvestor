## Report Contract (Mandatory)

The subagent's final message MUST contain:

- **signal:** exactly one of `done` | `stuck` | `plan-assumption-broken`
  - `done` — all covered-AC tests written and green.
  - `stuck` — cannot reach green after genuine attempts; MUST list the root-cause hypotheses tested.
  - `plan-assumption-broken` — the plan's premise for this phase is false; include the broken assumption verbatim.
- **files:** every file created or modified.
- **commands:** the test commands run and their exit codes.
- **tests:** which covered-AC tests exist, named by AC ID, and their final state.
- **notes:** anything the orchestrator must know (max 3 lines).

A report without a signal is treated as stuck.
