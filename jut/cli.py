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

from jut import Config, ParsingException, Render, RenderingException, ValidationError

logger = logging.getLogger(__name__)


def download_url(url):
    url_parts = urlparse(url)
    try:
        destination = url_parts.path.split("/")[-1]
        urlretrieve(url, destination)
    except HTTPError:
        logger.info(f'Failed to download the file in the URL" {url}')
        exit(-1)
    return destination


def handle_stdin() -> Path:
    """Receive input from stdin and store it in a sample file.

    Returns
    -------
        The path to the temporary file
    """
    buf = ""
    for line in sys.stdin:
        buf += line
    filename = "stdin.ipynb"
    with open(filename, "w") as fp:
        fp.write(buf)
    return Path(filename)


@click.command()
@click.option(
    "-u", "--url", type=str, default="", help="Render the ipynb file from the URL"
)
@click.option(
    "-i",
    "--input-file",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help="File from the local file-system",
)
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
    "--stdin",
    type=bool,
    default=False,
    is_flag=True,
    help="Receive the input from the stdin",
)
def display(
    url,
    input_file,
    head,
    tail,
    single_page,
    full_display,
    force_colors,
    start,
    end,
    stdin,
):
    destination_file = None
    if url:
        destination_file = download_url(url)
        destination_file = Path(destination_file)

    if input_file:
        destination_file = input_file

    if stdin:
        destination_file = handle_stdin()
    elif not (url or input_file):
        click.echo("pass --url or --input-file value", err=True)
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
        )
        render = Render(config)
        render.render()

        if url or stdin:
            Path(destination_file).unlink()
    except (ValidationError, ParsingException, RenderingException) as e:
        rich.print(e)
        exit(-1)


def main():
    display()


if __name__ == "__main__":
    main()
