locals {
  team_domain = "https://${var.team_name}.cloudflareaccess.com"

  # host => who is admitted; every host here is routed by the tunnel's catch-all
  gated_hosts = {
    frigate    = local.admins_only
    homebridge = local.admins_only
    cd         = local.admins_only
  }

  admins_only      = [cloudflare_zero_trust_access_policy.admins.id]
  admins_and_users = concat([cloudflare_zero_trust_access_policy.admins.id], cloudflare_zero_trust_access_policy.users[*].id)

  # Access rejects a group without members, so `users` exists only once it has some
  has_users = nonsensitive(length(var.user_emails) > 0)

  # hosts that stay public at the edge; without an entry the wildcard app gates them
  public_hosts = {
    play   = "play.${var.domain}" # private paths are carved out by the play_private app
    h      = "h.${var.domain}"    # Home Assistant, out of scope: native login
    assets = "assets.${var.domain}"
    # proxied records that do not go through the tunnel
    www   = "www.${var.domain}"
    inbox = "inbox.${var.domain}"
    chat  = "chat.${var.domain}"
    pi    = "pi.${var.domain}"
  }
}

resource "cloudflare_zero_trust_access_identity_provider" "google" {
  account_id = var.account_id
  name       = "Google"
  type       = "google"
  config = {
    client_id     = var.google_client_id
    client_secret = var.google_client_secret
  }
}

resource "cloudflare_zero_trust_access_identity_provider" "otp" {
  account_id = var.account_id
  name       = "One-time PIN"
  type       = "onetimepin"
  config     = {}
}

# The only user lists. Members come from the ACCESS_ADMIN_EMAILS / ACCESS_USER_EMAILS secrets.
resource "cloudflare_zero_trust_access_group" "admins" {
  account_id = var.account_id
  name       = "admins"
  include    = [for e in var.admin_emails : { email = { email = e } }]
}

resource "cloudflare_zero_trust_access_group" "users" {
  count = local.has_users ? 1 : 0

  account_id = var.account_id
  name       = "users"
  include    = [for e in var.user_emails : { email = { email = e } }]
}

resource "cloudflare_zero_trust_access_policy" "admins" {
  account_id = var.account_id
  name       = "Allow admins"
  decision   = "allow"
  include    = [{ group = { id = cloudflare_zero_trust_access_group.admins.id } }]
}

resource "cloudflare_zero_trust_access_policy" "users" {
  count = local.has_users ? 1 : 0

  account_id = var.account_id
  name       = "Allow users"
  decision   = "allow"
  include    = [{ group = { id = cloudflare_zero_trust_access_group.users[0].id } }]
}

resource "cloudflare_zero_trust_access_policy" "public" {
  account_id = var.account_id
  name       = "Bypass for everyone"
  decision   = "bypass"
  include    = [{ everyone = {} }]
}

resource "cloudflare_zero_trust_access_application" "gated" {
  for_each = local.gated_hosts

  account_id           = var.account_id
  name                 = each.key
  type                 = "self_hosted"
  domain               = "${each.key}.${var.domain}"
  session_duration     = "168h"
  app_launcher_visible = false
  policies             = [for i, id in each.value : { id = id, precedence = i + 1 }]
}

# Access apps match the most specific host and path, so these two paths are gated
# while the rest of play (/, /docs, /public/*) falls through to the bypass app below.
resource "cloudflare_zero_trust_access_application" "play_private" {
  account_id           = var.account_id
  name                 = "play (private routes)"
  type                 = "self_hosted"
  session_duration     = "168h"
  app_launcher_visible = false
  destinations = [
    { type = "public", uri = "play.${var.domain}/view" },
    { type = "public", uri = "play.${var.domain}/scheduled" },
  ]
  policies = [for i, id in local.admins_and_users : { id = id, precedence = i + 1 }]
}

resource "cloudflare_zero_trust_access_application" "public" {
  for_each = local.public_hosts

  account_id           = var.account_id
  name                 = "${each.key} (public)"
  type                 = "self_hosted"
  domain               = each.value
  app_launcher_visible = false
  policies             = [{ id = cloudflare_zero_trust_access_policy.public.id, precedence = 1 }]
}

# Default-deny: any hostname without its own app is admins-only.
resource "cloudflare_zero_trust_access_application" "wildcard" {
  count = var.fail_closed ? 1 : 0

  account_id           = var.account_id
  name                 = "default (admins only)"
  type                 = "self_hosted"
  domain               = "*.${var.domain}"
  session_duration     = "168h"
  app_launcher_visible = false
  policies             = [{ id = cloudflare_zero_trust_access_policy.admins.id, precedence = 1 }]
}
