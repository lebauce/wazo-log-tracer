#!/usr/bin/env python

import re
from datetime import datetime
from os import listdir
from os.path import isfile, join
import sys


def normalize_flask_logs(filenames):
    time_fmt = '%Y-%m-%d %H:%M:%S,%f'

    flask_re = re.compile(
        r'^(\d+-\d+-\d+ \d+:\d+:\d+,\d+) \[\d+\] \((\w+)\) .*? (.*?): (.*)$')
    req_re = re.compile(r'(GET|POST|HEAD|DELETE|OPTION) (.*?) ')
    resp_re = re.compile(r'\((.*?)\) (GET|POST|HEAD|DELETE|OPTION) (.*?) (\d+)')

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
                            key = "%s %s" % (mr.group(1), mr.group(2))
                            request = "%s %s %s" % (
                                mf.group(1), mr.group(1), mr.group(2))
                            requests[key] = (
                                request, datetime.strptime(mf.group(1), time_fmt))
                    elif mf.group(3) == "response":
                        mr = resp_re.match(mf.group(4))
                        if mr:
                            key = "%s %s" % (mr.group(2), mr.group(3))
                            if key in requests:
                                request, timestamp = requests.pop(key)

                                milli = (datetime.strptime(
                                    mf.group(1), time_fmt) - timestamp).microseconds / 1000
                                request = "%s %s %s %d\n" % (
                                    request, mr.group(1), mr.group(4), int(milli))

                                r.write(request)
                    s.write(l)
                else:
                    e.write(l)
            else:
                e.write(l)


def parse_flask_logs(filename):
    pass


def main():
    normalize_flask_logs(sys.argv[1:])


if __name__ == "__main__":
    main()