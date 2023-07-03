//! The persistence layer for Papyrus which stores key-value pairs in local files.
//!
//! All the layers in this module are designed to store key-value pairs in local
//! file system, serve the requests from the clients, and operate the data in
//! file(s).

mod file;

pub use file::FileLayer;
