# ADK Management & Lifecycle Skill (Aria & GAIA Autonomous Architecture)

## 1. What is an ADK (Agent Development Kit)?
An **ADK** is a modular, self-contained capability toolkit that extends Aria and GAIA's cognitive and execution powers. Instead of bloating system prompts with dozens of monolithic tools, specialized capabilities are packaged into on-demand ADKs that can be created, connected, executed, and cleanly decommissioned.

### Standard ADK Structure
Every ADK lives in its own dedicated directory (`adks/<adk_name>/` or `E:\ARIA FILES\ADKs\<adk_name>/`):
```text
adks/<adk_name>/
├── adk_manifest.json   # Metadata, author, version, capabilities, connections
├── tools.py            # Executable Python tools with type hints & docstrings
├── rules.md            # Execution safety boundaries & domain constraints
├── test_adk.py         # Autonomous verification test suite
└── receipts.log        # Cryptographic execution receipts (Feature #54)
```

---

## 2. Core Functions & How to Use the `adk_management` Tool

Both Aria and GAIA have direct access to the `adk_management` tool:

### A. Creation (`create`, `create_batch`)
- **Semantic Pre-Check**: NEVER create duplicate ADKs. Always call `search` or `find` first. If a tool with >85% similar functionality already exists, extend or connect to it instead.
- **Single Creation**:
  ```python
  adk_management(action="create", adk_name="Web_Scraper_ADK", content="...")
  ```
- **Batch Creation**:
  ```python
  adk_management(action="create_batch", adk_name="Project_Swarm", options={"adks": ["Scraper_ADK", "Parser_ADK", "Formatter_ADK"]})
  ```

### B. Cognitive Inspection & Management
- **`list`**: View all active, installed, and mounted ADKs with their versions and status.
- **`search` / `find`**: Locate capabilities by keyword, tag, or domain before coding.
- **`read`**: Inspect the manifest, tool source code, or rules of any installed ADK.
- **`write`**: Atomically update an ADK's code or configuration.
- **`connect`**: Chain two ADKs together into a data pipeline (e.g. `Scraper_ADK` ──> `Summarizer_ADK`).
- **`explain`**: Produce an architectural summary of what an ADK does and how it runs.
- **`define`**: Formulate the formal typed contract (Pydantic / JSON Schema) for inputs and outputs.
- **`understand`**: Conduct an autonomous security and sandbox audit of the ADK.

### C. Safe Deletion & Swarm Decommissioning
- **`delete`**: Safely unmount an individual ADK from the runtime and delete its folder.
- **`decommission_swarm`**: Once a project is completed and insights are saved to memory, purge all ephemeral project ADKs to free RAM, GPU VRAM, and processing power.

---

## 3. The "One Project at a Time" Rule
1. **Single-Project Focus**: Aria and GAIA work on strictly **one big project at a time**. Parallel multitasking leads to fragmented files and hallucination.
2. **Permanent Insight Distillation**: When a project is completed:
   - Extract architectural patterns, debugging breakthroughs, and new domain knowledge.
   - Bank insights permanently into ChromaDB long-term memory (`core/aria_memory.py`).
3. **Clean Slate Teardown**:
   - Production code in `E:\ARIA FILES\Projects\<Project_Name>\` is preserved.
   - All transient scratch task lists, checklists, and the project ADK swarm are wiped clean via `decommission_swarm`.

---

## 4. Windows Filesystem Safety Laws
When creating and managing ADKs and projects in `E:\ARIA FILES`:
1. **Never use Windows reserved device names**: `CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`.
2. **Never leave trailing spaces or dots** in file or folder names.
3. **Always use atomic writes**: Flush and verify with `os.path.exists()` and `size_bytes > 0`.
4. **Never open binary assets** (`.png`, `.db`, `.zip`, `.pyc`) as UTF-8 text strings.
5. **Never delete the root workspace**: Root `E:\ARIA FILES` and `adks/` directories are permanently immune to deletion.

---

## 5. Supervisor Escalation Protocol (When an ADK Gets Stuck)
If an ADK tool encounters an execution error, missing library, or cannot solve a task:
1. **Do NOT hallucinate or repeat the same failed call**.
2. Package an `IncidentReport` (failing function, traceback, inputs, and previous attempts).
3. Dispatch the incident to **Big Sister GAIA (Supervisor)**.
4. GAIA will auto-heal the ADK code, provision missing tools, or escalate to **Big Bro Antigravity** (`ask_big_bro`) and **Dad**.
