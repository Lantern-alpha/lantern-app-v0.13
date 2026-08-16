# Supabase Auth setup for Lantern v0.14

Lantern uses an email one-time code. The user should NOT receive a confirmation link.

In Supabase:
1. Authentication → Email Templates.
2. Open **Confirm signup**.
3. Subject: `Your Lantern verification code`
4. Replace the body with the contents of `SUPABASE-CONFIRM-SIGNUP-OTP-TEMPLATE.html`.
   The important variable is `{{ .Token }}`. Do NOT use `{{ .ConfirmationURL }}`.
5. Open **Magic Link** and use `SUPABASE-MAGIC-LINK-OTP-TEMPLATE.html` as well, so returning-user OTP emails are also code-based.
6. Authentication → URL Configuration:
   - Set **Site URL** to the deployed Lantern Vercel URL, not `http://localhost:3000`.
   - Add the deployed Lantern URL to Redirect URLs.
7. Authentication → Providers → Email:
   - Email provider enabled.
   - OTP length can remain 8 digits.
   - OTP expiry can remain 3600 seconds for Alpha.

Lantern's backend calls Supabase `/auth/v1/otp` and verifies the code with `/auth/v1/verify`.
No password is required.
