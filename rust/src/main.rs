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
    if args.dicomfile.is_some() {
        let path = args.dicomfile.unwrap();
        let found_modality = modality::modality(Some(path.as_str()));
        println!("Modality: {}", found_modality);
    }else{
      println!("No file provided");
      return;
    }
}