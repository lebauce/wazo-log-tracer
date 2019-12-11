token=$( curl -s -k -X POST -u $auth -H 'Content-Type: application/json' -H 'Host: buster' \
-d '{"expiration": 3600}' https://$host/api/auth/0.1/token | jq -r .data.token )

request=https://$WAZO_HOST/api/confd/1.1/incalls
method=GET
services=( wazo-auth wazo-confd )
headers=( "X-Auth-Token:$token" )