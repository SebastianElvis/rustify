use reqwest::{
    Method, StatusCode, Url,
    blocking::Client,
    header::{HeaderMap, HeaderValue},
    redirect::Policy,
};
use serde_json::{Map, Value};
use std::{env, error::Error, fmt, io::Write, process::ExitCode, time::Duration};

#[derive(Debug)]
enum ClientError {
    Input(String),
    Http(reqwest::Error),
    Json(serde_json::Error),
    Output(std::io::Error),
}

impl fmt::Display for ClientError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Input(message) => formatter.write_str(message),
            Self::Http(error) => error.fmt(formatter),
            Self::Json(error) => error.fmt(formatter),
            Self::Output(error) => error.fmt(formatter),
        }
    }
}

impl Error for ClientError {}

struct Request {
    method: Method,
    url: Url,
    headers: HeaderMap,
    body: Option<Vec<u8>>,
    follow: bool,
    check_status: bool,
}

fn local(url: &Url) -> bool {
    url.scheme() == "http" && url.host_str() == Some("127.0.0.1")
}

fn parse(args: impl IntoIterator<Item = String>) -> Result<Request, ClientError> {
    let mut args = args.into_iter();
    let mut operands = Vec::new();
    let mut raw = None;
    let mut follow = false;
    let mut check_status = true;
    let mut json = false;
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--body" | "-b" | "--pretty=none" | "--ignore-stdin" | "-I" => {}
            "--json" | "-j" => json = true,
            "--follow" | "-F" => follow = true,
            "--no-follow" => follow = false,
            "--check-status" => check_status = true,
            "--no-check-status" => check_status = false,
            _ if arg.starts_with("--raw=") => raw = Some(arg[6..].into()),
            "--raw" => {
                raw = Some(
                    args.next()
                        .ok_or_else(|| ClientError::Input("The raw body is missing.".into()))?,
                );
            }
            _ if arg.starts_with('-') => {
                return Err(ClientError::Input(format!(
                    "The option is outside this evaluation: {arg}"
                )));
            }
            _ => operands.push(arg),
        }
    }
    let explicit_method = operands
        .first()
        .map(|value| value.to_ascii_uppercase())
        .filter(|value| matches!(value.as_str(), "GET" | "HEAD" | "POST"));
    if explicit_method.is_some() {
        operands.remove(0);
    }
    if operands.is_empty() {
        return Err(ClientError::Input("The URL is missing.".into()));
    }
    let url =
        Url::parse(&operands.remove(0)).map_err(|error| ClientError::Input(error.to_string()))?;
    if !local(&url) {
        return Err(ClientError::Input(
            "The URL must use HTTP on 127.0.0.1.".into(),
        ));
    }
    let mut headers = HeaderMap::new();
    let mut fields = Map::new();
    for item in operands {
        let Some((name, value)) = item.split_once([':', '=']) else {
            return Err(ClientError::Input(format!(
                "The request item is invalid: {item}"
            )));
        };
        if item.as_bytes()[name.len()] == b'=' {
            fields.insert(name.into(), Value::String(value.into()));
        } else if let Some(value) = value.strip_prefix('=') {
            fields.insert(
                name.into(),
                serde_json::from_str(value).map_err(ClientError::Json)?,
            );
        } else {
            headers.append(
                reqwest::header::HeaderName::from_bytes(name.as_bytes())
                    .map_err(|error| ClientError::Input(error.to_string()))?,
                value
                    .trim()
                    .parse()
                    .map_err(|error: reqwest::header::InvalidHeaderValue| {
                        ClientError::Input(error.to_string())
                    })?,
            );
        }
    }
    let has_body = raw.is_some() || !fields.is_empty();
    let body = if let Some(raw) = raw {
        Some(raw.into_bytes())
    } else if !fields.is_empty() {
        Some(serde_json::to_vec(&fields).map_err(ClientError::Json)?)
    } else {
        None
    };
    let method = Method::from_bytes(
        explicit_method
            .as_deref()
            .unwrap_or(if has_body { "POST" } else { "GET" })
            .as_bytes(),
    )
    .map_err(|error| ClientError::Input(error.to_string()))?;
    headers
        .entry("user-agent")
        .or_insert(HeaderValue::from_static("xh/0.26.3"));
    headers
        .entry("accept")
        .or_insert(HeaderValue::from_static(if has_body || json {
            "application/json, */*;q=0.5"
        } else {
            "*/*"
        }));
    if has_body || json {
        headers
            .entry("content-type")
            .or_insert(HeaderValue::from_static("application/json"));
    }
    Ok(Request {
        method,
        url,
        headers,
        body,
        follow,
        check_status,
    })
}

