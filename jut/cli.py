"""CLI interface
"""
import logging
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlretrieve

import click

from jut import (Config, ParsingException, Render, RenderingException,
                 ValidationError)

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


@click.command()
@click.option(
    "-u", "--url", type=str, default="", help="Render the ipynb file from the URL"
)
@click.option(
    "-i", "--input-file", type=click.File(), help="File from the local file-system"
)
@click.option(
    "-h", "--head", type=int, default=10, help="Display first n cells. Default is 10"
)
@click.option("-t", "--tail", type=int, default=-1, help="Display last n cells")
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
def display(url, input_file, head, tail, single_page, full_display):
    destination_file = None
    if url:
        destination_file = download_url(url)
        destination_file = Path(destination_file)

    if input_file:
        destination_file = input_file

    if not (url or input_file):
        click.echo("pass --url or --input-file value", err=True)
        ctx = click.get_current_context()
        click.echo(display.get_help(ctx))
        exit(-1)

    if tail > 0:
        head = 0

    try:
        config = Config(
            input_file=destination_file,
            head=head,
            tail=tail,
            single_page=single_page,
            full_display=full_display,
        )
        render = Render(config)
        render.render()
    except (ValidationError, ParsingException, RenderingException) as e:
        render.console.print(e)


def main():
    display()


if __name__ == "__main__":
    main()
