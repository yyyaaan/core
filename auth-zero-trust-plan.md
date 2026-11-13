# Auth plan: Cloudflare Access for the home cluster

Date: 2026-11-13. Scope: the `core` monorepo only (k3s on the Pi, `yan.fi`). Status: implemented on the branch `zero-trust-to-replace-oauth2-proxy` and checked against the code; nothing merged or applied yet. `infra/terraform/` has not been run through `tofu` (not available in the devcontainer), so the first CI plan is its first real check.

## Summary

- Login for the cluster's services moves to Cloudflare Access (Zero Trust) at the edge; oauth2-proxy is retired.
- The user list lives only in Zero Trust, as two groups: `admins` and `users`. Apps trust the Access token instead of keeping their own lists. The repo is public, so the members come from GitHub secrets, not from the code.
- Frigate stays on `frigate.yan.fi`; its own login is turned off and everyone Access admits is a Frigate admin.
- ArgoCD keeps its Google OIDC login, with Access in front. Headlamp is deleted.
- The `staging.yan.fi` alias is removed. The `omop.fi` domain has been given up, so every reference to it is removed; the test environment itself stays, without a domain for now.
- All Cloudflare config is managed as code in `infra/terraform/`, run with OpenTofu on GitHub Actions.
- Home Assistant is out of scope and stays exactly as it is today. The research on it is kept at the end for later.

## Current state

- **Path:** Cloudflare tunnel (one wildcard route, configured by hand in the dashboard) → Traefik → service. Cloudflare terminates TLS.
- **oauth2-proxy guards very little:** only py-play's `/view` and `/scheduled`, plus Stirling-PDF (0 replicas in prod). Every py-web route is in the skip list.
- **oauth2-proxy admits any Google account** (`emailDomain: "*"`). py-play's own allowlist is the real gate; Stirling-PDF has none.
- **Frigate, Home Assistant and Homebridge are on the internet with only their own login pages.** Their ingresses carry no auth middleware.
- **Anything in the cluster can impersonate a user to py-play** by sending `X-Auth-Request-Email`. The mailing CronJob does exactly this.
- **Every new ingress is public by default**, because the tunnel route is a wildcard.
- **ArgoCD and Headlamp** use Google OIDC directly. The k3s API server trusts Google tokens with `hd=yan.fi`.

## Why Cloudflare Access

- Cloudflare already terminates TLS and carries all traffic, so this adds no new trust.
- Unauthenticated requests stop at the edge and never reach the Pi.
- It removes a pod, a secret and a namespace from the cluster.
- The free tier is listed as up to 50 users.
- Alternatives considered: a hardened oauth2-proxy keeps the origin exposed; a self-hosted IdP (Authelia, Authentik) also keeps the origin exposed and adds a stateful service for a handful of users; a private network (WARP, Tailscale) is strongest but needs a client on every device.

## Target design

### Identity and groups

- One Zero Trust team with Google as the identity provider and one-time PIN as fallback.
- Two Access groups defined in code: `admins` and `users`. These are the only user lists.
- MFA comes from the Google accounts (enforce 2-step verification or passkeys there).

### Per service

| Service | Who | Edge | In-app auth |
|---|---|---|---|
| `yan.fi` (py-web) | Everyone | Public; the apex is not covered by `*.yan.fi` | None |
| `play.yan.fi`, everything but the two paths below (`/`, `/docs`, `/openapi.json`, `/public/*`) | Everyone | Bypass app for the host | None |
| `play.yan.fi/view`, `/scheduled` | admins, users | Access app on the two paths; more specific than the host bypass | Validate the Access token; no email list |
| Frigate (`frigate.yan.fi`) | admins | Access | Off; everyone admitted is admin |
| Homebridge | admins | Access | Off (`auth: none`) |
| Stirling-PDF | admins, users | Access | None needed |
| ArgoCD (`cd.yan.fi`) | admins | Access | Keep Google OIDC and `policy.csv` RBAC |
| `assets.yan.fi` | Everyone | Bypass app; it serves the public site's images and the timelapse viewer embedded in Home Assistant | None |
| Home Assistant (`h.yan.fi`) | Unchanged | Bypass app, so the wildcard rule does not gate it | Unchanged |
| Any other `*.yan.fi` hostname | admins | Wildcard default-deny | n/a |

