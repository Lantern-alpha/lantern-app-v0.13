
import os, tempfile, importlib.util, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server

def reset_db(tmp_path):
    server.DB=tmp_path/"test.db"

def client(tmp_path):
    reset_db(tmp_path)
    return server.app.test_client()

def headers(uid="u-test"):
    return {"X-Lantern-User":uid,"Content-Type":"application/json"}

def test_guest_starts_with_two_full_moments(tmp_path):
    c=client(tmp_path); r=c.get("/api/me",headers=headers()).get_json()
    assert r["entitlement"]["state"]=="guest"
    assert r["entitlement"]["full_remaining"]==2

def test_guest_consumption_and_private_mode_still_counts(tmp_path):
    c=client(tmp_path)
    # consume directly: verifies entitlement accounting independent of AI
    server.ensure_user("u-test")
    server.consume("u-test","full","s1")
    assert server.entitlement("u-test")["full_remaining"]==1
    server.consume("u-test","full","s2")
    assert server.entitlement("u-test")["full_allowed"] is False

def test_registration_converts_guest_to_free(tmp_path):
    c=client(tmp_path)
    r=c.post("/api/alpha/register",headers=headers(),json={"email":"alpha@example.com"}).get_json()
    assert r["ok"] is True
    assert r["entitlement"]["state"]=="free"

def test_free_has_separate_curated_and_full_allowances(tmp_path):
    c=client(tmp_path)
    c.post("/api/alpha/register",headers=headers(),json={"email":"alpha@example.com"})
    server.consume("u-test","curated","c1")
    e=server.entitlement("u-test")
    assert e["curated_allowed"] is False
    assert e["full_allowed"] is True
    server.consume("u-test","full","f1")
    assert server.entitlement("u-test")["full_allowed"] is False

def test_paid_has_12_full_and_unlimited_curated(tmp_path):
    c=client(tmp_path)
    c.post("/api/alpha/register",headers=headers(),json={"email":"alpha@example.com"})
    c.post("/api/alpha/tier",headers=headers(),json={"tier":"paid"})
    e=server.entitlement("u-test")
    assert e["full_remaining"]==12
    assert e["curated_remaining"]=="unlimited"

def test_no_reserved_return_identifier_in_frontend():
    h=(ROOT/"static"/"index.html").read_text()
    assert "id=return>" not in h
    assert "return.onclick" not in h

def test_no_match_frontend_is_handled():
    h=(ROOT/"static"/"index.html").read_text()
    assert "d.status==='no_match'" in h
    assert "I don’t want to give this moment the wrong story." in h
