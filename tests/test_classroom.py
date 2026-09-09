"""
tests/test_classroom.py — Unit tests for the Closed-Book Classroom SDLC Exam Engine
"""

import pytest
import os
import json
from core.classroom import ClassroomEngine

def test_classroom_questions_loaded():
    engine = ClassroomEngine()
    assert len(engine.questions["aria"]) == 10
    assert len(engine.questions["gaia"]) == 10
    
    # Check difficulty distribution: 4 Beginner, 4 Medium, 2 Hard
    aria_diffs = [q["difficulty"] for q in engine.questions["aria"]]
    assert aria_diffs.count("Beginner") == 4
    assert aria_diffs.count("Medium") == 4
    assert aria_diffs.count("Hard") == 2

    gaia_diffs = [q["difficulty"] for q in engine.questions["gaia"]]
    assert gaia_diffs.count("Beginner") == 4
    assert gaia_diffs.count("Medium") == 4
    assert gaia_diffs.count("Hard") == 2

def test_classroom_lifecycle():
    engine = ClassroomEngine()
    status = engine.start_exam()
    assert status["is_active"] is True
    assert 1195 <= status["remaining_seconds"] <= 1200
    assert status["anti_cheat_active"] is True

    # Generate answer for Q1
    ans_res = engine.generate_closed_book_answers(0)
    assert ans_res["success"] is True
    assert len(engine.aria_answers) == 1
    assert len(engine.gaia_answers) == 1

    # Anti-cheat logging
    engine.log_cheating_attempt("aria", "web_search", "Attempted DuckDuckGo scrape during exam")
    assert len(engine.cheating_events) == 1
    assert engine.cheating_events[0]["sister"] == "aria"

    # Finish exam and export
    engine._finish_exam()
    assert engine.is_completed is True
    assert engine.is_active is False
    
    export_file = engine.export_evaluation_sheet()
    assert os.path.exists(export_file)
    with open(export_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["duration_minutes"] == 20
        assert "aria_submission" in data
        assert "gaia_submission" in data