### py-play

- `auth.py` validates the `Cf-Access-Jwt-Assertion` header: RS256 signature against the team's published keys (matched by `kid`), issuer, and the application ID (`aud`).
- Drop `allowed_emails`. It only existed because oauth2-proxy admits anyone; with Access, the policy is the list.
- The edge is open by default on this host and gated per path, the reverse of the other hosts. That keeps `/`, `/docs` and `/openapi.json` public as today. A new private route needs `Depends(require_user)` and its path in the Access app; with only the first it returns 401, so a forgotten path fails closed.
- Access tokens carry no group names. If admin-only routes appear, give them a second path-scoped Access app (its own application ID) and check which ID admitted the request.
- Replace the CronJob's spoofed `X-Auth-Request-Email` header with `Authorization: Bearer $INTERNAL_TOKEN`.
- Settings `ACCESS_TEAM_DOMAIN`, `ACCESS_AUD` and `INTERNAL_TOKEN` come from a new `play-credentials` secret (`infra/credentials/play.env`, seeded with `task infra:secrets` like every other secret). The application ID exists only after the first apply, and it differs per environment, so it is not in the chart values. Any of them unset disables that path.
- Remove the oauth middleware annotation from the ingress. This must not reach the cluster before the new image does: the old `auth.py` trusts `X-Auth-Request-Email`, which is only safe while the middleware overwrites it. A sync applies chart and image tag together, so syncing after the tag-bump PR is merged is enough.

### py-web

- Remove `staging.yan.fi` and `omop.fi` from `ingress.additionalHosts`; the site is served on `yan.fi` only.
- Remove the oauth middleware annotation. Every route is already public, and the middleware disappears with oauth2-proxy.
- Fix the link list on the front page: the Headlamp link goes, and the ArgoCD link pointed at `argocd.yan.fi` instead of `cd.yan.fi`.

### Frigate

- One hostname, `frigate.yan.fi`, as today. Access admits `admins`.
- Set `auth.enabled: false` and `proxy.default_role: admin`. No header mapping and no second hostname.
- Anyone added to the Frigate policy is a Frigate admin, so add people deliberately.
- Port 5000 stays internal and unauthenticated for Home Assistant, py-play and the poller, as today.
- Config lives on the Pi's hostPath, so the Frigate edit is a manual step.

### ArgoCD

- No in-cluster change. Access goes in front for `admins`.
- Its Google login decides permissions by email, so it stays.

### Headlamp (deleted)

- Remove the `headlamp` Application and `bootstrap/values/headlamp.yaml`, `dash.yan.fi`, the `headlamp` namespace and its `oidc-secret` entry in the Taskfile, the `headlamp:login` task, `rbac-oidc-admin.yaml`, and the Headlamp callback on the Google OAuth client.
- Update the mentions in the READMEs, `infra/AGENTS.md` and the `infra-upgrade` skill.
- Manual step on the Pi: remove the `oidc-*` API-server flags from `/etc/rancher/k3s/config.yaml` and restart k3s. `oidc.env` stays, because ArgoCD still uses it.
- ArgoCD syncs here are manual and do not prune by themselves: delete the `headlamp` Application in ArgoCD (with its resources), sync `cert-cloudflare-etc` with prune for the ClusterRoleBinding, and delete the `headlamp` namespace on the host.
- Replacement when a cluster UI is wanted: the ArgoCD UI, or Headlamp desktop or k9s with the kubeconfig.

### Failing closed

- A `*.yan.fi` Access app that allows only `admins` makes any new hostname private by default. More specific apps override it.
- Split the tunnel's single wildcard route: explicit routes for `yan.fi`, `play.yan.fi` (it has public paths, so cloudflared cannot demand a token; the app checks it) and Home Assistant, then a catch-all with "Protect with Access" on, so cloudflared rejects any request without a valid Access token.
- Both parts sit behind one switch, the `fail_closed` variable (GitHub variable `ACCESS_FAIL_CLOSED`), off until the last rollout step.
- The catch-all is what makes it safe to turn off the Frigate and Homebridge logins: a deleted or misconfigured Access app then blocks access instead of exposing the service.

