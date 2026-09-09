"""
test_adk.py — Autonomous Verification Test for Audio_Synthesis_ADK
"""

from tools import sample_tool

def test_audio_synthesis_adk_basic():
    res = sample_tool("test_ping")
    assert "Executed successfully" in res

if __name__ == "__main__":
    test_audio_synthesis_adk_basic()
    print("✅ Audio_Synthesis_ADK basic test passed!")
