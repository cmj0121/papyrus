//! The global settings for RevDB.
use serde::{Deserialize, Serialize};

/// The global settings for RevDB based on YAML.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Settings {
    /// to enable the debug information
    pub debug: bool,

    /// the base directory for the storage
    pub base: String,
}

impl Settings {
    /// Get the default base directory.
    fn default_basedir() -> String {
        match home::home_dir() {
            Some(path) => path.join(".revdb").to_str().unwrap().to_string(),
            None => ".revdb".to_string(),
        }
    }
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            debug: false,
            base: Self::default_basedir(),
        }
    }
}
