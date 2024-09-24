from pathlib import Path
from typing import Callable, Generator, Optional, Union

from loguru import logger
from pydicom.misc import is_dicom
import sys
logger.remove()

logger.add(sys.stderr, level="ERROR")

def find_dicoms(
    root: Union[str, Path],
    recursive: bool = True,
    yield_directories: bool = False,
    filter_pattern: str = "*.dcm",
    validate_func: Optional[Callable[[Path], bool]] = is_dicom,
) -> Generator[Path, None, None]:
    """Find DICOM file paths in the specified root directory file tree."""
    root_path = Path(root)
    if not root_path.exists():
        logger.error(f"The provided root path '{root}' does not exist.")
        return
    if not root_path.is_dir():
        logger.error(f"The provided root path '{root}' is not a directory.")
        return

    logger.info(f"Searching for DICOM files in {root}")

    try:
        if recursive:
            iterator = root_path.rglob(filter_pattern)
        else:
            iterator = root_path.glob(filter_pattern)

        for path in iterator:
            try:
                if path.is_dir() and yield_directories:
                    logger.debug(f"Yielding directory: {path}")
                    yield path
                elif path.is_file():
                    if validate_func and not validate_func(path):
                        logger.debug(
                            # f"File {path} did not pass validation and will be skipped."
                            f"This file did not pass validation and will be skipped: {path}"
                        )
                        continue
                    logger.debug(f"Yielding file: {path}")
                    yield path
            except (PermissionError, FileNotFoundError) as e:
                logger.error(f"Error processing path '{path}': {e}")
                # continue for loop to process other files
            except Exception as e:
                logger.error(f"Unexpected error processing path '{path}': {e}")
                raise  # Re-raise the exception to avoid silent failures
    except (PermissionError, FileNotFoundError) as e:
        logger.error(f"Error walking through the directory '{root}': {e}")
    except Exception as e:
        logger.error(f"Unexpected error walking through the directory '{root}': {e}")
        raise  # Re-raise the exception to avoid silent failures


def find_niftis(
    root: Union[str, Path],
    recursive: bool = True,
    yield_directories: bool = False,
    filter_pattern: str = "*.nii.gz",
) -> Generator[Path, None, None]:
    """Find NIFTI file paths in the specified root directory file tree."""
    raise NotImplementedError
