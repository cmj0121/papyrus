//! The write-ahead log (WAL) persistence Layer.
use super::file::{FileBaseLayer, FileLayer};
use crate::{Key, Layer, Packer, Pair, Result, Value};
use tracing::error;
use url::Url;

/// The write-ahead log (WAL) persistence Layer.
///
/// It store the key-value pairs in a log file based on the FileBaseLayer, which
/// provides the Layer like operations and store into the data section on the
/// FileBaseLayer.
pub struct WALLayer {
    /// The basic file layer and handle the file operations.
    base: FileBaseLayer,

    /// the internal bit to check the layer is initialized.
    initialized: bool,
}

impl FileLayer for WALLayer {
    /// The type of the WAL layer.
    const TYPE: u8 = 0x01;
}

impl Layer for WALLayer {
    /// Open Layer by the passed URL.
    fn open(url: &Url) -> Result<Self> {
        let domain: String = url.domain().unwrap_or_default().to_string();
        let path: String = format!("{}{}", domain, url.path());
        let base = FileBaseLayer::new(&path, Some((Self::TYPE, 0)))?;

        Ok(Self {
            base,
            initialized: true,
        })
    }

    // ======== the general methods ========
    /// Get the value of the specified key, return None if the key does not exist.
    /// Note that the value may return if marked as deleted.
    fn get(&mut self, key: &Key) -> Option<Value> {
        let mut value: Option<Value> = None;

        for (search_key, search_value) in self.iter() {
            if search_key == *key {
                // update the latest value
                value = Some(search_value);
            }
        }

        value
    }

    /// Set the value of the specified key, which may overwrite and return the old value
    /// without any warning.
    fn put(&mut self, key: &Key, value: Value) -> Option<Value> {
        let pair = Pair::new(key.clone(), value);

        if let Err(err) = self.base.append(&pair.pack()) {
            error!("put data got error: {:?}", err);
        }

        None
    }

    /// Delete the value of the specified key, which may not actually delete the value
    /// but mark it as deleted.
    fn del(&mut self, key: &Key) {
        let value: Value = Value::DELETED;
        let _ = self.put(key, value);
    }

    // ======== the iteration methods ========
    /// Iterate over the key-value pairs in the layer which the order is based on the insertion
    /// order.
    fn iter(&mut self) -> Box<dyn Iterator<Item = (Key, Value)> + '_> {
        let mut data: Vec<u8> = Vec::new();
        let _ = self.base.read_to_end(&mut data);

        let pairs: Vec<Pair> = Pair::unpack_iter(&data).collect();

        Box::new(pairs.into_iter().map(move |pair| (pair.key, pair.value)))
    }

    /// Iterate over the key-value pairs with the ascending order of the key, pass the optional
    /// based key to start the iteration.
    fn forward<'a>(
        &'a mut self,
        base: Option<&'a Key>,
    ) -> Box<dyn Iterator<Item = (Key, Value)> + '_> {
        let mut data: Vec<u8> = Vec::new();
        let _ = self.base.read_to_end(&mut data);

        let mut pairs: Vec<Pair> = Pair::unpack_iter(&data)
            .filter(move |x| match base {
                Some(base) => x.key >= *base,
                None => true,
            })
            .collect();

        // sort by the key order
        pairs.sort_by(|a, b| a.key.cmp(&b.key));

        Box::new(pairs.into_iter().map(move |pair| (pair.key, pair.value)))
    }

    /// Iterate over the key-value pairs with the descending order of the key, pass the optional
    /// based key to start the iteration.
    fn backward<'a>(
        &'a mut self,
        base: Option<&'a Key>,
    ) -> Box<dyn Iterator<Item = (Key, Value)> + '_> {
        let mut data: Vec<u8> = Vec::new();
        let _ = self.base.read_to_end(&mut data);

        let mut pairs: Vec<Pair> = Pair::unpack_iter(&data)
            .filter(move |x| match base {
                Some(base) => x.key <= *base,
                None => true,
            })
            .collect();

        // sort by the key order
        pairs.sort_by(|a, b| b.key.cmp(&a.key));

        Box::new(pairs.into_iter().map(move |pair| (pair.key, pair.value)))
    }

    // ======== the authenticated methods ========
    /// Remove the existing data and files. The layer may not be initialized until any
    /// general method is called.
    fn unlink(&mut self) {
        self.base.unlink();
        drop(&self.base);

        self.initialized = false;
    }

    /// Remove all the data marked as deleted, reorganize the data and file, and make
    /// the layer compact.
    fn compact(&mut self) {}
}
