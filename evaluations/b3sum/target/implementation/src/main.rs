use std::fs::File;
use std::io::{self, BufRead, BufReader, Read, Write};
use std::process::ExitCode;

#[derive(Default)]
enum Mode {
    #[default]
    Hash,
    Keyed,
    Derive(String),
}

#[derive(Default)]
struct Options {
    mode: Mode,
    length: u64,
    seek: u64,
    raw: bool,
    no_names: bool,
    tag: bool,
    check: bool,
    quiet: bool,
    files: Vec<String>,
}

fn options() -> Result<Option<Options>, String> {
    let mut options = Options {
        length: 32,
        ..Options::default()
    };
    let mut args = std::env::args().skip(1);
    let mut positional = false;
    while let Some(arg) = args.next() {
        let (flag, attached) = arg
            .split_once('=')
            .map_or((arg.as_str(), None), |(a, b)| (a, Some(b)));
        if positional {
            options.files.push(arg);
            continue;
        }
        match flag {
            "--" => positional = true,
            "-h" | "--help" => {
                print!("{}", include_str!("../help.txt"));
                return Ok(None);
            }
            "-V" | "--version" => {
                println!("b3sum 1.8.7");
                return Ok(None);
            }
            "--keyed" => options.mode = Mode::Keyed,
            "--derive-key" => {
                options.mode = Mode::Derive(
                    attached
                        .map(str::to_owned)
                        .or_else(|| args.next())
                        .ok_or("A context is required.")?,
                )
            }
            "-l" | "--length" | "--seek" | "--num-threads" => {
                let value = attached
                    .map(str::to_owned)
                    .or_else(|| args.next())
                    .ok_or("A number is required.")?;
                let number = value
                    .parse::<u64>()
                    .map_err(|_| "A number must be nonnegative.")?;
                match flag {
                    "--seek" => options.seek = number,
                    "--num-threads" => (),
                    _ => options.length = number,
                }
            }
            "--raw" => options.raw = true,
            "--no-names" => options.no_names = true,
            "--tag" => options.tag = true,
            "-c" | "--check" => options.check = true,
            "--quiet" => options.quiet = true,
            "--no-mmap" => (),
            _ if !arg.starts_with('-') || arg == "-" => options.files.push(arg),
            _ if arg.starts_with("-l") => {
                options.length = arg[2..]
                    .parse()
                    .map_err(|_| "A number must be nonnegative.")?
            }
            _ => return Err(format!("Unsupported option: {arg}")),
        }
    }
    if options.raw && options.files.len() > 1 {
        return Err("Only one filename can be provided when using --raw".into());
    }
    if options.files.is_empty() {
        options.files.push("-".into());
    }
    Ok(Some(options))
}

fn input(path: &str) -> io::Result<Box<dyn Read>> {
    if path == "-" {
        Ok(Box::new(io::stdin()))
    } else {
        Ok(Box::new(File::open(path)?))
    }
}

fn hash_input(path: &str, initial: &blake3::Hasher, seek: u64) -> io::Result<blake3::OutputReader> {
    let mut hasher = initial.clone();
    io::copy(&mut input(path)?, &mut hasher)?;
    let mut reader = hasher.finalize_xof();
    reader.set_position(seek);
    Ok(reader)
}

fn escaped_name(name: &str) -> (bool, String) {
    let escaped = name
        .replace('\\', "\\\\")
        .replace('\n', "\\n")
        .replace('\r', "\\r");
    (escaped != name, escaped)
}

fn parse_check_line(line: &str) -> Result<(String, blake3::Hash, String), &'static str> {
    if line.is_empty() {
        return Err("Empty line");
    }
    let (escaped, line) = line.strip_prefix('\\').map_or((false, line), |s| (true, s));
    let (hex, name) = if let Some(parts) = line.split_once("  ") {
        parts
    } else if let Some(tagged) = line.strip_prefix("BLAKE3 (") {
        let (name, hex) = tagged
            .rsplit_once(") = ")
            .ok_or("Invalid check line format")?;
        (hex, name)
    } else {
        return Err("Invalid check line format");
    };
    if hex.len() != 64 {
        return Err("Invalid hash length");
    }
    if hex.bytes().any(|c| c.is_ascii_uppercase()) {
        return Err("Invalid hex");
    }
    let expected = blake3::Hash::from_hex(hex).map_err(|_| "Invalid hex")?;
    let mut path = String::new();
    let mut chars = name.chars();
    while let Some(c) = chars.next() {
        path.push(if escaped && c == '\\' {
            match chars.next() {
                Some('n') => '\n',
                Some('r') => '\r',
                Some('\\') => '\\',
                _ => return Err("Invalid backslash escape"),
            }
        } else {
            c
        });
    }
    match () {
        _ if path.is_empty() => return Err("empty file path"),
        _ if path.contains('\0') => return Err("Null character in path"),
        _ if path.contains('\u{fffd}') => return Err("Unicode replacement character in path"),
        _ => (),
    }
    let display = format!("{}{name}", if escaped { "\\" } else { "" });
    Ok((path, expected, display))
}

