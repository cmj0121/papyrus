//! The basic file layer implementation for Papyrus.
use crate::{Error, Result};
use std::io::{Read, Write};
use tracing::warn;

/// The basic file layer implementation for Papyrus.
///
/// This layer is designed to store key-value pairs in local and single file,
/// provide the basic operations. It has three sections: header, meta and data.
/// The header section define how to read the file with the meta and data information.
///
/// The header section is 16 bytes binary format data, which is defined as below:
///
///   - magic    always be `\x30\x14\x15\x92`.
///   - version  the version of the file format, now is 1.
///   - type     the type of the file, depends on the layer implementation.
///   - flags    the extra flags of the file.
///
/// 0       8      16     24     32     40     48     56     64
/// +------+------+------+------+------+------+------+------+
/// |           MAGIC           |  VER | TYPE |    FLAGS    |
/// +-------------------------------------------------------+
/// ~                                                       ~
/// ~                         Data                          ~
/// ~                                                       ~
/// +-------------------------------------------------------+
#[derive(Debug)]
pub struct FileLayer {
    /// the path of the file.
    path: std::path::PathBuf,

    /// the file descriptor of the file, which may not opened yet.
    file: Option<std::fs::File>,
}

#[allow(dead_code)]
impl FileLayer {
    /// the magic number of the file header.
    const MAGIC: [u8; 4] = [0x30, 0x14, 0x15, 0x92];
    /// the default version of the file header.
    const VERSION: u8 = 0;

    /// Create an new file layer by the specified file path.
    pub fn new(path: &str, meta: Option<(u8, u16)>) -> Result<Self> {
        let path = std::path::PathBuf::from(path);
        let mut layer = Self { path, file: None };

        layer.open(meta)?;
        Ok(layer)
    }

    fn open(&mut self, meta: Option<(u8, u16)>) -> Result<()> {
        if let Some(_) = self.file {
            return Ok(());
        }

        let exists = self.path.exists();

        let mut file = std::fs::OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(&self.path)?;

        match (exists, meta) {
            (true, _) => {
                // check the file header
                let mut header = [0u8; 8];

                file.read_exact(&mut header)?;
                Self::verify(header, meta)?;
            }
            (false, Some((typ, flags))) => {
                let header = FileLayer::header(typ, flags);

                // write the file header
                file.write_all(&header)?;
            }
            _ => {
                warn!("cannot open layer without meta");
                return Err(Error::InvalidArgument);
            }
        };

        self.file = Some(file);
        Ok(())
    }

    /// Create the file header.
    fn header(typ: u8, flags: u16) -> [u8; 8] {
        let mut header = [0u8; 8];

        header[0..4].copy_from_slice(&Self::MAGIC);
        header[4] = Self::VERSION;
        header[5] = typ;
        header[6..8].copy_from_slice(&flags.to_be_bytes());

        header
    }

    /// Verify the current header is valid or not
    fn verify(header: [u8; 8], meta: Option<(u8, u16)>) -> Result<()> {
        let hdr_magic = &header[0..4];
        let hdr_ver = header[4];
        let hdr_typ = header[5];
        let hdr_flags = u16::from_be_bytes([header[6], header[7]]);

        let check_meta = match meta {
            Some((typ, flags)) => hdr_typ == typ && hdr_flags == flags,
            None => true,
        };

        let check = check_meta && hdr_magic == &Self::MAGIC && hdr_ver == Self::VERSION;
        if !check {
            warn!("invalid file header");
            return Err(Error::InvalidArgument);
        }

        Ok(())
    }
}

impl Drop for FileLayer {
    fn drop(&mut self) {
        if let Some(file) = &self.file {
            let _ = file.sync_all();

            drop(file);
            self.file = None;
        }
    }
}
