//! The key-value pair as type in Papyrus.
use crate::{Key, Packer, Result, Value};

/// The key-value pair as type in Papyrus.
///
/// It is the syntax sugar for the tuple of `(Key, Value)`.
#[derive(Debug, PartialEq)]
pub struct Pair {
    pub key: Key,
    pub value: Value,
}

impl Pair {
    pub fn new(key: Key, value: Value) -> Self {
        Self { key, value }
    }
}

impl Packer for Pair {
    /// Convert the type into binary format with type information.
    fn pack(&self) -> Vec<u8> {
        let mut data: Vec<u8> = Vec::new();

        data.extend_from_slice(&self.key.pack());
        data.extend_from_slice(&self.value.pack());

        data
    }

    /// Convert from binary format to the type, which the binary format contains the
    /// type information.
    fn unpack(data: &[u8]) -> Result<(Self, &[u8])> {
        let mut rest: &[u8] = data;
        let key: Key;
        let value: Value;

        (key, rest) = Key::unpack(rest)?;
        (value, rest) = Value::unpack(rest)?;

        Ok((Self { key, value }, rest))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pair_packer() {
        let key: Key = "key".into();
        let value: Value = "value".into();

        let orig: Pair = Pair::new(key.clone(), value.clone());
        let data: Vec<u8> = orig.pack();

        let (pair, rest) = Pair::unpack(&data).unwrap();

        assert_eq!(orig, pair);
        assert_eq!(rest.len(), 0);
        assert_eq!(pair.key, key);
        assert_eq!(pair.value, value);
    }
}
