# Bucket behind assets.<domain>. Its custom domain stays in the dashboard (not importable),
# and so do the poller's S3 keys.
import {
  to = cloudflare_r2_bucket.static
  id = "${var.account_id}/static/default"
}

resource "cloudflare_r2_bucket" "static" {
  account_id = var.account_id
  name       = "static"

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [location, storage_class] # as created by hand
  }
}

# Not importable: the first apply overwrites the dashboard's rules with these.
# Keep in step with apps/bash-poller/README.md.
resource "cloudflare_r2_bucket_lifecycle" "static" {
  account_id  = var.account_id
  bucket_name = cloudflare_r2_bucket.static.name

  rules = [
    {
      id         = "timelapse-daily-7d"
      enabled    = true
      conditions = { prefix = "timelapse/daily/" }
      delete_objects_transition = {
        condition = { type = "Age", max_age = 7 * 86400 }
      }
    },
    {
      id         = "timelapse-monthly-730d"
      enabled    = true
      conditions = { prefix = "timelapse/monthly/" }
      delete_objects_transition = {
        condition = { type = "Age", max_age = 730 * 86400 }
      }
    },
  ]
}
