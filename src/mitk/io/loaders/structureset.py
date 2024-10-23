from concurrent.futures import ProcessPoolExecutor
import pydicom.misc
from mitk.io.loaders import DICOMBase
from mitk.io import find_dicoms
from mitk.mitk import modality
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from pydicom import dcmread
import pydicom.dataset
from pydicom.errors import InvalidDicomError
import pydicom
from loguru import logger
import numpy as np
from pathlib import Path
import sys  # set logger to DEBUG level
from itertools import chain
from rich import print, progress


from multiprocessing import Pool
import multiprocessing
from rich.pretty import Pretty
from rich.console import Console
from rich.panel import Panel
import time

import click

console = Console()

logger.remove()


def _log_formatter(record: dict) -> str:
    """Log message formatter"""
    color_map = {
        "TRACE": "dim blue",
        "DEBUG": "cyan",
        "INFO": "bold",
        "SUCCESS": "bold green",
        "WARNING": "yellow",
        "ERROR": "bold red",
        "CRITICAL": "bold white on red",
    }
    lvl_color = color_map.get(record["level"].name, "cyan")
    return (
        "[not bold green]{time:YYYY/MM/DD HH:mm:ss}[/not bold green] | {level.icon}"
        + f"  - [{lvl_color}]{{message}}[/{lvl_color}]"
    )


# logger.add(sys.stdout, level="INFO")
# logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)

# add rich


@dataclass
class ROI:
    ROIName: str
    ROINumber: int
    ReferencedFrameOfReferenceUID: str
    Contour: List[np.ndarray]

    def __post_init__(self):
        self.ROINumber = int(self.ROINumber)
        assert self.ROINumber >= 0

        if isinstance(self.Contour, pydicom.dataset.Dataset):
            self.Contour = self._get_roi_points(self.ROIName, roi=self.Contour)

    @staticmethod
    def _get_roi_points(
        roi_name,
        roi: pydicom.dataset.Dataset,
        allow_last_missing_slice: bool = True,
    ) -> List[np.ndarray[Any, np.dtype[Any]]]:
        # Extract contour points from ROIContourSequence (3D points)
        if not hasattr(roi, "ContourSequence"):
            logger.warning(
                f"ROI {roi_name} does not have a ContourSequence attribute."
                "Returning an empty list."
            )
            return []

        try:
            logger.debug(
                f"For ROI {roi_name}, the ContourSequence has {len(roi.ContourSequence)} slices."
            )
            return [
                np.array(slc.ContourData).reshape(-1, 3) for slc in roi.ContourSequence
            ]
        except AttributeError:
            if not allow_last_missing_slice:
                raise AttributeError(
                    "A slice in the ROIContourSequence is missing. This is likely due to a missing slice in the DICOM file."
                )
            try:
                pts = [
                    np.array(slc.ContourData).reshape(-1, 3)
                    for slc in roi.ContourSequence[:-1]
                ]
                if pts:
                    logger.warning(
                        f"For ROI {roi_name}, The last slice is missing in the RTSTRUCT"
                        "file, but the rest of the slices are present. "
                        f"While ContourSequence has {len(roi.ContourSequence)} slices, "
                        f"only the first {len(pts)} slices will be used."
                    )
                return pts
            except AttributeError:
                logger.warning(
                    "A slice that is not the last in the ROIContourSequence is missing for "
                    f"ROI {roi_name}. "
                    "Returning an empty list."
                )
                return []

    def __repr__(self) -> str:
        # Get the number of contours
        num_contours = len(self.Contour)

        # Get the first and last contour shapes
        first_contour_shape = self.Contour[0].shape if num_contours > 0 else None
        last_contour_shape = self.Contour[-1].shape if num_contours > 1 else None

        # Construct the representation string
        contour_summary = (num_contours, first_contour_shape, last_contour_shape)

        # Return the pretty representation
        return f"ROI(ROIName={self.ROIName}, ROINumber={self.ROINumber}, num_contours,first_contour_shape,last_contour_shape={contour_summary})"


@dataclass
class ROISet:
    roi_list: List[ROI]

    @classmethod
    def from_rtstruct(cls, rtstruct: pydicom.dataset.Dataset) -> "ROISet":
        """Initializes the ROISet class from a RTSTRUCT dataset."""
        roi_list = []

        for roi in rtstruct.StructureSetROISequence:
            roi_points = ROI._get_roi_points(
                roi.ROIName,
                roi=ROISet.get_contour(roi.ROINumber, rtstruct),
                allow_last_missing_slice=True,
            )
            if not roi_points:
                logger.warning(
                    f"ROI {roi.ROIName} has no contour points. Skipping this ROI."
                )
                continue
            roi_list.append(
                ROI(
                    ROIName=roi.ROIName,
                    ROINumber=roi.ROINumber,
                    ReferencedFrameOfReferenceUID=roi.ReferencedFrameOfReferenceUID,
                    Contour=roi_points,
                )
            )

        return cls(roi_list=roi_list)

    @staticmethod
    def get_contour(
        roi_number: int, rtstruct: pydicom.dataset.Dataset
    ) -> pydicom.dataset.Dataset:
        """Get the contour for a given ROI number from the RTSTRUCT dataset."""
        for roi in rtstruct.ROIContourSequence:
            if int(roi.ReferencedROINumber) == roi_number:
                return roi
        raise ValueError(f"ROI number {roi_number} not found in RTSTRUCT dataset.")

    @property
    def roi_names(self) -> List[str]:
        """Returns the names of all ROIs in the StructureSet."""
        return [roi.ROIName for roi in self.roi_list]