## Infrastructure as code

- **Tool:** OpenTofu as the runtime, with ordinary `.tf` files and the Cloudflare provider v5, version pinned. The code stays Terraform-compatible as long as no OpenTofu-only features are used.
- **Layout:** `infra/terraform/`.
- **Where it runs:** GitHub Actions only. A pull request runs `tofu fmt -check`, `tofu validate` and `tofu plan`, with a PR comment listing which resources change (not their attributes: the repo and its Actions logs are public, so every account-specific input is a GitHub secret or variable and the sensitive ones are marked as such). Merge to `main` runs `tofu apply`.
- **State:** an R2 bucket, encrypted with OpenTofu's state encryption. Note that encrypted state can no longer be read by Terraform itself.
- **Secrets:** GitHub Actions secrets hold the Cloudflare API token, the R2 credentials, the state passphrase, the Google client secret and the members of the two groups. Nothing goes in the repo. The full list is in `infra/terraform/README.md`.
- **One-time manual bootstrap:** create the R2 state bucket, the scoped API token and the GitHub secrets and variables, and add Cloudflare's callback URL to the Google OAuth client.
- **Managed resources:** identity provider, the two groups, Access apps and policies, tunnel routes, DNS records for tunnel hostnames, and the existing R2 bucket with its lifecycle rules.
- **Import, not recreate:** the tunnel's route configuration, the wildcard and apex CNAMEs and the `static` bucket, using `import` blocks so the import also runs in CI. The tunnel object itself is deliberately not managed: only its ID is passed in, so no plan can ever replace the tunnel or its token.
- **Token scopes:** Access apps, policies and identity providers; Cloudflare Tunnel; zone DNS; R2.

### Existing R2 resources

- **Bucket (`static`, behind `assets.yan.fi`):** import is supported, with the ID `<account_id>/<bucket_name>/<jurisdiction>`. Objects are never touched.
- **Lifecycle rules (timelapse retention):** the resource cannot be imported. Declare the same rules in code and let the first apply write them; this moves retention out of the dashboard.
- **Custom domain (`assets.yan.fi`):** the resource cannot be imported. Leave it in the dashboard for now; taking it over would mean removing and recreating it, with a short outage.
- **S3 access keys used by the poller:** leave as they are; existing secrets cannot be read back.
- **State bucket:** a separate bucket created by hand, not managed by the configuration it stores.

### Test environment (kept, domain removed)

- The test setup stays: both `values-test.yaml` files, `infra/gitops-config/test-domain/`, the `ENV=test` branches in the Taskfile and the tag-bump line in `build-play.yml`.
- Only the `omop.fi` references go: the `domain` and `pdf.omop.fi` host in `infra/helm-chart/values-test.yaml`, and `play.omop.fi` in `apps/py-play/helm-chart/values-test.yaml`. They become `example.invalid` until a new test domain is chosen.
- Fixed on the way: `homebridge.enabled: false` and its two siblings in the test values were dotted keys that Helm ignores, so the test render still produced ingresses for `h.yan.fi` and `homebridge.yan.fi`.
- The oauth2-proxy block in the test values is removed with oauth2-proxy itself.
- Access is not set up for the test environment. Until a new test domain is added to the Terraform config, py-play's protected routes there rely on the local-auth settings, set in that cluster's `play.env`.

## Rollout

Everything is on one branch. Merging it changes Cloudflare at once (the `tofu` workflow applies), while the cluster changes wait for manual ArgoCD syncs, and the fail-closed part waits for a switch. The order below keeps every state working.

