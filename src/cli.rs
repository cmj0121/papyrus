//! The command-line tool for Papyrus.
use clap::Parser as ClapParser;
use pest::{iterators::Pair, Parser};
use pest_derive::Parser as PestParser;
use rustyline::{error::ReadlineError, DefaultEditor};
use tracing::{debug, error, trace, warn};

/// The PEG based parser for Parser CLI.
///
/// # Grammar
///
/// ```peg
/// expression = { space* ~ command ~ space* ~ EOI }
/// command    = { put_command | get_command | del_command | iter_command }
///
/// put_command  = { put ~ key ~ space ~ value }
/// get_command  = { get ~ keys }
/// del_command  = { del ~ keys }
/// iter_command = { ord ~ ( space ~ key )? }
///
/// put = { ( ( ^"put" ~ space ) | "+" ~ ( space )? ) }
/// get = { ( ( ^"get" ~ space ) | "?" ~ ( space )? ) }
/// del = { ( ( ^"del" ~ space ) | "-" ~ ( space )? ) }
/// ord = { ^"asc" | ^"desc" }
///
/// space = { SPACE_SEPARATOR+ }
/// keys  = { key ~ ( space ~ key)* }
/// key   = @{ ( !space ~ ANY )+ }
/// value = { ANY+ }
/// ```
#[derive(PestParser)]
#[grammar = "papyrus.pest"]
pub struct PapyrusParser;

/// The command-line tool for Papyrus.
#[derive(Debug, ClapParser)]
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
                Ok(line) => self.parse_and_eval(&line),
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

    /// read the input from the user, parse the syntax and evaluate the expression
    fn parse_and_eval(&self, expr: &str) {
        debug!("try to evaluate: {}", expr);

        match PapyrusParser::parse(Rule::expression, expr) {
            Err(err) => {
                warn!("invalid syntax: {}", err);
                println!("invalid syntax: {}", expr);
            }
            Ok(pairs) => {
                let expression = pairs
                    .filter(|p| p.as_rule() == Rule::expression)
                    .next()
                    .expect("expression pair not found");
                let command = expression
                    .into_inner()
                    .next()
                    .expect("command pair not found");

                self.evaluate(command);
            }
        }
    }

    /// evaluate the parsed pair
    fn evaluate(&self, pair: Pair<Rule>) {
        trace!("evaluate pair: {:?}", pair);

        match pair.as_rule() {
            Rule::command => {
                let command = pair.into_inner().next().expect("command pair not found");
                self.evaluate(command);
            }
            Rule::get_command | Rule::del_command => {
                let operator = pair.as_rule();
                let keys: Vec<String> = pair
                    // seach the keys pair
                    .into_inner()
                    .filter(|p| p.as_rule() == Rule::keys)
                    .next()
                    .expect("keys pair not found")
                    // list all the key pairs
                    .into_inner()
                    .filter(|p| p.as_rule() == Rule::key)
                    // convert the key pair to key string
                    .map(|p| p.as_str().to_string())
                    .collect();

                println!("{:?} {:?}", operator, keys);
            }
            Rule::put_command => {
                let key_value: Vec<String> = pair
                    .into_inner()
                    .filter(|p| p.as_rule() == Rule::key || p.as_rule() == Rule::value)
                    .map(|p| p.as_str().to_string())
                    .collect();

                println!("put_command: {:?}", key_value);
            }
            Rule::iter_command => {
                let ord: String = pair
                    .clone()
                    .into_inner()
                    .filter(|p| p.as_rule() == Rule::ord)
                    .map(|p| p.as_str().to_string())
                    .next()
                    .unwrap();
                let key: Option<String> = pair
                    .clone()
                    .into_inner()
                    .filter(|p| p.as_rule() == Rule::key)
                    .map(|p| p.as_str().to_string())
                    .next();

                println!("iter_command: {:?} {:?}", ord, key);
            }
            _ => {
                warn!("invalid command: {:?}", pair);
                println!("invalid command: {:?}", pair.as_rule());
            }
        }
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
