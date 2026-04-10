# YYYaan Core Monorepo

Concept: Monorepo, GitOps, Strict Typing in Python, Rest API, MCP server.

No more helm apply, use ArgoCD for kubernetes deployments: currently requires Manual Approval in addition to PR.

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
uv run play
uv run autobrowser
```

## Services

Home Internal: Home Assistant, MariaDB, Homebridge, Frigate

General Web: Play FastAPI App, Stirling PDF (on-demand)

Supporting service: OAuth2 Proxy, headlamp; Cloudflare tunnel and Cert Issuers
