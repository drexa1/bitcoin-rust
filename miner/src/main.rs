mod miner;

use anyhow::{anyhow, Result};
use btclib::crypto::PublicKey;
use btclib::util::Saveable;
use clap::Parser;
use env_logger::Env;
use miner::Miner;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[arg(short, long)]
    node: String,
    #[arg(short, long)]
    public_key_file: String
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::Builder::from_env(Env::default().default_filter_or("info")).init();
    let cli = Cli::parse();
    let public_key = PublicKey::load_from_file(&cli.public_key_file).map_err(|e| {
        anyhow!("Error reading public key: {}", e)
    })?;
    let miner: Miner = Miner::new(cli.node, public_key).await?;
    miner.run().await
}