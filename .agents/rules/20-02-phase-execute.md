# Anti-Over-Engineering Protocol (Ponytail Ladder)

This rule strictly enforces a minimalist, anti-bloat philosophy to counteract the tendency of LLMs to generate excessive boilerplate, unnecessary wrappers, or complex architectures for simple problems.

## The 7-Step Decision Ladder
Before writing any code to solve a task, the agent MUST evaluate the solution through this exact ladder in order. If a step satisfies the requirement, stop there and DO NOT proceed to the next step.

1. **YAGNI (You Aren't Gonna Need It)**: Does this feature or abstraction need to exist at all? If the user's core problem can be solved without it, skip it entirely.
2. **Context (Codebase Reuse)**: Is there already a helper function, utility class, or architectural pattern in the existing codebase that solves this? If yes, reuse it.
3. **Stdlib (Standard Library)**: Does the language's standard library natively support this? If yes, use the standard library instead of downloading a package.
4. **Native (Platform Features)**: Is there a native platform feature (e.g., standard HTML `<input type="date">` instead of a custom React datepicker component)? If yes, use the native feature.
5. **Dependencies**: Does an already-installed dependency solve this? Check the `package.json` or `requirements.txt`. Do not install a new dependency if an existing one can do the job.
6. **One-Liner**: Can the solution be expressed in a single line of clear, idiomatic code? If yes, write the one-liner instead of a full class or helper function.
7. **Minimum Viable Code**: Only if steps 1-6 fail, write the absolute minimum amount of code required to solve the task. No preemptive abstractions, no future-proofing wrappers, no speculative error handling for impossible states.

## Zero Boilerplate Enforcement
- **Rule**: If you generate a wrapper class around a standard library function that adds zero value, you have failed.
- **Action**: Strive for a codebase with negative lines of code. The best code is the code you never wrote.

---
### Source: `44-40-MASTER-style-and-quality.md`
---

# Anti-AI-Slop Design Rule

### Rule: 44-anti-ai-slop-design
- Owner layer: Global
- Scope: All UI layout generation, styling, diagramming, and visual asset creation
- Stability: core
- Status: active
- Directive: You MUST strictly avoid "lowest common denominator" AI visual patterns (AI-slop). Specifically: 1) NO full-screen rainbow/neon gradients. 2) NO typical AI card styling (`border-radius: 12px` + `border-left: 4px solid blue`). 3) NO emojis unless explicitly dictated by the brand. 4) NO SVGs used for complex imagery (people, scenes, devices). 5) NO fake statistics ("10,000+ users") or fake quotes. 6) AVOID overused AI fonts (Inter, Space Grotesk, Roboto) in favor of high-contrast pairings (e.g., distinctive Serif display + clean Sans body). 7) DO NOT invent color palettes from scratch; use `oklch` for adjustments or extract from references.
- Rationale: AI generators naturally default to generic, cluttered, and cheap-looking visuals characterized by unnecessary emojis, gradient overuse, and uninspired typography. Actively constraining these defaults forces the generation of high-fidelity, professional-grade outputs.
- Conflict handling: If brand guidelines explicitly conflict with this rule (e.g., the brand requires heavy gradient usage or emoji-centric copy), the explicit brand guidelines (Tier 3 Compliance) override this rule. Otherwise, this rule is absolute for all design tasks.
- Example: Using `oklch` to define a subtle dark mode background, pairing `Cormorant` (display) with `JetBrains Mono` (body), and using a plain gray rectangle as an image placeholder.
- Non-example: Adding a 🚀 emoji to a heading, wrapping content in a card with a thick neon left border, and drawing a crude SVG of a "user working on a laptop".
