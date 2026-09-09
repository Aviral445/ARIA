"""
test_adk.py — Autonomous Verification Test for Data_Analyzer_ADK
"""

from tools import sample_tool

def test_data_analyzer_adk_basic():
    res = sample_tool("test_ping")
    assert "Executed successfully" in res

if __name__ == "__main__":
    test_data_analyzer_adk_basic()
    print("✅ Data_Analyzer_ADK basic test passed!")
