//! The command-line tool for RevDB.
use clap::Parser as ClapParser;

/// The command-line tool for RevDB.
#[derive(Debug, ClapParser)]
#[command(author, version, about, long_about = None)]
pub struct RevDB {
    #[clap(flatten)]
    verbose: clap_verbosity_flag::Verbosity,
}

impl RevDB {
    /// Run the RevDB on the command-line. It will exit the process with the exit code.
    pub fn run_and_exit(&self) {
        let code = self.run();
        std::process::exit(code);
    }

    // ======== private methods ========

    /// execute revdb with the given arguments, and return the exit code.
    fn run(&self) -> i32 {
        0
    }
}
