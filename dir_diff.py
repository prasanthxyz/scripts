import argparse
import os

from tabulate import tabulate


def get_size_mb(path):
    try:
        if os.path.isfile(path):
            return float(os.path.getsize(path)) / (1024 * 1024)
        elif os.path.isdir(path):
            # Directories are not size-measured; treat as 0.0
            return 0.0
    except (OSError, ValueError):
        return 0.0
    return 0.0


def find_common_files(dir1, dir2, diff_only):
    if not os.path.isdir(dir1):
        print(f"Error: {dir1} is not a directory.")
        return
    if not os.path.isdir(dir2):
        print(f"Error: {dir2} is not a directory.")
        return

    s1 = set(os.listdir(dir1))
    s2 = set(os.listdir(dir2))
    common_names = sorted(s1 & s2)
    common_files = [
        name
        for name in common_names
        if os.path.isfile(os.path.join(dir1, name))
        or os.path.isfile(os.path.join(dir2, name))
    ]

    if not common_files:
        print("No common files found.")
        return

    table_headers = [
        "#",
        "filename",
        f"size in {dir1} (MB)",
        f"size in {dir2} (MB)",
    ]
    table_rows = []
    for i, cf in enumerate(common_files, 1):
        size1 = get_size_mb(os.path.join(dir1, cf))
        size2 = get_size_mb(os.path.join(dir2, cf))

        if diff_only and size1 == size2:
            continue

        table_rows.append([len(table_rows) + 1, cf, size1, size2])

    print(tabulate(table_rows, headers=table_headers, tablefmt="simple_grid"))


def find_diff(dir1, dir2):
    if not os.path.isdir(dir1):
        print(f"Error: {dir1} is not a directory.")
        return
    if not os.path.isdir(dir2):
        print(f"Error: {dir2} is not a directory.")
        return

    s1 = set(os.listdir(dir1))
    s2 = set(os.listdir(dir2))
    diff_names = sorted(s1 - s2)

    if not diff_names:
        print(f"All items in '{dir1}' are also present in '{dir2}'.")
        return

    table_headers = [
        "#",
        "filename",
        f"size in {dir1} (MB)",
    ]
    table_rows = []
    for i, name in enumerate(diff_names, 1):
        path = os.path.join(dir1, name)
        size = get_size_mb(path)
        table_rows.append([i, name, size])

    print(tabulate(table_rows, headers=table_headers, tablefmt="simple_grid"))


def main():
    parser = argparse.ArgumentParser(
        description="Find common files or differences between two directories."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common_parser = subparsers.add_parser(
        "common",
        help="Find common files between two directories",
    )
    common_parser.add_argument("dir1", help="First directory")
    common_parser.add_argument("dir2", help="Second directory")
    common_parser.add_argument(
        "--diff-only",
        action="store_true",
        help="Only show files with different sizes",
    )

    diff_parser = subparsers.add_parser(
        "diff",
        help="Find items in the first directory that are not in the second",
    )
    diff_parser.add_argument("dir1", help="First directory (A)")
    diff_parser.add_argument("dir2", help="Second directory (B)")

    args = parser.parse_args()

    if args.command == "common":
        find_common_files(args.dir1, args.dir2, args.diff_only)
    elif args.command == "diff":
        find_diff(args.dir1, args.dir2)


if __name__ == "__main__":
    main()
