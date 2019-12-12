#!/usr/bin/env python

import os
import re
import sys

from datetime import datetime, timedelta, timezone
from os import listdir
from os.path import isfile, join
from record import Record


def normalize_flask_logs(filenames):
    time_fmt = '%Y-%m-%d %H:%M:%S,%f'

    flask_re = re.compile(
        r'^(\d+-\d+-\d+ \d+:\d+:\d+,\d+) \[\d+\] \((\w+)\) .*? (.*?): (.*)$')
    req_re = re.compile(r'(GET|POST|HEAD|DELETE|OPTION) (.*?) ')
    resp_re = re.compile(r'\((.*?)\) (GET|POST|HEAD|DELETE|OPTION) (.*?) (\d+)')
    user_agent_re = re.compile(r".*'User-Agent': '([^']+)'")

    fds = dict()
    for f in filenames:
        name = f.split(".")[0]

        print("Processing: %s" % f)

        if name not in fds:
            s = open("%s-nobt.log" % name, "w+")
            e = open("%s-bt.log" % name, "w+")
            r = open("%s-req.log" % name, "w+")
            fds[name] = (s, e, r)

        s, e, r = fds[name]

        requests = dict()
        for l in open(f).readlines():
            mf = flask_re.match(l)
            if mf:
                if mf.group(2) == 'INFO':
                    if mf.group(3) == "request":
                        mr = req_re.match(mf.group(4))
                        if mr:
                            user_agent = "unknown"
                            mua = user_agent_re.match(mf.group(0))
                            if mua:
                                user_agent = mua.group(1)
                            key = "%s %s" % (mr.group(1), mr.group(2))
                            request = "%s %s %s" % (
                                mf.group(1), mr.group(1), mr.group(2))
                            requests[key] = (
                                request, datetime.strptime(mf.group(1), time_fmt), user_agent)
                    elif mf.group(3) == "response":
                        mr = resp_re.match(mf.group(4))
                        if mr:
                            key = "%s %s" % (mr.group(2), mr.group(3))
                            if key in requests:
                                request, timestamp, user_agent = requests.pop(key)

                                milli = (datetime.strptime(
                                    mf.group(1), time_fmt) - timestamp).microseconds / 1000
                                request = "%s %s %s %d %s\n" % (
                                    request, mr.group(1), mr.group(4), int(milli), user_agent)

                                r.write(request)
                    s.write(l)
                else:
                    e.write(l)
            else:
                e.write(l)


def parse_flask_logs(input):
    time_fmt = '%Y-%m-%d %H:%M:%S,%f'

    log_re = re.compile(
        r'^(\d+-\d+-\d+ \d+:\d+:\d+\,\d+) ([A-Z]+) (\S+) (\S+) (\d+) (\d+) (\S+)$')

    service = os.path.splitext(os.path.basename(input.name))[0]
    if service.endswith("-req"):
        service = service[:-4]

    records = []
    for id, l in enumerate(input.readlines()):
        mf = log_re.match(l)
        if mf:
            dt, method, request, duration, user_agent = datetime.strptime(mf.group(1), time_fmt), mf.group(2), mf.group(3), timedelta(microseconds=float(mf.group(6))*1000), mf.group(7)
            dt = dt.replace(tzinfo=timezone.utc)
            request_start = dt
            request_record = Record(id, method, request[:80], 200, user_agent, service, request_start, request_start, duration, "request")
            response_record = Record(id, method, request[:80], 200, user_agent, service, request_start+duration, request_start, duration, "response")
            records.append(request_record)
            records.append(response_record)

    return records


def main():
    normalize_flask_logs(sys.argv[1:])


if __name__ == "__main__":
    main()