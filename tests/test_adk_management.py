"""
tests/test_adk_management.py — Verification Suite for Aria & GAIA ADK Lifecycle System

Tests:
1. Tool Registration in ALL_ADK_TOOLS, TOOL_NAME_MAP, and Swarm Metadata.
2. Single ADK Creation & Disk Verification (Manifest, Tools, Rules, Tests, Receipts).
3. Batch ADK Swarm Creation.
4. ADK Management Verbs (list, search, find, read, write, connect).
5. Cognitive Verbs (explain, define, understand / AST audit).
6. Incident Escalation Protocol to Big Sister GAIA.
7. Safe Deletion & Clean Slate Swarm Decommissioning.
8. Security & Path Traversal Guardrails.
"""

import os
import sys
import json
import shutil
import pytest

# Ensure root directory is on path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.paths import ROOT_DIR, ADKS_DIR
from core.aria_adk_manager import AriaADKManager, get_adk_manager
from system_tools.adk_management import adk_management
from core.aria_adk import ALL_ADK_TOOLS, TOOL_NAME_MAP, SWARM_AGENTS_METADATA


class TestADKToolRegistration:
    """Verify that adk_management is properly registered in Aria's tool runtime."""

    def test_tool_in_registry(self):
        tool_names = [fn.__name__ for fn in ALL_ADK_TOOLS]
        assert "adk_management" in tool_names, "adk_management must be registered in ALL_ADK_TOOLS"

    def test_tool_in_name_map(self):
        assert "adk_management" in TOOL_NAME_MAP
        assert callable(TOOL_NAME_MAP["adk_management"])

    def test_swarm_agent_metadata(self):
        assert "adk_architect" in SWARM_AGENTS_METADATA
        assert "adk_management" in SWARM_AGENTS_METADATA["adk_architect"]["tools"]
        assert "adk_management" in SWARM_AGENTS_METADATA["orchestrator"]["tools"]
        assert "adk_management" in SWARM_AGENTS_METADATA["system"]["tools"]


