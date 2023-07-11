//! The persistence layer for Papyrus which stores key-value pairs in local files.
//!
//! All the layers in this module are designed to store key-value pairs in local
//! file system, serve the requests from the clients, and operate the data in
//! file(s).

mod file;
mod wal;

pub(crate) use wal::WALLayer;

use crate::layers::traits::Layer;
use tracing::trace;
use url::Url;

pub fn get_file_layer(url: &Url) -> Option<Box<dyn Layer>> {
    match url.scheme() {
        "wal" => match WALLayer::open(url) {
            Ok(layer) => Some(Box::new(layer)),
            Err(err) => {
                trace!("failed to open {}: {:?}", &url, err);
                None
            }
        },
        _ => {
            trace!("failed to get file layer: {:?}", url);
            None
        }
    }
}
