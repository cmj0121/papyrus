//! Papyrus: the embeddable, persistent, and revision storage.
use clap::Parser;
mod cli;

fn main() {
    let papyrus = cli::Papyrus::parse();

    papyrus.run_and_exit();
}
