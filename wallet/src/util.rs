use crate::core::{Config, Core, FeeConfig, FeeType, Recipient};
use anyhow::Result;
use std::path::PathBuf;
use text_to_ascii_art::to_art;

/// Generate a start config
pub(crate) fn generate_config(path: &PathBuf) -> Result<()> {
    let config = Config {
        my_keys: vec![],
        contacts: vec![
            Recipient {
                name: "drexa".to_string(),
                key: PathBuf::from("drexa.pub.pem"),
            },
            Recipient {
                name: "ian".to_string(),
                key: PathBuf::from("ian.pub.pem"),
            }
        ],
        default_node: "127.0.0.1:9000".to_string(),
        fee_config: FeeConfig { fee_type: FeeType::Percent, value: 0.1 }
    };
    let config_str = toml::to_string_pretty(&config)?;
    std::fs::write(path, config_str)?;
    log::info!("Config generated at: {}", path.display());
    Ok(())
}

pub fn sats_to_btc(sats: u64) -> String {
    let btc = sats as f64 / 100_000_000.0;
    format!("{} BTC", btc)
}

/// Make it big
pub fn big_mode_btc(core: &Core) -> String {
    let btc_value = sats_to_btc(core.get_balance()).to_string();
    to_art(btc_value, "standard", 80, 8, 1).unwrap()
}