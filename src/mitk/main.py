from mitk.mitk import modality
import click
from pathlib import Path


@click.command()
@click.argument(
    "dicomfile",
    type=click.Path(
        exists=True,
        path_type=Path,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
)
def main(dicomfile: Path):
    """
    A tool to process DICOM files.
    """
    
    import time
    start = time.time()
    m = modality(dicomfile.as_posix())
    print(f"Modality: {m}, time taken: {time.time() - start:.4f} milliseconds")

if __name__ == "__main__":
    main()