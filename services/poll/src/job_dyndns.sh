#!/bin/bash

echo "@$(date -u '+%b%d %H:%M:%S')"

external_ip1=$(curl -s https://api.ipify.org)
echo -n "[ipify] $external_ip1"

external_ip2=$(curl -s https://ipv4.svc.joker.com/nic/myip)
echo " [joker] $external_ip2"

if [ ${#external_ip1} -ge ${#external_ip2} ]; then
  external_ip=$external_ip1
else
  external_ip=$external_ip2
fi

echo -n "$(curl -s "https://svc.joker.com/nic/update?username=$U1&password=$P1&myip=$external_ip&hostname=$D1")"
echo " $(curl -s "https://svc.joker.com/nic/update?username=$U2&password=$P2&myip=$external_ip&hostname=$D2")"

echo "$(curl -s -X POST "https://pi.yan.fi/play/scheduled?audience=2")"
