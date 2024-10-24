
# AWS Logs Viewer

A tool for viewing AWS CloudWatch logs nicely in the terminal.

## Installation

You can install it from [PyPI](https://pypi.org/project/zmunk-awslogs/):

    python -m pip install zmunk-awslogs

The tool is supported on Python 3.10 and above.

## How to use

    $ export AWS_DEFAULT_PROFILE=<your-profile>
    $ python
    >>> from awslogs import trail_logs
    >>> trail_logs("/aws/lambda/your-function", "5m")

You could also use it from the command line.

    $ python -m awslogs /aws/lambda/your-function 5m
