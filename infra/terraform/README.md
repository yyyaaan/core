# infra/terraform (Cloudflare as code)

OpenTofu with the Cloudflare provider v5. It runs only in the `tofu` GitHub workflow: a pull request plans, a merge to `main` applies. The repo is public, so nothing account-specific is in the `.tf` files; it all arrives as `TF_VAR_*` from GitHub secrets and variables.

| File | What |
|------|------|
| `access.tf` | Identity providers (Google, one-time PIN), the `admins` and `users` groups, reusable policies, one Access app per gated host, the bypass apps, the wildcard default-deny |
| `tunnel.tf` | Routes of the existing tunnel, and one CNAME per hostname served from the cluster. The tunnel itself and its token are not managed |
| `r2.tf` | The `static` bucket (imported) and its lifecycle rules |
| `versions.tf` | Provider pin, R2 state backend, state encryption |

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
| variable | `CLOUDFLARE_DNS_RECORD_IDS` | JSON map of hostname to the ID of its existing CNAME (`GET /zones/<zone>/dns_records`), for import: `yan.fi`, `play`, `h`, `cd`, `frigate`, `homebridge` (full names, e.g. `cd.yan.fi`) |
| variable | `CLOUDFLARE_ACCESS_IDP_IDS` | Only if a login method already exists: JSON map with the keys `google` and/or `otp` and their IDs (`GET /accounts/<account>/access/identity_providers`), for import |
| variable | `ACCESS_FAIL_CLOSED` | Unset at first; `true` for the last rollout step |

## Working with it

- Changing who is in a group: edit the `ACCESS_*_EMAILS` secret, then run the workflow by hand on `main`.
- A new gated hostname: add it to `gated_hosts` in `access.tf`; its CNAME is created with it. A new public one: `public_hosts`, plus a route and a `tunnel_hosts` entry in `tunnel.tf` if it is served from the cluster.
- The first plan must show the imports (tunnel config, six DNS records, the bucket, any existing login method) and no change to the DNS records. If a record differs from the code, fix the code, not the record.
- `ACCESS_FAIL_CLOSED=true` adds the `*.yan.fi` admins-only app and also gates every other proxied record in the zone that has no app of its own, tunnel or not, and makes cloudflared reject requests on the catch-all route that carry no valid Access token. Hosts that must be reachable without a token need their own route above the catch-all.
- In the devcontainer: `tofu fmt && tofu init -backend=false && tofu validate`. Commit `.terraform.lock.hcl`; after a provider bump, `tofu init -backend=false -upgrade` and `tofu providers lock -platform=linux_amd64 -platform=linux_arm64` so the lock covers the CI runner too.
- Outputs `access_team_domain` and `play_access_aud` go into `infra/credentials/play.env`.
