# Lantern v0.13.1 — Vercel Build Hotfix

This hotfix changes only Vercel deployment configuration.

Vercel's current Flask deployment supports root-level `server.py` through
zero-configuration Flask detection. The previous `vercel.json` incorrectly
declared `server.py` under `functions`, which caused:

`The pattern "server.py" defined in functions doesn't match any Serverless Functions inside the api directory.`

The corrected `vercel.json` contains only:

{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "flask"
}

No Supabase changes and no environment-variable changes are required.
