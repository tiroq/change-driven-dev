# Security Model

AI output is untrusted.

## File sandbox
- IO restricted to project root
- Realpath validation
- Symlink escape blocked

## Command allowlist
- Explicit allowlist only
- No network by default
- Timeouts enforced

Violations block progress and require human intervention.
