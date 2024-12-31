#!/bin/bash
env >> /etc/environment

crontab /etc/cron.d/mounted-cron
cron
tail -f /dev/null

# crontab -l
# check environmental variables are global