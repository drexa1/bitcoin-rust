use btclib::types::Transaction;
use btclib::util::Saveable;
use clap::Parser;
use std::fs::File;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[arg(short, long)]
    tx_file: String
}

fn main() {
    let cli = Cli::parse();
    if let Ok(file) = File::open(cli.tx_file) {
        let tx = Transaction::load(file).expect("Failed to load transaction");
        println!("{:#?}", tx);
    }
}