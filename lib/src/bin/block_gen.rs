use btclib::crypto::Hash;
use btclib::crypto::{MerkleRoot, PrivateKey};
use btclib::types::{Block, BlockHeader, Transaction, TransactionOutput};
use btclib::util::Saveable;
use chrono::Utc;
use clap::Parser;
use uuid::Uuid;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[arg(short, long)]
    block_file: String
}

fn main() {
    let cli = Cli::parse();

    let private_key = PrivateKey::new_key();
    let transactions = vec![Transaction::new(
        vec![],
        vec![TransactionOutput {
            unique_id: Uuid::new_v4(),
            value: btclib::INITIAL_REWARD * 10u64.pow(8),
            public_key: private_key.public_key(),
        }]
    )];
    let merkle_root = MerkleRoot::calculate(&transactions);
    let block = Block::new(
        BlockHeader::new(
            Utc::now(),
            0,
            Hash::zero(),
            merkle_root,
            btclib::MIN_TARGET
        ), transactions
    );

    block.save_to_file(cli.block_file).expect("Failed to save block");
    println!("Saved");
}