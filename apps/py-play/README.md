Authentication based header (X-Forwarded-Email) verification from OAUTH proxy.

To test locally, using curl or environment variables:
- curl -H 'X-Forwarded-Email: yan@yan.fi' http://localhost:7999/view
- ALLOW_LOCAL_AUTH=true LOCAL_AUTH_EMAIL=t@t.dev ALLOWED_EMAILS='["t@t.dev"]' uv run play