fn checks(path: &str, options: &Options, hasher: &blake3::Hasher) -> io::Result<u64> {
    let mut failures = 0;
    for line in BufReader::new(input(path)?).lines() {
        let line = line?;
        let (name, expected, display) = match parse_check_line(line.trim_end_matches('\r')) {
            Ok(value) => value,
            Err(error) => {
                eprintln!("b3sum: {error}");
                failures += 1;
                continue;
            }
        };
        match hash_input(&name, hasher, 0) {
            Ok(mut reader) => {
                let mut actual = [0; 32];
                reader.fill(&mut actual);
                if blake3::Hash::from(actual) == expected {
                    if !options.quiet {
                        println!("{display}: OK");
                    }
                } else {
                    println!("{display}: FAILED");
                    failures += 1;
                }
            }
            Err(error) => {
                println!("{display}: FAILED ({error})");
                failures += 1;
            }
        }
    }
    Ok(failures)
}

fn execute(options: Options) -> Result<u8, Box<dyn std::error::Error>> {
    let hasher = match &options.mode {
        Mode::Hash => blake3::Hasher::new(),
        Mode::Derive(context) => blake3::Hasher::new_derive_key(context),
        Mode::Keyed => {
            let mut key = Vec::new();
            io::stdin().take(33).read_to_end(&mut key)?;
            if key.len() > 32 {
                return Err("read more than 32 key bytes from stdin".into());
            }
            let key: [u8; 32] = key.try_into().map_err(|v: Vec<u8>| {
                format!("expected 32 key bytes from stdin, found {}", v.len())
            })?;
            blake3::Hasher::new_keyed(&key)
        }
    };
    let mut failures = 0;
    for path in &options.files {
        if options.check {
            failures += checks(path, &options, &hasher)?;
            continue;
        }
        if path == "-" && matches!(options.mode, Mode::Keyed) {
            eprintln!("b3sum: -: Cannot open `-` in keyed mode");
            failures += 1;
            continue;
        }
        let mut reader = match hash_input(path, &hasher, options.seek) {
            Ok(reader) => reader,
            Err(error) => {
                eprintln!("b3sum: {path}: {error}");
                failures += 1;
                continue;
            }
        };
        let (escaped, display) = escaped_name(path);
        let mut output = io::stdout().lock();
        if !options.raw && !options.no_names {
            if escaped {
                write!(output, "\\")?;
            }
            if options.tag {
                write!(output, "BLAKE3 ({display}) = ")?;
            }
        }
        let mut remaining = options.length;
        let mut buffer = [0; 8192];
        while remaining > 0 {
            let size = remaining.min(buffer.len() as u64) as usize;
            reader.fill(&mut buffer[..size]);
            if options.raw {
                output.write_all(&buffer[..size])?;
            } else {
                for byte in &buffer[..size] {
                    write!(output, "{byte:02x}")?;
                }
            }
            remaining -= size as u64;
        }
        if !options.raw {
            if !options.no_names && !options.tag {
                write!(output, "  {display}")?;
            }
            writeln!(output)?;
        }
    }
    if options.check && failures > 0 {
        eprintln!(
            "b3sum: WARNING: {failures} computed checksum{} did NOT match",
            if failures == 1 { "" } else { "s" }
        );
    }
    Ok(u8::from(failures > 0))
}

fn main() -> ExitCode {
    match options() {
        Ok(Some(options)) => match execute(options) {
            Ok(code) => ExitCode::from(code),
            Err(error) => {
                eprintln!("Error: {error}");
                ExitCode::FAILURE
            }
        },
        Ok(None) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("Error: {error}");
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn escaped_paths_round_trip() {
        let name = "a\\b\nc\r";
        let (escaped, display) = escaped_name(name);
        assert!(escaped);
        let line = format!("\\{}  {display}", "00".repeat(32));
        assert_eq!(parse_check_line(&line).unwrap().0, name);
    }

    #[test]
    fn invalid_records_have_distinct_errors() {
        assert_eq!(parse_check_line(""), Err("Empty line"));
        assert_eq!(
            parse_check_line("garbage"),
            Err("Invalid check line format")
        );
        assert_eq!(parse_check_line("00  x"), Err("Invalid hash length"));
        assert_eq!(
            parse_check_line(&format!("{}  x", "ZZ".repeat(32))),
            Err("Invalid hex")
        );
        assert_eq!(
            parse_check_line(&format!("{}  ", "00".repeat(32))),
            Err("empty file path")
        );
    }

    #[test]
    fn output_seek_matches_a_longer_output() {
        let hasher = blake3::Hasher::new_derive_key("my context");
        let mut reader = hasher.finalize_xof();
        let mut full = [0; 100];
        reader.fill(&mut full);
        reader.set_position(63);
        let mut tail = [0; 37];
        reader.fill(&mut tail);
        assert_eq!(full[63..], tail);
    }

    #[test]
    fn tagged_record_parses() {
        let line = format!("BLAKE3 (a) = {}", "00".repeat(32));
        let (path, expected, display) = parse_check_line(&line).unwrap();
        assert_eq!((path, display), ("a".into(), "a".into()));
        assert_eq!(expected.as_bytes(), &[0; 32]);
    }
}
