//! The layer implementation for Papyrus.
//!
//! `Layer` is the core of Papyrus. It is the main interface for interacting with
//! the key-value pairs in Papyrus. It provides few methods and is designed to be
//! simple to use.
mod file;
mod mem;
mod traits;

pub(crate) use mem::MemLayer;
pub use traits::{get_layer, Layer};

pub use file::FileLayer;
