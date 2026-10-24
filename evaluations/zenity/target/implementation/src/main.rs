use objc2::MainThreadMarker;
use objc2_app_kit::{NSAlert, NSAlertStyle, NSApplication, NSTextField};
use objc2_foundation::{NSPoint, NSRect, NSSize, NSString};
use std::io::{self, Write};
use std::process::ExitCode;

#[derive(Clone, Debug, PartialEq)]
enum Mode {
    Entry,
    Question,
    Info,
    Warning,
    Error,
}

#[derive(Debug, PartialEq)]
struct Options {
    mode: Mode,
    title: String,
    text: String,
    value: String,
    ok: String,
    cancel: String,
}

fn parse(args: &[String]) -> Result<Options, String> {
    let mut options = Options {
        mode: Mode::Info,
        title: String::new(),
        text: String::new(),
        value: String::new(),
        ok: String::new(),
        cancel: String::new(),
    };
    let mut selected = false;
    let mut index = 0;
    while index < args.len() {
        let arg = args[index].trim_start_matches('-');
        match arg {
            "entry" | "question" | "info" | "warning" | "error" => {
                options.mode = match arg {
                    "entry" => Mode::Entry,
                    "question" => Mode::Question,
                    "warning" => Mode::Warning,
                    "error" => Mode::Error,
                    _ => Mode::Info,
                };
                selected = true;
            }
            "title" | "text" | "entry-text" | "ok-label" | "cancel-label" => {
                index += 1;
                let value = args
                    .get(index)
                    .ok_or_else(|| format!("The {arg} option requires a value."))?
                    .clone();
                match arg {
                    "title" => options.title = value,
                    "text" => options.text = value,
                    "entry-text" => options.value = value,
                    "ok-label" => options.ok = value,
                    _ => options.cancel = value,
                }
            }
            _ => {
                return Err(format!(
                    "The option is outside the evaluation contract: {arg}"
                ));
            }
        }
        index += 1;
    }
    if !selected {
        return Err("The command requires a dialog mode.".into());
    }
    if options.ok.is_empty() {
        options.ok = if options.mode == Mode::Question {
            "Yes"
        } else {
            "OK"
        }
        .into();
    }
    if options.cancel.is_empty() {
        options.cancel = if options.mode == Mode::Question {
            "No"
        } else {
            "Cancel"
        }
        .into();
    }
    Ok(options)
}

fn outcome(mode: &Mode, response: isize, value: &str) -> (u8, String) {
    if response != 1000 {
        (1, String::new())
    } else if *mode == Mode::Entry {
        (0, format!("{value}\n"))
    } else {
        (0, String::new())
    }
}

fn show(options: Options) -> (u8, String) {
    let main = MainThreadMarker::new().expect("The dialog requires the main thread.");
    let app = NSApplication::sharedApplication(main);
    app.finishLaunching();
    let alert = NSAlert::new(main);
    alert.setMessageText(&NSString::from_str(&options.text));
    alert.window().setTitle(&NSString::from_str(&options.title));
    alert.setAlertStyle(match options.mode {
        Mode::Error => NSAlertStyle::Critical,
        Mode::Warning => NSAlertStyle::Warning,
        _ => NSAlertStyle::Informational,
    });
    alert.addButtonWithTitle(&NSString::from_str(&options.ok));
    if matches!(options.mode, Mode::Entry | Mode::Question) {
        alert.addButtonWithTitle(&NSString::from_str(&options.cancel));
    }
    let entry = NSTextField::textFieldWithString(&NSString::from_str(&options.value), main);
    entry.setFrame(NSRect::new(
        NSPoint::new(0.0, 0.0),
        NSSize::new(280.0, 24.0),
    ));
    if options.mode == Mode::Entry {
        alert.setAccessoryView(Some(&entry));
        alert.window().setInitialFirstResponder(Some(&entry));
    }
    #[allow(deprecated)]
    app.activateIgnoringOtherApps(true);
    let response = alert.runModal();
    outcome(&options.mode, response, &entry.stringValue().to_string())
}

fn main() -> ExitCode {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let options = match parse(&args) {
        Ok(options) => options,
        Err(error) => {
            eprintln!("{error}");
            return ExitCode::FAILURE;
        }
    };
    let (status, output) = show(options);
    if io::stdout().lock().write_all(output.as_bytes()).is_err() {
        return ExitCode::FAILURE;
    }
    ExitCode::from(status)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn question_defaults_match_the_observed_buttons() {
        let args = vec!["--question".into(), "--text".into(), "A & B?".into()];
        let options = parse(&args).unwrap();
        assert_eq!(
            (options.ok.as_str(), options.cancel.as_str()),
            ("Yes", "No")
        );
        assert_eq!(options.text, "A & B?");
    }

    #[test]
    fn missing_values_and_modes_fail() {
        assert!(parse(&["--entry".into(), "--title".into()]).is_err());
        assert!(parse(&[]).is_err());
    }

    #[test]
    fn entry_results_keep_unicode_and_newlines() {
        assert_eq!(
            outcome(&Mode::Entry, 1000, "caf\u{e9}"),
            (0, "caf\u{e9}\n".into())
        );
        assert_eq!(outcome(&Mode::Entry, 1001, "ignored"), (1, String::new()));
    }

    #[test]
    fn question_results_have_no_output() {
        assert_eq!(outcome(&Mode::Question, 1000, ""), (0, String::new()));
        assert_eq!(outcome(&Mode::Question, 1001, ""), (1, String::new()));
    }
}
