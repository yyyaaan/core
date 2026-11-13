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

import {
  to = cloudflare_dns_record.wildcard
  id = "${var.zone_id}/${var.dns_record_id_wildcard}"
}

resource "cloudflare_dns_record" "wildcard" {
  zone_id = var.zone_id
  name    = "*.${var.domain}"
  type    = "CNAME"
  content = "${var.tunnel_id}.cfargotunnel.com"
  proxied = true
  ttl     = 1
}

import {
  to = cloudflare_dns_record.apex
  id = "${var.zone_id}/${var.dns_record_id_apex}"
}

resource "cloudflare_dns_record" "apex" {
  zone_id = var.zone_id
  name    = var.domain
  type    = "CNAME"
  content = "${var.tunnel_id}.cfargotunnel.com"
  proxied = true
  ttl     = 1
}
