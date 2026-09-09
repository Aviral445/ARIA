"""
test_adk.py — Autonomous Verification Test for Image_Processing_ADK
"""

from tools import sample_tool

def test_image_processing_adk_basic():
    res = sample_tool("test_ping")
    assert "Executed successfully" in res

if __name__ == "__main__":
    test_image_processing_adk_basic()
    print("✅ Image_Processing_ADK basic test passed!")
