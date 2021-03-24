`jut - JUpyter notebook Terminal viewer`.

The command line tool view the IPython/Jupyter notebook in the terminal.

### Install

`pip install jut`

### Usage

``` shell
$jut --help
Usage: jut [OPTIONS]

Options:
  -u, --url TEXT             Render the ipynb file from the URL
  -i, --input-file FILENAME  File from the local file-system
  -h, --head INTEGER         Display first n cells. Default is 10
  -t, --tail INTEGER         Display last n cells
  -p, --single-page          Should the result be in a single page?
  -f, --full-display         Should all the contents in the file displayed?
  --force-colors             Force colored output even if stdout is not a
                             terminal

  --help                     Show this message and exit.

```

### ASCIICinema Demo

[![asciicast](https://asciinema.org/a/400349.svg)](https://asciinema.org/a/400349)


### Display first five cells

![jut-head-example](https://raw.githubusercontent.com/kracekumar/jut/main/images/jut-head.png)

### Display last five cells

![jut-tail-example](https://raw.githubusercontent.com/kracekumar/jut/main/images/jut-tail.png)

### Download the file and display first five cells

![jut-download-url](https://raw.githubusercontent.com/kracekumar/jut/main/images/jut-download.png)