1. **Bootstrap, before the PR.** The steps in `infra/terraform/README.md`. Also create `infra/credentials/play.env` with `INTERNAL_TOKEN` and run `task infra:secrets`.
2. **Open the PR and read the plan.** Four imports, no change to the DNS records, and the tunnel config changing from one wildcard route to the explicit routes with the same origin. Inventory the proxied DNS records so nothing is gated by surprise.
3. **Merge.** Access is now in front of Frigate, Homebridge, ArgoCD, Stirling-PDF and py-play's two private paths, with every in-app login still on (a temporary double login, oauth2-proxy included). Test precedence on `play.yan.fi/public/spot`, `play.yan.fi/view` and `h.yan.fi`.
4. **py-play.** Put the two outputs into `play.env`, run `task infra:secrets`, merge the tag-bump PRs, then sync `app-play`. Check `/view` in a browser and trigger the CronJob once.
5. **Remove oauth2-proxy and Headlamp from the cluster.** Sync `app-web` first: if `core-infra` loses the middleware while the site's ingress still references it, Traefik drops the route and `yan.fi` goes down. Then sync `core-infra` with prune, delete the `headlamp` Application, sync `cert-cloudflare-etc` with prune. On the host: delete the `auth` and `headlamp` namespaces and remove the `oidc-*` flags from k3s. In Google: remove the `auth.yan.fi` and `dash.yan.fi` redirect URIs.
6. **Fail closed, then drop in-app logins.** Set the GitHub variable `ACCESS_FAIL_CLOSED=true` and run the `tofu` workflow on `main`. Check Home Assistant (app included), `assets.yan.fi` and an unknown hostname. Only then turn off the Frigate and Homebridge logins (manual edits on the Pi).

Rolling back: steps 3 and 6 by reverting the Terraform change or the variable; steps 4 and 5 by reverting the merge and syncing.

## To verify during implementation

- Frigate 0.18: that `auth.enabled: false` with `proxy.default_role: admin` behaves as documented on port 8971.
- The exact Terraform field for "Protect with Access" on a remotely managed tunnel.
- Precedence between the wildcard Access app and the Bypass apps, tested on `play.yan.fi/public/*` and `h.yan.fi`.
- That the wildcard Access app applies to the R2 custom domain `assets.yan.fi`, and that its Bypass app keeps it public.
- That applying the R2 lifecycle resource with rules identical to the dashboard's changes nothing in practice.
- That the Home Assistant app keeps working unchanged once the wildcard rule and the split routes are in place.
- R2 as a state backend, including locking behaviour.

## Home Assistant (out of scope, kept for reference)

Home Assistant is not part of this migration. It keeps its native login and stays reachable as today. The findings below are kept for a later round.

### Why Access breaks the companion app

The app is a WebView plus a native background client (location, sensors, notification callbacks, widgets, watch). Access needs an interactive browser login and a cookie, which the background client cannot do.

### Community evidence

| Approach | Reported outcome |
|---|---|
| Access on the app hostname | Fails. Login loops (2020–2023), or works at first setup and dies when the session expires (max one month); the fix was clearing app data. Background location fails; one user warned notifications fail silently. |
| Service-token headers in the app | Not possible. The Android PR was closed in June 2023 because the WebView cannot carry the headers; a maintainer pointed to mTLS instead. An iOS header PR was also rejected. |
| Access plus IP bypass, with a phone shortcut updating a Cloudflare list | Works for some (Jul 2024, Jan 2026), but fragile: shortcut API errors, IPv6 needing /64 truncation (Jun 2025), and carrier IPs are shared with strangers. |
| WAF-only: geo-block, ASN or user-agent skip rules, HA login with 2FA | Works and is the common fallback. It reduces noise but adds no real authentication. |
| mTLS client certificate (Cloudflare issues 100 per zone free, enforced by a WAF rule) | Android: several successes in 2024, some failures on certificate install or "unable to connect". iOS: support arrived in 2026.4 as experimental; success reports in May, June and September 2026, one WebSocket failure with an RSA-2048 key. One guide says background webhook calls do not present the certificate, so `/api/webhook/*` must be exempted. |
| WARP, Tailscale or WireGuard | Works reliably, but needs an always-on client on every family phone; one report of WARP dropping the connection. |
| Alexa via service token and Lambda wrapper | Worked for the author; two later users failed account linking (2025). |

### Recommendation for a later round

