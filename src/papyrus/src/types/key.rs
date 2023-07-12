//! Key is the searchable and sortable data type used in Papyrus.
use crate::{Converter, Error, Packer, Result};
use std::convert::From;
use tracing::{error, warn};

/// Key is the searchable and sortable data type used in Papyrus.
///
/// It is the fixed length and well-known type that is used as the primary
/// key or index for the key-value pairs in Papyrus.
#[derive(Debug, Clone, Eq, PartialEq, Ord, PartialOrd, Hash)]
pub enum Key {
    /// The truth value
    BOOL(bool),

    /// The 64-bit signed integer
    INT(i64),

    /// The 128-bit unsigned integer
    UID(u128),

    /// The 64-bytes null-terminated string
    STR(String),

    /// The 256-bytes null-terminated string
    TEXT(String),
}

// ======== value-to-value conversions ========
trait Integer {}

impl Integer for i8 {}
impl Integer for u8 {}
impl Integer for i16 {}
impl Integer for u16 {}
impl Integer for i32 {}
impl Integer for u32 {}
impl Integer for i64 {}

impl From<bool> for Key {
    fn from(b: bool) -> Self {
        Key::BOOL(b)
    }
}

impl<T: Integer> From<T> for Key
where
    i64: From<T>,
{
    fn from(i: T) -> Self {
        Key::INT(i.into())
    }
}

impl From<usize> for Key {
    fn from(uid: usize) -> Self {
        Key::UID(uid as u128)
    }
}

impl From<u128> for Key {
    fn from(uid: u128) -> Self {
        Key::UID(uid)
    }
}

impl From<&str> for Key {
    fn from(s: &str) -> Self {
        match s.len() {
            0..=63 => Key::STR(s.to_string()),
            64..=255 => Key::TEXT(s.to_string()),
            _ => {
                let msg = format!("key too long: {}", s.len());
                error!(msg);
                panic!("{}", msg);
            }
        }
    }
}

// ======== the converter ========
impl Converter for Key {
    /// the capacity of the type.
    fn cap(&self) -> usize {
        match self {
            Key::BOOL(_) => 1,
            Key::INT(_) => 8,
            Key::UID(_) => 16,
            Key::STR(_) => 64,
            Key::TEXT(_) => 256,
        }
    }

    /// Convert the type into binary format. It only contains the data of the type
    /// itself, not including the type information.
    fn to_bytes(&self) -> Vec<u8> {
        let mut data: Vec<u8> = match self {
            Key::BOOL(b) => vec![*b as u8],
            Key::INT(i) => i.to_ne_bytes().to_vec(),
            Key::UID(uid) => uid.to_ne_bytes().to_vec(),
            Key::STR(s) => s.as_bytes().to_vec(),
            Key::TEXT(s) => s.as_bytes().to_vec(),
        };

        data.extend(vec![0; self.cap() - data.len()]);
        data
    }

    /// Convert from binary format to the type. It only contains the data of the type
    /// itself, not including the type information.
    fn from_bytes(data: &[u8]) -> Result<Self> {
        match data.len() {
            1 => Ok(Key::BOOL(data[0] != 0)),
            8 => {
                let mut buf = [0u8; 8];
                buf.copy_from_slice(data);
                Ok(Key::INT(i64::from_ne_bytes(buf)))
            }
            16 => {
                let mut buf = [0u8; 16];
                buf.copy_from_slice(data);
                Ok(Key::UID(u128::from_ne_bytes(buf)))
            }
            64 | 256 => match data.iter().rposition(|&b| b != 0) {
                Some(index) => {
                    let s = String::from_utf8_lossy(&data[..index + 1]).to_string();
                    Ok(Key::STR(s))
                }
                None => Ok(Key::STR("".to_string())),
            },
            _ => Err(Error::InvalidArgument),
        }
    }
}

impl Packer for Key {
    /// Convert the type into binary format with type information.
    fn pack(&self) -> Vec<u8> {
        let typ: u8 = match self {
            Key::BOOL(_) => 0,
            Key::INT(_) => 1,
            Key::UID(_) => 2,
            Key::STR(_) => 3,
            Key::TEXT(_) => 4,
        };

        let mut data = vec![typ];

        data.extend(self.to_bytes());
        data
    }

    /// Convert from binary format to the type, which the binary format contains the
    /// type information.
    fn unpack(data: &[u8]) -> Result<(Self, &[u8])>
    where
        Self: Sized,
    {
        if data.len() < 2 {
            return Err(Error::InvalidArgument);
        }

        let rest: &[u8] = &data[1..];
        let size: usize = match data[0] {
            0 => 1,
            1 => 8,
            2 => 16,
            3 => 64,
            4 => 256,
            _ => return Err(Error::InvalidArgument),
        };

        if rest.len() < size {
            warn!(
                "expected the length of rest data is {}, but got {}",
                size,
                rest.len()
            );
            return Err(Error::InvalidArgument);
        }

        let (data, rest) = rest.split_at(size);
        let key = Key::from_bytes(data)?;

        Ok((key, rest))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use paste::paste;

    macro_rules! test_key_convert {
        ($type:ident, $value:expr) => {
            paste! {
                #[test]
                fn [<test_key_convert_ $type:lower _ $value>]() {
                    let key: Key = $value.into();
                    assert_eq!(key, Key::$type($value.into()));
                }

                #[test]
                fn [<test_key_converter_ $type:lower _ $value>]() {
                    let key: Key = $value.into();
                    let data: Vec<u8> = key.to_bytes();

                    assert_eq!(data.len(), key.cap());
                    assert_eq!(Key::from_bytes(&data), Ok(key));
                }

                #[test]
                fn [<test_key_packer_ $type:lower _ $value>]() {
                    let key: Key = $value.into();
                    let rest: &[u8] = &[];

                    assert_eq!(Key::unpack(&key.pack()), Ok((key, rest)));
                }
            }
        };
    }

    #[test]
    fn test_invalid_key_convert() {
        let v: Vec<u8> = vec![1, 2, 3];
        assert_eq!(Key::from_bytes(&v), Err(Error::InvalidArgument));
    }

    test_key_convert!(BOOL, true);
    test_key_convert!(BOOL, false);
    test_key_convert!(INT, 0);
    test_key_convert!(INT, 1);
    test_key_convert!(INT, 65535);
    test_key_convert!(INT, 4294967295i64);
    test_key_convert!(UID, 18446744073709551616u128);
    test_key_convert!(UID, 36893488147419103231u128);
    test_key_convert!(UID, 340282366920938463463374607431768211455u128);
    test_key_convert!(STR, "");
    test_key_convert!(STR, "a");
    test_key_convert!(STR, "aaaaaa");

    macro_rules! test_key_unpack_iter {
        ($count:expr) => {
            paste! {
                #[test]
                fn [<test_key_unpack_iter_ $count>]() {
                    let size: usize = $count;
                    let mut data: Vec<u8> = vec![];

                    for i in 0..size {
                        let key: Key = i.into();
                        data.extend(key.pack());
                    }

                    assert_eq!(Key::unpack_iter(&data).count(), size);
                }
            }
        };
    }

    test_key_unpack_iter!(0);
    test_key_unpack_iter!(1);
    test_key_unpack_iter!(2);
    test_key_unpack_iter!(16);
    test_key_unpack_iter!(64);
    test_key_unpack_iter!(4096);
    test_key_unpack_iter!(65535);
}
