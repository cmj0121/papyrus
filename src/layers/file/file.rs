//! The basic file layer implementation for Papyrus.
use crate::{Error, Result};
use std::io::{Read, Seek, SeekFrom, Write};
use tracing::warn;

pub trait FileLayer {
    const TYPE: u8;
}

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
///   - pid      the PID of the current process.
///   - checksum the checksum of the header.
///
/// 0       8      16     24     32     40     48     56     64
/// +------+------+------+------+------+------+------+------+
/// |           MAGIC           |  VER | TYPE |    FLAGS    |
/// +-------------------------------------------------------+
/// |           PID             |         CHECKSUM          |
/// +-------------------------------------------------------+
/// ~                                                       ~
/// ~                         Data                          ~
/// ~                                                       ~
/// +-------------------------------------------------------+
#[derive(Debug)]
pub struct FileBaseLayer {
    /// the path of the file.
    path: std::path::PathBuf,

    /// the file descriptor of the file, which may not opened yet.
    file: Option<std::fs::File>,

    /// the metadata of the file.
    ver: Option<u8>,
    typ: Option<u8>,
    flags: Option<u16>,
}

#[allow(dead_code)]
impl FileBaseLayer {
    /// the magic number of the file header.
    const MAGIC: [u8; 4] = [0x30, 0x14, 0x15, 0x92];
    /// the default version of the file header.
    const VERSION: u8 = 1;
    /// the total size of the header
    const HEADER_SIZE: usize = 16;

    /// Create an new file layer by the specified file path.
    pub fn new(path: &str, meta: Option<(u8, u16)>) -> Result<Self> {
        let path = std::path::PathBuf::from(path);
        let mut layer = Self {
            path,
            file: None,
            typ: None,
            flags: None,
            ver: None,
        };

        layer.open(meta)?;
        Ok(layer)
    }

    /// Get the type of the file.
    pub fn typ(&self) -> u8 {
        self.typ.expect("file layer not opened")
    }

    /// Get the flags of the file.
    pub fn flags(&self) -> u16 {
        self.flags.expect("file layer not opened")
    }

    /// Read data from data section by the specified offset and length.
    pub fn read_at(&mut self, buff: &mut [u8], offset: usize) -> Result<()> {
        self.seek(offset)?;

        let file = self.file.as_mut().expect("file layer not opened");
        file.read_exact(buff)?;

        Ok(())
    }

    /// Read all data from data section.
    pub fn read_to_end(&mut self, buff: &mut Vec<u8>) -> Result<()> {
        self.seek(0)?;

        let file = self.file.as_mut().expect("file layer not opened");
        file.read_to_end(buff)?;

        Ok(())
    }

    /// Write data into data section by the specified offset and length.
    pub fn write_at(&mut self, buff: &[u8], offset: usize) -> Result<()> {
        self.seek(offset)?;

        let file = self.file.as_mut().expect("file layer not opened");
        file.write_all(buff)?;

        Ok(())
    }

    /// Write data into the end of data section.
    pub fn append(&mut self, buff: &[u8]) -> Result<()> {
        // re-open the current file
        let meta = (self.typ(), self.flags());
        self.open(Some(meta))?;

        let file = self.file.as_mut().expect("file layer not opened");
        let _ = file.seek(SeekFrom::End(0))?;

        file.write_all(buff)?;

        Ok(())
    }

    /// Get the file descriptor of the current file, may reopen the file if not opened yet.
    pub fn file(&mut self) -> &mut std::fs::File {
        if let None = self.file {
            let meta = Some((self.typ(), self.flags()));
            let _ = self.open(meta);
        }

        self.file.as_mut().expect("file layer not opened")
    }

    /// Unlink the current file.
    pub fn unlink(&mut self) {
        if let Some(file) = &self.file {
            let _ = file.sync_all();

            drop(file);
            self.file = None;
        }

        // there is no guarantee that the file is immediately deleted,
        // in this case we can only ignore the error
        let _ = std::fs::remove_file(&self.path);
    }

    /// Migrate from another file layer.
    pub fn migrate_from_file(&mut self, path: &str) -> Result<()> {
        self.close()?;

        std::fs::rename(path, &self.path)?;
        self.open(None)?;

        Ok(())
    }
}

/// The private methods of FileBaseLayer
impl FileBaseLayer {
    /// Open the current file with the optional meta information.
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
                let mut header = [0u8; Self::HEADER_SIZE];