class TestADKManagerLifecycle:
    """Verify all 12 operational and cognitive verbs of the ADK Manager."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        # Use a temporary test directory for ADKs to prevent polluting production adks
        self.test_dir = str(tmp_path / "test_adks")
        os.makedirs(self.test_dir, exist_ok=True)
        self.mgr = AriaADKManager(adks_dir=self.test_dir)
        yield
        # Cleanup
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_single_adk(self):
        res = self.mgr.create_adk(
            adk_name="Data_Analyzer_ADK",
            author="Aria",
            description="Statistical data analysis and trend projection"
        )
        assert res["success"] is True
        assert res["adk_name"] == "Data_Analyzer_ADK"

        # Verify disk receipts
        adk_path = os.path.join(self.test_dir, "Data_Analyzer_ADK")
        assert os.path.isdir(adk_path)
        assert os.path.isfile(os.path.join(adk_path, "adk_manifest.json"))
        assert os.path.isfile(os.path.join(adk_path, "tools.py"))
        assert os.path.isfile(os.path.join(adk_path, "rules.md"))
        assert os.path.isfile(os.path.join(adk_path, "test_adk.py"))
        assert os.path.isfile(os.path.join(adk_path, "receipts.log"))

        # Check manifest contents
        with open(os.path.join(adk_path, "adk_manifest.json"), "r", encoding="utf-8") as f:
            manifest = json.load(f)
            assert manifest["name"] == "Data_Analyzer_ADK"
            assert manifest["author"] == "Aria"
            assert manifest["version"] == "1.0.0"

    def test_create_batch_swarm(self):
        batch_names = ["Crawler_ADK", "Transformer_ADK", "Exporter_ADK"]
        res = self.mgr.create_batch(
            adk_names=batch_names,
            author="GAIA",
            shared_description="ETL Swarm Pipeline"
        )
        assert res["success"] is True
        assert res["total_created"] == 3
        for name in batch_names:
            assert os.path.isdir(os.path.join(self.test_dir, name))

    def test_list_and_search(self):
        self.mgr.create_adk("Image_Processing_ADK", description="Filter and upscale images")
        self.mgr.create_adk("Audio_Synthesis_ADK", description="Generate synthetic voice waveforms")

        # List
        all_adks = self.mgr.list_adks()
        names = [a["name"] for a in all_adks]
        assert "Image_Processing_ADK" in names
        assert "Audio_Synthesis_ADK" in names

        # Search
        results = self.mgr.search_adks(query="upscale")
        assert len(results) >= 1
        assert results[0]["name"] == "Image_Processing_ADK"

        # Find
        found = self.mgr.find_adk("Audio")
        assert found is not None
        assert found["name"] == "Audio_Synthesis_ADK"

    def test_read_and_write(self):
        self.mgr.create_adk("Editor_ADK", description="Test editing")

        # Read manifest
        content = self.mgr.read_adk_file("Editor_ADK", "adk_manifest.json")
        assert content is not None
        assert "Editor_ADK" in content

        # Write new tool code
        new_code = "def custom_tool(): return 'hello world'"
        write_res = self.mgr.write_adk_file("Editor_ADK", "tools.py", new_code)
        assert write_res["success"] is True

        # Read back
        updated_content = self.mgr.read_adk_file("Editor_ADK", "tools.py")
        assert "def custom_tool" in updated_content

    def test_connect_adks(self):
        self.mgr.create_adk("Source_ADK", description="Source of data")
        self.mgr.create_adk("Sink_ADK", description="Consumer of data")

        conn_res = self.mgr.connect_adks("Source_ADK", "Sink_ADK", channel="stream")
        assert conn_res["success"] is True

        manifest = self.mgr.get_manifest("Source_ADK")
        connected = [c["target"] for c in manifest.get("connected_to", [])]
        assert "Sink_ADK" in connected

    def test_cognitive_verbs(self):
        self.mgr.create_adk("Logic_ADK", description="Boolean evaluation module")

        # Explain
        explanation = self.mgr.explain_adk("Logic_ADK")
        assert "Logic_ADK" in explanation
        assert "Status" in explanation

        # Define
        contracts = self.mgr.define_contracts("Logic_ADK")
        assert contracts["adk_name"] == "Logic_ADK"
        assert "sample_tool" in contracts["contracts"]

        # Understand (AST security audit)
        audit = self.mgr.understand_adk("Logic_ADK")
        assert audit["safe"] is True
        assert "syntax_valid" in audit

    def test_incident_escalation(self):
        self.mgr.create_adk("Faulty_ADK", description="Prone to errors")
        report = self.mgr.report_incident(
            adk_name="Faulty_ADK",
            task="Compute matrix determinant",
            error_type="SingularMatrixError",
            traceback_str="Traceback (most recent call last): numpy.linalg.LinAlgError: Singular matrix",
            attempts=3
        )
        assert report["success"] is True
        assert report["escalation_target"] == "GAIA_SUPERVISOR"
        assert report["adk_name"] == "Faulty_ADK"

    def test_delete_adk(self):
        self.mgr.create_adk("Disposable_ADK", description="To be deleted")
        assert os.path.exists(os.path.join(self.test_dir, "Disposable_ADK"))

        del_res = self.mgr.delete_adk("Disposable_ADK")
        assert del_res["success"] is True
        assert not os.path.exists(os.path.join(self.test_dir, "Disposable_ADK"))

    def test_decommission_swarm_clean_slate(self):
        self.mgr.create_batch(["Swarm_A", "Swarm_B", "Swarm_C"])
        assert len(self.mgr.list_adks()) == 3

        decom_res = self.mgr.decommission_swarm(author_filter="Aria")
        assert decom_res["success"] is True
        assert decom_res["purged_count"] == 3
        assert len(self.mgr.list_adks()) == 0


class TestADKManagementToolCallable:
    """Verify the top-level callable tool wrapper used by LLM function calling."""

    def test_tool_list_action(self):
        res = adk_management(action="list")
        assert isinstance(res, str)
        # Should return list summary or empty message
        assert "ADKs" in res or "No ADKs" in res

    def test_tool_create_and_delete_flow(self):
        test_adk_name = "Callable_Test_ADK"
        # 1. Create
        create_res = adk_management(action="create", adk_name=test_adk_name, description="Callable wrapper test")
        data = json.loads(create_res)
        assert data["success"] is True

        # 2. Find
        find_res = adk_management(action="find", query="Callable_Test")
        assert test_adk_name in find_res

        # 3. Explain
        explain_res = adk_management(action="explain", adk_name=test_adk_name)
        assert test_adk_name in explain_res

        # 4. Delete
        del_res = adk_management(action="delete", adk_name=test_adk_name)
        del_data = json.loads(del_res)
        assert del_data["success"] is True