@dataclass
class StructureSet(DICOMBase):
    roi_list: Optional[ROISet] = None

    @classmethod
    def from_rtstruct_path(
        cls,
        rtstruct_path: str | Path | pydicom.dataset.Dataset,
        force_dcmread: bool = False,
    ) -> "StructureSet":
        """Initializes the StructureSet class containing contour points

        Parameters
        ----------
        rtstruct_path
            Path to the DICOM RTSTRUCT file.
        """
        if isinstance(rtstruct_path, pydicom.dataset.Dataset):
            if rtstruct_path.modality == "RTSTRUCT":
                return cls.from_dataset(rtstruct_path)
            else:
                logger.error(
                    "The provided dataset is not an RTSTRUCT dataset."
                    f"Received modality: {rtstruct_path.Modality}"
                )
                raise ValueError("The provided dataset is not an RTSTRUCT dataset.")

        if not isinstance(rtstruct_path, Path):
            rtstruct_path = Path(rtstruct_path)

        if not rtstruct_path.exists():
            raise FileNotFoundError(f"RTSTRUCT file not found at {rtstruct_path}")
        elif not rtstruct_path.is_file():
            raise ValueError(f"{rtstruct_path} is not a file")

        try:
            rtstruct = dcmread(rtstruct_path, force=force_dcmread)
        except InvalidDicomError as ide:
            logger.error(f"Error reading RTSTRUCT file: {ide}")
            raise

        return cls.from_dataset(rtstruct)

    @classmethod
    def from_dataset(cls, dataset: pydicom.dataset.Dataset) -> "StructureSet":
        """Initializes the StructureSet class containing contour points"""
        metadata = cls._extract_common_metadata(dataset)
        metadata.update(cls._extract_rtstruct_metadata(dataset))
        roi_list = ROISet.from_rtstruct(dataset)
        return cls(
            metadata=metadata,
            roi_list=roi_list,
        )

    @staticmethod
    def _extract_rtstruct_metadata(rtstruct_data) -> Dict[str, Any]:
        """Extract RTSTRUCT-specific metadata."""
        num_rois = len(rtstruct_data.StructureSetROISequence)
        referenced_series_uid = (
            getattr(rtstruct_data, "ReferencedFrameOfReferenceSequence", [{}])[0]
            .get("RTReferencedStudySequence", [{}])[0]
            .get("RTReferencedSeriesSequence", [{}])[0]
            .get("SeriesInstanceUID", None)
        )

        return {
            "numROIs": num_rois,
            "ReferencedSeriesUID": referenced_series_uid,
        }

    @property
    def roi_names(self) -> List[str]:
        """Returns the names of all ROIs in the StructureSet."""
        return self.roi_list.roi_names if self.roi_list else []

    def __rich_repr__(self):
        # return metadata after filtering out None values
        yield "metadata", {k: v for k, v in self.metadata.items() if v is not None}

        if len(self.roi_names) > 0:
            yield "ROI Names", self.roi_names

    __rich_repr__.angular = True


def process_dicom_file(file_path: Path) -> StructureSet:
    """Processes a single DICOM file into a StructureSet."""
    try:
        # Assuming each file is a DICOM RTSTRUCT file; adjust as necessary
        logger.info(f"Processing DICOM file: {file_path}")
        return StructureSet.from_rtstruct_path(file_path)
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        raise ValueError(f"Error processing file {file_path}: {e}")


def is_rtstruct(p: Path) -> bool:
    return (
        dcmread(p, stop_before_pixels=True, specific_tags=["Modality"]).Modality
        == "RTSTRUCT"
    )
    # return modality(p.as_posix()) == "RTSTRUCT"


def get_dicom_files(dicom_dir: Path, progress: dict, task_id: int) -> List[Path]:
    """Wrapper to run find_dicoms for a single directory and return a list of paths."""
    # CAN REPLACE THIS WITH RUST TOOL!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Materialize the generator into a list before returning
    files = list(
        find_dicoms(
            root=dicom_dir,
            recursive=True,
            yield_directories=False,
            filter_pattern="*.dcm",
            validate_func=is_rtstruct,
        )
    )
    progress[task_id] = {"progress": 1, "total": 1}
    return files


