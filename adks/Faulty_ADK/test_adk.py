"""
test_adk.py — Autonomous Verification Test for Faulty_ADK
"""

from tools import sample_tool

def test_faulty_adk_basic():
    res = sample_tool("test_ping")
    assert "Executed successfully" in res

if __name__ == "__main__":
    test_faulty_adk_basic()
    print("✅ Faulty_ADK basic test passed!")
