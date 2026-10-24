use std::env;
use std::ffi::OsString;
use std::fs::File;
use std::io::{self, BufWriter, Read, Write};
use std::os::fd::AsFd;
use std::os::unix::ffi::{OsStrExt, OsStringExt};

const ALPHABET: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

#[derive(Debug, PartialEq)]
struct Diagnostic {
    message: Vec<u8>,
    usage: bool,
}

impl Diagnostic {
    fn new(message: impl AsRef<[u8]>, usage: bool) -> Self {
        Self {
            message: message.as_ref().to_vec(),
            usage,
        }
    }
}

#[derive(Debug, PartialEq)]
enum Action {
    Help,
    Version,
    Run {
        decode: bool,
        ignore: bool,
        wrap: usize,
        file: OsString,
    },
}

fn escape(byte: u8) -> String {
    match byte {
        b'\x07' => "\\a".into(),
        b'\x08' => "\\b".into(),
        b'\x0c' => "\\f".into(),
        b'\n' => "\\n".into(),
        b'\r' => "\\r".into(),
        b'\t' => "\\t".into(),
        b'\x0b' => "\\v".into(),
        b'\\' => "\\\\".into(),
        b'\'' => "\\'".into(),
        32..=126 => char::from(byte).to_string(),
        _ => format!("\\{byte:03o}"),
    }
}

fn quote(bytes: &[u8]) -> String {
    format!("'{}'", bytes.iter().map(|&b| escape(b)).collect::<String>())
}

fn file_quote(bytes: &[u8]) -> String {
    if !bytes.is_empty()
        && bytes != b"{"
        && bytes != b"}"
        && bytes.iter().enumerate().all(|(i, &b)| {
            b.is_ascii_alphanumeric()
                || b"_./-+,@%]}{".contains(&b)
                || (i > 0 && b"#~".contains(&b))
        })
    {
        return String::from_utf8_lossy(bytes).into_owned();
    }
    if bytes.contains(&b'\'')
        && bytes
            .iter()
            .all(|b| (32..=126).contains(b) && !b"\"$`\\".contains(b))
    {
        return format!("\"{}\"", String::from_utf8_lossy(bytes));
    }
    let mut result = String::from("'");
    let mut control = false;
    for &byte in bytes {
        let next_control = !(32..=126).contains(&byte);
        if control != next_control {
            result.push_str(if next_control { "'$'" } else { "''" });
            control = next_control;
        }
        if control {
            result.push_str(&escape(byte));
        } else if byte == b'\'' {
            result.push_str("'\\''");
        } else {
            result.push(char::from(byte));
        }
    }
    result.push('\'');
    result
}

fn wrap_size(bytes: &[u8]) -> Option<usize> {
    let start = bytes.iter().position(|b| !matches!(b, b' ' | 9..=13))?;
    let mut digits = &bytes[start..];
    let negative = digits[0] == b'-';
    if matches!(digits[0], b'+' | b'-') {
        digits = &digits[1..];
    }
    if digits.is_empty() || !digits.iter().all(u8::is_ascii_digit) {
        return None;
    }
    let value = digits.iter().try_fold(0u64, |n, &b| {
        n.checked_mul(10)?.checked_add(u64::from(b - b'0'))
    });
    match (negative, value) {
        (true, Some(0)) => Some(0),
        (true, _) => None,
        (false, Some(n)) if n <= i64::MAX as u64 => Some(n as usize),
        (false, _) => Some(0),
    }
}

