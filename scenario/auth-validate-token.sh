token=$( curl -s -k -X POST -u $auth -H 'Content-Type: application/json' -H 'Host: buster' \
    -d '{"expiration": 3600}' https://$host/api/auth/0.1/token | jq -r .data.token )

request=https://$WAZO_HOST/api/auth/0.1/token/$token
method=HEAD
services=( wazo-auth )