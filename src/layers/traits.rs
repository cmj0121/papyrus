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

#[cfg(test)]
mod tests {
    use super::*;
    use paste::paste;

    macro_rules! test_layer {
        ($scheme:ident, $url:expr) => {
            paste! {
                #[test]
                fn [<test_get_layer_from_ $scheme>]() {
                    let layer = get_layer($url);

                    assert_eq!(layer.is_some(), true);
                }

                #[test]
                fn [<test_layer_get_empty_on_ $scheme>]() {
                    let key: Key = "key".into();
                    let layer = get_layer($url).unwrap();

                    assert_eq!(layer.get(&key), None);
                }

                #[test]
                fn [<test_layer_put_and_get_on_ $scheme>]() {
                    let key: Key = "key".into();
                    let value: Value = "value".into();
                    let mut layer = get_layer($url).unwrap();

                    layer.put(&key, value.clone());

                    assert_eq!(layer.get(&key), Some(value));
                }

                #[test]
                fn [<test_layer_put_and_del_on_ $scheme>]() {
                    let key: Key = "key".into();
                    let value: Value = "value".into();
                    let mut layer = get_layer($url).unwrap();

                    layer.put(&key, value.clone());
                    layer.del(&key);

                    assert_eq!(layer.get(&key), Some(Value::DELETED));
                }

                #[test]
                fn [<test_layer_compact_on_ $scheme>]() {
                    let key: Key = "key".into();
                    let value: Value = "value".into();
                    let mut layer = get_layer($url).unwrap();

                    layer.put(&key, value.clone());
                    layer.compact();
                    assert_eq!(layer.get(&key), Some(value));

                    layer.del(&key);
                    layer.compact();

                    assert_eq!(layer.get(&key), None);
                }

                #[test]
                fn [<test_layer_unlink_on_ $scheme>]() {
                    let key: Key = "key".into();
                    let value: Value = "value".into();
                    let mut layer = get_layer($url).unwrap();

                    layer.put(&key, value.clone());
                    layer.unlink();

                    assert_eq!(layer.get(&key), None);
                }

            }
        };
    }

    test_layer!(mem, "mem://");
}
