# Tools to help analyzing Wazo service logs

## wazo-log-tracer

This tool aims at showing the interactions between Wazo services.
It parses nginx logs to produce a sequence diagrams of all HTTP calls.

Example:

[Example sequence diagram](example.png)

### Setting up

* Edit nginx config for log formatting. In `/etc/nginx/sites-available/wazo`:

  * Add the following:
    ```
    log_format main
      '$remote_addr - $remote_user [$time_local] "$request" '
      '$status $body_bytes_sent "$http_referer" "$http_user_agent" "$sent_http_x_powered_by" '
      '$request_length $msec $request_time $upstream_addr '
      '$upstream_response_length $upstream_response_time $upstream_status';
    ```

* Add a header in the response for each service: In `/etc/nginx/locations/https-enabled/<service name>`
  ```
  add_header          X-Powered-By        <service name> always;
  ```
* Reload nginx: `systemctl reload nginx`
* Redirect all HTTP calls to nginx:
  * Create `/etc/wazo.yml`:
    ```
    amid:
      port: 443
      prefix: /api/amid
      verify_certificate: false
    auth:
      port: 443
      timeout: 30
      prefix: /api/auth
      verify_certificate: false
    call-logd:
      port: 443
      prefix: /api/call-logd
      verify_certificate: false
    confd:
      port: 443
      prefix: /api/confd
      verify_certificate: false
    dird:
      port: 443
      prefix: /api/dird
      verify_certificate: false
    plugind:
      port: 443
      prefix: /api/plugind
      verify_certificate: false
    provd:
      port: 443
      prefix: /api/provd
      verify_certificate: false
    webhookd:
      port: 443
      prefix: /api/webhookd
      verify_certificate: false
    ```

  * Apply it to all Wazo services:
    ```
    for service in /etc/wazo-*
    do
        sudo ln -s /etc/wazo.yml $service/conf.d/wazo-log-tracer.yml
    done
    ```
* Patch `wazo-lib-rest-client`: 
  ```
  patch -p1 -d /usr/lib/python3/dist-packages < wazo-lib-rest-client-user-agent.patch
  patch -p1 -d /usr/lib/python2.7/dist-packages < wazo-lib-rest-client-user-agent.patch
  ```
* Restart services: `wazo-service restart`

### Usage

* Capture nginx logs in `/var/log/nginx/wazo.access.log`
* You can use `logrotate -f /etc/logrotate.d/nginx` to purge the log file
* Use it: `./wazo-log-tracer.py wazo.access.log wazo.puml`
* Generate PNG file `wazo.png`: `plantuml wazo.puml`

### Advanced usage

* Use max-connections=1 in Firefox to see sequential calls

* Use a spreadsheet to analyse which requests are the more costly: the ones initiated from the browser which are the longest. Then analyse them in the call graph.

## flask.py

This tool re arrange Wazo service flask logs in order to extract
backtraces and provide a single file for request/response that
can be analyze with goaccess.

```
python flask.py wazo-auth.log*
```

This command generates 3 files:

* wazo-auth-nobt.log: log file with all the backtraces removed
* wazo-auth-bt.log: log file with only the backtraces
* wazo-auth-req.log: log file with request and response merged, can be analyzed with goaccess

## detokenize.py

Replace tokens from the log by a unique placeholder. This can be applied before goaccess
analysis.

```
cat wazo-auth-req.log | python detokenize.py > detokenized.log
```

## mkgoaccess

This short shell script call goaccess with the required format to read *-req.log" files

```
mkgoaccess wazo-auth-req.log
```

or 

```
mkgoaccess detokenized.log
```

## Benchmark

### bench.sh

This tool is used to run apache bench against an engine. While running the benchmark it collects metrics from the
engine host. All the files are written in a folder and can be processed by the report.py tool which generates a single
html report page.

Examples:

Token creation

Data file:
```
cat new-token.json
{"expiration": 3600}
```

Bench:
```
./bench.sh -d ./new-token.json -u 10 -n 50 -a root:pass -m POST -r https://192.168.1.201/api/auth/0.1/token -s wazo-auth -o run-1
```

### monitor.sh

This tool collects the same metrics as the bench one except that it doesn't run any stress test.

```
./monitor.sh -d 30 -o run-2 -s wazo-auth
```

### report.py

This tool generates a report from files collected by bench.sh

Examples:

```
report.py run-1
``̀

This generates a file named `report.html` within the bench folder.

### Scenario

This is a way to create file that will be used to pre-configure a bench. These files
have to be placed in the scenario folder. A scenario file is basically a shell file
that fill variable that the bench will use.

Example :

`̀ `
token=$( curl -s -k -X POST -u $auth -H 'Content-Type: application/json' -H 'Host: buster' \
-d '{"expiration": 3600}' https://$host/api/auth/0.1/token | jq -r .data.token )

request=https://$WAZO_HOST/api/confd/1.1/incalls
method=GET
services=( wazo-auth wazo-confd )
headers=( "X-Auth-Token:$token" )
```

Here the variable that can be set

* method: method of the HTTP request
* data: data file path used for POST, PUT requests
* auth: basic auth parameter, user:password
* request: URL of the request
* services: service to be monitored
* headers: list of header that will be used for the request
