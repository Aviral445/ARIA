"""
test_adk.py — Autonomous Verification Test for Sink_ADK
"""

from tools import sample_tool

def test_sink_adk_basic():
    res = sample_tool("test_ping")
    assert "Executed successfully" in res

if __name__ == "__main__":
    test_sink_adk_basic()
    print("✅ Sink_ADK basic test passed!")
