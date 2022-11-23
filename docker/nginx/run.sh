#!/bin/sh

set -eu

resolver=$(awk '/^nameserver/ { print $2; exit; }' /etc/resolv.conf)
sed -i "s;{{DNS_RESOLVER}};$resolver;g" /etc/nginx/conf.d/app.conf

sed -i "s;{{API_HOST}};$API_HOST;g" /etc/nginx/conf.d/app.conf

echo "Running nginx .."
/usr/local/openresty/bin/openresty -g "daemon off; pid /dev/null;"

