//! The RevDB builder and constructor.
use crate::settings::Settings;

/// The RevDB builder.
#[derive(Debug, Default)]
pub struct Builder {
    settings: Settings,
}

impl Builder {
    /// build the RevDB by the given settings.
    pub fn build(&self) -> RevDB {
        RevDB {
            settings: self.settings.clone(),
        }
    }
}

/// The instance for RevDB storage.
pub struct RevDB {
    settings: Settings,
}

impl RevDB {
    /// create a new RevDB builder.
    pub fn builder() -> Builder {
        Builder::default()
    }

    /// get the settings of RevDB.
    pub fn settings(&self) -> &Settings {
        &self.settings
    }
}
