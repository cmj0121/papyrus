//! The BTree-like persistent storage layer for Papyrus.
use super::file::{FileBaseLayer, FileLayer};
use crate::{Error, Key, Layer, Result, Value};

use url::Url;

/// The BTree-like persistent storage layer for Papyrus.
///
/// It store the key-value pairs into separated sections based on the FileBaseLayer,
/// which key is the BTree like structure with the offset of the value, and value is
/// stored in another section.
///
/// 0       8      16     24     32     40     48     56     64
/// +------+------+------+------+------+------+------+------+
/// ~                                                       ~
/// ~                   header section                      ~
/// ~                                                       ~
/// +-------------------------------------------------------+
/// |    key offset             |    value offset           |
/// +-------------------------------------------------------+
/// ~                                                       ~
/// ~                  key section                          ~
/// ~                                                       ~
/// +-------------------------------------------------------+
/// ~                                                       ~
/// ~                   value section                       ~
/// ~                                                       ~
/// +-------------------------------------------------------+
pub struct BTreeLayer {
    /// The basic file layer and handle the file operations.
    base: FileBaseLayer,
}

impl FileLayer for BTreeLayer {
    /// The type of the BTree layer.
    const TYPE: u8 = 0x02;
}

impl Layer for BTreeLayer {
    /// Open Layer by the passed URL.
    fn open(url: &Url) -> Result<Self> {
        Err(Error::NotImplemented)
    }

    // ======== the general methods ========
    /// Get the value of the specified key, return None if the key does not exist.
    /// Note that the value may return if marked as deleted.
    fn get(&mut self, key: &Key) -> Option<Value> {
        None
    }

    /// Set the value of the specified key, which may overwrite and return the old value
    /// without any warning.
    fn put(&mut self, key: &Key, value: Value) -> Option<Value> {
        None
    }

    /// Delete the value of the specified key, which may not actually delete the value
    /// but mark it as deleted.
    fn del(&mut self, key: &Key) {}

    // ======== the iteration methods ========
    /// Iterate over the key-value pairs in the layer which the order is based on the insertion
    /// order.
    fn iter(&mut self) -> Box<dyn Iterator<Item = (Key, Value)> + '_> {
        Box::new(std::iter::empty())
    }

    /// Iterate over the key-value pairs with the ascending order of the key, pass the optional
    /// based key to start the iteration.
    fn forward<'a>(
        &'a mut self,
        base: Option<&'a Key>,
    ) -> Box<dyn Iterator<Item = (Key, Value)> + '_> {
        Box::new(std::iter::empty())
    }

    /// Iterate over the key-value pairs with the descending order of the key, pass the optional
    /// based key to start the iteration.
    fn backward<'a>(
        &'a mut self,
        base: Option<&'a Key>,
    ) -> Box<dyn Iterator<Item = (Key, Value)> + '_> {
        Box::new(std::iter::empty())
    }

    // ======== the authenticated methods ========
    /// Remove the existing data and files. The layer may not be initialized until any
    /// general method is called.
    fn unlink(&mut self) {}

    /// Remove all the data marked as deleted, reorganize the data and file, and make
    /// the layer compact.
    fn compact(&mut self) {}
}
