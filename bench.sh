#!/bin/bash

host=wazo
users=1
requests=25
method=GET
output=
services=()
headers=()

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
    while IFS=: read -r key value; do
        case "$key" in
            "Concurrency Level") concurrency=$( echo $value );;
            "Complete requests") complete=$( echo $value );;
            "Requests per second") persec=$( echo $value | cut -d ' ' -f 1 );;
            "Failed requests") failed=$( echo $value );;
        esac 
    done <<<$( $cmd )

    echo "Benchmark done"

    echo "$concurrency,$complete,$failed,$persec" > $o
}

declare -A top_pids
start_system_monitor() {
    local d=$1; shift
    local o=$1; shift

    for arg in "$@"; do
        echo Start monitoring $arg

        pid=$( ssh $host "pgrep -f $arg" )
        num=$(( $d * 2 ))
        
        ssh $host "top -b -n $num -d 0.5 -p $pid | grep $pid | sed 's/,/./' | awk '{print ((NR+1)/2)\",\"\$6\",\"\$9}'" > $o/$arg-sys.csv &
        top_pids["$arg"]="$!"
    done
}

wait_system_monitor() {
    for pid in "${top_pids[@]}"; do
        wait $pid
    done
}

truncate_logs() {
    for arg in "$@"; do
        echo Truncate log of $arg

        ssh $host "sudo truncate -s 0 /var/log/$arg.log"
    done

    ssh $host "sudo truncate -s 0 /var/log/postgresql/postgresql-*-main.log"
}

retrieve_logs() {
    local d=$1; shift

    pushd $d

    for arg in "$@"; do
        echo Retrieve log of $arg

        scp $host:/var/log/$arg.log .

        python ../flask.py $arg.log
        cat $arg-req.log | python ../detokenize.py >  $arg-notok.log

        # generate goaccess
        goaccess -o goaccess.html --date-format '%Y-%m-%d' \
            --time-format '%H:%M:%S'  --log-format '%d %t,%^ %m %U %h %s %L' $arg-notok.log
    done

    ssh $host "sudo cat /var/log/postgresql/postgresql-*-main.log" > postgresql.log

    popd
}

declare -A pids
start_profile() {
    local duration=$1; shift
    
    for arg in "$@"; do
        echo Start profiling of $arg

        ssh $host "pgrep -f $arg | xargs -I{} sudo py-spy record --duration $duration  --format flamegraph  --output /tmp/$arg-flame.svg --pid {}" &
        pids["$arg"]="$!"
    done
}

wait_profile() {
    echo Waiting profiling end

    for pid in "${pids[@]}"; do
        wait $pid
    done
}

retrieve_profile() {
    local d=$1; shift

    pushd $d

    for arg in "$@"; do
        echo Retrieve profile of $arg

        scp $host:/tmp/$arg-flame.svg .
    done

    popd
}

run() {
    local o=$1

    mkdir -p $o

    # heuristic to define the duration based on request time avg
    # has to be adapted in the future
    duration=$(( 900 * $requests / 1000 + 20 ))

    echo $duration

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

while getopts ":u:n:m:d:a:r:s:o:" option; do
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
        H) header+=("$OPTARG");;
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

    exit -1
fi

# run the bench
run $output

