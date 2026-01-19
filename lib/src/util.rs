use std::fs::File;
use std::io::{Read, Result as IoResult, Write};
use std::path::Path;

pub trait Saveable
where
    Self: Sized
{
    fn load<I: Read>(reader: I) -> IoResult<Self>;

    fn save<O: Write>(&self, writer: O) -> IoResult<()>;

    fn save_to_file<P: AsRef<Path>>(&self, path: P) -> IoResult<()> {
        let file = File::create(&path)?;
        self.save(file)
    }

    fn load_from_file<P: AsRef<Path>>(path: P) -> IoResult<Self> {
        let file = File::open(&path)?;
        Self::load(file)
    }
}