fn parse(args: &[OsString], posix: bool) -> Result<Action, Diagnostic> {
    let mut decode = false;
    let mut ignore = false;
    let mut wrap = 76;
    let mut operands = Vec::new();
    let mut options = true;
    let mut index = 0;
    while index < args.len() {
        let arg = args[index].as_bytes();
        if options && arg == b"--" {
            options = false;
        } else if options && arg.starts_with(b"--") {
            let split = arg.iter().position(|&b| b == b'=');
            let name = &arg[2..split.unwrap_or(arg.len())];
            let choices = ["decode", "wrap", "ignore-garbage", "help", "version"];
            let matching: Vec<_> = choices
                .iter()
                .filter(|s| s.as_bytes().starts_with(name))
                .collect();
            if matching.len() != 1 {
                let message = if matching.is_empty() {
                    [b"unrecognized option '", arg, b"'"].concat()
                } else {
                    [
                        b"option '",
                        arg,
                        b"' is ambiguous; possibilities:",
                        choices
                            .iter()
                            .map(|s| format!(" '--{s}'"))
                            .collect::<String>()
                            .as_bytes(),
                    ]
                    .concat()
                };
                return Err(Diagnostic::new(message, true));
            }
            let option = *matching[0];
            if option != "wrap" && split.is_some() {
                return Err(Diagnostic::new(
                    format!("option '--{option}' doesn't allow an argument"),
                    true,
                ));
            }
            match option {
                "help" => return Ok(Action::Help),
                "version" => return Ok(Action::Version),
                "decode" => decode = true,
                "ignore-garbage" => ignore = true,
                _ => {
                    let value = if let Some(at) = split {
                        &arg[at + 1..]
                    } else {
                        index += 1;
                        args.get(index)
                            .ok_or_else(|| {
                                Diagnostic::new("option '--wrap' requires an argument", true)
                            })?
                            .as_bytes()
                    };
                    wrap = wrap_size(value).ok_or_else(|| {
                        Diagnostic::new(format!("invalid wrap size: {}", quote(value)), false)
                    })?;
                }
            }
        } else if options && arg.len() > 1 && arg[0] == b'-' {
            let mut at = 1;
            while at < arg.len() {
                match arg[at] {
                    b'd' => decode = true,
                    b'i' => ignore = true,
                    b'w' => {
                        let value = if at + 1 < arg.len() {
                            &arg[at + 1..]
                        } else {
                            index += 1;
                            args.get(index)
                                .ok_or_else(|| {
                                    Diagnostic::new("option requires an argument -- 'w'", true)
                                })?
                                .as_bytes()
                        };
                        wrap = wrap_size(value).ok_or_else(|| {
                            Diagnostic::new(format!("invalid wrap size: {}", quote(value)), false)
                        })?;
                        break;
                    }
                    b => {
                        return Err(Diagnostic::new(
                            [b"invalid option -- '".as_slice(), &[b], b"'"].concat(),
                            true,
                        ));
                    }
                }
                at += 1;
            }
        } else {
            operands.push(args[index].clone());
            if posix {
                options = false;
            }
        }
        index += 1;
    }
    if operands.len() > 1 {
        return Err(Diagnostic::new(
            format!("extra operand {}", quote(operands[1].as_bytes())),
            true,
        ));
    }
    Ok(Action::Run {
        decode,
        ignore,
        wrap,
        file: operands.into_iter().next().unwrap_or_else(|| "-".into()),
    })
}

fn value(byte: u8) -> Option<u8> {
    match byte {
        b'A'..=b'Z' => Some(byte - b'A'),
        b'a'..=b'z' => Some(byte - b'a' + 26),
        b'0'..=b'9' => Some(byte - b'0' + 52),
        b'+' => Some(62),
        b'/' => Some(63),
        _ => None,
    }
}

#[derive(Debug)]
enum ProcessError {
    Read(io::Error),
    Write(io::Error),
    Invalid,
}

fn encode(input: &mut dyn Read, output: &mut dyn Write, wrap: usize) -> Result<(), ProcessError> {
    let mut buffer = [0; 30720];
    let mut quantum = [0; 3];
    let mut used = 0;
    let mut column = 0;
    loop {
        let count = input.read(&mut buffer).map_err(ProcessError::Read)?;
        for &byte in &buffer[..count] {
            quantum[used] = byte;
            used += 1;
            if used == 3 {
                write_quantum(&quantum, used, output, wrap, &mut column)?;
                used = 0;
            }
        }
        if count == 0 {
            break;
        }
    }
    if used > 0 {
        quantum[used..].fill(0);
        write_quantum(&quantum, used, output, wrap, &mut column)?;
    }
    if wrap != 0 && column > 0 {
        output.write_all(b"\n").map_err(ProcessError::Write)?;
    }
    Ok(())
}

fn write_quantum(
    q: &[u8; 3],
    used: usize,
    output: &mut dyn Write,
    wrap: usize,
    column: &mut usize,
) -> Result<(), ProcessError> {
    let encoded = [
        ALPHABET[(q[0] >> 2) as usize],
        ALPHABET[((q[0] & 3) << 4 | q[1] >> 4) as usize],
        if used > 1 {
            ALPHABET[((q[1] & 15) << 2 | q[2] >> 6) as usize]
        } else {
            b'='
        },
        if used > 2 {
            ALPHABET[(q[2] & 63) as usize]
        } else {
            b'='
        },
    ];
    for byte in encoded {
        output.write_all(&[byte]).map_err(ProcessError::Write)?;
        if wrap != 0 {
            *column += 1;
            if *column == wrap {
                output.write_all(b"\n").map_err(ProcessError::Write)?;
                *column = 0;
            }
        }
    }
    Ok(())
}

