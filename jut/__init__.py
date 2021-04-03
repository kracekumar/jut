"""Render and formatter code.
"""

import io
from enum import Enum
from pathlib import Path, PosixPath
from typing import Any, Optional, Union

import nbformat  # type: ignore
from pydantic import BaseModel, PositiveInt, ValidationError, root_validator, validator
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

    input_file: PosixPath
    head: PositiveInt
    tail: Optional[PositiveInt]
    single_page: bool
    full_display: bool
    force_colors: bool
    start: Optional[PositiveInt]
    end: Optional[PositiveInt]

    class Config:
        arbitrary_types_allowed = True

    def is_cell_range(self):
        return self.start <= self.end

    @validator("input_file")
    def validate_input_file(cls, val):
        if isinstance(val, PosixPath):
            if val.exists() and val.is_dir():
                raise ValueError(f"input_file: {val} is not the notebook")

        return val

    @classmethod
    def validate_tail(cls, values):
        val = values.get("tail")
        if val is not None:
            if val > 0:
                if values.get("head"):
                    values["head"] = None

                if values.get("start"):
                    values["start"] = None

                if values.get("end"):
                    values["end"] = None

        return values

    @classmethod
    def validate_cell_range(cls, values):
        start, end = values.get("start"), values.get("end")
        if start is None or end is None:
            return values

        if start >= 0 and end >= 0:
            if start >= end:
                raise ValueError(
                    f"--start should be greater than --end. Received, start: {start}, end: {end}"
                )

            if start <= end:
                values["head"] = None
                values["tail"] = None

        return values

    @root_validator
    def validate_all(cls, values):
        values = cls.validate_tail(values)
        values = cls.validate_cell_range(values)
        return values


class FormatMixin:
    """Formatting specific methods"""

    def format_index(self, index: int, source_type="input") -> str:
        """Given cell prefix format based on the source_type."""
        if source_type == "input":
            return f"[green]In [/][bold green][{index}]: [/bold green]"
        elif source_type == "output":
            return f"[red]Out [/][bold red][{index}]: [/bold red]"
        return "{index}"

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
                panels.append(
                    Panel(f"[bold red] Not rendering {lexer_name} [/bold red]")
                )
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
            for key, lexer_name in OUTPUT_TYPES_TO_LEXER_NAMES.items():
                if key in ("text", "text/plain"):
                    continue

                val = output.get("data", {}).get(key)
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
        if config.force_colors:
            self.console = Console(
                theme=custom_theme, force_terminal=config.force_colors
            )
        else:
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
            start = max(len(self.node.cells) - self.config.tail, 0)
        elif self.config.is_cell_range():
            block = self.node.cells[self.config.start - 1 : self.config.end]
            start = self.config.start - 1

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
