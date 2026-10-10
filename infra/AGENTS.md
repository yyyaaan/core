# infra/ (Helm, ArgoCD, k3s on Raspberry Pi)

Everything here deploys from `main` through ArgoCD (manual sync). Ingress: Cloudflare tunnel → Traefik → service. Cloudflare terminates TLS, so ingresses need no `tls:` block or cert-issuer annotations.

| Path | What |
|------|------|
| `helm-chart/` | Umbrella chart for platform services: HA, Frigate, MQTT, MariaDB, Homebridge, oauth2-proxy, Stirling-PDF, Restic CronJob. One subdir per service under `templates/` |
| `gitops-config/` | ArgoCD Applications: `bootstrap-cluster/` (external charts), `yan-fi/` (prod), `test-domain/` (test) |
| `bootstrap/` | Manifests and values applied by hand at cluster bootstrap (ArgoCD, Headlamp, tunnel, RBAC) |
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
- Protected ingress: annotation `traefik.ingress.kubernetes.io/router.middlewares: auth-oauth@kubernetescrd`, `ingressClassName: traefik`.

## Common tasks

**Upgrade a service image or bootstrap chart**: use the `infra-upgrade` skill.

**Cross-service dependencies**: `apps/bash-poller` calls Frigate's export API (`/api/export/custom/...`, `/api/exports`) from `job_timelapse.py` and inline in `helm-chart/templates/cronjob-ffmpeg.yaml`. `apps/py-play` publishes meter readings to Mosquitto. Changing Frigate or MQTT means checking those.

**Add a service**: copy the closest existing `templates/<svc>/` (deployment, service, ingress), add a values block with `enabled`, `namespace`, `image`, `ingress.host`, plus test overrides. A new namespace must also be added to `Taskfile.yaml` `setup-namespaces`.

## Verify

```bash
helm lint helm-chart && helm template t helm-chart > /dev/null
helm template t helm-chart -f helm-chart/values-test.yaml > /dev/null
```

Rendering, not applying. Nothing here may run `kubectl` or `helm upgrade` against the cluster.