                file.read_exact(&mut header)?;

                let (ver, typ, flags) = Self::verify(header, meta)?;
                self.ver = Some(ver);
                self.typ = Some(typ);
                self.flags = Some(flags);
            }
            (false, Some((typ, flags))) => {
                let header = FileBaseLayer::header(typ, flags, false);

                // write the file header
                file.write_all(&header)?;

                self.ver = Some(Self::VERSION);
                self.typ = Some(typ);
                self.flags = Some(flags);
            }
            _ => {
                warn!("cannot open layer without meta");
                return Err(Error::InvalidArgument);
            }
        };

        self.file = Some(file);

        self.lock()?;
        Ok(())
    }

    /// Close the opened file.
    fn close(&mut self) -> Result<()> {
        self.unlock()?;

        if let Some(file) = &self.file {
            let _ = file.sync_all();

            drop(file);
            self.file = None;
        }

        Ok(())
    }

    /// Lock the current file with the PID of the current process.
    /// It modify the file header and erase when the process exits.
    fn lock(&mut self) -> Result<()> {
        let pid: u32 = std::process::id();
        if self.locked(pid) {
            // file already open and not locked by current process
            return Err(Error::Locked);
        }

        let header = FileBaseLayer::header(self.typ(), self.flags(), true);
        let file = self.file();

        file.seek(SeekFrom::Start(0))?;
        file.write_all(&header)?;

        Ok(())
    }

    /// Unlink the current file and erase PID on the file header.
    fn unlock(&mut self) -> Result<()> {
        // only erase the PID when file exists
        let header = FileBaseLayer::header(self.typ(), self.flags(), false);

        if let Some(file) = &mut self.file {
            file.seek(SeekFrom::Start(0))?;
            file.write_all(&header)?;
        }

        Ok(())
    }

    /// check file locked by the current process.
    fn locked(&mut self, pid: u32) -> bool {
        let mut header = [0u8; Self::HEADER_SIZE];
        let file = self.file();

        file.seek(SeekFrom::Start(0)).expect("seek file failed");
        let resp = match file.read_exact(&mut header) {
            Ok(_) => {
                let locked_pid: u32 =
                    u32::from_be_bytes([header[8], header[9], header[10], header[11]]);

                !(locked_pid == 0 || pid == locked_pid)
            }
            Err(_) => false,
        };

        resp
    }

    /// Change the current position of file descriptor.
    fn seek(&mut self, offset: usize) -> Result<()> {
        // re-open the current file
        let meta = (self.typ(), self.flags());
        self.open(Some(meta))?;

        let file = self.file.as_mut().expect("file layer not opened");
        let _ = file.seek(SeekFrom::Start((Self::HEADER_SIZE + offset) as u64))?;

        Ok(())
    }

    /// Create the file header.
    fn header(typ: u8, flags: u16, locked: bool) -> [u8; Self::HEADER_SIZE] {
        let mut header = [0u8; Self::HEADER_SIZE];

        header[0..4].copy_from_slice(&Self::MAGIC);
        header[4] = Self::VERSION;
        header[5] = typ;
        header[6..8].copy_from_slice(&flags.to_be_bytes());

        if locked {
            let pid: u32 = std::process::id();
            header[8..12].copy_from_slice(&pid.to_be_bytes());
        }

        let checksum = Self::checksum(&header[0..12]);
        header[12..16].copy_from_slice(&checksum.to_be_bytes());

        header
    }

    /// Verify the current header is valid or not
    fn verify(header: [u8; Self::HEADER_SIZE], meta: Option<(u8, u16)>) -> Result<(u8, u8, u16)> {
        let checksum = u32::from_be_bytes([header[12], header[13], header[14], header[15]]);
        let verify = Self::checksum(&header[0..12]);

        if checksum != verify {
            warn!("invalid file header checksum: {} != {}", checksum, verify);
            return Err(Error::InvalidArgument);
        }

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

        Ok((hdr_ver, hdr_typ, hdr_flags))
    }

    /// Calculate the checksum to u32.
    fn checksum(data: &[u8]) -> u32 {
        let chksum = crc::Crc::<u32>::new(&crc::CRC_32_CKSUM);
        chksum.checksum(data)
    }
}

