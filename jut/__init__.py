"""Render and formatter code.
"""

import io
from enum import Enum
from pathlib import Path, PosixPath
from typing import Any

import nbformat
from pydantic import BaseModel, ValidationError, validator
from rich.columns import Columns
from rich.console import Console, RenderGroup
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.theme import Theme


class ParsingException(Exception):
    """Exception to raise during parsing"""


class RenderingException(Exception):
    """Exception to raise during rendering."""


class CellType(Enum):
    MARKDOWN = "markdown"
    CODE = "code"
    RAW = "raw"


OUTPUT_TYPES_TO_LEXER_NAMES = {
    "text": "python",
    "text/plain": "python",
    "text/html": "html",
    "application/vnd.jupyter.widget-view+json": "json",
    "application/x-ipynb+json": "json",
    "application/vnd.geo+json": "json",
    "application/geo+json": "json",
    "application/geo+json": "json",
    "application/vnd.plotly.v1+json": "json",
    "application/vdom.v1+json": "json",
    "image/png": "png",
    "image/jpg": "jpg",
    "text/latex": "latex",
    "image/svg+xml": "svg",
    "image/jpeg": "jpeg",
    "image/gif": "gif",
    "application/pdf": "pdf",
}


def can_render_in_terminal(mime_type: str):
    """Can the mime_type be rendered in the terminal as it is?

    Parameters
    ----------
    mime_type: mime_type of the cell content.
    """
    return mime_type not in ("png", "jpg", "jpeg", "gif", "svg", "pdf", "latex")


class Config(BaseModel):
    """Input config passed by the user."""

    input_file: Any
    head: int
    tail: int
    single_page: bool
    full_display: bool

    @validator("input_file")
    def validate_input_file(cls, val):
        if not isinstance(val, (io.TextIOWrapper, PosixPath)):
            raise ValueError(f"input_file is not valid path: {val}")
        return val


class FormatMixin:
    """Formatting specific methods"""

    def format_index(self, index: int, source_type="input") -> str:
        """Given cell prefix format based on the source_type."""
        if source_type == "input":
            return f"[green]In [/][bold green][{index}]: [/bold green]"
        elif source_type == "output":
            return f"[red]Out [/][bold red][{index}]: [/bold red]"

    def format_markdown(self, index, cell):
        """Format the markdown cell content. Render only input and leave out output."""
        panels = []
        panels.append(self.format_index(index, source_type="input"))
        source = self.get_source_text(cell)
        panels.append(Panel(Markdown(source)))
        return panels

    def format_code(self, index, cell):
        """Format the code block. Print both the source and output."""
        panels = []
        panels.append(self.format_index(index, source_type="input"))
        code = Syntax(self.get_source_text(cell), lexer_name="python")
        panels.append(Panel(code))
        for output in cell.get("outputs"):
            panels.append(self.format_index(index, source_type="output"))
            output_text, lexer_name = self.get_output_text(output)
            if can_render_in_terminal(lexer_name):
                code = Syntax(output_text, lexer_name=lexer_name)
                panels.append(Panel(code))
            else:
                panels.append(f"Not rendering {lexer_name}")
        return panels

    def format_raw(self, index, cell):
        """Format raw code block. Render only input source."""
        panels = []
        panels.append(self.format_index(index))
        panels.append(Panel(self.get_source_text(cell)))
        return panels

    def get_source_text(self, cell):
        return cell.get("source")

    def get_output_text(self, output):
        """Given a output cell, extract proper output content."""
        if output["output_type"] == "stream":
            return output.get("text"), OUTPUT_TYPES_TO_LEXER_NAMES["text"]
        elif output["output_type"] == "execute_result":
            plain = output.get("data", {}).get("text/plain")
            return plain, OUTPUT_TYPES_TO_LEXER_NAMES["text/plain"]
        elif output["output_type"] == "display_data":
            for key, lexer_name in OUTPUT_TYPES_TO_LEXER_NAMES:
                if key in ("text", "text/plain"):
                    continue

                val = output.get("data", {}).get("text/html")
                if val:
                    return str(val), lexer_name

        return "", OUTPUT_TYPES_TO_LEXER_NAMES["text"]


class Render(FormatMixin):
    def __init__(self, config: Config):
        self.config = config
        self.node = None
        custom_theme = Theme(
            {"info": "dim cyan", "warning": "magenta", "danger": "bold red"}
        )
        self.console = Console(theme=custom_theme)

    def parse_notebook(self):
        """Parse the notebook content."""
        try:
            self.node = nbformat.read(self.config.input_file, as_version=4)
        except nbformat.reader.NotJSONError as exc:
            raise ParsingException(
                f"{self.config.input_file.name} is not a proper notebook"
            )

    def iter_cells(self):
        block = None
        if self.config.full_display:
            block = self.node.cells
            start = 0
        elif self.config.head:
            block = self.node.cells[: self.config.head]
            start = 0
        elif self.config.tail:
            block = self.node.cells[-self.config.tail :]
            start = len(self.node.cells) - self.config.tail

        for cell in block:
            start += 1
            yield start, cell

    def format_cell(self, index, cell):
        cell_type = cell.get("cell_type")
        if cell_type == CellType.MARKDOWN.value:
            return self.format_markdown(index, cell)
        elif cell_type == CellType.CODE.value:
            return self.format_code(index, cell)
        elif cell_type == CellType.RAW.value:
            return self.format_raw(index, cell)

    def render_cell(self, panels):
        self.console.print(*panels)

    def _render_to_terminal(self):
        for index, cell in self.iter_cells():
            panels = self.format_cell(index, cell)
            self.render_cell(panels)

    def render_to_terminal(self):
        if self.config.single_page:
            with self.console.pager():
                self._render_to_terminal()
        else:
            self._render_to_terminal()

    def render(self):
        self.parse_notebook()
        self.render_to_terminal()
