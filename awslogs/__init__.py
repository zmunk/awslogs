import json
import os
import boto3
from copy import copy
from datetime import datetime, timedelta

client = boto3.client("logs")
TIMESTAMP_COL_WIDTH = 21
DATE_DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S"


def blue(s):
    return f"\033[0;34m{s}\033[0m"


def grey(s):
    return f"\033[2;37m{s}\033[0m"


def trail_logs(log_group, log_time):
    terminal_width = os.get_terminal_size().columns

    print(grey("retrieving log history..."), end="\r")
    try:
        for timestamp, message in get_log_history(log_group, log_time):
            print_message(timestamp, message, terminal_width)
    except NoLogsException:
        print("no logs")
        return

    print(grey("waiting for new logs..."), end="\r")
    for timestamp, message in live_tail(log_group):
        print_message(timestamp, message, terminal_width)
        print(grey("waiting for new logs..."), end="\r")


def parse_time_from_timestamp(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp / 1000).strftime(DATE_DISPLAY_FORMAT)


def live_tail(log_group):
    response = client.describe_log_groups(logGroupNamePrefix=log_group)
    log_group_arn = response["logGroups"][0]["logGroupArn"]

    try:
        response = client.start_live_tail(logGroupIdentifiers=[log_group_arn])
        for event in response["responseStream"]:
            if "sessionStart" in event:
                pass
            elif "sessionUpdate" in event:
                log_events = event["sessionUpdate"]["sessionResults"]
                for log_event in log_events:
                    timestamp = parse_time_from_timestamp(log_event["timestamp"])
                    message = log_event["message"]
                    yield timestamp, message
            else:
                raise RuntimeError(str(event))
    except KeyboardInterrupt:
        return
    except Exception as e:
        print(e)


def get_log_history(log_group, delta):
    """
    :param delta: e.g. "5m" meaning starting 5 minutes ago
    """
    start_time = (datetime.now() - parse_delta(delta)).strftime(DATE_DISPLAY_FORMAT)
    next_token = None
    params = {
        "logGroupName": log_group,
        "orderBy": "LastEventTime",
        "descending": True,
        "limit": 1,
    }
    log_stream_names = []
    while True:
        params = copy(params)
        if next_token is not None:
            params["nextToken"] = next_token
        stream_response = client.describe_log_streams(**params)
        stream = stream_response["logStreams"][0]
        log_stream_names.append(stream["logStreamName"])
        if parse_time_from_timestamp(stream["firstEventTimestamp"]) < start_time:
            break
        try:
            next_token = stream_response["nextToken"]
        except KeyError:
            break

    for log_stream_name in log_stream_names[::-1]:
        response = client.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream_name,
        )
        for event in response["events"]:
            timestamp = parse_time_from_timestamp(event["timestamp"])
            if timestamp < start_time:
                continue
            yield timestamp, event["message"]


def get_lines(message):
    try:
        data = json.loads(message)
    except json.decoder.JSONDecodeError:
        return [message]
    except Exception:
        raise
    else:
        return json.dumps(data, indent=4).split("\n")


def split_string_into_chunks(message, chunk_size):
    for line in get_lines(message):
        for i in range(0, len(line), chunk_size):
            yield line[i : i + chunk_size]


def print_message(timestamp: str, message, terminal_width):
    print(blue(timestamp.ljust(TIMESTAMP_COL_WIDTH)), end="")
    message = message.strip("\n").replace("\n", " ").replace("\t", "  ")
    chunks = split_string_into_chunks(message, terminal_width - TIMESTAMP_COL_WIDTH)
    print(next(chunks))
    for chunk in chunks:
        print(" " * TIMESTAMP_COL_WIDTH + chunk)


def parse_delta(delta_str):
    if delta_str[-1] == "m":
        return timedelta(minutes=int(delta_str.replace("m", "")))
    elif delta_str[-1] == "h":
        return timedelta(hours=int(delta_str.replace("h", "")))
    elif delta_str[-1] == "d":
        return timedelta(days=int(delta_str.replace("d", "")))
    else:
        raise NotImplementedError(f"{delta_str = }")


class NoLogsException(Exception):
    pass


def get_log_group_arn(log_group):
    response = client.describe_log_groups(logGroupNamePrefix=log_group)
    return response["logGroups"][0]["logGroupArn"]
