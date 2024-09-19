import rich_click as click
from pathlib import Path
from .helpers import AliasedGroup

__version__ = '0.1.0'

@click.group(
    cls=AliasedGroup,
    name='imgtools',
    context_settings={'help_option_names': ['-h', '--help']},
)
@click.version_option(__version__, prog_name='imgtools')
def cli() -> None:
    """
    A tool to interact with systems implementing the 
    Data Management Plan (DMP) standard.
    
    This tool is meant to allow sys-admins to easily query and audit the metadata of their
    projects.
    """
    pass

@cli.command(context_settings={'help_option_names': ['-h', '--help']})
@click.argument(
    'directory',
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


@cli.command(context_settings={'help_option_names': ['-h', '--help']})
@click.argument(
    'directory',
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

@cli.command(context_settings={'help_option_names': ['-h', '--help']})
@click.argument(
    'directory',
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
    original autopipeline.
    """
    pass

if __name__ == '__main__':
    cli()