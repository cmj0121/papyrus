//! Papyrus: the embeddable, persistent, and revision storage.
//!
//! It provides the few operations needed to store and retrieve data, and
//! nothing more. It is designed to be embedded in other applications and
//! programming languages.

mod errors;
mod layers;
mod types;

pub use errors::{Error, Result};
pub use layers::{get_layer, Layer};
pub use types::{Key, Value};
