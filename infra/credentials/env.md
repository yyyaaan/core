# Environment variables are directly delivered to Kubernetes

This folder shall put `theme.env` by the nature of secrets; __Taskfile.yaml `infra:secrets:` task loads them__.

```
# from consolidated file
for f in *.env; do echo "### File: $f ###"; cat "$f"; echo -e "\n"; done > .env.combined

# concatenate envs
awk '/^### File: / { out=$3; next } { if (out) print > out }' .env.combined
```
## Files

One file per secret, as listed in `Taskfile.yaml` `secrets.ITEMS`. `play.env` (secret `play-credentials`, namespace `web`):

```
INTERNAL_TOKEN=<random, e.g. openssl rand -hex 32>
ACCESS_TEAM_DOMAIN=https://<team>.cloudflareaccess.com
ACCESS_AUD=<application ID>
```

`INTERNAL_TOKEN` is the mailing CronJob's bearer token; the other two are the `tofu` outputs `access_team_domain` and `play_access_aud`. No trailing comments in the file: they would become part of the value.

On a cluster without Cloudflare Access (test), use `ALLOW_LOCAL_AUTH=true` and `LOCAL_AUTH_EMAIL=...` instead of the two `ACCESS_*` values.
