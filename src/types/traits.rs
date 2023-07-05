//! The abstraction of Type.
use crate::Result;

/// The type converter that can convert between type and binary format.
pub trait Converter {
    /// the capacity of the type.
    fn cap(&self) -> usize;

    /// Convert the type into binary format. It only contains the data of the type
    /// itself, not including the type information.
    fn to_bytes(&self) -> Vec<u8>;

    /// Convert from binary format to the type. It only contains the data of the type
    /// itself, not including the type information.
    fn from_bytes(data: &[u8]) -> Result<Self>
    where
        Self: Sized;
}

/// The abstraction of Converter with the type information within the binary format.
pub trait Packer {
    /// Convert the type into binary format with type information.
    fn pack(&self) -> Vec<u8>;

    /// Convert from binary format to the type, which the binary format contains the
    /// type information.
    fn unpack(data: &[u8]) -> Result<(Self, &[u8])>
    where
        Self: Sized;

    /// Convert from binary format into the iterate of the type as many as possible,
    /// which the binary format contains the type information.
    fn unpack_iter(data: &[u8]) -> Box<dyn Iterator<Item = Self> + '_>
    where
        Self: Sized,
    {
        let mut remains: &[u8] = data;

        Box::new(std::iter::from_fn(move || {
            if remains.is_empty() {
                return None;
            }

            let (value, rest) = Self::unpack(remains).ok()?;
            remains = rest;

            Some(value)
        }))
    }
}
