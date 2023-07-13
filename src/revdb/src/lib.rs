//! The library for RevDB.

mod builder;
mod errors;
mod settings;

pub use builder::{Builder, RevDB};
pub use errors::{Error, Result};
pub use settings::Settings;