fn decode(input: &mut dyn Read, output: &mut dyn Write, ignore: bool) -> Result<(), ProcessError> {
    let mut buffer = [0; 4096];
    let mut position = 0;
    let mut previous = 0;
    let mut padding = false;
    loop {
        let count = input.read(&mut buffer).map_err(ProcessError::Read)?;
        if count == 0 {
            break;
        }
        for &byte in &buffer[..count] {
            if byte == b'\n' || (ignore && value(byte).is_none() && byte != b'=') {
                continue;
            }
            if byte == b'=' {
                if position == 2 && previous & 15 == 0 {
                    padding = true;
                } else if position == 3 && (padding || previous & 3 == 0) {
                    padding = false;
                } else {
                    return Err(ProcessError::Invalid);
                }
            } else {
                let next = value(byte)
                    .filter(|_| !padding)
                    .ok_or(ProcessError::Invalid)?;
                if position > 0 {
                    let decoded = previous << (position * 2) | next >> (6 - position * 2);
                    output.write_all(&[decoded]).map_err(ProcessError::Write)?;
                }
                previous = next;
            }
            position = (position + 1) % 4;
        }
    }
    match position {
        0 => Ok(()),
        2 if previous & 15 == 0 => Ok(()),
        3 if !padding && previous & 3 == 0 => Ok(()),
        _ => Err(ProcessError::Invalid),
    }
}

fn io_text(error: &io::Error) -> String {
    let text = error.to_string();
    text.split(" (os error ").next().unwrap_or(&text).into()
}

fn execute(action: Action, name: &[u8], output: &mut dyn Write) -> Result<(), Diagnostic> {
    match action {
        Action::Help => {
            let help = [b"Usage: ", name, &include_bytes!("help.txt")[13..]].concat();
            output
                .write_all(&help)
                .map_err(|e| Diagnostic::new(format!("write error: {}", io_text(&e)), false))?;
        }
        Action::Version => output
            .write_all(include_bytes!("version.txt"))
            .map_err(|e| Diagnostic::new(format!("write error: {}", io_text(&e)), false))?,
        Action::Run {
            decode: decoding,
            ignore,
            wrap,
            file,
        } => {
            let mut input: Box<dyn Read> = if file == "-" {
                Box::new(io::stdin().lock())
            } else {
                Box::new(File::open(&file).map_err(|e| {
                    Diagnostic::new(
                        format!("{}: {}", file_quote(file.as_bytes()), io_text(&e)),
                        false,
                    )
                })?)
            };
            let result = if decoding {
                decode(&mut input, output, ignore)
            } else {
                encode(&mut input, output, wrap)
            };
            result.map_err(|error| {
                Diagnostic::new(
                    match error {
                        ProcessError::Invalid => "invalid input".into(),
                        ProcessError::Read(e) => format!("read error: {}", io_text(&e)),
                        ProcessError::Write(e) => format!("write error: {}", io_text(&e)),
                    },
                    false,
                )
            })?;
        }
    }
    Ok(())
}

