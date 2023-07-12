//! RevDB: the embeddable, persistent, and revision storage.
use clap::Parser;
mod cli;

fn main() {
    let revdb = cli::RevDB::parse();
    revdb.run_and_exit();
}
