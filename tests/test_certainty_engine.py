import pytest
import datetime
from app.milestones.routes import calculate_certainty

def test_calculate_certainty_high():
    now = datetime.datetime.now(datetime.timezone.utc)
    due = now + datetime.timedelta(hours=100)
    # Remaining work: 1 issue, Velocity: 48h, Time needed: 48h
    # Time remaining: 100h
    # Certainty: 100 / 48 = 2.08 (> 1.2)
    res = calculate_certainty(1, 48.0, due)
    assert res["tier"] == "High"
    assert res["score"] == 2.08

def test_calculate_certainty_medium():
    now = datetime.datetime.now(datetime.timezone.utc)
    due = now + datetime.timedelta(hours=50)
    # Certainty: 50 / 48 = 1.04 (0.9 - 1.2)
    res = calculate_certainty(1, 48.0, due)
    assert res["tier"] == "Medium"
    assert res["score"] == 1.04

def test_calculate_certainty_low():
    now = datetime.datetime.now(datetime.timezone.utc)
    due = now + datetime.timedelta(hours=30)
    # Certainty: 30 / 48 = 0.62 (< 0.9)
    res = calculate_certainty(1, 48.0, due)
    assert res["tier"] == "Low"
    assert res["score"] == 0.62

def test_calculate_certainty_overdue():
    now = datetime.datetime.now(datetime.timezone.utc)
    due = now - datetime.timedelta(hours=10)
    res = calculate_certainty(1, 48.0, due)
    assert res["tier"] == "Low"
    assert res["score"] == 0.0
    assert res["message"] == "Deadline passed"

def test_calculate_certainty_no_issues():
    now = datetime.datetime.now(datetime.timezone.utc)
    due = now + datetime.timedelta(hours=100)
    res = calculate_certainty(0, 48.0, due)
    assert res["tier"] == "High"
    assert res["score"] == 2.0
    assert res["message"] == "All tasks completed"

def test_calculate_certainty_no_deadline():
    res = calculate_certainty(1, 48.0, None)
    assert res["tier"] == "Unknown"
    assert res["score"] is None
