#!/bin/bash

host=${WAZO_HOST:-wazo}
services=()

declare -A top_pids
start_system_monitor() {
    local d=$1; shift
    local o=$1; shift
    
    for arg in "$@"; do
        echo Start monitoring $arg
        
        pid=$( ssh $ssh_host "pgrep $arg" )
        num=$(( $d * 2 ))

        ssh $ssh_host "top -b -n $num -d 0.5 -p $pid | grep $pid | sed 's/,/./' | awk '{print ((NR+1)/2)\",\"\$6\",\"\$9}'" > $o/$arg-sys.csv &
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
        
        ssh $ssh_host "sudo truncate -s 0 /var/log/$arg.log"
    done
    
    ssh $ssh_host "sudo truncate -s 0 /var/log/postgresql/postgresql-*-main.log"
}

retrieve_logs() {
    local d=$1; shift
    
    pushd $d
    
    for arg in "$@"; do
        echo Retrieve log of $arg
        
        scp $ssh_host:/var/log/$arg.log .
        
        python ../flask.py $arg.log
        cat $arg-req.log | python ../detokenize.py >  $arg-notok.log
        
        # generate goaccess
        goaccess -o goaccess.html --date-format '%Y-%m-%d' \
        --time-format '%H:%M:%S'  --log-format '%d %t,%^ %m %U %h %s %L' *-notok.log
    done
    
    ssh $ssh_host "sudo cat /var/log/postgresql/postgresql-*-main.log" > postgresql.log
    
    popd
}

declare -A pids
start_profile() {
    local duration=$1; shift
    
    for arg in "$@"; do
        echo Start profiling of $arg
        
        ssh $ssh_host "pgrep -f $arg | xargs -I{} sudo py-spy record --duration $duration  --format flamegraph  --output /tmp/$arg-flame.svg --pid {}" &
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
        
        scp $ssh_host:/tmp/$arg-flame.svg .
    done
    
    popd
}