#!/usr/bin/python3

import re
import sys

from datetime import datetime, timedelta, timezone
from os import listdir
from os.path import isfile, join
from record import Record


def parse_postgresql_logs(input):
    """
    postgresql log format is expected to be:
    log_line_prefix = '%m [%p] [%a] %q%u@%d'
    """

    time_fmt = '%Y-%m-%d %H:%M:%S.%f %Z'

    log_re = re.compile(
        r'^(\d+-\d+-\d+ \d+:\d+:\d+\.\d+ [A-Z]+) \[\d+\] \[([a-zA-Z\-]+)\] \w+@\w+ LOG:\s+duration:\s+(\d+\.\d+) ms\s+statement: ([A-Z]+)(.*)$')

    records = []
    for id, l in enumerate(input.readlines()):
        mf = log_re.match(l)
        # if id == 0:
        #     import pdb; pdb.set_trace()
        if mf:
            dt, service, duration, method, request = datetime.strptime(mf.group(1), time_fmt), mf.group(2), timedelta(microseconds=float(mf.group(3))*1000), mf.group(4), mf.group(5)
            dt = dt.replace(tzinfo=timezone.utc)
            request_start = dt-duration
            request_record = Record(id, method, request[:80], 200, service, "postgresql", request_start, request_start, duration, "request")
            response_record = Record(id, method, request[:80], 200, service, "postgresql", dt, request_start, duration, "response")
            records.append(request_record)
            records.append(response_record)
    
    return records


if __name__ == "__main__":
    parse_postgresql_logs(sys.argv[1])