//! The definition of the data types used in Papyrus.
//!
//! This module contains the definition of the data types, include
//! the search and sortable Key and arbitrary length Value.

mod key;
mod value;

pub use key::Key;
pub use value::Value;