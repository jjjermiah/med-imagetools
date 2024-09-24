from dataclasses import dataclass, field
from typing import Dict, Any
from pydicom import FileDataset, dcmread
from pydicom.dicomdir import DicomDir
from pydicom.dataset import Dataset

DICOM_BASE_METADATA_KEYS = {
    "BodyPartExamined",
    "DataCollectionDiameter",
    "NumberOfSlices",
    "SliceThickness",
    "ScanType",
    "ScanProgressionDirection",
    "PatientPosition",
    "ContrastType",
    "Manufacturer",
    "ScanOptions",
    "RescaleType",
    "RescaleSlope",
    "ManufacturerModelName",
}


# Base class for DICOM-related classes
@dataclass
class DICOMBase:
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dicom(cls, dicom_path: str) -> "DICOMBase":
        dicom_data: FileDataset | DicomDir = dcmread(dicom_path, force=True)
        metadata = cls._extract_common_metadata(dicom_data)
        return cls(metadata=metadata)

    @staticmethod
    def _extract_common_metadata(
        dicom_data: FileDataset | DicomDir | Dataset
    ) -> Dict[str, Any]:
        """Extract common DICOM metadata that applies across modalities."""
        return {k: getattr(dicom_data, k, None) for k in DICOM_BASE_METADATA_KEYS}
