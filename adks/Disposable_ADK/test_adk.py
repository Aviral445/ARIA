"""
test_adk.py — Autonomous Verification Test for Disposable_ADK
"""

from tools import sample_tool

def test_disposable_adk_basic():
    res = sample_tool("test_ping")
    assert "Executed successfully" in res

if __name__ == "__main__":
    test_disposable_adk_basic()
    print("✅ Disposable_ADK basic test passed!")
