//! The command-line tool for Papyrus.
use clap::Parser;
use rustyline::{error::ReadlineError, DefaultEditor};
use tracing::{debug, error, trace};

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
        let code = self.run();
        std::process::exit(code);
    }

    fn run(&self) -> i32 {
        self.setup_logging();

        self.prologue();
        let code = self.eval_loop();
        self.epologue();

        code
    }

    /// the read-eval-print-loop
    fn eval_loop(&self) -> i32 {
        let mut code = 0;
        let mut rl = DefaultEditor::new().unwrap();

        loop {
            let readline = rl.readline("papyrus> ");

            match readline {
                Ok(line) => self.eval(&line),
                Err(ReadlineError::Interrupted) => break,
                Err(ReadlineError::Eof) => break,
                Err(err) => {
                    error!("readline error: {:?}", err);

                    code = 1;
                    break;
                }
            }
        }

        code
    }

    /// read the input from the user and evaluate it
    fn eval(&self, expr: &str) {
        debug!("try to evaluate: {}", expr);
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
