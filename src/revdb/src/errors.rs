//! The customized error type for Papyrus.

/// The customized result type for Papyrus. It is a wrapper of `std::result::Result`
/// and the error type is `Error`.
pub type Result<T> = std::result::Result<T, Error>;

/// The pre-define error type for Papyrus.
#[derive(Debug, PartialEq)]
pub enum Error {
    /// Not Implemented
    NotImplemented,

    /// Invalid Command
    InvalidCommand,

    /// Stop the remaining execution
    StopExecution,
}
