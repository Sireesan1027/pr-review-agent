"""
diff_stats.py — Analyse a unified diff and return useful statistics.
"""

from langchain_core.tools import tool


def parse_diff_stats(diff: str) -> dict:
    files = []
    current = None
    additions = 0
    deletions = 0

    for line in diff.splitlines():
        if line.startswith("diff --git"):
            if current:
                files.append(current)
            parts = line.split(" b/")
            filename = parts[-1] if len(parts) > 1 else "unknown"
            current = {"file": filename, "additions": 0, "deletions": 0, "changes": []}
        elif line.startswith("+") and not line.startswith("+++"):
            if current:
                current["additions"] += 1
                current["changes"].append(line)
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            if current:
                current["deletions"] += 1
                current["changes"].append(line)
            deletions += 1

    if current:
        files.append(current)

    return {
        "total_files": len(files),
        "total_additions": additions,
        "total_deletions": deletions,
        "files": files,
    }


@tool
def diff_stats_tool(diff: str) -> str:
    """Parse a unified diff and return statistics about files changed, lines added and removed.

    Args:
        diff: Unified diff string.

    Returns:
        Summary of diff statistics per file.
    """
    stats = parse_diff_stats(diff)
    lines = [
        f"Total files changed: {stats['total_files']}",
        f"Total additions: +{stats['total_additions']}",
        f"Total deletions: -{stats['total_deletions']}",
        "",
        "Per file:",
    ]
    for f in stats["files"]:
        lines.append(f"  {f['file']}: +{f['additions']} -{f['deletions']}")
    return "\n".join(lines)
