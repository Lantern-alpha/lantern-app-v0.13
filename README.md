# Lantern v0.14 — Relatable Story & Experience Correction

v0.14 corrects the main issues found in v0.13 testing.

## Story
- Plain, conversational, relatable storytelling.
- Rejects poetic/literary prose and decorative description.
- Story engine requires a person, goal, complication, events, turn and earned ending.
- Story Distance remains mandatory.
- Quality gate scores relatability, hook, forward motion, plain language and stay-to-end.

## Sound
- Removed WAV-loop playback from the active experience.
- Sound is generated continuously in-browser with Web Audio; there is no short audio file to restart.
- Every pathway has a different musical identity.
- Story sound_palette subtly changes pace/harmony/brightness.
- Score changes across the story arc and fades out at completion.
- Generation begins with pathway-specific sound immediately after Find My Story.

## Generation
- 10 varied microcopy lines per pathway.
- Sound starts while the story is being generated.
- Microcopy continues only as long as needed.

## Listen
- No internal visual-description text is shown.
- Symbolic visual beats change during the story without displaying art prompts.
- Narration automatically transitions to the post-story screen after the ending.
- No Finish Story button.

## Read / Read + Soundscape
- Opening hook is not duplicated.
- Visual breaks contain no explanatory placeholder captions.
- Read + Soundscape uses the same continuous score engine.

## Ending
One CTA only:
- Encourage Me / Comfort Me / Calm Me → `Close for now`
- Prepare Me / Inspire Me / Teach Me / Connect Me / Surprise Me → `Return to Life`

Flow remains:
Story → Private Reflection → one exit CTA → resonance survey.

## Just Stay With Me
- Soft continuous generative score starts automatically.
- Microcopy changes approximately every 4 seconds.
- One CTA only: Close for now.

## Auth
See `SUPABASE-AUTH-v0.14.md`. New accounts must receive an OTP code, not a confirmation link.
