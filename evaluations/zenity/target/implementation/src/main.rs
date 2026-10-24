use serde_json::{Value, json};
use std::{
    error::Error,
    io::{self, Write},
    process::{Command, ExitCode, Stdio},
};

#[derive(Clone, Debug, Default, PartialEq)]
enum Mode {
    #[default]
    Unselected,
    Entry,
    Question,
    Info,
}

#[derive(Debug, Default, PartialEq)]
struct Options {
    mode: Mode,
    title: String,
    text: String,
    value: String,
    ok: String,
    cancel: String,
}

fn parse(args: &[String]) -> Result<Options, String> {
    let mut options = Options::default();
    let mut args = args.iter();
    while let Some(arg) = args.next() {
        match arg.trim_start_matches('-') {
            mode @ ("entry" | "question" | "info") => {
                options.mode = match mode {
                    "entry" => Mode::Entry,
                    "question" => Mode::Question,
                    _ => Mode::Info,
                };
            }
            key @ ("title" | "text" | "entry-text" | "ok-label" | "cancel-label") => {
                let field = match key {
                    "title" => &mut options.title,
                    "text" => &mut options.text,
                    "entry-text" => &mut options.value,
                    "ok-label" => &mut options.ok,
                    _ => &mut options.cancel,
                };
                *field = args
                    .next()
                    .ok_or_else(|| format!("The {key} option requires a value."))?
                    .clone();
            }
            arg => {
                return Err(format!(
                    "The option is outside the evaluation contract: {arg}"
                ));
            }
        }
    }
    if options.mode == Mode::Unselected {
        return Err("The command requires a dialog mode.".into());
    }
    let (ok, cancel) = if options.mode == Mode::Question {
        ("Yes", "No")
    } else {
        ("OK", "Cancel")
    };
    if options.ok.is_empty() {
        options.ok = ok.into();
    }
    if options.cancel.is_empty() {
        options.cancel = cancel.into();
    }
    Ok(options)
}

fn parameters(options: &Options) -> Value {
    json!({"entry": options.mode == Mode::Entry, "question": options.mode == Mode::Question, "title": options.title, "text": options.text, "value": options.value, "ok": options.ok, "cancel": options.cancel})
}

fn outcome(mode: &Mode, bytes: &[u8]) -> Result<(u8, String), Box<dyn Error>> {
    let (accepted, value): (bool, String) = serde_json::from_slice(bytes)?;
    Ok(if !accepted {
        (1, String::new())
    } else if *mode == Mode::Entry {
        (0, format!("{value}\n"))
    } else {
        (0, String::new())
    })
}

fn show(options: Options) -> Result<(u8, String), Box<dyn Error>> {
    let mut child = Command::new("/usr/bin/osascript")
        .args(["-l", "JavaScript", "-", &parameters(&options).to_string()])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?;
    child
        .stdin
        .take()
        .ok_or("The script input pipe is missing.")?
        .write_all(include_bytes!("../assets/dialog.js"))?;
    let result = child.wait_with_output()?;
    if !result.status.success() {
        return Err(String::from_utf8_lossy(&result.stderr).into_owned().into());
    }
    outcome(&options.mode, &result.stdout)
}

fn main() -> Result<ExitCode, Box<dyn Error>> {
    let options = parse(&std::env::args().skip(1).collect::<Vec<_>>())?;
    let (status, output) = show(options)?;
    io::stdout().lock().write_all(output.as_bytes())?;
    Ok(ExitCode::from(status))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn question_defaults_match_the_observed_buttons() {
        let args = vec!["--question".into(), "--text".into(), "A & B?".into()];
        let options = parse(&args).unwrap();
        assert_eq!(
            [options.ok, options.cancel, options.text],
            ["Yes", "No", "A & B?"]
        );
    }

    #[test]
    fn missing_values_and_modes_fail() {
        assert!(parse(&["--entry".into(), "--title".into()]).is_err());
        assert!(parse(&[]).is_err());
    }

    #[test]
    fn script_results_keep_text_status_and_cancel_semantics() {
        for (mode, reply, expected) in [
            (Mode::Entry, r#"[true,"caf\u00e9\n"]"#, (0, "caf\u{e9}\n\n")),
            (Mode::Entry, r#"[false,"ignored"]"#, (1, "")),
            (Mode::Question, r#"[true,""]"#, (0, "")),
            (Mode::Question, r#"[false,""]"#, (1, "")),
        ] {
            let (status, text) = outcome(&mode, reply.as_bytes()).unwrap();
            assert_eq!((status, text.as_str()), expected);
        }
    }

    #[test]
    fn parameters_preserve_quotes_unicode_and_script_text() {
        let value = "\"\\\n\u{2028}caf\u{e9}'); throw Error('injected');";
        let options = parse(&["--entry".into(), "--entry-text".into(), value.into()]).unwrap();
        let decoded: Value = serde_json::from_str(&parameters(&options).to_string()).unwrap();
        assert_eq!(decoded["value"], value);
    }

    #[test]
    fn malformed_script_results_fail() {
        for data in [b"not json".as_slice(), br#"["yes",""]"#, br#"[true]"#] {
            assert!(outcome(&Mode::Info, data).is_err());
        }
    }
}
