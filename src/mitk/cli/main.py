from pathlib import Path
from typing import Generator

import rich_click as click
from rich_click import rich_config

from .helpers import AliasedGroup
from mitk.logging_config import setup_logger
from loguru import logger
from mitk.io.locators import find_dicoms as _find_dicoms

__version__ = "0.1.0"


click.rich_click.STYLE_OPTIONS_TABLE_BOX = "SIMPLE"
click.rich_click.STYLE_COMMANDS_TABLE_SHOW_LINES = True
click.rich_click.STYLE_COMMANDS_TABLE_PAD_EDGE = True
click.rich_click.STYLE_COMMANDS_TABLE_COLUMN_WIDTH_RATIO = (1, 5)

click.rich_click.OPTION_GROUPS = {
    "damply": [
        {
            "name": "Basic options",
            "options": ["--help", "--version"],
        },
    ]
}

click.rich_click.COMMAND_GROUPS = {
    "mitk": [
        {
            "name": "Basic Commands",
            "commands": ["autopipeline", "dicomsort", "index"],
        },
        {
            "name": "Conversion Commands",
            "commands": [
                "dicom2nrrd",
                "dicom2nifti",
                "nifti2nrrd",
                "nrrd2dicom",
                "nrrd2nifti",
            ],
        },
    ]
}


help_config = click.RichHelpConfiguration(
    show_arguments=True,
    option_groups={"damply": [{"name": "Arguments", "panel_styles": {"box": "ASCII"}}]},
)


@click.group(
    cls=AliasedGroup,
    name="mitk",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(__version__, prog_name="mitk")
def cli() -> None:
    """
    med-imagetools (mitk) is a tool for working with medical imaging data.
    
    CLI tools because you deserve better than just "autopipeline"
    """
    pass


@cli.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "directory",
    type=click.Path(
        exists=True,
        path_type=Path,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    default=Path().cwd(),
)
def index(directory: Path) -> None:
    """
    Index a directory of DICOM files.
    """
    pass


@cli.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "directory",
    type=click.Path(
        exists=True,
        path_type=Path,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    default=Path().cwd(),
)
def dicomsort(directory: Path) -> None:
    """
    Sort DICOM files by defined pattern rules.
    """
    pass


@cli.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "directory",
    type=click.Path(
        exists=True,
        path_type=Path,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    default=Path().cwd(),
)
def autopipeline(directory: Path) -> None:
    """
    original autopipeline 🤢.
    """
    pass


@cli.command()
def dicom2nrrd():
    """
    Convert DICOM files to NRRD files.
    """
    pass


@cli.command()
def dicom2nifti():
    """
    Convert DICOM files to NIFTI files.
    """
    pass


# @cli.command()
# def nifti2nrrd():
#     """
#     Convert NIFTI files to NRRD files.
#     """
#     pass

# @cli.command()
# def nrrd2dicom():
#     """
#     Convert NRRD files to DICOM files.
#     """
#     pass

# @cli.command()
# def nrrd2nifti():
#     """
#     Convert NRRD files to NIFTI files.
#     """
#     pass


@cli.command()
@click.argument(
    "directory",
    type=click.Path(
        exists=True,
        path_type=Path,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    default=Path().cwd(),
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
)
def find_dicoms(directory: Path, log_level: str) -> None:
    """
    Find DICOM files in a directory.
    """
    setup_logger(level=log_level)
    result: Generator[Path, None, None] = _find_dicoms(directory)

    # get length of results generator
    length = len(list(result))
    logger.info(f"Found {length} DICOM files.")


if __name__ == "__main__":
    cli()
