#!/bin/bash

. ./common.sh

users=1
requests=25
method=GET
output=
headers=()
scenario=
ssh_user=
ssh_host=

bench() {
    local c=$1
    local n=$2
    local o=$3
    
    echo Start benchmark of $n requests by $c users

    cmd="ab -T application/json"
    
    case "$method" in
        POST) cmd+=" -p" ;;
        PUT) cmd+=" -u" ;;
        HEAD) cmd+=" -i" ;;
        DELETE) cmd+=" -m DELETE"
    esac
    
    if [ ! -z "$data" ]; then
        cmd+=" $data"
    fi
    
    if [ ! -z "$auth" ]; then
        cmd+=" -A $auth"
    fi

    for header in "${headers[@]}"; do
        cmd+=" -H $header"
    done

    cmd="$cmd -c $c -n $n $request"

    echo $cmd

    while IFS=: read -r key value; do
        case "$key" in
            "Concurrency Level") concurrency=$( echo $value );;
            "Complete requests") complete=$( echo $value );;
            "Requests per second") persec=$( echo $value | cut -d ' ' -f 1 );;
            "Failed requests") failed=$( echo $value );;
        esac 
    done <<< $( $cmd )

    echo "Benchmark done"

    echo "$concurrency,$complete,$failed,$persec" > $o
}

call_flow() {
    local o=$1

    truncate_logs "${services[@]}"
    bench 1 1 $o/bench.csv
    retrieve_logs $o "${services[@]}"
    cmd="./wazo-log-tracer.py --input=postgresql:$o/postgresql.log"
    for service in "${services[@]}"; do
        cmd+=" --input=flask:$o/$service-req.log"
    done

    $cmd > $o/call-flow.uml
    plantuml -tsvg $o/call-flow.uml
}

run_bench() {
    local o=$1

    # heuristic to define the duration based on request time avg
    # has to be adapted in the future
    duration=$(( 900 * $requests / 1000 + 20 ))

    truncate_logs "${services[@]}"
    start_system_monitor $duration $o "${services[@]}"
    start_profile $duration "${services[@]}"

    sleep 10
    bench $users $requests $o/bench.csv
    sleep 10

    retrieve_logs $o "${services[@]}"
    wait_profile
    wait_system_monitor

    retrieve_profile $o "${services[@]}"
}

run() {
    local o=$1

    mkdir -p $o

    # run the scenario once to determine call between services
    call_flow $o

    # run it multiple times to benchmark it
    run_bench $o
}

OPTIND=1
while getopts ":h:u:n:m:d:a:r:s:o:H:S:U:" option; do
    case "$option" in
        h) host=$OPTARG;;
        u) users=$OPTARG;;
        n) requests=$OPTARG;;
        m) method=$OPTARG;;
        d) data=$OPTARG;;
        a) auth=$OPTARG;;
        r) request=$OPTARG;;
        s) services+=("$OPTARG");;
        o) output=$OPTARG;;
        H) headers+=("$OPTARG");;
        U) ssh_user=("$OPTARG");;
        S) . ./scenario/$OPTARG.sh;;
        :) echo "Option -$OPTARG requires an argument !" >&2;;
        \?) echo "Unsupported option: -$OPTARG !" >&2;;
    esac
done

if [ -z "$request" ] || [ -z "$output" ]; then
    echo Usage: "$0 -d <filename> -r <http://> -o <output folder name> [options]"

    echo -e "\t-h wazo engine hostname, use ssh as root"
    echo -e "\t-u number of concurrent users"
    echo -e "\t-n number of total requests"
    echo -e "\t-m method used for the requests"
    echo -e "\t-d file used as data for PUT, POST requests"
    echo -e "\t-a authentication <login:password>"
    echo -e "\t-r url of the request"
    echo -e "\t-s service to monitor, can be used multiple times"
    echo -e "\t-o output folder name"
    echo -e "\t-H specify additional headers"
    echo -e "\t-S specify scenario to load"
    echo -e "\t-U ssh user to be used"

    exit -1
fi

ssh_host=${WAZO_SSH_HOST:-$host}

if [ ! -z "$ssh_user" ]; then
    ssh_host="$ssh_user@$ssh_host"
fi

# run the bench
run $output

