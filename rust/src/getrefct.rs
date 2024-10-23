
use clap::Parser;

use std::fmt::Debug;

use mitk::modality;
#[derive(Parser, Debug)]
#[command(name = "DICOM Processor")]
#[command(about = "A tool to process DICOM files", long_about = None)]
struct Args {
    /// Path to a dicom file instead
    #[arg(short, long)]
    dicomfile: Option<String>,
}

fn main() {
    let args = Args::parse();
    if let Some(path) = args.dicomfile {
        let found_modality = modality::getrefct(path.as_str());
        println!("ref ct: {}", found_modality);
    } else {
      println!("No file provided");
      return;
    }
}
