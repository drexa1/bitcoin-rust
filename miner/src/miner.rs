use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time::Duration;
use anyhow::anyhow;
use flume::{Receiver, Sender};
use tokio::net::TcpStream;
use tokio::sync::Mutex;
use tokio::time::interval;
use btclib::crypto::PublicKey;
use btclib::network::Message;
use btclib::types::Block;
use log::{info, warn};

pub struct Miner {
    public_key: PublicKey,
    conn: Mutex<TcpStream>,
    current_template: Arc<std::sync::Mutex<Option<Block>>>,
    mining: Arc<AtomicBool>,
    mined_block_receiver: Receiver<Block>,
    mined_block_sender: Sender<Block>
}
impl Miner {
    pub(crate) async fn new(address: String, public_key: PublicKey) -> anyhow::Result<Self> {
        let stream = TcpStream::connect(&address).await?;
        let (mined_block_sender, mined_block_receiver) = flume::unbounded();
        info!("🔗 Connected to node: [{}]", address);
        Ok(Self {
            public_key,
            conn: Mutex::new(stream),
            current_template: Arc::new(std::sync::Mutex::new(None)),
            mining: Arc::new(AtomicBool::new(false)),
            mined_block_sender,
            mined_block_receiver
        })
    }

    pub(crate) async fn run(&self) -> anyhow::Result<()> {
        self.spawn_mining_thread();
        let mut template_interval = interval(Duration::from_secs(5));
        loop {
            let receiver_clone = self.mined_block_receiver.clone();
            tokio::select! {
                _ = template_interval.tick() => {
                    self.fetch_and_validate_template().await?;
                }
                Ok(mined_block) = receiver_clone.recv_async() => {
                    self.submit_block(mined_block).await?;
                }
            }
        }
    }

    fn spawn_mining_thread(&self) -> thread::JoinHandle<()> {
        let template = self.current_template.clone();
        let mining = self.mining.clone();
        let sender = self.mined_block_sender.clone();
        thread::spawn(move || loop {
            if mining.load(Ordering::Relaxed) {
                if let Some(mut block) = template.lock().unwrap().clone() {
                    if block.header.mine(2_000_000) {
                        info!("📦️Block mined: {}{}", " ".repeat(22), block.hash());
                        sender.send(block).expect("Failed to send mined block", );
                        mining.store(false, Ordering::Relaxed);
                    }
                }
            }
            thread::yield_now();
        })
    }

    async fn fetch_and_validate_template(&self) -> anyhow::Result<()> {
        if !self.mining.load(Ordering::Relaxed) {
            self.fetch_template().await?;
        } else {
            self.validate_template().await?;
        }
        Ok(())
    }

    async fn fetch_template(&self) -> anyhow::Result<()> {
        info!("Fetching new template");
        let message = Message::FetchTemplate(self.public_key.clone());
        let mut conn_lock = self.conn.lock().await;
        message.send_async(&mut *conn_lock).await?;
        drop(conn_lock);
        let mut conn_lock = self.conn.lock().await;
        match Message::receive_async(&mut *conn_lock).await? {
            Message::Template(template) => {
                drop(conn_lock);
                info!("↪️ Received new template with target: {}", template.header.target);
                *self.current_template.lock().unwrap() = Some(template);
                self.mining.store(true, Ordering::Relaxed);
                Ok(())
            }
            _ => Err(anyhow!("Unexpected message received when fetching template")),
        }
    }

    async fn validate_template(&self) -> anyhow::Result<()> {
        if let Some(template) = self.current_template.lock().unwrap().clone() {
            let message = Message::ValidateTemplate(template);
            let mut conn_lock = self.conn.lock().await;
            message.send_async(&mut *conn_lock).await?;
            drop(conn_lock);
            let mut conn_lock = self.conn.lock().await;
            match Message::receive_async(&mut *conn_lock).await? {
                Message::TemplateValidity(valid) => {
                    drop(conn_lock);
                    if !valid {
                        warn!("Current template is no longer valid");
                        self.mining.store(false, Ordering::Relaxed);
                    } else {
                        info!("Current template is still valid");
                    }
                    Ok(())
                }
                _ => Err(anyhow!("Unexpected message received when validating template")),
            }
        } else {
            Ok(())
        }
    }

    async fn submit_block(&self, block: Block) -> anyhow::Result<()> {
        info!("🚚 Submitting mined block");
        let message = Message::SubmitTemplate(block, self.public_key.clone());
        let mut conn_lock = self.conn.lock().await;
        message.send_async(&mut *conn_lock).await?;
        self.mining.store(false, Ordering::Relaxed);
        Ok(())
    }
}