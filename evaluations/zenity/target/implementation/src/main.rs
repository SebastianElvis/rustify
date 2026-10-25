use serde_json::{Value, json};
use std::{
    error::Error,
    fs::File,
    io::{self, Seek, Write},
    os::unix::process::CommandExt,
    process::{Command, Stdio},
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

fn parameters(o: &Options) -> Value {
    match o.mode {
        Mode::Entry => {
            json!({"operation":"displayDialog","text":o.text,"options":{"withTitle":o.title,"defaultAnswer":o.value,"buttons":[o.cancel,o.ok],"defaultButton":2,"cancelButton":1}})
        }
        Mode::Question => {
            json!({"operation":"displayAlert","text":o.title,"options":{"message":o.text,"buttons":[o.cancel,o.ok],"defaultButton":2,"cancelButton":1}})
        }
        Mode::Info => {
            json!({"operation":"displayAlert","text":o.title,"options":{"message":o.text,"as":"informational","buttons":[o.ok],"defaultButton":1}})
        }
        Mode::Unselected => unreachable!("The parser requires a dialog mode."),
    }
}

fn program(options: &Options) -> String {
    let data = parameters(options)
        .to_string()
        .replace('\u{2028}', "\\u2028")
        .replace('\u{2029}', "\\u2029");
    format!("var p = {data};\n{}", include_str!("../assets/dialog.js"))
}

fn script_file(options: &Options) -> io::Result<File> {
    let mut file = tempfile::tempfile()?;
    file.write_all(program(options).as_bytes())?;
    file.rewind()?;
    Ok(file)
}

fn main() -> Result<(), Box<dyn Error>> {
    let options = parse(&std::env::args().skip(1).collect::<Vec<_>>())?;
    Err(Command::new("/usr/bin/osascript")
        .args(["-l", "JavaScript"])
        .env_clear()
        .stdin(script_file(&options)?)
        .stderr(Stdio::null())
        .exec()
        .into())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn question_defaults_match_the_observed_buttons() {
        let options = parse(&["--question".into(), "--text".into(), "A & B?".into()]).unwrap();
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
    fn parameters_preserve_the_original_dialog_protocol() {
        for (flag, operation, buttons) in [
            ("--entry", "displayDialog", vec!["Cancel", "OK"]),
            ("--question", "displayAlert", vec!["No", "Yes"]),
            ("--info", "displayAlert", vec!["OK"]),
        ] {
            let p = parameters(&parse(&[flag.into()]).unwrap());
            assert_eq!(p["operation"], operation);
            assert_eq!(p["options"]["buttons"], json!(buttons));
            assert_eq!(p["options"]["defaultButton"], buttons.len());
        }
    }

    #[test]
    fn parameters_preserve_quotes_unicode_and_script_text() {
        let value = "\"\\\n\u{2028}caf\u{e9}'); throw Error('injected');";
        let options = parse(&["--entry".into(), "--entry-text".into(), value.into()]).unwrap();
        let script = program(&options);
        let data = script.strip_prefix("var p = ").unwrap();
        let (data, _) = data.split_once(";\n").unwrap();
        let decoded: Value = serde_json::from_str(data).unwrap();
        assert_eq!(decoded["options"]["defaultAnswer"], value);
        assert!(!data.contains(['\u{2028}', '\u{2029}']));
    }

    #[test]
    fn script_file_starts_at_the_complete_program() {
        let options = parse(&["--info".into(), "--text".into(), "a\nb".into()]).unwrap();
        assert_eq!(
            io::read_to_string(script_file(&options).unwrap()).unwrap(),
            program(&options)
        );
    }
}
