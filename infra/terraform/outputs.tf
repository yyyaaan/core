# Both go into infra/credentials/play.env (ACCESS_TEAM_DOMAIN, ACCESS_AUD).
output "access_team_domain" {
  value = local.team_domain
}

output "play_access_aud" {
  value = cloudflare_zero_trust_access_application.play_private.aud
}