def process_path(p) -> StructureSet:
    return StructureSet.from_rtstruct_path(p)


@click.command()
@click.argument(
    "dicom_dirs",
    nargs=-1,
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        resolve_path=True,
        path_type=Path,
    ),
)
@click.option(
    "--n_proc",
    "-n",
    type=int,
    default=40,
    help="Number of processes to use for parallel processing.",
)
@click.option(
    "--verbosity",
    "-v",
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"]),
    default="INFO",
    envvar="LOG_LEVEL",
    help="Set the logging level.",
)
def main(dicom_dirs: List[Path], n_proc: int, verbosity: str):
    N_PROC = n_proc
    if len(dicom_dirs) == 0:
        logger.error("No DICOM directories provided.")
        return
    logger.info(f"Processing {len(dicom_dirs)} DICOM directories...")

    dicom_file_paths = []
    structure_set_list = []
    with progress.Progress(
        "[progress.description]{task.description}",
        progress.BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        progress.MofNCompleteColumn(),
        "Time elapsed:",
        progress.TimeElapsedColumn(),
        "Time remaining:",
        progress.TimeRemainingColumn(compact=True),
        refresh_per_second=10,  # bit slower updates
        transient=True,
        console=console,
    ) as progress_bar:
        msg = f"Searching DICOM directories..."
        task = progress_bar.add_task(f"{msg:.<21}", total=len(dicom_dirs))

        futures = []  # keep track of the jobs
        start = time.time()
        with multiprocessing.Manager() as manager:
            _progress = manager.dict()
            with ProcessPoolExecutor(N_PROC) as executor:
                for i, dicom_dir in enumerate(dicom_dirs):
                    task_id = progress_bar.add_task(
                        f"task {i} : {dicom_dir.name}",
                        total=len(dicom_dirs),
                        visible=False,
                    )
                    futures.append(
                        executor.submit(get_dicom_files, dicom_dir, _progress, task_id)  # type: ignore
                    )

                while (n_finished := sum([future.done() for future in futures])) < len(
                    futures
                ):
                    progress_bar.update(task, completed=n_finished, total=len(futures))
                    for task_id, result in _progress.items():
                        latest = result["progress"]
                        total = result["total"]
                        progress_bar.update(
                            task_id,
                            completed=latest,
                            total=total,
                            visible=latest < total,
                            refresh=True,
                        )
                else:
                    progress_bar.update(task, completed=n_finished, total=len(futures))
                    # complete all the tasks
                    for task_id, result in _progress.items():
                        latest = result["progress"]
                        total = result["total"]
                        progress_bar.update(
                            task_id,
                            completed=latest,
                            total=total,
                            visible=latest < total,
                            refresh=True,
                        )

                    # Collect results
                    for future in futures:
                        dicom_file_paths.extend(future.result())
        print(f"\nTime taken: {time.time() - start:.2f} seconds")

    #     create_structuresets_task = progress_bar.add_task(
    #         "Creating StructureSets...", total=len(dicom_file_paths)
    #     )
    #     futures = []  # keep track of the jobs
    #     with ProcessPoolExecutor(max_workers=N_PROC) as executor:
    #         for i, dicom_file_path in enumerate(dicom_file_paths):
    #             task_id = progress_bar.add_task(
    #                 f"task {i} : {dicom_file_path.name}",
    #                 total=len(dicom_file_paths),
    #                 visible=False,
    #             )
    #             futures.append(executor.submit(process_path, dicom_file_path))

    #         while (n_finished := sum([future.done() for future in futures])) < len(
    #             futures
    #         ):
    #             progress_bar.update(
    #                 create_structuresets_task, completed=n_finished, total=len(futures)
    #             )

    #         # Collect results
    #         for future in futures:
    #             structure_set_list.append(future.result())

    # logger.info(f"\n\nProcessed {len(structure_set_list)} RTSTRUCT files.")
    # print(structure_set_list[0])

    # # print(f"Found {len(dicom_file_paths)} RTSTRUCT files.")

    # # logger.info(f"\n\nProcessed {len(rtstruct_list)} RTSTRUCT files.")
    # # logger.info(f"Time taken: {time.time() - start:.2f} seconds")

    # # # logger.info(f"Found {len(list(files))} DICOM files.")
    # start = time.time()

    # with Pool() as pool:
    #     rt_list: List[StructureSet] = pool.map(process_path, dicom_file_paths)

    # print(f"\n\nTime taken: {time.time() - start:.2f} seconds")
    # print(f"\n\nTime taken: {time.time() - start:.2f} seconds")
    # print(f"Found {len(rtstruct_list)} RTSTRUCT files.")
    # print(rt_list[:2])


if __name__ == "__main__":
    main()
