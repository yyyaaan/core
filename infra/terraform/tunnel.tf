locals {
  # tokens cloudflared accepts on the catch-all route
  catch_all_auds = concat(
    [for app in cloudflare_zero_trust_access_application.gated : app.aud],
    cloudflare_zero_trust_access_application.wildcard[*].aud,
  )
}

import {
  to = cloudflare_zero_trust_tunnel_cloudflared_config.home
  id = "${var.account_id}/${var.tunnel_id}"
}

# Replaces the routes configured by hand in the dashboard.
resource "cloudflare_zero_trust_tunnel_cloudflared_config" "home" {
  account_id = var.account_id
  tunnel_id  = var.tunnel_id
  source     = "cloudflare"

  config = {
    ingress = concat(
      # public at the edge: no token to check (assets is R2, not routed here)
      [for host in [var.domain, local.public_hosts.play, local.public_hosts.h] : {
        hostname = host
        service  = var.tunnel_origin
      }],
      [{
        hostname = "*.${var.domain}"
        service  = var.tunnel_origin
        # a missing or broken Access app then blocks the request instead of exposing the service
        origin_request = var.fail_closed ? {
          access = {
            required  = true
            team_name = var.team_name
            aud_tag   = local.catch_all_auds
          }
        } : null
      }],
      [{ service = "http_status:404" }],
    )
  }
}

# One proxied CNAME per hostname served from the cluster; there is no wildcard record,
# so a hostname is unreachable until it is listed here.
locals {
  tunnel_hosts = toset(concat(
    [var.domain, local.public_hosts.play, local.public_hosts.h],
    [for name in keys(local.gated_hosts) : "${name}.${var.domain}"],
  ))
}

import {
  # IDs of hostnames no longer listed are ignored, not an error
  for_each = { for host, id in var.dns_record_ids : host => id if contains(local.tunnel_hosts, host) }
  to       = cloudflare_dns_record.tunnel[each.key]
  id       = "${var.zone_id}/${each.value}"
}

resource "cloudflare_dns_record" "tunnel" {
  for_each = local.tunnel_hosts

  zone_id = var.zone_id
  name    = each.key
  type    = "CNAME"
  content = "${var.tunnel_id}.cfargotunnel.com"
  proxied = true
  ttl     = 1
}
