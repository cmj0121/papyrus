//! RevDB: the embeddable, persistent, and revision storage.
use atty::Stream;
use clap::Parser as ClapParser;
use pest::Parser;
use pest_derive::Parser as PestParser;
use rustyline::{error::ReadlineError, DefaultEditor};
use tracing::{error, info, trace};

use revdb::{Error, Result};

/// The PEG based parser for RevDB CLI.
#[derive(PestParser)]
#[grammar = "revdb.pest"]
pub struct RevDBParser;

/// The command-line tool for RevDB.
#[derive(Debug, ClapParser)]
#[command(author, version, about, long_about = None)]
pub struct RevDBCli {
    #[clap(flatten)]
    verbose: clap_verbosity_flag::Verbosity,
}

impl RevDBCli {
    /// Run the RevDB on the command-line. It will exit the process with the exit code.
    pub fn run_and_exit(&self) {
        let code = self.run();
        std::process::exit(code);
    }

    /// Evaluate the given command and return the exit code.
    pub fn eval(&self, command: &str) -> Result<()> {
        trace!("eval command: {}", command);

        match RevDBParser::parse(Rule::expression, command) {
            Err(err) => {
                info!("invalid syntax: {}", err);
                return Err(Error::InvalidCommand);
            }
            Ok(_) => {
                // execute the command
            }
        }

        Ok(())
    }

    // ======== private methods ========

    /// execute revdb with the given arguments, and return the exit code.
    fn run(&self) -> i32 {
        self.setup_logging();

        self.prologue();
        let code = self.repl();
        self.epologue();

        code
    }

    /// REPL (read-eval-print-loop) for RevDB
    fn repl(&self) -> i32 {
        let mut code = 0;
        let mut rl = DefaultEditor::new().unwrap();

        loop {
            let readline = rl.readline("revdb> ");

            match readline {
                Ok(line) => match self.eval(&line) {
                    Ok(_) => {
                        // add to history
                    }
                    Err(Error::InvalidCommand) => {
                        println!("invalid command: {}", line);
                    }
                    Err(err) => {
                        println!("eval error: {:?}", err);
                    }
                },
                Err(ReadlineError::Interrupted) => break,
                Err(ReadlineError::Eof) => break,
                Err(err) => {
                    error!("readline error: {:?}", err);

                    code = 1;
                    break;
                }
            }
        }

        if atty::is(Stream::Stdin) {
            // show the bye message only if the input is from the terminal
            println!("~ Bye ~");
        }

        code
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

fn main() {
    let revdb = RevDBCli::parse();
    revdb.run_and_exit();
}
