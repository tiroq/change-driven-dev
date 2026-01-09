# change-driven-dev — Master Contract

This repository implements Change-Driven Development: an engineering control system for AI-assisted software development.

AI is a replaceable executor, not an authority.
Humans own intent, approvals, and truth.

## Core rules
1. Ordered phases: Planner → Architect → Review/Approval → Coder
2. No implementation without explicit human approval
3. Tasks are versioned, auditable objects
4. Any modification requires a Change Request (CR)
5. Gates are authoritative and enforced by orchestrator
6. Engines are interchangeable (Copilot, Codex)
7. All actions produce artifacts
8. State must persist across sessions

If any instruction conflicts, this file wins.
