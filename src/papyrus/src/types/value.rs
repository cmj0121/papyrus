//! Value is the arbitrary length data used in Papyrus.
use crate::{Converter, Error, Packer, Result};
use std::convert::From;
use tracing::{trace, warn};

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
    /// The total size of the raw value.
    pub fn len(&self) -> usize {
        match self {
            Value::EMPTY => 0,
            Value::DELETED => 0,
            Value::RAW(data) => data.len(),
        }
    }

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

// ======== the converter ========
impl Converter for Value {
    /// the capacity of the type.
    fn cap(&self) -> usize {
        let header_size: usize = 4;
        let body_size: usize = match self {
            Value::EMPTY | Value::DELETED => 0,
            Value::RAW(data) => data.len(),
        };

        header_size + body_size
    }

    /// Convert the type into binary format.
    ///
    /// 0       8      16     24     32
    /// +------+------+------+------+
    /// | TYPE |       SIZE         |
    /// +---------------------------+
    /// ~                           ~
    /// ~          DATA             ~
    /// ~                           ~
    /// +---------------------------+
    fn to_bytes(&self) -> Vec<u8> {
        let typ: u8 = match self {
            Value::EMPTY => 0,
            Value::DELETED => 1,
            Value::RAW(_) => 2,
        };
        let header: u32 = (typ as u32) << 24 | (self.len() as u32) & 0x00FFFFFF;
        let mut data: Vec<u8> = header.to_le_bytes().to_vec();

        match self {
            Value::EMPTY => {}
            Value::DELETED => {}
            Value::RAW(raw) => data.extend(raw),
        }

        data
    }

    /// Convert from binary format to the type. It only contains the data of the type
    /// itself, not including the type information.
    fn from_bytes(data: &[u8]) -> Result<Self> {
        if data.len() < 4 {
            warn!("cannot convert value from {:?}", data);
            return Err(Error::InvalidArgument);
        }

        let header = u32::from_le_bytes(data[0..4].try_into().unwrap());
        let size = (header & 0x00FFFFFF) as usize;

        match ((header >> 24), size) {
            (0, 0) => Ok(Value::EMPTY),
            (1, 0) => Ok(Value::DELETED),
            (2, size) => {
                if data.len() < size + 4 {
                    warn!(
                        "cannot convert value with invalid size, expected {} but got {}",
                        size,
                        data.len() - 4
                    );
                    return Err(Error::InvalidArgument);
                }

                let raw = data[4..size + 4].to_vec();

                Ok(Value::RAW(raw))
            }
            _ => {
                warn!("cannot convert value with invalid header {:?}", header);
                Err(Error::InvalidArgument)
            }
        }
    }
}

impl Packer for Value {
    /// Convert the type into binary format with type information.
    fn pack(&self) -> Vec<u8> {
        self.to_bytes()
    }

    /// Convert from binary format to the type, which the binary format contains the
    /// type information.
    fn unpack(data: &[u8]) -> Result<(Self, &[u8])>
    where
        Self: Sized,
    {
        let value = Self::from_bytes(data)?;
        let size = value.cap();

        Ok((value, &data[size..]))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use paste::paste;

    #[test]
    fn test_empty_value() {
        let value: Value = Value::EMPTY;
        assert_eq!(value, Value::EMPTY);
    }

    #[test]
    fn test_empty_value_converter() {
        let value: Value = Value::EMPTY;
        let data: Vec<u8> = value.to_bytes();

        assert_eq!(data.len(), value.cap());
        assert_eq!(Value::from_bytes(&data), Ok(Value::EMPTY));
    }

    #[test]
    fn test_empty_value_unpack() {
        let value: Value = Value::EMPTY;
        let data: Vec<u8> = value.to_bytes();
        let rest: &[u8] = &vec![];

        assert_eq!(Value::unpack(&data), Ok((Value::EMPTY, rest)));
    }

    #[test]
    fn test_deleted_value() {
        let mut value: Value = Value::EMPTY;
        value.delete();

        assert_eq!(value, Value::DELETED);
    }

    #[test]
    fn test_deleted_value_converter() {
        let mut value: Value = Value::EMPTY;
        value.delete();

        let data: Vec<u8> = value.to_bytes();

        assert_eq!(data.len(), value.cap());
        assert_eq!(Value::from_bytes(&data), Ok(Value::DELETED));
    }

    #[test]
    fn test_deleted_value_packer() {
        let mut value: Value = Value::EMPTY;
        value.delete();

        let data: Vec<u8> = value.to_bytes();
        let rest: &[u8] = &vec![];

        assert_eq!(Value::unpack(&data), Ok((Value::DELETED, rest)));
    }

    macro_rules! test_value {
        ($name:ident, $data:expr) => {
            paste! {
                #[test]
                fn [<test_value_ $name>]() {
                    let value: Value = $data.into();
                    assert_eq!(value, Value::RAW($data.as_bytes().to_vec()));
                }

                #[test]
                fn [<test_value_ $name _converter>]() {
                    let value: Value = $data.into();
                    let data: Vec<u8> = value.to_bytes();

                    assert_eq!(data.len(), value.cap());
                    assert_eq!(Value::from_bytes(&data), Ok(Value::RAW($data.as_bytes().to_vec())));
                }

                #[test]
                fn [<test_value_ $name _packer>]() {
                    let value: Value = $data.into();
                    let data: Vec<u8> = value.pack();
                    let rest: &[u8] = &vec![];

                    assert_eq!(Value::unpack(&data), Ok((Value::RAW($data.as_bytes().to_vec()), rest)));
                }
            }
        };
    }

    test_value!(empty, "");
    test_value!(single_char, "a");
    test_value!(multi_char, "aaaaaaaa");

    macro_rules! test_value_unpack_iter {
        ($count:expr) => {
            paste! {
                #[test]
                fn [<test_value_unpack_iter_ $count>]() {
                    let size: usize = $count;
                    let mut data: Vec<u8> = vec![];

                    for i in 0..size {
                        let raw: String = "a".repeat(i);
                        let value: Value = raw.into();
                        data.extend(value.pack());
                    }

                    assert_eq!(Value::unpack_iter(&data).count(), size);
                }
            }
        };
    }

    test_value_unpack_iter!(0);
    test_value_unpack_iter!(1);
    test_value_unpack_iter!(2);
    test_value_unpack_iter!(16);
    test_value_unpack_iter!(64);
    test_value_unpack_iter!(4096);
    test_value_unpack_iter!(65535);
}