fn main() {
    let mut args = env::args_os();
    let original_name = args.next().unwrap_or_else(|| "base64".into()).into_vec();
    let name = if original_name.windows(7).any(|w| w == b"/.libs/") {
        let base = original_name
            .rsplit(|&b| b == b'/')
            .next()
            .unwrap_or(&original_name);
        base.strip_prefix(b"lt-").unwrap_or(base)
    } else {
        &original_name
    };
    let mut output = BufWriter::new(File::from(
        io::stdout()
            .as_fd()
            .try_clone_to_owned()
            .expect("The command cannot duplicate stdout."),
    ));
    let result = parse(
        &args.collect::<Vec<_>>(),
        env::var_os("POSIXLY_CORRECT").is_some(),
    )
    .and_then(|action| execute(action, name, &mut output));
    let flushed = output
        .flush()
        .map_err(|e| Diagnostic::new(format!("write error: {}", io_text(&e)), false));
    let mut errors = vec![result.err(), flushed.err()];
    errors.dedup();
    let failed = errors.iter().any(Option::is_some);
    for error in errors.into_iter().flatten() {
        let mut stderr = io::stderr().lock();
        let _ = stderr.write_all(&original_name);
        let _ = stderr.write_all(&[b": ", error.message.as_slice(), b"\n"].concat());
        if error.usage {
            let _ = stderr.write_all(b"Try '");
            let _ = stderr.write_all(name);
            let _ = stderr.write_all(b" --help' for more information.\n");
        }
    }
    if failed {
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn standard_vectors() {
        for (plain, encoded) in [
            ("", ""),
            ("f", "Zg=="),
            ("fo", "Zm8="),
            ("foo", "Zm9v"),
            ("foob", "Zm9vYg=="),
            ("fooba", "Zm9vYmE="),
            ("foobar", "Zm9vYmFy"),
        ] {
            let mut actual = Vec::new();
            encode(&mut plain.as_bytes(), &mut actual, 0).unwrap();
            assert_eq!(actual, encoded.as_bytes());
            actual.clear();
            decode(&mut encoded.as_bytes(), &mut actual, false).unwrap();
            assert_eq!(actual, plain.as_bytes());
        }
    }

    #[test]
    fn invalid_partial_output() {
        for (input, expected) in [
            ("Y", ""),
            ("YW", "a"),
            ("YWJ", "ab"),
            ("YR==", "a"),
            ("YWK=", "ab"),
            ("YQ=A", "a"),
            ("YQ===", "a"),
        ] {
            let mut actual = Vec::new();
            assert!(matches!(
                decode(&mut input.as_bytes(), &mut actual, false),
                Err(ProcessError::Invalid)
            ));
            assert_eq!(actual, expected.as_bytes());
        }
    }

    #[test]
    fn concatenation_and_filtering() {
        let mut actual = Vec::new();
        decode(&mut &b"YQ=\n=Yg=="[..], &mut actual, false).unwrap();
        assert_eq!(actual, b"ab");
        actual.clear();
        decode(&mut &b"!Y\tQ\r==\xff"[..], &mut actual, true).unwrap();
        assert_eq!(actual, b"a");
    }

    #[test]
    fn wrap_boundaries() {
        for (width, expected) in [
            (0, "YWJjZA=="),
            (1, "Y\nW\nJ\nj\nZ\nA\n=\n=\n"),
            (3, "YWJ\njZA\n==\n"),
            (4, "YWJj\nZA==\n"),
            (76, "YWJjZA==\n"),
        ] {
            let mut actual = Vec::new();
            encode(&mut &b"abcd"[..], &mut actual, width).unwrap();
            assert_eq!(actual, expected.as_bytes());
        }
    }

    #[test]
    fn wrap_numbers() {
        for (value, expected) in [
            ("0", Some(0)),
            ("-0", Some(0)),
            (" +3", Some(3)),
            ("-1", None),
            ("1 ", None),
            ("1k", None),
            ("9223372036854775808", Some(0)),
            ("", None),
        ] {
            assert_eq!(wrap_size(value.as_bytes()), expected);
        }
    }

    #[test]
    fn parsing_order() {
        let args = |a: &[&str]| a.iter().map(OsString::from).collect::<Vec<_>>();
        assert_eq!(parse(&args(&["file", "--help"]), false), Ok(Action::Help));
        assert!(parse(&args(&["file", "--help"]), true).is_err());
        assert!(parse(&args(&["--bad", "--help"]), false).is_err());
        assert_eq!(parse(&args(&["--h"]), false), Ok(Action::Help));
    }

    #[test]
    fn byte_roundtrip_and_chunk_edges() {
        for length in [1, 2, 3, 4095, 4096, 4097, 30719, 30720, 30721, 65536] {
            let plain: Vec<_> = (0..length).map(|n| n as u8).collect();
            let mut encoded = Vec::new();
            encode(&mut plain.as_slice(), &mut encoded, 76).unwrap();
            let mut decoded = Vec::new();
            decode(&mut encoded.as_slice(), &mut decoded, false).unwrap();
            assert_eq!(plain, decoded);
        }
    }

    #[test]
    fn missing_padding_uses_zero_bits() {
        for input in ["YQ", "YQA", "YQ==Yg", "YQ\n", "YQ\n="] {
            let mut output = Vec::new();
            let result = decode(&mut input.as_bytes(), &mut output, false);
            assert_eq!(result.is_ok(), input != "YQ\n=");
        }
    }

    #[test]
    fn short_reads_preserve_quanta() {
        struct Short<'a>(&'a [u8]);
        impl Read for Short<'_> {
            fn read(&mut self, buffer: &mut [u8]) -> io::Result<usize> {
                self.0.read(&mut buffer[..1])
            }
        }
        let plain = b"abcde";
        let mut encoded = Vec::new();
        encode(&mut Short(plain), &mut encoded, 0).unwrap();
        assert_eq!(encoded, b"YWJjZGU=");
        let mut decoded = Vec::new();
        decode(&mut Short(&encoded), &mut decoded, false).unwrap();
        assert_eq!(decoded, plain);
    }

    #[test]
    fn quotes() {
        assert_eq!(quote(b"a'\n"), "'a\\'\\n'");
        assert_eq!(file_quote(b"a:b"), "'a:b'");
        assert_eq!(file_quote(b"a\nb"), "'a'$'\\n''b'");
        assert_eq!(file_quote(b"a'b"), "\"a'b\"");
    }
}
