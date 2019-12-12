#!/usr/bin/python3

import re

from datetime import datetime, timedelta, timezone
from record import Record

MAGIC_REGEX = (
    ".*?(GET|HEAD|POST|PUT|OPTIONS|DELETE|PATCH) (\S+) "
    'HTTP/\d+\.\d+" (\d+) \d+ ".*?" "(.*?)" "(.*?)" \d+ '
    "(\d+\.\d+) (\d+\.\d+) .*"
)


def format_uri(url):
    return re.sub(r"(\w+)-\w+-\w+-\w+-\w+", r"\1", url)


def parse_nginx_logs(input):
    records = []

    for id, log in enumerate(input.readlines()):
        m = re.search(MAGIC_REGEX, log)
        (
            method,
            uri,
            status,
            user_agent,
            service,
            log_time,
            request_duration,
        ) = m.groups()
        request_duration = timedelta(milliseconds=float(request_duration)*1000)
        log_time = datetime.fromtimestamp(float(log_time), timezone.utc)
        status = int(status)
        request_start = log_time - request_duration
        uri = format_uri(uri)
        record = Record(
            id,
            method,
            uri,
            status,
            user_agent,
            service,
            request_start,
            request_start,
            request_duration,
            "request",
        )
        records.append(record)
        record = Record(
            id,
            method,
            uri,
            status,
            user_agent,
            service,
            log_time,
            request_start,
            request_duration,
            "response",
        )
        records.append(record)

    return records
