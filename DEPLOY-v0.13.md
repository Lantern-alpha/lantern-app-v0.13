# Deploy v0.13
Create private repo: lantern-app-v0.13

Use the same Vercel environment variables as v0.12:
OPENAI_API_KEY
OPENAI_LIGHT_MODEL=gpt-5-mini
SUPABASE_URL
SUPABASE_SECRET_KEY
SUPABASE_PUBLISHABLE_KEY
LANTERN_ADMIN_TOKEN

No new Supabase migration is required.

Gold test:
1. Enter a real Prepare Me moment.
2. Generate story.
3. Choose Listen.
4. Press Begin.
5. Confirm visual/microcopy starts while the two-segment narration buffer prepares.
6. Confirm narrator enters only after buffer is ready.
7. Confirm score remains under narration.
8. Confirm score stops shortly after story completion.
9. Test Read for editorial pacing.
10. Test Read + Soundscape.
