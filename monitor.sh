#!/bin/bash

. ./common.sh

duration=
output=
services=()
headers=()

run() {
    local d=$1
    local o=$2
    
    mkdir -p $o
    
    start_system_monitor $d $o "${services[@]}"
    start_profile $d "${services[@]}"
    
    sleep $d
    
    retrieve_logs $o "${services[@]}"
    wait_profile
    wait_system_monitor
    
    retrieve_profile $o "${services[@]}"
}

while getopts ":a:s:o:d:" option; do
    case "$option" in
        h) host=$OPTARG;;
        a) auth=$OPTARG;;
        s) services+=("$OPTARG");;
        o) output=$OPTARG;;
        d) duration=$OPTARG;;
        :) echo "Option -$OPTARG requires an argument !" >&2;;
        \?) echo "Unsupported option: -$OPTARG !" >&2;;
    esac
done

if [ -z "$duration" ]; [ -z "$output" ]; then
    echo Usage: "$0 -d <duration> -o <output folder name> [options]"
    
    echo -e "\t-h wazo engine hostname, use ssh as root"
    echo -e "\t-a authentication <login:password>"
    echo -e "\t-s service to monitor, can be used multiple times"
    echo -e "\t-o output folder name"
    
    exit -1
fi

# run the bench
run $duration $output

