# Deploy v0.12

Use a new private GitHub repo `lantern-app-v0.12` so v0.11.1 remains a rollback.

Environment variables are the same as v0.11.1:
- OPENAI_API_KEY
- OPENAI_LIGHT_MODEL = gpt-5-mini
- SUPABASE_URL
- SUPABASE_SECRET_KEY
- SUPABASE_PUBLISHABLE_KEY
- LANTERN_ADMIN_TOKEN

Optional:
- OPENAI_TTS_MODEL = gpt-4o-mini-tts
- LANTERN_VOICE_FEMALE
- LANTERN_VOICE_MALE

No new database migration is required for the v0.12 experience changes.

After deploy:
1. `/health`
2. `/health?deep=1`
3. Enter Lantern
4. Test Prepare Me with a real upcoming moment
5. Listen with soundscape
6. Read + Soundscape
7. Surprise Me
8. Just Stay With Me
