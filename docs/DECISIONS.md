# Decision Model

## Tasks
Tasks are immutable, versioned objects.

## Change Requests (CR)
Any change requires a CR.
CR lifecycle: DRAFT → APPROVED → APPLIED

## Rework
- Before implementation: new task version
- During: pause → CR → new version
- After PASS: new task or CR

## Gates
- Define correctness
- Executed by orchestrator
- AI output is advisory
