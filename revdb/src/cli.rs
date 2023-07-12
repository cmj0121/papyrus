//! The command-line tool for RevDB.
use clap::Parser as ClapParser;
use tracing::trace;

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
        self.setup_logging();

        self.prologue();
        // what you want to do here ...
        self.epologue();

        0
    }

    /// setup the logging system
    fn setup_logging(&self) {
        let subscriber = tracing_subscriber::FmtSubscriber::builder()
            .with_max_level(match self.verbose.log_level() {
                Some(level) => match level {
                    clap_verbosity_flag::Level::Error => tracing::Level::ERROR,
                    clap_verbosity_flag::Level::Warn => tracing::Level::WARN,
                    clap_verbosity_flag::Level::Info => tracing::Level::INFO,
                    clap_verbosity_flag::Level::Debug => tracing::Level::DEBUG,
                    _ => tracing::Level::TRACE,
                },
                None => tracing::Level::ERROR,
            })
            .finish();

        tracing::subscriber::set_global_default(subscriber).expect("failed to set logger");
    }

    /// setup everything before running
    fn prologue(&self) {
        trace!("prologue ...");
    }

    /// clean-up everything after running
    fn epologue(&self) {
        trace!("epologue ...");
    }
}
