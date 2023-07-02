//! Value is the arbitrary length data used in Papyrus.
use std::convert::From;
use tracing::trace;

/// Value is the arbitrary length data used in Papyrus.
///
/// It is the arbitrary length data upload from user and stored in the
/// Papyrus. It can be any binary data and may compressed or store as
/// another detached file.
#[derive(Debug, Clone, PartialEq)]
pub enum Value {
    /// The empty value.
    EMPTY,

    /// The marked as deleted value.
    DELETED,

    /// The raw binary data.
    RAW(Vec<u8>),
}

impl Value {
    /// make the current value as deleted.
    pub fn delete(&mut self) {
        *self = Value::DELETED
    }
}

// ======== value-to-value conversions ========
impl From<&[u8]> for Value {
    fn from(data: &[u8]) -> Self {
        Value::RAW(data.to_vec())
    }
}

impl From<&str> for Value {
    fn from(data: &str) -> Self {
        trace!("converting {} to value", data);

        let data = data.as_bytes();
        data.into()
    }
}

impl From<String> for Value {
    fn from(data: String) -> Self {
        trace!("converting {} to value", data);

        let data = data.as_bytes();
        data.into()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_deleted_value() {
        let mut value: Value = Value::EMPTY;
        value.delete();

        assert_eq!(value, Value::DELETED);
    }
}
