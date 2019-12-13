#!/usr/bin/env python3

import argparse
import csv
import json
import re
import sys
import urllib.parse

from flask import *
from nginx import *
from postgresql import *


def format_user_agent(user_agent):
    return user_agent.split()[0]


def output_uml(records, output):
    records.sort(key=lambda r: r.record_time)

    output.write("@startuml\n")

    for record in records:
        if record.type == "request":
            output.write(
                '"%s" -[#red]> "%s": %s %d %s ( <b>%d</b> Start: %f ms)\n'
                % (
                    format_user_agent(record.user_agent),
                    record.service,
                    record.method,
                    record.status,
                    record.uri,
                    len(records) / 2 - record.id + 1,
                    (record.request_start - records[0].request_start).total_seconds() * 1000.,
                )
            )
        else:
            output.write(
                '"%s" <-[#blue]- "%s": %s %d %s ( <b>%d</b> Duration: %f ms)\n'
                % (
                    format_user_agent(record.user_agent),
                    record.service,
                    record.method,
                    record.status,
                    record.uri,
                    len(records) / 2 - record.id + 1,
                    record.request_duration.total_seconds() * 1000,
                )
            )

    output.write("@enduml\n")


def output_csv(records, output):
    csv_writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    csv_writer.writerow(
        [
            "ID",
            "Method",
            "Path",
            "Query",
            "Status",
            "User Agent",
            "Service",
            "Request start",
            "Duration",
        ]
    )
    for record in records:
        if record.type == "request":
            result = urllib.parse.urlparse(record.uri)
            csv_writer.writerow(
                [
                    record.id,
                    record.method,
                    result.path,
                    result.query,
                    record.status,
                    record.user_agent,
                    record.service,
                    record.request_start,
                    record.request_duration.total_seconds() * 1000,
                ]
            )


def output_stats(records):
    records.sort(key=lambda r: r.record_time)

    status, calls, times = dict(), dict(), dict()

    for record in records:
        status[record.status] = status.get(record.status, 0) + 1

        key = "%s %s" % (record.method, record.service)
        calls[key] = calls.get(key, 0) + 1
        times[key] = times.get(key, 0) + record.request_duration

    stats = {
        "status": status,
        "calls": calls,
        "times": times,
        "duration": records[-1].record_time - records[0].record_time,
    }

    print(json.dumps(stats, indent=4, sort_keys=True))


def main(inputs, output, format):
    records = []

    for input in inputs:
        if input == "-":
            input_file = sys.stdin
        else:
            splitted = input.split(':', 1)
            if len(splitted) > 1:
                input_format, filename = splitted
            else:
                input_format = "nginx"
                filename = splitted[0]
            input_file = open(filename)

        if input_format == "nginx":
            records += parse_nginx_logs(input_file)
        elif input_format == "postgresql":
            records += parse_postgresql_logs(input_file)
        elif input_format == "flask":
            records += parse_flask_logs(input_file)

    if format == "uml":
        output_uml(records, output)
    elif format == "csv":
        output_csv(records, output)
    elif format == "stats":
        output_stats(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", default="uml",
                        help="output format (csv, uml, stats)")
    parser.add_argument("--output", default="-",
                        help="output file (defaults to standard output)")
    parser.add_argument("--input", default=[], action="append",
                        help="input file (defaults to standard input)")
    args = parser.parse_args()

    if args.output == "-":
        output_file = sys.stdout
    else:
        output_file = open(args.output, "w", newline="")

    main(args.input, output_file, args.format)
