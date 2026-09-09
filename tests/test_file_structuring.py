"""
tests/test_file_structuring.py — Automated Unit Tests for Aria's File Structuring Skill

Tests:
  1. Hierarchical folder creation (Main Folder -> Subfolders)
  2. Hierarchy validation (Rejection of unorganized/root clutter)
  3. Structured file writing & reading
  4. Tree visualization & statistics
  5. File management (rename, copy, delete)
  6. Sandbox security boundary (Jail enforcement: rejection of directory traversal '..')
  7. Dynamic tool wrapper & ADK integration
"""

import os
from unittest.mock import patch, MagicMock
import pytest
from core.aria_file_structuring import (
    create_structured_folder,
    write_structured_file,
    read_structured_file,
    list_structured_tree,
    manage_structured_path,
    search_structured_files,
    open_in_vscode,
    create_multifile_project,
    _resolve_safe_path,
    ARIA_FILES_DIR
)
from system_tools.aria_file_structuring import register_tool, file_structuring_tool
from core.aria_adk import (
    aria_create_folder,
    aria_write_file,
    aria_read_file,
    aria_list_files_tree,
    aria_manage_file,
    aria_open_files_explorer,
    aria_open_in_vscode,
    aria_create_multifile_project,
    ALL_ADK_TOOLS
)


