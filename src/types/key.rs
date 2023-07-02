//! Key is the searchable and sortable data type used in Papyrus.
use std::convert::From;
use tracing::error;

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

impl Key {
    /// the capacity of the Key type
    pub fn cap(&self) -> usize {
        match self {
            Key::BOOL(_) => 1,
            Key::INT(_) => 8,
            Key::UID(_) => 16,
            Key::STR(_) => 64,
            Key::TEXT(_) => 256,
        }
    }
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
            }
        };
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
}
