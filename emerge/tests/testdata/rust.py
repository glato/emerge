# Minimal Rust samples for parser tests.

RUST_TEST_FILES = {
    "lib.rs": """
use std::collections::HashMap;
use serde::Deserialize;
mod config;
pub use crate::inner::helper;

pub fn demo() -> HashMap<u32, String> {
    HashMap::new()
}
""",
    "main.rs": """
use std::io::{self, Write};

fn main() -> io::Result<()> {
    io::stdout().write_all(b"ok\\n")?;
    Ok(())
}
""",
}
