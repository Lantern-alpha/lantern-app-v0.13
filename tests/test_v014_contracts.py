from pathlib import Path
R=Path(__file__).resolve().parents[1]
S=(R/"server.py").read_text()
H=(R/"public"/"index.html").read_text()

def test_story_is_not_poetic_contract():
    assert "NOT literary. NOT poetic" in S
    assert "plain, conversational English" in S
    assert "Every 30-45 seconds" in S

def test_quality_gate_is_relatable():
    for word in ("relatable","forward_motion","plain_language","stay_to_end"):
        assert word in S

def test_no_wav_loop_in_active_sound_engine():
    active=H[H.index("let speechAudio="):H.index("function splitNarration")]
    assert "new Audio('/ambience/" not in active
    assert "AudioContext" in active
    assert "pathwaySoundProfile" in active

def test_generation_has_sound_and_varied_copy():
    assert "startAmbience(.045,S.path||'Surprise Me')" in H
    assert "Something is taking shape." in H
    assert "No destination this time." in H

def test_one_exit_cta_logic():
    assert "['Encourage Me','Comfort Me','Calm Me'].includes(pathway)?'Close for now':'Return to Life'" in H

def test_quiet_one_cta():
    q=H[H.index("function quiet(){"):H.index("function library()",H.index("function quiet(){"))]
    assert "Close for now" in q
    assert "Return to Life" not in q
    assert "startAmbience(.055,'Quiet')" in q

def test_visual_prompts_not_user_facing():
    assert 'data-caption="${escapeHtml(visualBeats' not in H
    assert "visualBeats[vi]?.description" not in H

def test_listen_auto_lands():
    assert "onComplete" in H
    assert "showPostStory()" in H

def test_otp_templates_exist():
    assert (R/"SUPABASE-CONFIRM-SIGNUP-OTP-TEMPLATE.html").exists()
    assert "{{ .Token }}" in (R/"SUPABASE-CONFIRM-SIGNUP-OTP-TEMPLATE.html").read_text()
