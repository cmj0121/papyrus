//! The SSTable-like persistent storage implementation.

/// The SSTable-like persistent storage implementation.
///
/// The key-value pairs are stored in a file, which is divided into several blocks.
/// The key is treated as dynamic-length string but stored via the packed format.
pub struct SSTable {}
