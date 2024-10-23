use dicom::core::value::Value;
use dicom::core::{DicomValue, PrimitiveValue, Tag};
use dicom::dictionary_std::tags;
use dicom::object::{FileDicomObject, InMemDicomObject, OpenFileOptions, StandardDataDictionary};
use pyo3::prelude::*;
use std::env;

#[derive(Debug)]
enum Modality {
    RTSTRUCT,
    CT,
    RTDOSE,
    SEG,
    RTPLAN,
    Unknown(String),
}
impl ToString for Modality {
    fn to_string(&self) -> String {
        match self {
            Modality::RTSTRUCT => "RTSTRUCT",
            Modality::CT => "CT",
            Modality::RTDOSE => "RTDOSE",
            Modality::SEG => "SEG",
            Modality::RTPLAN => "RTPLAN",
            Modality::Unknown(modality) => modality,
        }
        .to_string()
    }
}

const REF_UID_ORDER: &[Tag] = &[
    // tags::Referenced Frame of Reference Sequence
    tags::REFERENCED_FRAME_OF_REFERENCE_SEQUENCE,
    // tags::RT Referenced Study Sequence
    tags::RT_REFERENCED_STUDY_SEQUENCE,
    // tags::RT Referenced Series Sequence
    tags::RT_REFERENCED_SERIES_SEQUENCE,
    // tags::Series Instance UID
    tags::SERIES_INSTANCE_UID,
];

fn traverse_sequence(obj: &InMemDicomObject, tags: &[Tag]) -> Option<Vec<String>> {
    if tags.is_empty() {
        return None;
    }

    let current_tag = tags[0];
    let remaining_tags = &tags[1..];

    if let Ok(element) = obj.element(current_tag) {
        if remaining_tags.is_empty() {
            // Base case: We're at the last tag, extract the primitive values
            if let Value::Primitive(PrimitiveValue::Strs(strings)) = element.value() {
                return Some(strings.to_vec());
            }
        } else {
            // Recursive case: Traverse the sequence
            if let Some(seq) = element.value().items() {
                let mut collected_values = Vec::new();
                for item in seq {
                    if let Some(mut values) = traverse_sequence(item, remaining_tags) {
                        collected_values.append(&mut values);
                    }
                }
                if !collected_values.is_empty() {
                    return Some(collected_values);
                }
            }
        }
    }

    None
}

#[pyfunction]
#[pyo3(signature = (path=None))]
pub fn modality(path: Option<&str>) -> String {
    let modality = match path {
        Some(p) => get_modality(p),
        None => return "".to_string(),
    };
    modality.to_string()
}

fn get_modality(path: &str) -> Modality {
    let obj = OpenFileOptions::new()
        .read_until(tags::MODALITIES_IN_STUDY)
        .open_file(path)
        .unwrap();

    let modality_str = obj
        .element(tags::MODALITY)
        .unwrap()
        .to_str()
        .unwrap()
        .to_string();

    match modality_str.as_ref() {
        "RTSTRUCT" => Modality::RTSTRUCT,
        "CT" => Modality::CT,
        "RTDOSE" => Modality::RTDOSE,
        "SEG" => Modality::SEG,
        "RTPLAN" => Modality::RTPLAN,
        other => Modality::Unknown(other.to_string()),
    }
}

#[pyfunction]
#[pyo3(signature = (path))]
pub fn getrefct(path: &str) -> String {
    let obj = OpenFileOptions::new()
        .read_until(tags::PIXEL_DATA)
        .open_file(path)
        .unwrap();

    if let Some(uids) = traverse_sequence(&obj, &REF_UID_ORDER) {
        return uids.join(",");
    } else {
        return "".to_string();
    }
}

#[pyfunction]
fn modality_cli(py: Python) -> PyResult<()> {
    // Get the first argument from the command line
    let arg2 = env::args().nth(2).unwrap();

    // print them
    // println!("arg1: {}", arg1); // this is just the name of the executable
    // println!("arg2: {}", arg2); // this is the path

    let modality = modality(Some(arg2.as_str()));
    println!("Modality: {}", modality);

    Ok(())
}

/// A Python module implemented in Rust.
#[pymodule]
fn mitk(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(modality, m)?)?;
    m.add_wrapped(wrap_pyfunction!(modality_cli))?;
    Ok(())
}

// Unit tests
#[cfg(test)]
mod tests {
    use super::*;

    // Example test for the Modality enum's `to_string` method
    #[test]
    fn test_modality_to_string() {
        assert_eq!(Modality::CT.to_string(), "CT");
        assert_eq!(Modality::Unknown("Other".to_string()).to_string(), "Other");
    }

    // Example test for the get_modality function using a mocked path
    #[test]
    fn test_get_modality() {
        // Assuming `get_modality` can be tested with a valid DICOM file
        // You could mock this functionality or use a real test DICOM file for more accuracy.
        let modality = get_modality("/home/bioinf/bhklab/radiomics/radiomics_orcestra/rawdata/HNSCC/images/unzipped/HNSCC-01-0006/Study-57410/CT-41643/1.dcm");
        // Here you would check the result against your expectations
        assert!(matches!(modality, Modality::CT));

        let modality2 = get_modality("/home/bioinf/bhklab/radiomics/radiomics_orcestra/rawdata/HNSCC/images/unzipped/HNSCC-01-0006/Study-57410/RTSTRUCT-09366/1.dcm");
        assert!(matches!(modality2, Modality::RTSTRUCT));
    }
}

// export the modality function so it can be used in main.rs
