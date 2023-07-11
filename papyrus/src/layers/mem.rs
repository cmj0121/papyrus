//! The in-memory Layer implementation.
use crate::{Key, Layer, Result, Value};
use std::collections::{BTreeSet, HashMap};
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
    _del: BTreeSet<Key>,
}

impl Layer for MemLayer {
    fn open(_: &Url) -> Result<Self> {
        Ok(MemLayer::default())
    }

    // ======== the general methods ========
    /// Get the value of the specified key, return None if the key does not exist.
    /// Note that the value may return if marked as deleted.
    fn get(&mut self, key: &Key) -> Option<Value> {
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
        self._del.insert(key.clone());
        self._mem.insert(key.clone(), value)
    }

    /// Delete the value of the specified key, which may not actually delete the value
    /// but mark it as deleted.
    fn del(&mut self, key: &Key) {
        self._mem.remove(key);
    }

    // ======== the iteration methods ========
    /// Iterate over the key-value pairs in the layer which the order is not guaranteed.
    fn iter(&mut self) -> Box<dyn Iterator<Item = (Key, Value)> + '_> {
        Box::new(
            self._del
                .clone()
                .into_iter()
                .rev()
                .map(move |key| (key.clone(), self.get(&key).unwrap())),
        )
    }

    /// Iterate over the key-value pairs with the ascending order of the key, pass the optional
    /// based key to start the iteration.
    fn forward<'a>(
        &'a mut self,
        base: Option<&'a Key>,
    ) -> Box<dyn Iterator<Item = (Key, Value)> + '_> {
        Box::new(
            self._del
                .clone()
                .into_iter()
                .filter(move |x| match base {
                    Some(base) => x >= base,
                    None => true,
                })
                .map(move |key| (key.clone(), self.get(&key).unwrap())),
        )
    }

    /// Iterate over the key-value pairs with the descending order of the key, pass the optional
    /// based key to start the iteration.
    fn backward<'a>(
        &'a mut self,
        base: Option<&'a Key>,
    ) -> Box<dyn Iterator<Item = (Key, Value)> + '_> {
        Box::new(
            self._del
                .clone()
                .into_iter()
                .filter(move |x| match base {
                    Some(base) => x <= base,
                    None => true,
                })
                .rev()
                .map(move |key| (key.clone(), self.get(&key).unwrap())),
        )
    }

    // ======== the authenticated methods ========
    /// Remove the existing data and files. The layer may not be initialized until any
    /// general method is called.
    fn unlink(&mut self) {
        self._mem.clear();
        self._del.clear();
    }

    /// Remove all the data marked as deleted, reorganize the data and file, and make
    /// the layer compact.
    fn compact(&mut self) {
        self._del.clear();
        self._del = self._mem.keys().cloned().collect();
    }
}
