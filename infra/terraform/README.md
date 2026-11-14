# infra/terraform (Cloudflare as code)

OpenTofu with the Cloudflare provider v5. It runs only in the `tofu` GitHub workflow: a pull request plans, a merge to `main` applies. The repo is public, so nothing account-specific is in the `.tf` files; it all arrives as `TF_VAR_*` from GitHub secrets and variables.

| File | What |
|------|------|
| `access.tf` | Identity providers (Google, one-time PIN), the `admins` and `users` groups, reusable policies, one Access app per gated host, the bypass apps, the wildcard default-deny |
| `tunnel.tf` | Routes of the existing tunnel, and one CNAME per hostname served from the cluster. The tunnel itself and its token are not managed |
| `r2.tf` | The `static` bucket (imported) and its lifecycle rules |
| `versions.tf` | Provider pin, R2 state backend, state encryption |

## How access is decided

- Login happens at Cloudflare's edge, before a request enters the tunnel. oauth2-proxy is gone and nothing in the cluster keeps a user list; the `admins` and `users` groups here are the only ones.
- `gated_hosts`: one Access app per hostname, admitting the listed groups. Frigate and Homebridge have their own logins switched off, so anyone admitted to them is an admin there; ArgoCD keeps its Google login behind Access because it maps emails to roles.
- `public_hosts`: a bypass app per hostname. On `play.yan.fi` the host is public and only `/view` and `/scheduled` are gated by a more specific app (`play_private`); py-play verifies that app's token itself.
- Fail closed (on by default): a `*.yan.fi` app makes every proxied hostname without its own app admins-only, and cloudflared rejects requests on the catch-all route that carry no valid Access token. A deleted or broken app therefore blocks a service instead of exposing it. Hosts that must work without a token (`yan.fi`, `play`, `h`) have their own route above the catch-all.
- Home Assistant (`h.yan.fi`) is deliberately public at the edge with its native login: Access breaks the companion app. Notes for a later round are in `infra/README.md`.

## One-time bootstrap (by hand)

1. R2: create the bucket `yan-fi-iac-state` and an R2 API token with Object Read & Write on that bucket only.
2. Cloudflare API token with: Account → Access: Apps and Policies (Edit), Access: Organizations, Identity Providers, and Groups (Edit), Cloudflare Tunnel (Edit), Workers R2 Storage (Edit); Zone `yan.fi` → DNS (Edit).
3. Google OAuth client: add the redirect URI `https://<team>.cloudflareaccess.com/cdn-cgi/access/callback`.
4. GitHub repository secrets and variables:

| Kind | Name | Value |
|------|------|-------|
| secret | `CLOUDFLARE_API_TOKEN` | Token from step 2 |
| secret | `TOFU_STATE_ACCESS_KEY_ID`, `TOFU_STATE_SECRET_ACCESS_KEY` | R2 token from step 1 |
| secret | `TOFU_STATE_PASSPHRASE` | At least 16 characters. Keep a copy: without it the state is unreadable |
| secret | `ACCESS_ADMIN_EMAILS`, `ACCESS_USER_EMAILS` | JSON lists, e.g. `["a@x.fi"]`; `[]` for none |
| secret | `ACCESS_GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| variable | `ACCESS_GOOGLE_CLIENT_ID` | Google OAuth client ID |
| variable | `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_ZONE_ID`, `CLOUDFLARE_TEAM_NAME`, `CLOUDFLARE_TUNNEL_ID` | From the dashboard |
| variable | `ACCESS_FAIL_CLOSED` | Optional; fail-closed is on unless this is `false`. Set `false` only as an emergency switch, or on a fresh setup until every public host has been checked |

## Working with it

- Changing who is in a group: edit the `ACCESS_*_EMAILS` secret, then run the workflow by hand on `main`.
- A new gated hostname: add it to `gated_hosts` in `access.tf`; its CNAME is created with it. A new public one: `public_hosts`, plus a route and a `tunnel_hosts` entry in `tunnel.tf` if it is served from the cluster.
- Read the plan before merging: merge applies at once.
- Everything here is tracked in the state; the `import` blocks used to adopt the hand-made tunnel routes, DNS records, bucket and One-time PIN were removed afterwards. To adopt another existing resource, add a temporary `import` block (ID formats are in the provider docs), merge, then delete it. If the state is ever lost, the same applies to all of them.
- A token for the state bucket needs Object Read & Write (the lock is a write); a read-only one fails with 403 on `PutObject`.
- A proxied DNS record added by hand in the dashboard (not through the tunnel) is admins-only until it gets an entry in `public_hosts`.
- Routes and DNS records edited in the dashboard are overwritten by the next apply.
- In the devcontainer: `tofu fmt && tofu init -backend=false && tofu validate`. Commit `.terraform.lock.hcl`; after a provider bump, `tofu init -backend=false -upgrade` and `tofu providers lock -platform=linux_amd64 -platform=linux_arm64` so the lock covers the CI runner too.
- Outputs `access_team_domain` and `play_access_aud` go into `infra/credentials/play.env`.