fn result_code(status: StatusCode, check: bool) -> u8 {
    if check && status.as_u16() >= 300 {
        (status.as_u16() / 100) as u8
    } else {
        0
    }
}

fn execute(request: Request) -> Result<u8, ClientError> {
    let follow = request.follow;
    let client = Client::builder()
        .no_proxy()
        .timeout(Duration::from_secs(5))
        .redirect(Policy::custom(move |attempt| {
            if follow && local(attempt.url()) && attempt.previous().len() < 10 {
                attempt.follow()
            } else {
                attempt.stop()
            }
        }))
        .build()
        .map_err(ClientError::Http)?;
    let mut builder = client
        .request(request.method, request.url)
        .headers(request.headers);
    if let Some(body) = request.body {
        builder = builder.body(body);
    }
    let response = builder.send().map_err(ClientError::Http)?;
    let status = response.status();
    let body = response.bytes().map_err(ClientError::Http)?;
    std::io::stdout()
        .lock()
        .write_all(&body)
        .map_err(ClientError::Output)?;
    let code = result_code(status, request.check_status);
    if code != 0 {
        eprintln!(
            "xh: warning: HTTP {} {}",
            status.as_u16(),
            status.canonical_reason().unwrap_or("")
        );
    }
    Ok(code)
}

fn main() -> ExitCode {
    let result = parse(env::args().skip(1)).and_then(execute);
    match result {
        Ok(code) => ExitCode::from(code),
        Err(error) => {
            eprintln!("xh: {error}");
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn request(args: &[&str]) -> Request {
        parse(args.iter().map(ToString::to_string)).expect("The test request is valid.")
    }

    #[test]
    fn get_has_no_body() {
        let value = request(&["get", "http://127.0.0.1:1234/echo"]);
        assert_eq!(value.method, Method::GET);
        assert!(value.body.is_none());
    }

    #[test]
    fn json_keeps_field_order_and_types() {
        let value = request(&["http://127.0.0.1:1234/echo", "z=foo:=bar", "a:=2"]);
        assert_eq!(value.method, Method::POST);
        assert_eq!(
            value.body.as_deref(),
            Some(br#"{"z":"foo:=bar","a":2}"#.as_slice())
        );
        assert_eq!(value.headers["content-type"], "application/json");
    }

    #[test]
    fn raw_body_keeps_empty_data() {
        let value = request(&["--raw=", "http://127.0.0.1:1234/echo"]);
        assert_eq!(value.method, Method::POST);
        assert_eq!(value.body, Some(Vec::new()));
    }

    #[test]
    fn custom_headers_override_defaults() {
        let value = request(&[
            "http://127.0.0.1:1234/echo",
            "Accept:text/plain",
            "X-Test:a=b",
            "Hello:world",
            "Hello:people",
        ]);
        assert_eq!(value.headers["accept"], "text/plain");
        assert_eq!(value.headers["x-test"], "a=b");
        assert_eq!(value.headers.get_all("hello").iter().count(), 2);
    }

    #[test]
    fn status_classes_select_exit_codes() {
        for (status, code) in [(200, 0), (302, 3), (404, 4), (500, 5)] {
            let status = StatusCode::from_u16(status).expect("The test status is valid.");
            assert_eq!(result_code(status, true), code);
            assert_eq!(result_code(status, false), 0);
        }
    }

    #[test]
    fn external_urls_fail_before_transport() {
        for url in ["http://example.org/", "https://127.0.0.1/", "http://[::1]/"] {
            assert!(parse([url.to_string()]).is_err());
        }
    }
}
