token=$( curl -s -k -X POST -u $auth -H 'Content-Type: application/json' -H 'Host: buster' \
-d '{"expiration": 3600}' https://$host/api/auth/0.1/token | jq -r .data.token )

request=https://$WAZO_HOST/api/calld/1.0/calls
method=GET
services=( wazo-auth wazo-calld )
headers=( "X-Auth-Token:$token" )