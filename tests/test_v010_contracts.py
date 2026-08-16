from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
H=(ROOT/"public"/"index.html").read_text()

def test_moment_is_not_cleared_by_pathway():
    assert "S.moment='';render()" not in H.split("document.querySelectorAll('[data-p]')",1)[1].split("privateEl.onchange",1)[0]
    assert "S.moment=momentEl.value" in H

def test_rotating_microcopy():
    assert "findingCopyTimer" in H
    assert "4300" in H
    assert "glow-in" in H and "glow-out" in H

def test_visual_reading():
    assert "storyReadingMarkup" in H
    assert "story-beat" in H
    assert "story-atmosphere" in H
    assert "story-emphasis" in H

def test_close_for_now_restored():
    assert "Close for now" in H
    assert "function closed()" in H

def test_exit_then_survey():
    assert "chooseExit" in H
    assert "resonancePanel" in H
    assert "completeStoryExit" in H

def test_true_black():
    assert '--bg:#000000' in H
    assert 'theme-color" content="#000000"' in H
