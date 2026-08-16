from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
H=(ROOT/'public'/'index.html').read_text()
S=(ROOT/'server.py').read_text()
SQL=(ROOT/'supabase-v0.11-migration.sql').read_text()

def test_real_auth_endpoints():
    assert '/api/auth/request-otp' in S
    assert '/api/auth/verify-otp' in S
    assert '/api/auth/refresh' in S
    assert 'SUPABASE_PUBLISHABLE_KEY' in S

def test_account_fields():
    assert 'regFirst' in H and 'regEmail' in H and 'regCountry' in H
    assert 'first_name' in SQL and 'country' in SQL

def test_old_email_only_registration_disabled():
    assert 'Legacy Alpha registration is disabled' in S

def test_real_tts():
    assert '/v1/audio/speech' in S
    assert 'gpt-4o-mini-tts' in S
    assert 'SpeechSynthesisUtterance' not in H

def test_two_voices_and_lantern_choice():
    assert 'Female voice' in H and 'Male voice' in H
    assert "Lantern's Choice" in H
    assert 'VOICE_FEMALE' in S and 'VOICE_MALE' in S

def test_listen_plus_ambience():
    assert 'Story ambience' in H
    assert 'startAmbience' in H

def test_read_plus_ambience():
    assert 'Read + Ambience' in H
    assert '/ambience/' in H

def test_session_persistence():
    assert 'lantern_refresh_token' in H
    assert 'refreshSession' in H
