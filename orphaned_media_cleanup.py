#!/usr/bin/env python3
"""Delete orphaned metadata sidecar files from a media directory tree.

Scans a directory of movies (Jellyfin/Emby style) and removes "sidecar"
files -- artwork, .nfo, subtitles, ... -- that no longer have a matching
video file in the same folder. These leftovers typically show up when
Jellyfin wrote metadata before the media was renamed, or after the media
itself was deleted out from under it.

Safety rails:
- Only likely-metadata files (see SIDECAR) are ever considered for
  deletion; anything else (videos, archives, ...) is ignored.
- Folders containing no video file are skipped entirely: without a video
  there is nothing to compare against (e.g. the item is still
  downloading), so the sidecars are not classified as orphans.
- Jellyfin's folder-level names (poster.jpg, fanart.jpg, movie.nfo, ...)
  are kept; they describe the folder, not a single video.
- A sidecar is kept when it matches a video either exactly
  ("Movie.nfo" next to "Movie.mkv") or as a suffixed variant
  ("Movie-poster.jpg", "Movie-fanart.jpg", "Movie.chs.ass", ...).

Dry-run by default: it prints which files would go. Pass --delete to
actually remove them.
"""

import argparse
import os

# Extensions that count as "the movie is here".
VIDEO = {".mkv", ".mp4", ".avi", ".m4v", ".mov", ".wmv", ".ts", ".mpg", ".mpeg", ".iso", ".strm"}
# Extensions that only belong here as long as a video exists.
SIDECAR = {".nfo", ".jpg", ".jpeg", ".png", ".srt", ".ass", ".sub", ".vtt", ".trickplay"}
# Folder-level names that are valid without a same-named video file.
FOLDER_ART = {"poster", "folder", "fanart", "backdrop", "banner", "logo",
              "clearlogo", "landscape", "thumb", "movie", "disc", "cover"}


def find_orphans(folder: str, files: list[str]) -> list[str]:
    """Return the orphaned sidecar files (full paths) in one folder."""
    video_bases = {
        base.lower()
        for base, ext in (os.path.splitext(f) for f in files)
        if ext.lower() in VIDEO
    }
    if not video_bases:
        return []  # skip folders without videos; see module docstring

    orphans = []
    for f in files:
        base, ext = os.path.splitext(f)
        if ext.lower() not in SIDECAR:
            continue
        # Folder-level art like poster.jpg, fanart.jpg, movie.nfo is valid.
        if base.lower() in FOLDER_ART:
            continue
        # Matches a video name, or "<video>-poster", "<video>-fanart", etc.
        # Extending with "." also keeps split-name subtitles ("Movie.chs.ass").
        if any(base.lower() == v or base.lower().startswith(v + "-") or base.lower().startswith(v + ".")
               for v in video_bases):
            continue
        orphans.append(os.path.join(folder, f))
    return orphans


def cleanup(root: str, delete: bool) -> int:
    """Walk the tree; print orphans and delete them if requested.

    Returns the number of orphaned files found.
    """
    found = 0
    for folder, _dirs, files in os.walk(root):
        for path in find_orphans(folder, files):
            found += 1
            print(("DELETING " if delete else "ORPHAN   ") + path)
            if delete:
                os.remove(path)
    return found


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete sidecar files (.nfo, artwork, subtitles, ...) "
        "orphaned by missing video files, e.g. leftovers from Jellyfin"
    )
    parser.add_argument("root", help="directory with movies to clean up")
    parser.add_argument("--delete", action="store_true",
                        help="actually delete the orphaned files (otherwise dry-run)")
    args = parser.parse_args()

    if not os.path.isdir(args.root):
        parser.error(f"not a directory: {args.root}")

    found = cleanup(args.root, args.delete)
    if not found:
        print("No orphaned files found.")
    elif not args.delete:
        print(f"{found} orphan(s) found. Dry run only; pass --delete to remove them.")


if __name__ == "__main__":
    main()
