from pathlib import Path
R=Path(__file__).resolve().parents[1]
S=(R/"server.py").read_text()
H=(R/"public"/"index.html").read_text()

def test_story_contract():
    assert "CURIOSITY -> IMMERSION -> TENSION -> MOVEMENT -> RELEASE -> AFTERGLOW" in S
    assert '"hook_score":1-10' in S
    assert "Story Distance" in S or "STORY DISTANCE" in S

def test_tts_is_slower():
    assert '"speed":0.88' in S
    assert "Let punctuation breathe" in S

def test_continuous_soundscape():
    assert "ambienceDecks" in H
    assert "cross=3500" in H
    assert "fadeAudio" in H

def test_listen_keeps_sound():
    assert "if(withAmbience)startAmbience(.085)" in H

def test_surprise_me_click_no_forced_render():
    block=H[H.index("document.querySelectorAll('[data-p]')"):H.index("momentEl.oninput")]
    assert "render()" not in block

def test_quiet_space():
    assert "const quietLines=" in H
    assert "Nothing needs your answer right now." in H
    assert "No story. No lesson. No need to explain anything." not in H
    assert "3350" in H and "650" in H

def test_new_sound_beds_exist():
    assert (R/"public"/"ambience"/"soft_music.wav").exists()
    assert (R/"public"/"ambience"/"rain_music.wav").exists()
