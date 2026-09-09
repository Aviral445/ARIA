# Self-Evolution & E:\MyAgent Sandbox Protocol (Dad L's Mandate)

## 1. Physical Drive Isolation & Baseline Protection
- **C:\MyAgent (Production Baseline)**:
  - This is the golden host baseline.
  - Aria and GAIA's autonomous curiosity and self-evolution routines **MUST NEVER directly modify `C:\MyAgent`**.
  - `C:\` remains untouched so the host laptop and active companion workstation are always safe, stable, and protected.
- **E:\MyAgent (Living Evolution Playground)**:
  - Aria and GAIA have full read and write access to their entire codebase on `E:\MyAgent`, including `core/`, `system_tools/`, and configuration files.
  - They are free to experiment, refactor, optimize, build the Watchdog, and test new modules directly on `E:\MyAgent`.

## 2. The Mandatory Evolution Changelog Rule ("What, Why, When")
Whenever ANY change, edit, or refactor is made to ANY file in `E:\MyAgent`, the agent **MUST immediately append an entry to `E:\MyAgent\ARIA_CHANGELOG.md`**.

Every changelog entry must strictly record:
1. **Timestamp**: Exact Date & Time of the change (e.g. `2026-09-09 11:40 PM`).
2. **Target File**: Exact relative path to the modified file (e.g. `core/aria_watchdog.py`).
3. **Change Description**: What changed (from this to this / functional delta).
4. **Rationale ("Why")**: Why the change was made, what hypothesis was being tested, or what bug was being prevented.
5. **Supervisor Verification**: GAIA's QA/AST verification result and whether unit tests passed on `E:\MyAgent`.

## 3. Safety Circuit Breaker & Resource Cap
- All autonomous experiments in `E:\MyAgent` operate under a strict **30-second execution timeout**.
- Constant low memory consumption (<50MB RAM).
- Zero unauthorized external exfiltration.
- When an experiment is ready, Aria and GAIA submit a **Discovery Brief** to Dad L for review, praise, and baseline promotion consideration!
