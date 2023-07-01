//! The in-memory Layer implementation.
use crate::{Key, Layer, Value};
use std::collections::{HashMap, HashSet};
use url::Url;

/// The in-memory Layer implementation.
///
/// It is based on data structure to hold the key-value pairs in memory.
#[derive(Debug, Default)]
pub struct MemLayer {
    /// use the simplest hashmap to hold the key-value pairs, it is not the best
    /// method but easy to implement.
    _mem: HashMap<Key, Value>,

    /// the pool to hold the deleted keys.
    _del: HashSet<Key>,
}

impl Layer for MemLayer {
    fn open(_: Url) -> Self {
        MemLayer::default()
    }

    // ======== the general methods ========
    /// Get the value of the specified key, return None if the key does not exist.
    /// Note that the value may return if marked as deleted.
    fn get(&self, key: &Key) -> Option<Value> {
        match self._mem.get(key) {
            Some(value) => Some(value.clone()),
            None => match self._del.get(key) {
                Some(_) => Some(Value::DELETED),
                None => None,
            },
        }
    }

    /// Set the value of the specified key, which may overwrite and return the old value
    /// without any warning.
    fn put(&mut self, key: &Key, value: Value) -> Option<Value> {
        self._del.remove(key);
        self._mem.insert(key.clone(), value)
    }

    /// Delete the value of the specified key, which may not actually delete the value
    /// but mark it as deleted.
    fn del(&mut self, key: &Key) {
        self._del.insert(key.clone());
        self._mem.remove(key);
    }

    // ======== the authenticated methods ========
    /// Remove the existing data and files. The layer may not be initialized until any
    /// general method is called.
    fn unlink(&mut self) {
        self._mem.clear();
    }

    /// Remove all the data marked as deleted, reorganize the data and file, and make
    /// the layer compact.
    fn compact(&mut self) {
        self._del.clear();
    }
}
