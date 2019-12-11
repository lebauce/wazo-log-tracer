#!/usr/bin/env python3

import csv
from datetime import datetime
import glob
from jinja2 import Template
import os
import sys


def read_bench(folder, width):
    tmpl = """
    <div class="card" style="width: {{ width }}px; margin-right: 2rem;">
        <div class="card-header">
            Global bench information
        </div>
        <table class="table">
            <tbody>
                <tr>
                <td>Concurrency :</td>
                <td>{{ bench[0] }}</td>
                </tr>
                <td>Complete :</td>
                <td>{{ bench[1] }}</td>
                </tr>
                <td>Failed :</td>
                <td>{{ bench[2] }}</td>
                </tr>
                <td>Request per sec. :</td>
                <td>{{ bench[3] }}</td>
                </tr>
                </tr>
                <td>Avg request time (ms). :</td>
                {% set ms = ( 1 / ( bench[3] | float ) * 1000 ) | int %}
                <td>{{ ms }}</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
    tm = Template(tmpl)

    try:
        with open("%s/bench.csv" % folder, mode='r') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                return tm.render(bench=row, width=width)
    except:
        pass


def read_sys(folder, width, height):
    tmpl = """
    <div class="card">
        <div class="card-header" style="width: {{ width }}px;" >
            System load
        </div>

        <div id="cpu" style="width: {{ width }}px; height: {{ height }}px"></div>
        <script type="text/javascript">
        google.charts.load('current', {'packages':['corechart']});
        google.charts.setOnLoadCallback(drawChart);

        function drawChart() {
            data = [
                [
                {% for field in rows[0] -%}
                    '{{ field }}',
                {% endfor %}
                ],
                {% for row in rows[1:] -%}
                    [ '{{ row[0] }}', {{ row[1] }}, {{ row[2] }} ],
                {% endfor %}
            ]

            var data = google.visualization.arrayToDataTable(data);

            var options = {
                title: 'CPU',
                curveType: 'function',
                legend: { position: 'bottom' }
            };

            var chart = new google.visualization.LineChart(document.getElementById('cpu'));

            chart.draw(data, options);
        }
        </script>
    </div>
    """
    tm = Template(tmpl)

    rows = []

    files = glob.glob("%s/*-sys.csv" % folder)

    # tiles
    row = ['Time']
    for f in files:
        name = os.path.basename(f).replace("-sys.csv", "")
        row.append(name)
    rows.append(row)

    files = [csv.reader(open(i, "r"), delimiter=',') for i in files]
    for records in zip(*files):
        row = [records[0][0]]

        for record in records:
            row.append(record[2])

        rows.append(row)
    return tm.render(rows=rows, width=width, height=height)


def read_req(folder, width, height):
    tmpl = """
    <div class="card" style="margin-top: 20px;">
        <div class="card-header" style="width: {{ width }}px;">
            {{ id }} request time(ms)
        </div>
        <div id="{{ id }}" style="width: {{ width }}px; height: {{ height }}px;"></div>
        <script type="text/javascript">
        google.charts.load('current', {'packages':['corechart']});
        google.charts.setOnLoadCallback(drawChart);

        function drawChart() {
            data = [
                ['Timestamp', 'GET', 'HEAD', 'OPTIONS', 'DELETE', 'POST', 'PUT'],
                {% for row in rows -%}
                    [ '{{ row[0] }}', {{ row[1] }}, {{ row[2] }}, {{ row[3] }}, {{ row[4] }}, {{ row[5] }}, {{ row[6] }} ],
                {% endfor %}
            ]

            var data = google.visualization.arrayToDataTable(data);

            var options = {
                title: 'Request',
                curveType: 'function',
                legend: { position: 'bottom' }
            };

            var chart = new google.visualization.LineChart(document.getElementById('{{ id }}'));

            chart.draw(data, options);
        }
        </script>
    </div>
    """
    tm = Template(tmpl)

    result = []

    mi = {
        "GET": 1,
        "HEAD": 2,
        "OPTIONS": 3,
        "DELETE": 4,
        "POST": 5,
        "PUT": 6
    }

    for file in glob.glob("%s/*-notok.log" % folder):
        with open(file, mode='r') as f:
            rows = []

            for line in f.readlines():
                entries = line.rstrip().split(" ")

                ds = "%s %s" % (entries[0], entries[1])
                dt = datetime.strptime(ds, '%Y-%m-%d %H:%M:%S,%f')

                a = [0] * 7
                a[0] = dt.timestamp()
                i = mi[entries[2]]
                a[i] = entries[6]

                rows.append(a)

            id = os.path.basename(file).replace("-notok.log", "")
            result.append(tm.render(id=id, rows=rows,
                                    width=width, height=height))

    return result


def read_flame(folder, width):
    tmpl = """
    <div class="card" style="margin-top: 20px;">
        <div class="card-header" style="width: {{ width }}px;">
            {{ name }}
        </div>
        <object type="image/svg+xml" data="{{ file }}" align="left"></object>
    </div>
    """
    tm = Template(tmpl)

    files = glob.glob("%s/*-flame.svg" % folder)

    result = []
    for f in files:
        file = os.path.basename(f)
        name = file.replace("-flame.svg", "")
        result.append(tm.render(file=file, name=name, width=width))

    return result


def render(folder):
    tmpl = """
    <html>
    <head>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    <link href="https://stackpath.bootstrapcdn.com/bootswatch/4.4.1/darkly/bootstrap.min.css" rel="stylesheet" integrity="sha384-rCA2D+D9QXuP2TomtQwd+uP50EHjpafN+wruul0sXZzX/Da7Txn4tB9aLMZV4DZm" crossorigin="anonymous">
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <style>
    .content {
        margin: 10px;
    }
    .flex {
        display: inline-flex;
    }
    </style>
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <span class="navbar-brand mb-0 h1">Benchmark report : {{ date }}</span>
        </nav>
        <div class="content">
            <div class="flex">
            {% if bench -%}
                {{ bench }}
            {% endif %}
                {{ sys }}
            </div>
            <div class="flex" style="flex-direction: column;">
                {% for r in req -%}
                    {{ r }}
                {% endfor %}
            </div>
            <div class="flex" style="margin-top: 20px; margin-bottom: 20px;">
                GoAccess Report :&nbsp;<a href="goaccess.html">here</a>
            </div>
            <div class="flex" style="flex-direction: column;">
                {% for f in flame -%}
                    {{ f }}
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """
    tm = Template(tmpl)

    bench = read_bench(folder, 300)
    sys = read_sys(folder, 900 if bench else 1232, 300)
    req = read_req(folder, 1232, 300)
    flame = read_flame(folder, 1232)

    with open("%s/report.html" % folder, "w+") as f:
        f.write(tm.render(
            date=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            bench=bench,
            sys=sys,
            req=req,
            flame=flame
        ))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: %s <bench folder>" % sys.argv[0])
        exit(255)

    render(sys.argv[1])
