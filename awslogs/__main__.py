"""A tool for viewing AWS CloudWatch logs nicely in the terminal.

Usage:
------

    $ python -m awslogs [options] <log-group-id> [time]

The log group id is the id of the CloudWatch log group for the resource.
E.g. `/aws/lambda/some-function' or '/ecs/some-container'

Specifying time is optional and defaults to '5m', and specified how far back the logs should show.
Examples for time are '1m', '2h', '5d'.

Available options are:

    -h, --help         Show this help
"""

import sys


if len(sys.argv) <= 1 or sys.argv[1] in ("-h", "--help"):
    print(__doc__)
    exit(0)


from awslogs import trail_logs

log_group = sys.argv[1]
if len(sys.argv) < 3:
    time = "5m"
else:
    time = sys.argv[2]
trail_logs(log_group, time)
