# Lantern v0.11 Verification

Build-time checks completed:
- PASS: Python server syntax compilation
- PASS: JavaScript syntax check with Node
- PASS: v0.11 static contract tests (8/8)
- PASS: real Supabase Auth endpoints present
- PASS: First name + Email + Country account UI
- PASS: legacy email-only registration disabled
- PASS: OpenAI TTS endpoint present; browser speech synthesis removed
- PASS: Female / Male / Lantern's Choice controls present
- PASS: Listen + ambience and Read + Ambience paths present
- PASS: persistent refresh-token session logic present

Deployment-time tests still required because they depend on your live Supabase/OpenAI/Vercel credentials:
- send and verify email OTP
- cross-device account continuity
- TTS voice audition
- ambience quality on phone/headphones
- end-to-end Guest/Free/Paid entitlements
