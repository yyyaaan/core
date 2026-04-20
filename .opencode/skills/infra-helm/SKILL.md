---
name: infra-helm
description: K8s infrastructure patterns for the yan-fi-server Helm chart — template conventions, secrets, ingress, GitOps
---

## Chart

- Name: `yan-fi-server`, type application, single umbrella chart
- Templates organized by service subdirectory under `templates/`
- Two value files: `values.yaml` (prod, `yan.fi`) and `values-test.yaml` (test, `omop.fi`)

## Template Conventions

### Labels & Selectors

```yaml
labels:
  app.kubernetes.io/name: <service>
selector:
  matchLabels:
    app.kubernetes.io/name: <service>
```

### Conditional Rendering

```yaml
{{- if .Values.<service>.enabled }}       # simple toggle
{{- if and .Values.ha.enabled .Values.migrationState.completed }}  # dual gate
```

Replicas set to 0 can also disable a service without removing manifests.

### Deployment Strategy

All services use `strategy: { type: Recreate }` — hostPath volumes prevent rolling updates.

## Secrets

- Injected via `envFrom.secretRef` referencing `Values.<svc>.envFromSecret`
- HA uses `envFromSecretList` (range loop) for multiple secrets
- Restic CronJob uses `secretKeyRef` for individual keys
- Secret sources: `infra/credentials/*.env`, loaded by `task infra:secrets`

## Ingress Pattern

```yaml
annotations:
  cert-manager.io/cluster-issuer: {{ .Values.certManager.issuerName }}
spec:
  ingressClassName: traefik
  tls:
  - hosts: [{{ .Values.<svc>.ingress.host }}]
    secretName: <svc>-tls-cert
```

Protected services add: `traefik.ingress.kubernetes.io/router.middlewares: auth-oauth@kubernetescrd`

## Namespaces

| Namespace | Services |
|-----------|----------|
| `home-internal` | HA, Frigate, MQTT, MariaDB, Homebridge, Restic, Poller |
| `web` | Stirling-PDF |
| `auth` | OAuth2-Proxy |

## Storage

| Type | Use |
|------|-----|
| hostPath | Config persistence (all services). Prod: `/mnt/kingston/...`, Test: `~/Lab/home/...` |
| PV + PVC | MariaDB data (Retain policy, local-path) |
| emptyDir Memory | Frigate shm/cache |

## GitOps

- ArgoCD app-of-apps in `infra/gitops-config/`
- Projects: `bootstrap` (external charts), `gitops` (self), `lab` (apps)
- Test domain overrides `valueFiles: [values-test.yaml]`
- Bootstrap: `task infra:bootstrap ENV=test|prod`

## Adding a New Service

1. Create `templates/<service>/deployment.yaml`, `service.yaml`, `ingress.yaml`
2. Add values block with `enabled`, `namespace`, `image`, `ingress.host`
3. Wrap all manifests in `{{- if .Values.<service>.enabled }}`
4. Use existing label/selector/ingress patterns above
5. Add corresponding test overrides in `values-test.yaml`
