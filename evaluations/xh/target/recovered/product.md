# Recovered product

xh sends HTTP requests from a command line.
The observed version is 0.26.3.
The original source stays hidden during this reconstruction.

| Feature | Observed rule | Evidence |
| --- | --- | --- |
| HTTP-01 | A URL without data selects GET. | `runtime-probes.json:get` |
| HTTP-02 | An explicit HEAD request produces no body. | `runtime-probes.json:head` |
| HTTP-03 | Data fields select POST when the method is absent. | `runtime-probes.json:json-inferred-post` |
| HTTP-04 | `name=value` creates a JSON string field. `name:=value` creates a typed JSON field. | `runtime-probes.json:json-fields` |
| HTTP-05 | `--raw` sends literal request bytes. | `runtime-probes.json:raw-post` |
| HTTP-06 | `Name:value` sets a request header. | `runtime-probes.json:header` |
| HTTP-07 | A redirect stays unfollowed unless `--follow` is present. | `runtime-probes.json:redirect,follow` |
| HTTP-08 | A followed 302 changes POST to GET. A followed 307 preserves POST and its body. | `runtime-probes.json:post-follow-302,post-follow-307` |
| HTTP-09 | Status classes 3xx, 4xx, and 5xx return codes 3, 4, and 5. | `runtime-probes.json:redirect,status404,status500` |
| HTTP-10 | `--no-check-status` suppresses HTTP failure warnings and returns success. | `runtime-probes.json:status404-ignore` |

The inferred product goal is convenient HTTP inspection.
The evidence does not establish the creators' intent or roadmap.
The contract limits this evaluation to loopback HTTP.
