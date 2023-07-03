//! The customized error type for Papyrus.
use std::convert::From;

/// The customized result type for Papyrus. It is a wrapper of `std::result::Result`
/// and the error type is `Error`.
pub type Result<T> = std::result::Result<T, Error>;

/// The pre-define error type for Papyrus.
#[derive(Debug, PartialEq)]
pub enum Error {
    /// Not Implemented
    NotImplemented,

    /// Invalid Argument
    InvalidArgument,

    /// I/O Error
    IOError(String),
}

// ======== value-to-value conversions ========
impl From<std::io::Error> for Error {
    fn from(err: std::io::Error) -> Self {
        let err = format!("{}", err);
        Self::IOError(err)
    }
}
