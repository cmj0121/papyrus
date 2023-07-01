//! The abstraction of the Layer.
use crate::layers::MemLayer;
use crate::{Key, Value};
use tracing::{trace, warn};
use url::Url;

/// The abstraction of the Layer.
///
/// `Layer` provides general methods for interacting with the key-value pairs,
/// and extra but danger methods for specific usages. It is designed to be
/// simple to use and easy to implement.
pub trait Layer {
    /// Open Layer by the passed URL.
    fn open(url: Url) -> Self
    where
        Self: Sized;

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

/// Get the Layer via passed URL.
pub fn get_layer(url: &str) -> Option<Box<dyn Layer>> {
    trace!("try to get layer from {}", url);

    match Url::parse(url) {
        Ok(url) => match url.scheme() {
            "mem" => Some(Box::new(MemLayer::open(url))),
            _ => {
                warn!("cannot find scheme {} for layer", url.scheme());
                None
            }
        },
        Err(err) => {
            trace!("failed to parse url {}: {}", url, err);
            None
        }
    }
}
