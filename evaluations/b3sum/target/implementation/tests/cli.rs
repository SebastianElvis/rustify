use std::io::Write;
use std::process::{Command, Stdio};

fn run(args: &[&str], input: &[u8]) -> std::process::Output {
    let mut child = Command::new(env!("CARGO_BIN_EXE_rustify-b3sum"))
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(input).unwrap();
    child.wait_with_output().unwrap()
}

#[test]
fn hashes_stdin() {
    let output = run(&[], b"hello");
    assert!(output.status.success());
    assert_eq!(
        output.stdout,
        b"ea8f163db38682925e4491c5e58d4bb3506ef8c14eb78a86e908c5624a67200f  -\n"
    );
}

#[test]
fn raw_length_and_seek_match_hex() {
    let raw = run(&["--raw", "--length", "65", "--seek", "63"], b"hello");
    let hex = run(&["--no-names", "--length", "65", "--seek", "63"], b"hello");
    assert_eq!(raw.stdout.len(), 65);
    let expected = raw
        .stdout
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect::<String>()
        + "\n";
    assert_eq!(hex.stdout, expected.as_bytes());
}

#[test]
fn rejects_short_key() {
    let output = run(&["--keyed", "missing"], b"short");
    assert!(!output.status.success());
    assert_eq!(
        output.stderr,
        b"Error: expected 32 key bytes from stdin, found 5\n"
    );
}

#[test]
fn rejects_malformed_checkfile() {
    let output = run(&["--check"], b"garbage\n");
    assert!(!output.status.success());
    assert_eq!(
        output.stderr,
        b"b3sum: Invalid check line format\nb3sum: WARNING: 1 computed checksum did NOT match\n"
    );
}
