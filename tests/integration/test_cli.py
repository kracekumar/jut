from click.testing import CliRunner
from parameterized import parameterized

from jut.cli import display


@parameterized.expand(
    [
        ("-i tests/test1_all.ipynb", 0),
        ("-i tests/test1_all.ipynb --single-page --full-display --force-colors", 0),
        (
            "--url https://raw.githubusercontent.com/fastai/fastbook/master/06_multicat.ipynb",
            0,
        ),
        ("-i tests/test1_all.ipynb --tail 1", 0),
        ("-i tests/test1_all.ipynb --start 1 --end 3", 0),
        # Failure cases
        ("--head 5", -1),
        ("-i tests/test1_all2.ipynb --start 1 --end 3", 2),
        ("-i tests/test1_all.ipynb --start 10 --end 3", -1),
        ("--url https://httpbin.org/status/404", -1),
    ]
)
def test_display(args, exit_code):
    runner = CliRunner()
    result = runner.invoke(display, args)
    assert result.exit_code == exit_code
