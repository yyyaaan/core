# infra/ (Helm, ArgoCD, k3s on Raspberry Pi)

Everything here deploys from `main` through ArgoCD (manual sync). Ingress: Cloudflare tunnel → Traefik → service. Cloudflare terminates TLS, so ingresses need no `tls:` block or cert-issuer annotations. Login happens at the edge with Cloudflare Access; there is no auth proxy or auth middleware in the cluster.

| Path | What |
|------|------|
| `helm-chart/` | Umbrella chart for platform services: HA, Frigate, MQTT, MariaDB, Homebridge, Restic CronJob. One subdir per service under `templates/` |
| `gitops-config/` | ArgoCD Applications: `bootstrap-cluster/` (external charts), `yan-fi/` (prod), `test-domain/` (test). Each env's app-of-apps tracks `bootstrap-cluster/` via `argocd-gitops-bootstrap`; ArgoCD itself is a pinned Helm install in `Taskfile.yaml` (`task infra:argocd`), outside ArgoCD |
| `bootstrap/` | Manifests and values applied by hand at cluster bootstrap (ArgoCD, tunnel, Traefik middleware) |
| `terraform/` | Cloudflare as code (OpenTofu, provider v5): Access identity providers, groups, policies and apps, tunnel routes, DNS, the `static` R2 bucket. Runs only in the `tofu` GitHub workflow; state is encrypted in R2. See `terraform/README.md` |
| `credentials/` | Gitignored `*.env` secret files. Only `env.md` is committed |

## Values

- `values.yaml` is prod (`yan.fi`, hostPaths under `/mnt/kingston/...`).
- `values-test.yaml` is an override layer for the test domain, not a full copy. When adding a value that differs per environment (host, domain, hostPath), add the test override too.
- Use `{{ .Values.domain }}` / values for hosts; no hardcoded domains in templates.

## Template conventions

- Gate every manifest of a service with `{{- if .Values.<svc>.enabled }}`. HA and MariaDB are additionally gated by `migrationState.*`; leave that alone unless doing a DB migration (see `README.md`).
- Labels/selectors: `app.kubernetes.io/name: <svc>`.
- Deployments using hostPath use `strategy: { type: Recreate }`; a rolling update would run two pods on the same host directory.
- Secrets: `envFrom.secretRef` with the name from `Values.<svc>.envFromSecret` (`envFromSecretList` for HA). A new secret also needs an entry in `Taskfile.yaml` `secrets.ITEMS` and a `credentials/<name>.env` on the host.
- Ingress: `ingressClassName: traefik`, no auth annotation. Who can reach a host is decided in `terraform/access.tf`.

## Common tasks

**Upgrade a service image or bootstrap chart**: use the `infra-upgrade` skill. Dependabot opens the image bump PRs on the 9th and 23rd (`.github/dependabot.yml`); the skill then only reviews the release notes. Traefik, ArgoCD and the MariaDB version line stay manual.

**Cross-service dependencies**: `apps/bash-poller` calls Frigate's export API (`/api/export/custom/...`, `/api/exports[/{id}]`, `/api/jobs/export[/{id}]`, matching exports by `name`, reading `video_path`; relies on Frigate 0.18's export queue semantics) inline in `helm-chart/templates/cronjob-ffmpeg.yaml`. `apps/py-play` proxies Frigate's `/api/tech/latest.jpg` snapshot. Changing Frigate or MQTT means checking those.

**Add a service**: copy the closest existing `templates/<svc>/` (deployment, service, ingress), add a values block with `enabled`, `namespace`, `image`, `ingress.host`, plus test overrides. A new namespace must also be added to `Taskfile.yaml` `setup-namespaces`. A new hostname is admins-only by default (wildcard Access app); and has no DNS record until it is in `terraform/`: add it to `gated_hosts` in `terraform/access.tf` (creates the CNAME and the Access app), or to `public_hosts` plus a route and `tunnel_hosts` entry in `terraform/tunnel.tf` to make it public.

## Verify

```bash
helm lint helm-chart && helm template t helm-chart > /dev/null
helm template t helm-chart -f helm-chart/values-test.yaml > /dev/null
```

For `terraform/`: `tofu fmt && tofu init -backend=false && tofu validate` in that directory. `plan` needs credentials the container does not have; CI runs it on the PR.

Rendering, not applying. Nothing here may run `kubectl` or `helm upgrade` against the cluster.
