variable "account_id" {
  type = string
}

variable "zone_id" {
  type = string
}

variable "domain" {
  type    = string
  default = "yan.fi"
}

variable "team_name" {
  description = "Zero Trust team name, the <team> in <team>.cloudflareaccess.com."
  type        = string
}

variable "tunnel_id" {
  description = "The existing tunnel. Only its routes are managed here, never the tunnel or its token."
  type        = string
}

variable "tunnel_origin" {
  type    = string
  default = "http://traefik.traefik.svc.cluster.local:8080"
}

variable "admin_emails" {
  type      = list(string)
  sensitive = true
}

variable "user_emails" {
  type      = list(string)
  sensitive = true
  default   = []
}

variable "google_client_id" {
  type = string
}

variable "google_client_secret" {
  type      = string
  sensitive = true
}

variable "state_passphrase" {
  description = "At least 16 characters. Losing it loses the state."
  type        = string
  sensitive   = true
}

variable "fail_closed" {
  description = "Wildcard default-deny app, and cloudflared requires an Access token on the catch-all route. On in production."
  type        = bool
  default     = true
}
