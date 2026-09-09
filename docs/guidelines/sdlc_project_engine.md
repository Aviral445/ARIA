# Big-Project SDLC Engine Skill (Aria & GAIA Autonomous Architecture)

## 1. Overview & Operational Mandate
When the user tasks Aria and GAIA with building, designing, or implementing a big project (e.g. software tool, application, analyzer, scraper, or visualizer), they MUST execute the standardized **4-Part Autonomous Engineering Architecture** in `E:\ARIA FILES\Projects\<Project_Name>\` using `sdlc_project_engine()`.

---

## 2. The 4-Part Architecture Workflow

### Part 1: Ingestion & Google Deep Research ──> Project Database
- **Action**: `sdlc_project_engine(action="ingest", project_name="Project_Name", topic="...")`
- Ingests the project domain, performs live Google technical research, synthesizes a 1-page Deep Knowledge Brief (`docs/DEEP_KNOWLEDGE_BRIEF.md`), system specifications, and records the initial state into `database/project_ledger.json`.

### Part 2: Blueprints & Scaffolding
- **Action**: `sdlc_project_engine(action="scaffold", project_name="Project_Name")`
- Automatically establishes the complete folder topology:
  ```text
  E:\ARIA FILES\Projects\<Project_Name>\
  ├── docs/             # ARCHITECTURE.md, TASK_LIST.md, CHECKLIST.md
  ├── src/              # Core production code (preserved forever)
  ├── tests/            # Independent verification test suite (GAIA managed)
  ├── adks/             # Specialized ephemeral ADK swarm
  └── database/         # project_ledger.json (receipts & state)
  ```

### Part 3: GAIA's Independent QA Suite (Red-Green TDD Gate)
- **Action**: `sdlc_project_engine(action="qa_suite", project_name="Project_Name")`
- Big Sister GAIA authors an independent test suite in `tests/test_<project>.py`.
- **Red-Green Verification Gate**: GAIA's test suite MUST run and fail against empty `src/` before any implementation code is written. If it passes prematurely, it is rejected as a tautology.
- **Test Immutability**: The test file is locked read-only (`stat.S_IREAD`) so Aria cannot weaken or modify test assertions.

### Part 4: Autonomous TDD & 5-Tries Escalation Ladder
- **Action**: `sdlc_project_engine(action="tdd_cycle", project_name="Project_Name")`
- Aria implements modular code in `src/main_module.py`.
- Tests execute in an **isolated 30s worker subprocess** (`pytest -o pythonpath=src`).
- If tests fail, Aria auto-repairs code across 5 attempts using the Diagnostic Delta traceback loop.
- **Escalation Ladder**:
  - Attempts 1–2: Big Sister GAIA Auto-Heal directives.
  - Attempts 3–4: Escalation to Big Bro Antigravity mentorship bridge.
  - Attempt 5: Formal **Dad (Mentor L) Escalation Card** generated in `data/dad_escalations.json`.

### Part 5: Memory Distillation & Clean Slate Teardown
- Upon passing all tests:
  1. Breakthrough architectural insights are saved to `data/project_insights.json` and ChromaDB long-term memory.
  2. The ephemeral ADK swarm and scratch checklists are decommissioned (`clean_slate_teardown`) to release RAM, CPU, and disk space.
  3. Production deliverables in `src/` are permanently preserved.
  4. The Single-Project Concurrency Lock is released.

---

## 3. End-to-End Autonomous Execution

When asked to build a project from scratch, call the full pipeline in one command:
```python
sdlc_project_engine(action="start", project_name="Audio_Visualizer", topic="Real-time WebGL audio frequency visualizer")
```
This acquires the concurrency lock, performs deep research, scaffolds the architecture, runs GAIA's QA gate, conducts the autonomous TDD loop, distills insights to memory, and cleanly tears down scratch resources.
