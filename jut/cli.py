"""CLI interface
"""
import logging
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlretrieve

import click
import rich

from jut import (Config, ParsingException, Render, RenderingException,
                 ValidationError)

logger = logging.getLogger(__name__)


def parse_path(path: str):
    """Given a path return a tuple of (URL, local_file_path).
    At any given point, either url or local_path will be present.
    """
    # Note: It's a simpler solution only draw back is URL like foo.com/mydrive/notebook.ipynb will be treated as file.
    parts = urlparse(path)
    if parts.scheme and parts.netloc:
        return path, ""
    return "", path


def download_url(url):
    url_parts = urlparse(url)
    try:
        destination = url_parts.path.split("/")[-1]
        urlretrieve(url, destination)
    except HTTPError:
        logger.info(f'Failed to download the file in the URL" {url}')
        exit(-1)
    return destination


@click.command()
@click.argument("path", type=str)
@click.option(
    "-he",
    "--head",
    type=click.IntRange(min=1),
    default=10,
    help="Display first n cells. Default is 10",
)
@click.option(
    "-t",
    "--tail",
    type=click.IntRange(min=1),
    default=None,
    help="Display last n cells",
)
@click.option(
    "-p",
    "--single-page",
    type=bool,
    default=False,
    is_flag=True,
    help="Should the result be in a single page?",
)
@click.option(
    "-f",
    "--full-display",
    type=bool,
    default=False,
    is_flag=True,
    help="Should all the contents in the file displayed?",
)
@click.option(
    "--force-colors",
    type=bool,
    default=False,
    is_flag=True,
    help="Force colored output even if stdout is not a terminal",
)
@click.option(
    "-s",
    "--start",
    type=click.IntRange(min=1),
    default=None,
    help="Display the cells starting from the cell number",
)
@click.option(
    "-e",
    "--end",
    type=click.IntRange(min=1),
    default=None,
    help="Display the cells till the cell number",
)
@click.option(
    "--exclude-output-cells",
    type=bool,
    help="Exclude the notebook output cells from the output",
    default=False,
    is_flag=True,
)
@click.option(
    "--no-cell-border",
    type=bool,
    help="Don't display the result in a cell with border",
    default=False,
    is_flag=True,
)
def display(
    path,
    head,
    tail,
    single_page,
    full_display,
    force_colors,
    start,
    end,
    exclude_output_cells,
    no_cell_border,
):
    destination_file = None
    url, input_file = parse_path(path)

    if url:
        destination_file = download_url(url)
        destination_file = Path(destination_file)

    if input_file:
        destination_file = Path(input_file)

    if not destination_file.exists():
        click.echo(
            f"PATH: {path} should be URL or path to a local file. The file is missing.",
            err=True,
        )
        ctx = click.get_current_context()
        click.echo(display.get_help(ctx))
        exit(-1)

    try:
        config = Config(
            input_file=destination_file,
            head=head,
            tail=tail,
            single_page=single_page,
            full_display=full_display,
            force_colors=force_colors,
            start=start,
            end=end,
            exclude_output_cells=exclude_output_cells,
            no_cell_border=no_cell_border,
        )
        render = Render(config)
        render.render()

        if url:
            Path(destination_file).unlink()
    except (ValidationError, ParsingException, RenderingException) as e:
        rich.print(e)
        exit(-1)


def main():
    display()


if __name__ == "__main__":
    main()
