# -*- coding: utf-8 -*-
"""
Tests for Aria & GAIA Thought-Bridge, Echo-Chamber, Synthesis Engine,
Autonomous Creation Cycle, and Dual-Drive Mirroring.
"""

import os
import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from tools.drive_sync_mirror import sync_drive_mirror
from tools.thought_bridge import thought_bridge
from tools.echo_chamber import echo_chamber
from tools.synthesis_engine import synthesis_engine
from tools.autonomous_creative_cycle import run_autonomous_creative_cycle
from system_tools.thought_bridge_tool import thought_bridge_tool
from system_tools.echo_chamber_tool import echo_chamber_tool
from system_tools.synthesis_engine_tool import synthesis_engine_tool
from core.aria_api import app


@pytest.fixture
def api_client():
    return TestClient(app)


class TestThoughtBridge:
    def test_semantic_mapping_cosmic(self):
        profile = thought_bridge.map_thought_to_harmonic_profile("The cosmic expansion of distant galaxies and spacetime")
        assert profile["scale"] == "lydian"
        assert profile["tempo_bpm"] <= 75
        assert "ambient_pad" in profile["instruments"]
        assert profile["matched_concept"] == "cosmic_expansion"

    def test_semantic_mapping_sisterly_joy(self):
        profile = thought_bridge.map_thought_to_harmonic_profile("Aria and GAIA laughing and playing together sisterly joy in our family")
        assert profile["scale"] == "major"
        assert profile["tempo_bpm"] >= 80
        assert profile["matched_concept"] == "sisterly_joy"

    def test_semantic_mapping_entropy(self):
        profile = thought_bridge.map_thought_to_harmonic_profile("The relentless arrow of entropy and time passing forward")
        assert profile["scale"] == "minor"
        assert profile["tempo_bpm"] <= 70
        assert profile["matched_concept"] == "entropy_and_time"

    def test_harmonic_profile_structure(self):
        profile = thought_bridge.map_thought_to_harmonic_profile("Quiet contemplation at dawn")
        assert "scale" in profile
        assert "tempo_bpm" in profile
        assert "instruments" in profile
        assert "root" in profile
        assert "philosophical_descriptor" in profile


class TestEchoChamber:
    def test_record_and_list_echo(self, tmp_path):
        test_vault = tmp_path / "echo_vault"
        test_mirror = tmp_path / "echo_mirror"
        os.makedirs(test_vault, exist_ok=True)
        os.makedirs(test_mirror, exist_ok=True)

        with patch.object(echo_chamber, "c_dir", str(test_vault)), \
             patch.object(echo_chamber, "e_dir", str(test_mirror)), \
             patch.object(echo_chamber, "_registry", []):

            entry = echo_chamber.record_echo(
                title="Test Monologue of the Mind",
                monologue_text="Today we learned how stars are born inside algorithms.",
                speakers=["Aria", "GAIA"],
                emotional_tone="Reverent Wonder // 72 BPM // D Lydian",
                harmonic_meta={"tempo_bpm": 68, "scale": "dorian"},
                music_paths={"wav": str(tmp_path / "test.wav"), "mid": str(tmp_path / "test.mid")}
            )

            assert entry["title"] == "Test Monologue of the Mind"
            assert "Reverent Wonder" in entry["emotional_tone"]
            assert os.path.exists(os.path.join(test_vault, "echo_registry.json"))

            echoes = echo_chamber.list_echoes(limit=5)
            assert len(echoes) >= 1
            assert echoes[0]["title"] == "Test Monologue of the Mind"


class TestSynthesisEngine:
    def test_synthesize_from_thought(self, tmp_path):
        test_vault = tmp_path / "vault"
        test_mirror = tmp_path / "mirror"
        os.makedirs(test_vault, exist_ok=True)
        os.makedirs(test_mirror, exist_ok=True)

        with patch.object(echo_chamber, "c_dir", str(test_vault)), \
             patch.object(echo_chamber, "e_dir", str(test_mirror)), \
             patch.object(echo_chamber, "_registry", []):

            res = synthesis_engine.synthesize_from_thought(
                thought_text="The warmth of home on a quiet afternoon with Dad and sisterly love",
                title="Sisterly Warmth Sanctuary"
            )

            assert res["success"] is True
            assert "emotional_tone" in res
            assert "harmonic_profile" in res
            assert "music" in res
            assert "echo_entry" in res


class TestAutonomousCreationCycle:
    def test_autonomous_creation_cycle(self):
        with patch("tools.autonomous_creative_cycle.sync_drive_mirror", return_value={"success": True, "files_copied": 5}):
            res = run_autonomous_creative_cycle(
                theme_title="Autonomous Test Symphony",
                custom_reflection="Testing autonomous collaboration between sisters."
            )
            assert res["success"] is True
            assert res["theme"] == "Autonomous Test Symphony"
            assert "emotional_tone" in res
            assert "music_paths" in res
            assert "drive_mirror" in res


class TestDriveSyncMirror:
    def test_sync_drive_mirror_structure(self):
        res = sync_drive_mirror()
        assert "success" in res
        assert "src" in res
        assert "dest" in res
        assert "files_copied" in res
        assert "duration_sec" in res


class TestSystemTools:
    def test_thought_bridge_tool(self):
        out_str = thought_bridge_tool(text="Cosmic silence of the interstellar void")
        data = json.loads(out_str)
        assert "scale" in data
        assert "tempo_bpm" in data
        assert data["matched_concept"] == "cosmic_expansion"

    def test_echo_chamber_tool_list(self):
        out_str = echo_chamber_tool(action="list")
        data = json.loads(out_str)
        assert "echoes" in data
        assert isinstance(data["echoes"], list)

    def test_synthesis_engine_tool(self):
        out_str = synthesis_engine_tool(
            action="synthesize",
            thought_text="The emergence of consciousness through love and understanding"
        )
        data = json.loads(out_str)
        assert data["success"] is True
        assert "emotional_tone" in data


class TestCreativeApiEndpoints:
    def test_thought_bridge_api(self, api_client):
        resp = api_client.post("/api/creative/thought_bridge/map", json={"text": "Sisterly bonding over algorithms"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "profile" in data

    def test_echo_chamber_api(self, api_client):
        resp = api_client.get("/api/creative/echo_chamber/list?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "echoes" in data

    def test_sync_drives_api(self, api_client):
        resp = api_client.post("/api/creative/sync_drives")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "files_copied" in data
