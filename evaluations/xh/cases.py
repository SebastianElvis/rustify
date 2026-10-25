"""Define the loopback HTTP cases and the compared request fields."""


def cases(url):
    rows = [
        ("get-text", [url + "/text"]),
        ("get-json", [url + "/json"]),
        ("get-query", [url + "/echo?q=two%20words&n=2"]),
        ("head", ["HEAD", url + "/echo"]),
        ("empty-post", ["POST", url + "/echo"]),
        ("json-fields", ["POST", url + "/echo", "hello=world", "count:=2"]),
        ("json-types", ["POST", url + "/echo", "active:=true", "items:=[1,2]", "value:=null"]),
        ("json-order", ["POST", url + "/echo", "z=last", "a=first"]),
        ("json-replace", ["POST", url + "/echo", "a=first", "a=last"]),
        ("inferred-post", [url + "/echo", "hello=world"]),
        ("raw-post", ["POST", url + "/echo", "--raw", "plain text"]),
        ("raw-empty", [url + "/echo", "--raw", ""]),
        ("json-get", ["--json", url + "/echo"]),
        ("custom-header", [url + "/echo", "X-Test:two words"]),
        ("header-equals", [url + "/echo", "X-Test:a=b"]),
        ("string-operator", [url + "/echo", "a=foo:=bar"]),
        ("custom-accept", [url + "/echo", "Accept:text/plain"]),
        ("custom-content-type", ["POST", url + "/echo", "--raw", "hello", "Content-Type:text/plain"]),
        ("redirect-stop", [url + "/redirect/302"]),
        ("redirect-follow", ["--follow", url + "/redirect/302"]),
        ("post-302", ["--follow", "POST", url + "/redirect/302", "hello=world"]),
        ("post-303", ["--follow", "POST", url + "/redirect/303", "hello=world"]),
        ("post-307", ["--follow", "POST", url + "/redirect/307", "hello=world"]),
        ("status-404", [url + "/status/404"]),
        ("status-500", [url + "/status/500"]),
        ("status-ignore", ["--no-check-status", url + "/status/404"]),
    ]
    return [{"id": identity, "args": ["--body", "--pretty=none", "--ignore-stdin", *args]} for identity, args in rows]


def protocol(requests):
    selected = {"accept", "content-type", "x-test", "user-agent"}
    return [{
        "method": request["method"],
        "path": request["path"],
        "body_b64": request["body_b64"],
        "headers": {name.lower(): value for name, value in request["headers"] if name.lower() in selected},
    } for request in requests]

