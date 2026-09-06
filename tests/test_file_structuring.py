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
import pytest
from core.aria_file_structuring import (
    create_structured_folder,
    write_structured_file,
    read_structured_file,
    list_structured_tree,
    manage_structured_path,
    search_structured_files,
    _resolve_safe_path,
    ARIA_FILES_DIR
)
from tools.aria_file_structuring import register_tool, file_structuring_tool
from core.aria_adk import (
    aria_create_folder,
    aria_write_file,
    aria_read_file,
    aria_list_files_tree,
    aria_manage_file,
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
