//! The abstraction of the Layer.
use crate::layers::{get_file_layer, MemLayer};
use crate::{Key, Result, Value};
use tracing::{trace, warn};
use url::Url;

/// The abstraction of the Layer.
///
/// `Layer` provides general methods for interacting with the key-value pairs,
/// and extra but danger methods for specific usages. It is designed to be
/// simple to use and easy to implement.
pub trait Layer {
    /// Open Layer by the passed URL.
    fn open(url: &Url) -> Result<Self>
    where
        Self: Sized;

    // ======== the general methods ========
    /// Get the value of the specified key, return None if the key does not exist.
    /// Note that the value may return if marked as deleted.
    fn get(&mut self, key: &Key) -> Option<Value>;

    /// Set the value of the specified key, which may overwrite and return the old value
    /// without any warning.
    fn put(&mut self, key: &Key, value: Value) -> Option<Value>;

    /// Delete the value of the specified key, which may not actually delete the value
    /// but mark it as deleted.
    fn del(&mut self, key: &Key);

    // ======== the iteration methods ========
    /// Iterate over the key-value pairs in the layer which the order is not guaranteed.
    fn iter(&mut self) -> Box<dyn Iterator<Item = (Key, Value)> + '_>;

    /// Iterate over the key-value pairs with the ascending order of the key, pass the optional
    /// based key to start the iteration.
    fn forward<'a>(
        &'a mut self,
        base: Option<&'a Key>,
    ) -> Box<dyn Iterator<Item = (Key, Value)> + '_>;

    /// Iterate over the key-value pairs with the descending order of the key, pass the optional
    /// based key to start the iteration.
    fn backward<'a>(
        &'a mut self,
        base: Option<&'a Key>,
    ) -> Box<dyn Iterator<Item = (Key, Value)> + '_>;

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
            "mem" => match MemLayer::open(&url) {
                Ok(layer) => Some(Box::new(layer)),
                Err(err) => {
                    trace!("failed to open {}: {:?}", &url, err);
                    None
                }
            },
            "wal" => get_file_layer(&url),
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
                    let mut layer = get_layer($url).unwrap();

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

                test_layer_iter!($scheme, $url, 0);
                test_layer_iter!($scheme, $url, 1);
                test_layer_iter!($scheme, $url, 2);
                test_layer_iter!($scheme, $url, 3);
                test_layer_iter!($scheme, $url, 16);
                test_layer_iter!($scheme, $url, 64);
                test_layer_iter!($scheme, $url, 256);
                test_layer_iter!($scheme, $url, 4096);
                test_layer_iter!($scheme, $url, 8196);
                test_layer_iter!($scheme, $url, 65535);
            }
        };
    }

    macro_rules! test_layer_iter {
        ($scheme:ident, $url:expr, $count:expr) => {
            paste! {
                #[test]
                fn [<test_layer_iter_ $count _on_ $scheme>]() {
                    let size: usize = $count as usize;
                    let mut layer = get_layer($url).unwrap();

                    for index in 0..size {
                        let key: Key = index.into();
                        let value: Value = format!("value {}", index).into();

                        layer.put(&key, value.clone());
                        assert_eq!(layer.get(&key), Some(value));
                    }

                    assert_eq!(layer.iter().count(), size);
                }

                #[test]
                fn [<test_layer_iter_ $count _on_ $scheme _with_del>]() {
                    let size: usize = $count as usize;
                    let mut layer = get_layer($url).unwrap();

                    for index in 0..size {
                        let key: Key = index.into();
                        let value: Value = format!("value {}", index).into();

                        layer.put(&key, value.clone());
                        layer.del(&key);
                        assert_eq!(layer.get(&key), Some(Value::DELETED));
                    }

                    assert_eq!(layer.iter().count(), size);
                }

                #[test]
                fn [<test_layer_forward_ $count _on_ $scheme>]() {
                    let size: usize = $count as usize;
                    let mut layer = get_layer($url).unwrap();
                    let mut base: Option<Key> = None;

                    for index in 0..size {
                        let key: Key = index.into();
                        let value: Value = format!("value {}", index).into();

                        layer.put(&key, value.clone());
                        assert_eq!(layer.get(&key), Some(value));

                        if index == size / 2 {
                            base = Some(key);
                        }
                    }

                    assert_eq!(layer.forward(base.as_ref()).count(), size - size / 2);

                    let is_sorted = layer
                        .forward(base.as_ref())
                        .map(|(key, _)| key)
                        .collect::<Vec<_>>()
                        .windows(2)
                        .all(|w| w[0] < w[1]);
                    assert_eq!(is_sorted, true);
                }

                #[test]
                fn [<test_layer_backward_ $count _on_ $scheme>]() {
                    let size: usize = $count as usize;
                    let mut layer = get_layer($url).unwrap();
                    let mut base: Option<Key> = None;

                    for index in 0..size {
                        let key: Key = index.into();
                        let value: Value = format!("value {}", index).into();

                        layer.put(&key, value.clone());
                        assert_eq!(layer.get(&key), Some(value));

                        if index == size / 2 {
                            base = Some(key);
                        }
                    }

                    let shift: usize = match size {
                        0 => 0,
                        _ => 1 - size  %2,
                    };
                    assert_eq!(layer.backward(base.as_ref()).count(), size - size / 2 + shift);

                    let is_sorted = layer
                        .backward(base.as_ref())
                        .map(|(key, _)| key)
                        .collect::<Vec<_>>()
                        .windows(2)
                        .all(|w| w[0] > w[1]);
                    assert_eq!(is_sorted, true);
                }
            }
        };
    }

    test_layer!(mem, "mem://");
}
