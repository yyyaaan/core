# YYYaan Core Monorepo

Concept: Monorepo, GitOps, Strict Typing in Python, Rest API, MCP server.

No more helm apply, use ArgoCD for kubernetes deployments: currently requires Manual Approval in addition to PR.

Home Automation with Home Assistant, HomeBridge, Frigate and more are only available under /infra/helm-charts, and they are part of core infra

## Technologies

- __Kubernetes__, helm charts, networking, oauth2-proxy and more 
- __Python__, FastAPI and a lot more
- __CI/CD__, go-task + github actions
- __Public Networking__, cloudflare DNS tunnel (in-cluster only)

`Taskfile` is used to manage local and cloud workflow. See [taskfile.dev](https://taskfile.dev) and [go-task/task](https://github.com/go-task/task).

> All projects suffixed with `py` (`python`) or `rs` (`Rust`)<br/> __apps/__ contains the main projects<br/> __Crates/__ for `Rust` only<br/> __packages/__ for `python` only<br/> 

## Quick Start Dev

For `python` and `Rust` projects, please use devcontainer. Infra relies on GitOps, and shall be tested on host.

```
uv run autobrowser
uv run play
# with header for dev
ALLOW_LOCAL_AUTH=true LOCAL_AUTH_EMAIL=t@t.dev ALLOWED_EMAILS='["t@t.dev"]' uv run play
```

## Services

Home Internal: Home Assistant, MariaDB, Homebridge, Frigate

General Web: Play FastAPI App, Stirling PDF (on-demand)

Supporting service: OAuth2 Proxy, headlamp; Cloudflare tunnel and Cert Issuers

## Restic Backups

A Cronjob is registered to backup the MariaDB and config folders.

```
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
export RESTIC_PASSWORD=

restic -r s3:s3.eu-central-003.backblazeb2.com/yyyRestic forget --keep-daily 7 --keep-weekly 8 --dry-run [--prune to run]

restic -r s3:s3.eu-central-003.backblazeb2.com/yyyRestic snapshots
restic -r s3:s3.eu-central-003.backblazeb2.com/yyyRestic ls -l latest

unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY RESTIC_PASSWORD
```

## Remember to confirm Kube Context

`export KUBECONFIG=~/.kube/pi-config` (default is config)