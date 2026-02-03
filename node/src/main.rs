mod util;
mod message_handler;

use std::path::Path;
use std::sync::Arc;
use clap::Parser;
use anyhow::Result;
use dashmap::DashMap;
use env_logger::Env;
use static_init::dynamic;
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::{Mutex, RwLock};
use btclib::types::Blockchain;
use log::{info, warn};


#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[arg(short, long, default_value_t = 9000)]
    port: u16,
    #[arg(short = 'f', long)]
    blockchain_file: String,
    #[arg()]
    nodes: Vec<String>
}

#[dynamic]
pub static BLOCKCHAIN: RwLock<Blockchain> = RwLock::new(Blockchain::new());  // RwLock for sync

#[dynamic]
pub static NODES: DashMap<String, Arc<Mutex<TcpStream>>> = DashMap::new();  // Immutable map of address and stream

#[tokio::main]
async fn main() -> Result<()> {
    // Init logger
    env_logger::Builder::from_env(Env::default().default_filter_or("info")).init();

    // Parse command line arguments
    let cli = Cli::parse();
    let port = cli.port;
    let blockchain_file = cli.blockchain_file;
    let nodes = cli.nodes;

    // Check if the blockchain_file exists
    if Path::new(&blockchain_file).exists() {
        info!("✅  Blockchain file '{}' exists", blockchain_file);
        util::load_blockchain(&blockchain_file).await?;
    } else {
        warn!("❌  Blockchain file '{}' does not exist", blockchain_file);
        if nodes.is_empty() {
            info!("No nodes provided, starting as a seed node");
        } else {
            let (longest_node, longest_count) = util::find_longest_chain_node().await?;
            // Request the blockchain from the node with the longest blockchain
            util::download_blockchain(&longest_node, longest_count).await?;
            info!("↪️ Blockchain downloaded from [{}]", longest_node);
            {
                let mut blockchain = BLOCKCHAIN.write().await;
                blockchain.rebuild_utxos();     // Recalculate utxos
                blockchain.try_adjust_target(); // Adjust difficulty
            }
        }
    }

    // Start the listener
    let bind_addr = format!("0.0.0.0:{}", port);
    let listener = TcpListener::bind(&bind_addr).await?;
    info!("👂 Listening on {}", bind_addr);

    // Node discovery
    let node_addr = format!("localhost:{}", port);
    util::populate_connections(&node_addr, &nodes).await?;

    // Start a task to periodically clean up the mempool
    tokio::spawn(util::mempool_cleanup());
    // and a task to periodically save the blockchain
    tokio::spawn(util::save(blockchain_file.clone()));
    loop {
        let (socket, _) = listener.accept().await?;
        tokio::spawn(message_handler::handle(socket));
    }
}
