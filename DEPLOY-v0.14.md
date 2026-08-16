# Deploy Lantern v0.14

Recommended repo: `lantern-app-v0.14`

Use the same Vercel variables:
- OPENAI_API_KEY
- OPENAI_LIGHT_MODEL = gpt-5-mini
- SUPABASE_URL
- SUPABASE_SECRET_KEY
- SUPABASE_PUBLISHABLE_KEY
- LANTERN_ADMIN_TOKEN

Optional:
- OPENAI_TTS_MODEL
- LANTERN_VOICE_FEMALE
- LANTERN_VOICE_MALE

No new database migration is required.

IMPORTANT AUTH STEP:
Before account testing, follow `SUPABASE-AUTH-v0.14.md` and update BOTH:
- Confirm signup email template
- Magic Link email template

Use `{{ .Token }}`, not `{{ .ConfirmationURL }}`.
Also change Supabase Site URL away from localhost.

Acceptance test:
1. /health
2. /health?deep=1
3. Prepare Me story: plain/relatable, not poetic.
4. Generation sound starts immediately.
5. Listen: no art-direction captions.
6. Sound does not audibly loop.
7. Narration completion automatically opens post-story reflection.
8. Carrying pathways show only Close for now.
9. Other pathways show only Return to Life.
10. Read opening is not duplicated.
11. Read + Soundscape stays continuous.
12. Just Stay With Me starts soft score automatically and has one Close for now CTA.
13. Create account receives a numeric verification code, not a link.
