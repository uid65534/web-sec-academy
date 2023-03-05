Scripts & notes written in various languages to solve labs at PortSwigger's [Web Security Academy](https://portswigger.net/web-security)

# SQL Injection

## Blind
### [Blind SQL injection with conditional errors](https://github.com/uid65534/web-sec-academy/tree/master/lab/sqli/blind/conditional-errors)
Determines the length of the target password using a binary search, then simultaneously performs a binary search of ASCII space for each character to quickly determine the password.
### [Blind SQL injection with time delays and information retrieval](https://github.com/uid65534/web-sec-academy/tree/master/lab/sqli/blind/time-delays-info-retrieval)
Performs the same process as above, but measures the response times to determine the result.

# Logic flaws
### [Infinite money logic flaw](https://github.com/uid65534/web-sec-academy/tree/master/lab/logic-flaws/examples/logic-flaws-infinite-money)
Automates the process of adding gift cards to your cart, applying the discount coupon, purchasing and redeeming the gift cards until you have enough funds to purchase the target product.

# Authentication

## Multi-factor
### [2FA bypass using a brute-force attack](https://github.com/uid65534/web-sec-academy/tree/master/lab/authentication/multi-factor/2fa-bypass-using-a-brute-force-attack)
Automates the lab by logging into the target account and enumerating MFA codes with multiple simultaneous login sessions to speed up the process.

## Other mechanisms
### [Password brute-force via password change](https://github.com/uid65534/web-sec-academy/tree/master/lab/authentication/other-mechanisms/password-brute-force-via-password-change)
A shell script that enumerates passwords via the exploit using `ffuf`.

# OAuth
### [Stealing OAuth access tokens via a proxy page](github.com/uid65534/web-sec-academy/tree/master/lab/oauth/oauth-stealing-oauth-access-tokens-via-a-proxy-page)

# Deserialization

### [Developing a custom gadget chain for Java deserialization](https://github.com/uid65534/web-sec-academy/tree/master/lab/deserialization/developing-a-custom-gadget-chain-for-java-deserialization)
Contains a shell script that builds the payload generator, generates a payload using SQL from the command line arguments, then sends a web request to execute the payload and outputs the result.
