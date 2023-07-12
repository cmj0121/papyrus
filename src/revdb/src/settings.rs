//! The global settings for RevDB.
use serde::{Deserialize, Serialize};

/// The global settings for RevDB based on YAML.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Settings {
    /// to enable the debug information
    pub debug: bool,
}

impl Default for Settings {
    fn default() -> Self {
        Self { debug: false }
    }
}
