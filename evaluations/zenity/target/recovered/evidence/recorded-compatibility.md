# Desktop smoke compatibility

All five native GUI workflows have matching stdout, stderr, and exit status.
The replay uses actual reference and Rust dialogs.
The Rust unit suite has four passing tests.
Formatting and clippy pass.
The first Rust GUI attempt lacked application initialization.
The correction calls finishLaunching before modal display.
The code correction removes the prior activation-policy call.
The track permits icon and title-placement differences.
The track does not claim full zenity or desktop compatibility.
The parent agent performs this smoke evaluation.
The original source remains hidden until the freeze.
