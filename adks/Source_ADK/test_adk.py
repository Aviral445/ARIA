"""
test_adk.py — Autonomous Verification Test for Source_ADK
"""

from tools import sample_tool

def test_source_adk_basic():
    res = sample_tool("test_ping")
    assert "Executed successfully" in res

if __name__ == "__main__":
    test_source_adk_basic()
    print("✅ Source_ADK basic test passed!")
