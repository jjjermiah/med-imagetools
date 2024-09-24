from pathlib import Path
import click

from mitk.io.locators import find_dicoms
from pydicom import dcmread


@click.command()
@click.argument(
    "root",
    type=click.Path(
        exists=True,
        dir_okay=True,
        path_type=Path,
        resolve_path=True,
    ),
)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    default=True,
    help="Search recursively for DICOM files in the specified root directory.",
)
def find_cli(root: Path, recursive: bool):
    paths = find_dicoms(
        root,
        recursive,
        validate_func=lambda p: dcmread(
            p,
            stop_before_pixels=True,
            specific_tags=["Modality"],
        ).Modality
        == "RTSTRUCT",
    )
    all_paths = list(paths)
    print(f"Found {len(all_paths)} DICOM files in {root}")
    print(all_paths[:2])


if __name__ == "__main__":
    find_cli()
