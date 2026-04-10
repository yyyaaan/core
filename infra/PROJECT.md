# Production Readiness Project

## Moving from Docker to Kubernetes

Installation steps are detailed in `Taskfile.yaml`.

## Additional Manual Checks

Manual update non-git:
- storageClassName for mariadb persistent volume
- http://traefik.default.svc.cluster.local:80 can be different! check name space, even kube-system
- mqtt-service or mqtt-service.home-internal or mqtt-service.home-internal.svc.cluster.local (mqtt://...:1883)
- play/public/spot & water.jpg update path in HA
- start?rd=https:// for all login button
- Cloudflared pod needs API Key explicitly
- login page customization https://oauth2-proxy.github.io/oauth2-proxy/configuration/overview#page-template-options

Gitignored
- credentials/active
- config/ha/secrets.yaml updated mariadb address
- config/frigate/config.yaml updated mqtt address

HA tasks
- change MQTT address
- possible path /play

## Networking Configuration

Cloudflare setups:
- Enable Cloudflare tunnel
- Zero Trust - Tunnel: Published application routes, add HTTP [traefik.kube-system.svc.cluster.local:80](http://traefik.default.svc.cluster.local:80), note for possible different namespace (can be default if on OrbStack)
- DNS: [should be auto created by step above] CNAME * tunnel_id.cfargotunnel.com (proxied)
