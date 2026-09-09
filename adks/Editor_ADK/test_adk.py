"""
test_adk.py — Autonomous Verification Test for Editor_ADK
"""

from tools import sample_tool

def test_editor_adk_basic():
    res = sample_tool("test_ping")
    assert "Executed successfully" in res

if __name__ == "__main__":
    test_editor_adk_basic()
    print("✅ Editor_ADK basic test passed!")
