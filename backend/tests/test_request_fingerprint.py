from __future__ import annotations

import json

from backend.utils.request_fingerprint import (
    log_request,
    make_fingerprint,
    normalise_brief,
)


def test_normalise_brief_keeps_expected_fields():
    brief = {
        "brand_name": "Test",
        "industry": "Food",
        "location": "Kolkata",
        "primary_goal": "Increase sales",
        "random_field": "ignore me",
        "target_audience": ["Students"],
    }

    normalised = normalise_brief(brief)
    assert "brand_name" in normalised
    assert "industry" in normalised
    assert "random_field" not in normalised


def test_make_fingerprint_is_stable_and_changes_with_input():
    brief1 = {"brand_name": "Brand A", "primary_goal": "Grow"}
    brief2 = {"brand_name": "Brand B", "primary_goal": "Grow"}

    fp1, payload1 = make_fingerprint(pack_key="quick_social_basic", brief=brief1, constraints=None)
    fp1b, _ = make_fingerprint(pack_key="quick_social_basic", brief=brief1, constraints=None)
    fp2, payload2 = make_fingerprint(pack_key="quick_social_basic", brief=brief2, constraints=None)

    assert fp1 == fp1b  # deterministic
    assert fp1 != fp2  # different brief => different fingerprint
    assert payload1["pack_key"] == "quick_social_basic"
    assert payload2["brief"]["brand_name"] == "Brand B"


def test_log_request_writes_jsonl(tmp_path, monkeypatch):
    # redirect log dir to tmp
    monkeypatch.setattr("backend.utils.request_fingerprint.LOG_DIR", tmp_path)
    monkeypatch.setattr(
        "backend.utils.request_fingerprint.REQUEST_LOG_PATH",
        tmp_path / "aicmo_requests.jsonl",
    )

    fp = "deadbeef"
    payload = {
        "pack_key": "quick_social_basic",
        "brief": {"brand_name": "Test"},
        "constraints": {},
    }
    log_request(
        fingerprint=fp,
        payload=payload,
        status="ok",
        duration_ms=123.4,
        error_detail=None,
    )

    log_file = tmp_path / "aicmo_requests.jsonl"
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    rec = json.loads(lines[0])
    assert rec["fingerprint"] == fp
    assert rec["status"] == "ok"
    assert rec["duration_ms"] == 123.4
    assert rec["pack_key"] == "quick_social_basic"
