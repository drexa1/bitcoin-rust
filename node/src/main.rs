mod util;
mod message_handler;

use std::path::Path;
use clap::Parser;
use anyhow::{Result};
use dashmap::DashMap;
use static_init::dynamic;
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::RwLock;
use btclib::types::Blockchain;

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
pub static NODES: DashMap<String, TcpStream> = DashMap::new();  // Immutable hash map

#[tokio::main]
async fn main() -> Result<()> {
    // Parse command line arguments
    let cli = Cli::parse();
    let port = cli.port;
    let blockchain_file = cli.blockchain_file;
    let nodes = cli.nodes;

    util::populate_connections(&nodes).await?;
    println!("Known nodes: {}", NODES.len());
    // Check if the blockchain_file exists
    if Path::new(&blockchain_file).exists() {
        util::load_blockchain(&blockchain_file).await?;
    } else {
        println!("Blockchain file does not exist!");
        if nodes.is_empty() {
            println!("No nodes provided, starting as a seed node");
        } else {
            let (longest_name, longest_count) = util::find_longest_chain_node().await?;
            // Request the blockchain from the node with the longest blockchain
            util::download_blockchain(&longest_name, longest_count).await?;
            println!("blockchain downloaded from {}", longest_name);
            {
                let mut blockchain = BLOCKCHAIN.write().await;
                blockchain.rebuild_utxos();  // Recalculate utxos
                blockchain.try_adjust_target();  // Adjust difficulty
            }
        }
    }

    // Start the listener
    let addr = format!("0.0.0.0:{}", port);
    let listener = TcpListener::bind(&addr).await?;
    println!("Listening on {}", addr);
    // Start a task to periodically clean up the mempool
    tokio::spawn(util::cleanup());
    // and a task to periodically save the blockchain
    tokio::spawn(util::save(blockchain_file.clone()));
    loop {
        let (socket, _) = listener.accept().await?;
        tokio::spawn(message_handler::handle(socket));
    }
}