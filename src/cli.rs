//! The command-line tool for Papyrus.
use clap::Parser;
use tracing::trace;

/// The command-line tool for Papyrus.
#[derive(Debug, Parser)]
#[command(author, version, about, long_about = None)]
pub struct Papyrus {
    #[clap(flatten)]
    verbose: clap_verbosity_flag::Verbosity,

    #[clap(default_value = "mem://", help = "The URL of the Papyrus location.")]
    url: String,
}

impl Papyrus {
    /// Run the papyrus in REPL mode.
    pub fn run_and_exit(&self) {
        self.setup_logging();
        std::process::exit(self.run());
    }

    fn run(&self) -> i32 {
        self.setup_logging();

        self.prologue();
        self.epologue();

        0
    }

    /// setup everything before running
    fn prologue(&self) {
        trace!("prologue ...");
    }

    /// clean-up everything after running
    fn epologue(&self) {
        trace!("epologue ...");
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
}
