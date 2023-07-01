//! The abstraction of the Layer.
use crate::{Key, Value};

/// The abstraction of the Layer.
///
/// `Layer` provides general methods for interacting with the key-value pairs,
/// and extra but danger methods for specific usages. It is designed to be
/// simple to use and easy to implement.
pub trait Layer {
    // ======== the general methods ========
    /// Get the value of the specified key, return None if the key does not exist.
    /// Note that the value may return if marked as deleted.
    fn get(&self, key: &Key) -> Option<Value>;

    /// Set the value of the specified key, which may overwrite and return the old value
    /// without any warning.
    fn put(&mut self, key: &Key, value: Value) -> Option<Value>;

    /// Delete the value of the specified key, which may not actually delete the value
    /// but mark it as deleted.
    fn del(&mut self, key: &Key);

    // ======== the authenticated methods ========
    /// Remove the existing data and files. The layer may not be initialized until any
    /// general method is called.
    fn unlink(&mut self);

    /// Remove all the data marked as deleted, reorganize the data and file, and make
    /// the layer compact.
    fn compact(&mut self);
}
