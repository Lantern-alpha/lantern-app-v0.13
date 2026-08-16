from pathlib import Path
R=Path(__file__).resolve().parents[1]
H=(R/'public'/'index.html').read_text();S=(R/'server.py').read_text()
def test_contracts():
 assert '--bg:#000000;' in H
 assert 'startAlphaAmbience' in H
 assert 'stopNarrationBtn' in H
 assert 'recentFingerprints' in H and 'recent_fingerprints' in S
 assert 'LANTERN_ADMIN_TOKEN' in S and '/api/admin/verify' in S
 assert 'Could not record feedback' in H
