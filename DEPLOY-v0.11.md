# Lantern v0.11 — Deployment Guide

## 1. Create a new private GitHub repo
Recommended name: `lantern-app-v0.11`. Keep v0.10.1 untouched as fallback. Upload the contents of this folder. Do not upload real secrets.

## 2. Run the Supabase v0.11 database migration
Supabase -> SQL Editor -> New query. Run `supabase-v0.11-migration.sql`. It only adds `first_name` and `country` to the existing Lantern users table.

## 3. Configure Supabase email OTP
Supabase -> Authentication -> Email Templates -> Magic Link / OTP template. Configure the email so it shows the one-time code using `{{ .Token }}` rather than only a confirmation link. A minimal template is:

Subject: `Your Lantern verification code`

```html
<h2>Your Lantern verification code</h2>
<p style="font-size:28px;letter-spacing:4px"><strong>{{ .Token }}</strong></p>
<p>Use this code to continue to Lantern. If you did not request it, you can ignore this email.</p>
```

## 4. Get the Supabase publishable key
Supabase -> Settings -> API Keys. Copy the `sb_publishable_...` key. This is different from the server Secret key.

## 5. Import the new GitHub repo into Vercel
Application preset: Flask. Root: `./`.

## 6. Add Vercel environment variables
Required:
- `OPENAI_API_KEY`
- `OPENAI_LIGHT_MODEL` = `gpt-5-mini`
- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- `SUPABASE_PUBLISHABLE_KEY` = your `sb_publishable_...` key
- `LANTERN_ADMIN_TOKEN`

Optional voice overrides:
- `OPENAI_TTS_MODEL` = `gpt-4o-mini-tts`
- `LANTERN_VOICE_FEMALE` = `marin`
- `LANTERN_VOICE_MALE` = `cedar`

## 7. Deploy
After Ready, test:
- `/health`
- `/health?deep=1`
- `/api/me`

`/health` should show `supabase_auth_configured: true`.

## 8. Test real account creation
Guest -> Create account -> First name + Email + Country -> Continue -> receive email code -> Verify & Continue.

Then confirm Account shows the correct first name, email, country. Sign out and sign back in using only email + verification code.

## 9. Test cross-device
Save a story on Device A. Sign in using the same verified email on Device B. Confirm Saved/Recent/preferences are tied to the same account.

## 10. Test production audio candidate
Open a story -> Listen. Test Lantern's Choice, Female, Male, Stop, ambience on/off. Then test Read and Read + Ambience.

Admin -> Voice Audition lets you hear both mapped candidates using the same sentence. Do this before inviting the 25-person Closed Alpha.
