"""
test_adk.py — Autonomous Verification Test for Logic_ADK
"""

from tools import sample_tool

def test_logic_adk_basic():
    res = sample_tool("test_ping")
    assert "Executed successfully" in res

if __name__ == "__main__":
    test_logic_adk_basic()
    print("✅ Logic_ADK basic test passed!")