- **Hardening that does not touch the app:** MFA, `ip_ban_enabled` with a login-attempt threshold, `trusted_proxies` with `use_x_forwarded_for`, and Cloudflare WAF rules (geo-restriction, rate limit on `/auth/*`).
- **Real edge auth:** split the hostnames. Browsers use one hostname behind Access. The app uses a second hostname that requires a client certificate, with `/api/webhook/*` exempted only if background updates fail without it.
- **All family phones are iOS.** That is one platform to test, but the less mature one: iOS client-certificate support is from 2026.4 and was still experimental in the latest reports. Use an EC key, since the one reported WebSocket failure was with RSA-2048.
- **Pilot first:** one phone for two weeks. Check background location, actionable notifications, widgets, watch, behaviour after a reboot, and certificate renewal.
- **Avoid:** Access on the app hostname, and IP-bypass automation.

## Sources

- [Frigate authentication](https://docs.frigate.video/configuration/authentication/)
- [Cloudflare: validate the Access JWT](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/)
- [Cloudflare: application paths and wildcards](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/app-paths/)
- [Cloudflare: tunnel origin parameters](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/cloudflared-parameters/origin-parameters/)
- [Cloudflare blog: wildcard and multi-hostname Access apps](https://blog.cloudflare.com/access-wildcard-and-multi-hostname)
- [Cloudflare: configure mTLS](https://developers.cloudflare.com/api-shield/security/mtls/configure/)
- [Cloudflare: cf.tls_client_auth.cert_verified](https://developers.cloudflare.com/ruleset-engine/rules-language/fields/reference/cf.tls_client_auth.cert_verified)
- [Cloudflare changelog: Terraform provider v5.17](https://developers.cloudflare.com/changelog/post/2026-02-12-terraform-v5.17.0-provider/)
- [Cloudflare changelog: Terraform provider v5.19](https://developers.cloudflare.com/changelog/post/2026-04-24-terraform-v5.19.0-provider/)
- [Terraform provider v5.22.0 release](https://newreleases.io/project/github/cloudflare/terraform-provider-cloudflare/release/v5.22.0)
- [OpenTofu vs Terraform 2026 (encore.dev)](https://encore.dev/articles/opentofu-vs-terraform-2026)
- [OpenTofu vs Terraform in 2026: the fork finally diverged](https://jorijn.com/en/blog/opentofu-vs-terraform-2026-the-fork-finally-diverged/)
- [Homebridge UI config schema](https://www.github.com/homebridge/homebridge-config-ui-x/blob/latest/config.schema.json)
- [HA community: Cloudflare Access and the Android app](https://community.home-assistant.io/t/cloudflare-access-and-the-android-app/155372)
- [HA community: HOWTO secure Cloudflare Tunnels remote access](https://community.home-assistant.io/t/howto-secure-cloudflare-tunnels-remote-access/570837)
- [HA community: relatively seamless Cloudflare iOS companion setup](https://community.home-assistant.io/t/relatively-seamless-cloudflare-ios-companion-app-security-configuration/822645)
- [HA community: WTH add support for Cloudflare Zero Trust](https://community.home-assistant.io/t/wth-add-support-for-ios-and-android-for-cloudflare-zero-trust/467460)
- [HA community: Cloudflare ZeroTrust + companion apps](https://community.home-assistant.io/t/cloudflare-zerotrust-cloudflared-add-on-companion-apps-better-security/696183)
- [HA community: app, Alexa and browser secured with Cloudflare](https://community.home-assistant.io/t/home-assistant-app-alexa-and-brower-access-secured-with-cloudflare/676294)
- [HA community: secure communication channel for iOS app](https://community.home-assistant.io/t/secure-communication-channel-for-ios-app/785129?page=4)
- [HA community: secure remote access with Cloudflare Tunnel and mTLS](https://community.home-assistant.io/t/secure-remote-access-with-cloudflare-tunnel-and-mtls/1024873)
- [HA community: guide to secure remote mTLS access](https://community.home-assistant.io/t/guide-secure-remote-mtls-and-local-ha-access/1003197)
- [home-assistant/android PR 3593: custom headers](https://github.com/home-assistant/android/pull/3593)
- [home-assistant/iOS discussion 1722: custom request headers](https://www.github.com/home-assistant/iOS/discussions/1722)
