import os
import pytest
from frontend.services.auth import get_required_access_token, verify_token, load_env_vars

def test_load_env_vars(monkeypatch):
    monkeypatch.delenv("ACCESS_TOKEN", raising=False)
    load_env_vars()
    token = os.getenv("ACCESS_TOKEN")
    assert token == "1ac3111181d1806767d5f1bfd07b5142d48911d48b3c6b4d7bf5bd98930a35a0"

def test_verify_token_valid(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN", "test_secret_123")
    assert verify_token("test_secret_123") is True
    assert verify_token("  test_secret_123  ") is True

def test_verify_token_invalid(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN", "test_secret_123")
    assert verify_token("wrong_token") is False
    assert verify_token("") is False

def test_verify_token_no_token_required(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN", "")
    assert verify_token("anything") is True
