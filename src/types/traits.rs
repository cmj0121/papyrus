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