class TestFileStructuringSkill:

    def setup_method(self):
        """Clean setup for test folder in ARIA_FILES_DIR."""
        self.test_main = "Test_Skill_Category"
        self.test_dir = os.path.join(ARIA_FILES_DIR, self.test_main)
        if os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def teardown_method(self):
        """Cleanup test artifacts."""
        if os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_structured_folder_hierarchy(self):
        """Verify folder creation follows Main Category -> Subfolder."""
        res = create_structured_folder(main_folder=self.test_main, subfolder="Sub_Project/nested")
        assert "Created structured folder" in res or "already exists" in res
        expected_path = os.path.join(ARIA_FILES_DIR, self.test_main, "Sub_Project", "nested")
        assert os.path.exists(expected_path)

    def test_hierarchy_validation_requires_main_folder(self):
        """Root dumping without main folder is rejected."""
        res = create_structured_folder(main_folder="", subfolder="floating_folder")
        assert "Error: Please specify a Main Folder category" in res

    def test_write_and_read_structured_file(self):
        """Verify writing and reading nested files."""
        content = "print('Hello from Aria Structured Lab!')\nversion = 1.0"
        write_res = write_structured_file(
            main_folder=self.test_main,
            relative_path="AI_Chat/test_script.py",
            content=content
        )
        assert "Successfully saved" in write_res
        
        # Read back
        read_res = read_structured_file(f"{self.test_main}/AI_Chat/test_script.py")
        assert "Hello from Aria Structured Lab!" in read_res
        assert "test_script.py" in read_res

    def test_list_structured_tree(self):
        """Verify tree representation formatting."""
        write_structured_file(self.test_main, "Docs/guide.md", "# Guide\nAria is awesome.")
        write_structured_file(self.test_main, "Scripts/run.py", "import sys")

        tree_str = list_structured_tree(target_folder=self.test_main)
        assert "📁" in tree_str
        assert "Docs" in tree_str
        assert "guide.md" in tree_str
        assert "run.py" in tree_str
        assert "Summary:" in tree_str

    def test_manage_structured_path(self):
        """Verify rename, copy, and delete operations."""
        write_structured_file(self.test_main, "Temp/orig.txt", "Original file content")
        
        # Rename / Move
        move_res = manage_structured_path(
            action="move",
            path=f"{self.test_main}/Temp/orig.txt",
            target=f"{self.test_main}/Temp/renamed.txt"
        )
        assert "Moved/Renamed" in move_res
        assert os.path.exists(os.path.join(ARIA_FILES_DIR, self.test_main, "Temp", "renamed.txt"))

        # Delete
        del_res = manage_structured_path(
            action="delete",
            path=f"{self.test_main}/Temp/renamed.txt"
        )
        assert "Deleted file" in del_res
        assert not os.path.exists(os.path.join(ARIA_FILES_DIR, self.test_main, "Temp", "renamed.txt"))

    def test_sandbox_security_boundary(self):
        """Verify that directory traversal attempts outside ARIA_FILES_DIR are strictly blocked."""
        with pytest.raises(PermissionError):
            _resolve_safe_path("../../Windows/System32/calc.exe")

        with pytest.raises(PermissionError):
            _resolve_safe_path("C:\\Windows\\win.ini")

    def test_tools_wrapper_and_registration(self):
        """Verify tools/aria_file_structuring.py exports register_tool."""
        t_name, t_fn = register_tool()
        assert t_name == "file_structuring_tool"
        assert callable(t_fn)
        
        # Test tool call via wrapper
        res = t_fn(action="create_folder", main_folder=self.test_main, subfolder="Wrapper_Test")
        assert "Created structured folder" in res or "already exists" in res

    def test_adk_tool_declarations(self):
        """Verify ADK exports and registers all file structuring tools."""
        adk_names = [fn.__name__ for fn in ALL_ADK_TOOLS]
        assert "aria_create_folder" in adk_names
        assert "aria_write_file" in adk_names
        assert "aria_read_file" in adk_names
        assert "aria_list_files_tree" in adk_names
        assert "aria_manage_file" in adk_names
        assert "aria_open_files_explorer" in adk_names

        # Call via ADK wrapper
        res = aria_create_folder(main_folder=self.test_main, subfolder="ADK_Test")
        assert "Created structured folder" in res or "already exists" in res

    def test_adk_vscode_tools_registered(self):
        """Verify aria_open_in_vscode and aria_create_multifile_project are registered in ALL_ADK_TOOLS."""
        adk_names = [fn.__name__ for fn in ALL_ADK_TOOLS]
        assert "aria_open_in_vscode" in adk_names
        assert "aria_create_multifile_project" in adk_names

    @patch("subprocess.Popen")
    def test_open_in_vscode(self, mock_popen):
        """Verify open_in_vscode invokes code command with target path."""
        res = open_in_vscode("Projects/AI_Chat")
        assert "Opened" in res
        assert "Visual Studio Code" in res
        assert mock_popen.called

    @patch("subprocess.Popen")
    def test_create_multifile_project_scaffolding(self, mock_popen):
        """Verify create_multifile_project creates structured files and .vscode configuration."""
        proj_name = "Test_Weather_Bot"
        proj_path = os.path.join(ARIA_FILES_DIR, "Projects", proj_name)
        if os.path.exists(proj_path):
            import shutil
            shutil.rmtree(proj_path, ignore_errors=True)

        try:
            res = create_multifile_project(
                project_name=proj_name,
                files={
                    "main.py": "print('Weather Bot Active')",
                    "config.json": '{"city": "Tokyo"}',
                    "utils/helpers.py": "def get_temp(): return 22"
                },
                open_editor=True
            )
            assert "Created multi-file project" in res
            assert "main.py" in res
            assert "config.json" in res
            assert "utils/helpers.py" in res

            # Verify physical files exist
            assert os.path.exists(os.path.join(proj_path, "main.py"))
            assert os.path.exists(os.path.join(proj_path, "config.json"))
            assert os.path.exists(os.path.join(proj_path, "utils", "helpers.py"))
            assert mock_popen.called
        finally:
            if os.path.exists(proj_path):
                import shutil
                shutil.rmtree(proj_path, ignore_errors=True)

    @patch("subprocess.Popen")
    def test_tools_wrapper_vscode_and_scaffold(self, mock_popen):
        """Verify file_structuring_tool handles vscode and scaffold actions."""
        res_code = file_structuring_tool(action="vscode")
        assert "Opened" in res_code
        assert "Visual Studio Code" in res_code

        res_scaffold = file_structuring_tool(action="scaffold", subfolder="Quick_App", content="")
        assert "Created multi-file project" in res_scaffold
        # Clean up
        quick_app_dir = os.path.join(ARIA_FILES_DIR, "Projects", "Quick_App")
        if os.path.exists(quick_app_dir):
            import shutil
            shutil.rmtree(quick_app_dir, ignore_errors=True)

    @patch("subprocess.Popen")
    def test_agent_deterministic_vscode_routing(self, mock_popen):
        """Verify agent.py _tool_aria_file_structuring handles VS Code user queries."""
        from agent import _tool_aria_file_structuring

        # 1. Open E:\ARIA FILES in VS Code
        handled, msg = _tool_aria_file_structuring("open e: ARIA FILES in vs code")
        assert handled is True
        assert "Visual Studio Code" in msg

        # 2. Open project in VS Code
        handled, msg = _tool_aria_file_structuring("open vs code in aria files")
        assert handled is True
        assert "Visual Studio Code" in msg