impl Drop for FileBaseLayer {
    fn drop(&mut self) {
        let _ = self.unlock();

        if let Some(file) = &self.file {
            let _ = file.sync_all();

            drop(file);
            self.file = None;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct TestContext {
        layer: FileBaseLayer,
    }

    impl TestContext {
        fn new(file: &str, meta: Option<(u8, u16)>) -> Self {
            let layer = FileBaseLayer::new(file, meta);

            assert_eq!(layer.is_ok(), true);
            Self {
                layer: layer.unwrap(),
            }
        }
    }

    impl Drop for TestContext {
        fn drop(&mut self) {
            std::fs::remove_file(&self.layer.path).unwrap();
        }
    }

    #[test]
    fn test_create_file_layer() {
        let typ: u8 = 1;
        let flags: u16 = 0x1234;

        let file = "test_create_file_layer";
        let ctx = TestContext::new(file, Some((typ, flags)));

        let path = std::path::PathBuf::from(file);

        assert_eq!(ctx.layer.path, path);
        assert_eq!(ctx.layer.typ(), typ);
        assert_eq!(ctx.layer.flags(), flags);
    }

    #[test]
    fn test_open_file_layer() {
        let typ: u8 = 1;
        let flags: u16 = 0x1234;

        let file = "test_open_file_layer";
        let mut ctx = TestContext::new(file, Some((typ, flags)));
        drop(&ctx.layer);

        ctx.layer = FileBaseLayer::new(file, None).unwrap();
        let path = std::path::PathBuf::from(file);

        assert_eq!(ctx.layer.path, path);
        assert_eq!(ctx.layer.typ(), typ);
        assert_eq!(ctx.layer.flags(), flags);
    }

    #[test]
    fn test_read_write_at() {
        let typ: u8 = 1;
        let flags: u16 = 0x1234;

        let file = "test_read_write_at";
        let mut ctx = TestContext::new(file, Some((typ, flags)));

        let data: &[u8] = &[0x01, 0x02, 0x03, 0x04];
        let mut buff: [u8; 4] = [0u8; 4];

        assert_eq!(ctx.layer.write_at(data, 0), Ok(()));
        assert_eq!(ctx.layer.read_at(&mut buff, 0), Ok(()));
        assert_eq!(buff, data);
    }

    #[test]
    fn test_read_to_end() {
        let typ: u8 = 1;
        let flags: u16 = 0x1234;

        let file = "test_read_to_end";
        let mut ctx = TestContext::new(file, Some((typ, flags)));

        let data: &[u8] = &[0x01, 0x02, 0x03, 0x04];
        let mut buff: Vec<u8> = Vec::new();

        assert_eq!(ctx.layer.write_at(data, 0), Ok(()));
        assert_eq!(ctx.layer.read_to_end(&mut buff), Ok(()));
        assert_eq!(buff, data);
    }

    #[test]
    fn test_write_append() {
        let typ: u8 = 1;
        let flags: u16 = 0x1234;

        let file = "test_write_append";
        let mut ctx = TestContext::new(file, Some((typ, flags)));

        let data: &[u8] = &[0x01, 0x02, 0x03, 0x04];
        let mut buff: [u8; 4] = [0u8; 4];

        assert_eq!(ctx.layer.write_at(data, 0), Ok(()));
        assert_eq!(ctx.layer.append(data), Ok(()));

        assert_eq!(ctx.layer.read_at(&mut buff, 0), Ok(()));
        assert_eq!(buff, data);

        assert_eq!(ctx.layer.read_at(&mut buff, 4), Ok(()));
        assert_eq!(buff, data);
    }

    #[test]
    fn test_file_locked() {
        let typ: u8 = 1;
        let flags: u16 = 0x1234;
        let pid: u32 = std::process::id();

        let file = "test_file_locked";
        let mut ctx = TestContext::new(file, Some((typ, flags)));
        let layer = &mut ctx.layer;

        assert_eq!(layer.locked(pid), false);
        assert_eq!(layer.locked(0), true);
    }

    #[test]
    fn test_file_lock_release() {
        let typ: u8 = 1;
        let flags: u16 = 0x1234;
        let pid: u32 = std::process::id();

        let file = "test_file_lock_release";
        let mut ctx = TestContext::new(file, Some((typ, flags)));
        let layer = &mut ctx.layer;

        assert_eq!(layer.locked(pid), false);
        assert_eq!(layer.locked(0), true);

        // close and release the file lock
        drop(&layer);
        let _ = layer.open(None);

        assert_eq!(layer.locked(pid), false);
        assert_eq!(layer.locked(0), true);
    }
}
