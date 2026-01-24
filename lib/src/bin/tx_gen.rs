use btclib::crypto::PrivateKey;
use btclib::types::{Transaction, TransactionOutput};
use btclib::util::Saveable;
use clap::Parser;
use uuid::Uuid;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[arg(short, long)]
    tx_file: String
}

fn main() {
    let cli = Cli::parse();

    let private_key = PrivateKey::new_key();
    let transaction = Transaction::new(
        vec![],
        vec![TransactionOutput {
            unique_id: Uuid::new_v4(),
            value: btclib::INITIAL_REWARD * 10u64.pow(8),
            public_key: private_key.public_key(),
        }],
    );

    transaction.save_to_file(cli.tx_file).expect("Failed to save transaction");
    println!("Saved");
}
