use btclib::types::Block;
use btclib::util::Saveable;
use clap::Parser;
use std::fs::File;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[arg(short, long)]
    block_file: String
}

fn main() {
    let cli = Cli::parse();
    if let Ok(file) = File::open(cli.block_file) {
        let block = Block::load(file).expect("Failed to load block");
        println!("{:#?}", block);
    }
}