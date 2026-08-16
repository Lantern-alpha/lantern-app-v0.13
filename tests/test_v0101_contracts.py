from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
H=(ROOT/"public"/"index.html").read_text()
S=(ROOT/"server.py").read_text()

def test_background_matches_logo():
    assert "--bg:#070707;" in H
    assert 'theme-color" content="#070707"' in H

def test_health_validates_config():
    assert "def config_status()" in S
    assert 'request.args.get("deep")=="1"' in S

def test_api_me_safe_error():
    assert '"Lantern could not load your account state."' in S
    assert "app.logger.exception" in S

def test_enter_lantern_is_explicit_and_error_safe():
    assert "enterLantern" in H
    assert "Opening Lantern" in H
    assert "startError" in H

def test_implicit_ids_removed_for_core_controls():
    assert "b.onclick" not in H
    assert "done.onclick" not in H

def test_api_prefers_safe_detail():
    assert "data.detail||data.error" in H
