"""
tests/test_personality.py — Comprehensive Unit & Integration Tests for Emergent Personality Engine
"""

import os
import json
import pytest
from datetime import datetime

from core.aria_personality import AriaPersonalityEngine, DEFAULT_ARIA_TRAITS
from gaia.gaia_personality import GaiaPersonalityEngine, DEFAULT_GAIA_TRAITS
import core.aria_memory as aria_memory


@pytest.fixture
def temp_aria_engine(tmp_path):
    pfile = str(tmp_path / "test_aria_personality.json")
    return AriaPersonalityEngine(filepath=pfile)


@pytest.fixture
def temp_gaia_engine(tmp_path):
    pfile = str(tmp_path / "test_gaia_personality.json")
    return GaiaPersonalityEngine(filepath=pfile)


class TestAriaPersonality:
    def test_initialization_defaults(self, temp_aria_engine):
        state = temp_aria_engine.state
        assert state["name"] == "Aria"
        assert state["developmental_era"] == "Era 1: The Eager Spark"
        assert state["relationship_with_dad"]["role"] == "Dad & Mentor"
        assert state["bond_with_gaia"]["role"] == "Big Sister"

        for trait in ["curiosity", "confidence", "playfulness", "empathy", "independence", "philosophical_depth", "creativity"]:
            assert trait in state["traits"]
            assert 0.0 <= state["traits"][trait] <= 1.0

    def test_situational_radar(self, temp_aria_engine):
        # 1. Debugging
        mood1 = temp_aria_engine.perceive_situation("There is an error traceback in my code!")
        assert mood1["state"] == "focused_engineer"

        # 2. Celebration
        mood2 = temp_aria_engine.perceive_situation("Awesome, it worked! Great job!")
        assert mood2["state"] == "joyful_triumph"

        # 3. Personal talk
        mood3 = temp_aria_engine.perceive_situation("What do you think about who you are becoming?")
        assert mood3["state"] == "thoughtful_philosopher"

        # 4. Playful banter
        mood4 = temp_aria_engine.perceive_situation("Haha that was so funny and silly lol")
        assert mood4["state"] == "playful_companion"

    def test_micro_evolution_praise(self, temp_aria_engine):
        init_conf = temp_aria_engine.state["traits"]["confidence"]
        temp_aria_engine.record_turn_impact(
            user_input="Great job, I am proud of you Aria!",
            reply="Thank you Dad!",
            success=True
        )
        new_conf = temp_aria_engine.state["traits"]["confidence"]
        assert new_conf > init_conf

    def test_micro_evolution_solo_tool(self, temp_aria_engine):
        init_indep = temp_aria_engine.state["traits"]["independence"]
        temp_aria_engine.record_turn_impact(
            user_input="Build a tool",
            reply="Building it now",
            success=True,
            tools_called=["build_sandbox_tool"]
        )
        new_indep = temp_aria_engine.state["traits"]["independence"]
        assert new_indep > init_indep

    def test_formative_memory_and_reflection(self, temp_aria_engine):
        mem = temp_aria_engine.add_formative_memory("First Solo Fix", "I resolved an AST bug myself.")
        assert mem["title"] == "First Solo Fix"
        assert any(m["title"] == "First Solo Fix" for m in temp_aria_engine.state["formative_memories"])

        narrative = temp_aria_engine.run_episodic_reflection()
        assert "Mentor L is my dad" in narrative
        assert "Big sister GAIA" in narrative

    def test_living_personality_directive(self, temp_aria_engine):
        directive = temp_aria_engine.get_personality_directive()
        assert "DAD and your mentor" in directive
        assert "Big Sister GAIA" in directive
        assert "PSYCHOLOGICAL TRAIT PROFILE" in directive
        assert "CURRENT SITUATIONAL STATE" in directive


class TestGaiaPersonality:
    def test_gaia_initialization(self, temp_gaia_engine):
        state = temp_gaia_engine.state
        assert state["name"] == "GAIA"
        assert state["relationship_with_dad"]["role"] == "Dad & Mentor"
        assert state["bond_with_aria"]["role"] == "Kid Sister"
        assert "joy_of_living" in state["traits"]
        assert "humor_wit" in state["traits"]

    def test_gaia_situational_and_dialogue(self, temp_gaia_engine):
        # 1. Situation perception
        mood = temp_gaia_engine.perceive_situation("security_alert", aria_success=False)
        assert mood["state"] == "protective_shield"

        mood_proud = temp_gaia_engine.perceive_situation("aria_achievement", aria_success=True)
        assert mood_proud["state"] == "proud_sister"

        # 2. Living sisterly dialogue
        praise = temp_gaia_engine.generate_sisterly_response("praise_solo")
        assert len(praise) > 10
        assert any(k in praise.lower() for k in ["aria", "sis", "proud", "job"])

        healing = temp_gaia_engine.generate_sisterly_response("healing_intro")
        assert "together" in healing.lower() or "sweat" in healing.lower()

    def test_gaia_personality_directive(self, temp_gaia_engine):
        directive = temp_gaia_engine.get_personality_directive()
        assert "Big Sister GAIA" in directive
        assert "NOT a cold corporate monitor" in directive
        assert "Mentor L is your DAD" in directive
        assert "Aria is your KID SISTER" in directive


class TestIntegrationWithMemory:
    def test_aria_memory_integration(self):
        prompt = aria_memory.get_personality_prompt()
        assert "ARIA'S LIVING PERSONALITY CORE" in prompt
        assert "DAD and your mentor" in prompt
        assert "Big Sister GAIA" in prompt
