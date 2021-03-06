from pathlib import Path

import pytest
from parameterized import parameterized
from pydantic import ValidationError

from jut import Config, ParsingException, Render

config_data = [
    (
        {
            "input_file": "",
            "head": 0,
            "tail": None,
            "single_page": True,
            "full_display": True,
            "force_colors": True,
            "start": None,
            "end": None,
            "exclude_output_cells": False,
            "no_cell_border": True,
        },
        ValidationError,
    ),
    (
        {
            "input_file": Path("/tmp/foo.txt"),
            "head": 1,
            "tail": None,
            "single_page": True,
            "full_display": True,
            "force_colors": True,
            "start": None,
            "end": None,
            "exclude_output_cells": False,
            "no_cell_border": True,
        },
        False,
    ),
    (
        {
            "input_file": Path("/tmp"),
            "head": 0,
            "tail": None,
            "single_page": True,
            "full_display": True,
            "force_colors": True,
            "start": None,
            "end": None,
            "exclude_output_cells": False,
            "no_cell_border": True,
        },
        ValidationError,
    ),
    (
        {
            "input_file": Path("/tmp"),
            "head": None,
            "tail": 0,
            "single_page": True,
            "full_display": True,
            "force_colors": True,
            "start": None,
            "end": None,
            "exclude_output_cells": False,
            "no_cell_border": True,
        },
        ValidationError,
    ),
    (
        {
            "input_file": Path("/tmp"),
            "head": None,
            "tail": -1,
            "single_page": True,
            "full_display": True,
            "force_colors": True,
            "start": None,
            "end": None,
            "exclude_output_cells": False,
            "no_cell_border": True,
        },
        ValidationError,
    ),
    (
        {
            "input_file": Path("/tmp"),
            "head": 10,
            "tail": 10,
            "single_page": True,
            "full_display": True,
            "force_colors": True,
            "start": 5,
            "end": 10,
            "exclude_output_cells": False,
            "no_cell_border": True,
        },
        ValidationError,
    ),
    (
        {
            "input_file": Path("/tmp"),
            "head": 10,
            "tail": -1,
            "single_page": True,
            "full_display": True,
            "force_colors": True,
            "start": 5,
            "end": 10,
            "exclude_output_cells": False,
            "no_cell_border": True,
        },
        ValidationError,
    ),  # tail < 1
    (
        {
            "input_file": Path("/tmp"),
            "head": 1,
            "tail": None,
            "single_page": True,
            "full_display": True,
            "force_colors": True,
            "start": 10,
            "end": 5,
            "exclude_output_cells": False,
            "no_cell_border": True,
        },
        ValidationError,
    ),
    (
        {
            "input_file": Path("/tmp"),
            "head": 1,
            "tail": None,
            "single_page": True,
            "full_display": True,
            "force_colors": True,
            "start": 10,
            "end": 15,
            "exclude_output_cells": False,
            "no_cell_border": True,
        },
        ValidationError,
    ),
    (
        {
            "input_file": Path("/tmp"),
            "head": 1,
            "tail": None,
            "single_page": True,
            "full_display": True,
            "force_colors": True,
            "start": 0,
            "end": 0,
            "exclude_output_cells": False,
            "no_cell_border": True,
        },
        ValidationError,
    ),
]


@parameterized.expand(config_data)
def test_config(config_data, exception):
    if exception:
        with pytest.raises(exception):
            Config(**config_data)
    else:
        assert Config(**config_data)


class TestRender:
    @parameterized.expand(
        [
            (
                {
                    "input_file": Path("tests/test1_all.ipynb"),
                    "head": 5,
                    "tail": None,
                    "single_page": False,
                    "full_display": True,
                    "force_colors": False,
                    "start": None,
                    "end": None,
                    "exclude_output_cells": False,
                    "no_cell_border": True,
                },
                False,
            ),
            (
                {
                    "input_file": Path("jut/cli.py"),
                    "head": 5,
                    "tail": None,
                    "single_page": False,
                    "full_display": True,
                    "force_colors": False,
                    "start": None,
                    "end": None,
                    "exclude_output_cells": False,
                    "no_cell_border": False,
                },
                ParsingException,
            ),
        ]
    )
    def test_parse_notebook(self, config_data, exception):
        if exception:
            with pytest.raises(exception):
                config = Config(**config_data)
                render = Render(config)
                render.parse_notebook()
        else:
            config = Config(**config_data)
            render = Render(config)
            render.parse_notebook()
            assert render.node

    def test_iter_cells(self):
        config = Config(
            **{
                "input_file": Path("tests/test1_all.ipynb"),
                "head": 10,
                "tail": None,
                "single_page": False,
                "full_display": True,
                "force_colors": False,
                "start": None,
                "end": None,
                "exclude_output_cells": False,
                "no_cell_border": True,
            }
        )
        render = Render(config)
        render.parse_notebook()
        cells = list(render.iter_cells())

        assert len(cells) == 7
