import argparse
import enum
import os
import sys
from collections.abc import Callable
from typing import Any

from googleapiclient.discovery import build

GOOGLE_CONSOLE_APP_DEVELOPER_KEY = os.getenv("GOOGLE_CONSOLE_APP_DEVELOPER_KEY")

if not GOOGLE_CONSOLE_APP_DEVELOPER_KEY:
    print("Error: GOOGLE_CONSOLE_APP_DEVELOPER_KEY environment variable is not set.", file=sys.stderr)
    sys.exit(1)
BATCH_SIZE_COMMENTS = 500
BATCH_SIZE_REPLIES = 100

_YOUTUBE: Any = None


class YT_ITEM(enum.Enum):
    COMMENT = enum.auto()
    REPLY = enum.auto()


def _get_youtube_client() -> Any:
    global _YOUTUBE
    if _YOUTUBE is None:
        _YOUTUBE = build("youtube", "v3", developerKey=GOOGLE_CONSOLE_APP_DEVELOPER_KEY)
    return _YOUTUBE


def get_yt_items(item: YT_ITEM, item_id: str, page_token: str = ""):
    youtube_client = _get_youtube_client()

    if item == YT_ITEM.COMMENT:
        list_method = youtube_client.commentThreads().list
        id_param_name = "videoId"
        max_results = BATCH_SIZE_COMMENTS
    else:  # YT_ITEM.REPLY
        list_method = youtube_client.comments().list
        id_param_name = "parentId"
        max_results = BATCH_SIZE_REPLIES

    params = {
        "part": "snippet",
        "textFormat": "plainText",
        id_param_name: item_id,
        "maxResults": max_results,
    }
    if page_token:
        params["pageToken"] = page_token

    return list_method(**params).execute()


def get_yt_comments(video_id: str, page_token: str = ""):
    return get_yt_items(YT_ITEM.COMMENT, video_id, page_token)


def get_yt_replies(comment_id: str, page_token: str = ""):
    return get_yt_items(YT_ITEM.REPLY, comment_id, page_token)


def get_paginated_items(item_id: str, get_content: Callable, get_text: Callable, print_info: bool = False):
    items = []

    batch = 0
    if print_info:
        print(f"Going for batch {batch}", file=sys.stderr)

    response = get_content(item_id)
    while response:
        for item in response["items"]:
            items.append(get_text(item))

        if "nextPageToken" in response:
            batch += 1
            if print_info:
                print(f"Going for batch {batch}", file=sys.stderr)
            response = get_content(item_id, response["nextPageToken"])
        else:
            break

    return items


def get_replies(comment_id):
    return get_paginated_items(comment_id, get_yt_replies, lambda item: {"text": item["snippet"]["textDisplay"],
                                                                         "author": item["snippet"]["authorDisplayName"]})


def get_video_comments(video_id: str, filter_text: str, should_get_replies: bool):
    top_comments = get_paginated_items(
        video_id,
        get_yt_comments,
        lambda item: {
            "text": item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
            "author": item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
            "id": item["snippet"]["topLevelComment"]["id"],
        },
        True,
    )
    for tc in top_comments:
        if should_get_replies and filter_text.lower() in tc["text"].lower():
            tc["replies"] = get_replies(tc["id"])
    return top_comments


def print_comments(comments, level=0):
    indent = "  " * (level * 2)
    for comment in comments:
        print(f"{indent}{comment['author']}: {comment['text']}")
        if comment.get("replies"):
            print_comments(comment["replies"], level + 1)


def main():
    parser = argparse.ArgumentParser(
        description="Grab and print youtube comments and optionally replies with optional filter on comments"
    )
    parser.add_argument("video_id", help="Youtube Video ID")
    parser.add_argument(
        "--get-replies",
        action="store_true",
        help="Get comment replies",
    )
    parser.add_argument("--filter-text", default="", help="Filter substring for comments to get replies of")
    args = parser.parse_args()

    print_comments(get_video_comments(args.video_id, args.filter_text, args.get_replies))


if __name__ == "__main__":
    main()
