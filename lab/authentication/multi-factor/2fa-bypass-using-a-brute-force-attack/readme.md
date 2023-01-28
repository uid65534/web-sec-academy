# [2FA bypass using a brute-force attack](https://portswigger.net/web-security/authentication/multi-factor/lab-2fa-bypass-using-a-brute-force-attack)

Automates the lab by logging into the target account and enumerating MFA codes.\

Uses multiple simultaneous login sessions to speed up the process.\
Each task sends one initial `GET /login` request to obtain a session ID and CSRF token.\
Then logs in with `POST /login` and obtains the CSRF token tied to the new session with `GET /login2`.\
Submits MFA verification attempts with `POST /login2`. Only repeats the login process when this results in the session being invalidated.

A note from the solution at the web security academy:
> As the verification code will reset while you're running your attack, you may need to repeat this attack several times before you succeed. This is because the new code may be a number that your current Intruder attack has already attempted.

### Usage

`dotnet script solve.csx -- lab-id`

### Requirements

Requires the .NET SDK and dotnet-script to run.

To install dotnet-script globally:\
`dotnet tool install -g dotnet-script`
