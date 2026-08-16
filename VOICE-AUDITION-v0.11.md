# v0.11 Voice Audition

Before external Closed Alpha, use Admin -> Voice Audition and compare the two mapped narrator candidates using the same Lantern sentence.

Current defaults are `marin` and `cedar`. OpenAI's current API documentation recommends Marin and Cedar for best quality, but does not officially label the built-in voices by gender. Lantern therefore treats the Female/Male mapping as a product configuration that must be auditioned.

Evaluate both for:
- warmth without sounding sentimental
- narrative credibility
- emotional restraint
- calm pauses
- clarity
- ability to carry Prepare, Comfort, Calm, Inspire and Teach without becoming theatrical
- how well the voice sits over subtle ambience

If the mapping is not right, change `LANTERN_VOICE_FEMALE` and/or `LANTERN_VOICE_MALE` in Vercel and redeploy.
