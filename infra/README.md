# Core Infrastructure - Kubernetes

If GitOps is used, be refrained from `helm install`. That is, choose either "gitops-config" or "helm-chart".

## Memo

Bootstrap always use Taskfile! Patterns for info only:
- Namespaces required
- Local manifest deployments: cert issuer and Cloudflare tunnel
- Helm chart with value files: headlamp, Argo CD

> Argo CD using community managed helm chart, which is arguably anti-pattern.

Callback URL: /auth/callback for `ArgoCD`, /oidc-callback for `headlamp`


## Cloudflare

Tunnel -> Published Application Routers. Remember DNS config

Bypass cache for argocd in cache bypass