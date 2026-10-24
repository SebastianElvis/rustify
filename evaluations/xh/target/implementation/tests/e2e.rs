use std::{path::Path, process::Command};

#[test]
fn loopback_process_and_protocol_contract() {
    let project = Path::new(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(2)
        .expect("The project has a parent.");
    let output = Command::new("python3")
        .arg("evaluate.py")
        .arg("--candidate")
        .arg(env!("CARGO_BIN_EXE_xh"))
        .args(["--port", "0", "--report-prefix", "evidence/cargo-e2e"])
        .current_dir(project)
        .output()
        .expect("The local evaluation starts.");
    assert!(
        output.status.success(),
        "{}\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}
