//! The global settings for RevDB.
use serde::{Deserialize, Serialize};
use tracing::warn;

/// The global settings for RevDB based on YAML.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Settings {
    /// to enable the debug information
    pub debug: bool,

    /// the base directory for the storage
    pub base: String,
}

impl Settings {
    /// Load the settings from the given file.
    pub fn load(path: Option<String>) -> Self {
        match path {
            None => Self::default(),
            Some(path) => match std::fs::read_to_string(&path) {
                Ok(content) => match serde_yaml::from_str(&content) {
                    Ok(settings) => return settings,
                    Err(err) => {
                        warn!("failed to parse the settings: {}", err);

                        Self::default()
                    }
                },
                Err(_) => {
                    warn!("failed to read the settings file: {}", &path);

                    Self::default()
                }
            },
        }
    }

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
