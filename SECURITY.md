# Security

## Admin catalog refresh

`POST /admin/refresh` rebuilds `tv_channels.json` from the public IPTV playlist.

- **Local / desktop:** If `ADAMSY_ADMIN_TOKEN` is unset, refresh stays open so `tv_main.py` and the web UI keep working without extra setup.
- **Fly, Vercel, or Docker:** A token is required. Set `ADAMSY_ADMIN_TOKEN` (Fly secrets, Vercel project env, and GitHub Actions). Docker images and Fly set `ADAMSY_REQUIRE_ADMIN_TOKEN=1`; Vercel is detected via `VERCEL`. If a token is required but missing, refresh returns HTTP 503 instead of running open.
- Send the token as the `x-admin-token` header (the web UI stores it locally).

If `ADAMSY_ADMIN_TOKEN` was shared, generate a new token and update Vercel, Fly, and GitHub secrets.

## CORS

The channel API is public JSON and does not use cookies (`allow_credentials=False`). The default `Access-Control-Allow-Origin: *` lets the same-origin web UI, the desktop webview, and third-party IPTV clients call it from any host. To restrict browser origins on a deploy, set `ADAMSY_CORS_ORIGINS` to a comma-separated list (for example `https://your-app.fly.dev`).

No Google API keys are required for basic CI; rotate any third-party tokens you use for channel refresh or deployment.
