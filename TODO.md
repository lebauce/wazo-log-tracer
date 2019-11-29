* OPTIONS managed by nginx (CORS)
* SSL managed only by nginx
* Listen only on 127.0.0.1 in the all-in-one use case
* Activate traffic shaping in nginx with a high level to protect from DDOS
* Find a way to capture requests and payloads for a use case in a browser
* Ansible role to activate service headers in nginx. Will be off by default.
* CI job:
  * Deploy with ansible with the role for service header
  * Replay in CI the the captured calls
  * Run wazo-log-tracer© to detect regression (terms of number of calls and time spent)
