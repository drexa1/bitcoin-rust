use clap::Parser;
use btclib::crypto::PrivateKey;
use btclib::util::Saveable;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[arg(short, long)]
    public_key_file: String
}

fn main() {
    let cli = Cli::parse();

    let private_key = PrivateKey::new_key();
    let public_key = private_key.public_key();
    let public_key_file = cli.public_key_file.clone() + ".pub.pem";
    let private_key_file = cli.public_key_file.clone() + ".priv.cbor";

    private_key.save_to_file(&private_key_file).unwrap();
    public_key.save_to_file(&public_key_file).unwrap();
    println!("Saved");
}