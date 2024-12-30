#!/bin/bash
crontab /etc/cron.d/mounted-cron
cron
tail -f /dev/null

# crontab -l
