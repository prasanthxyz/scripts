# scripts

A collection of frequently used nifty little scripts.

## Available Scripts

| Script | Description |
|--------|-------------|
| [adbsync-since.sh](adbsync-since.sh) | Pull only files modified on/after a given date, using better-adb-sync (adbsync) under the hood. |
| [adb_pull_and_delete](adb_pull_and_delete) | Pull files from a device and optionally delete them locally after verification. |
| [dir_diff.py](dir_diff.py) | Find common files or differences between two directories. |
| [parse_yt_comments.py](parse_yt_comments.py) | Grab and print YouTube comments and optionally replies with optional filter. |

To make the shimmed commands in [`bin/`](bin) available on `PATH`, run the
installer, which symlinks every shim into `~/bin` (created if needed; idempotent):

```
./bin/install
```
