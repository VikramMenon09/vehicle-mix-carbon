"""Rebuild the vehicle mix study from the archived research inputs."""

import argparse
import subprocess
import sys
from pathlib import Path

from scripts import analyze, sensitivity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-pdf", action="store_true",
                        help="first regenerate the source tables (requires Poppler pdftotext)")
    parser.add_argument("--analysis-only", action="store_true",
                        help="regenerate the result tables without rendering the paper")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if args.from_pdf:
        subprocess.run([sys.executable, str(root / "scripts/extract_data.py")], check=True)
    analyze.run(root / "data", root / "results")
    sensitivity.run(root / "data", root / "results")
    if not args.analysis_only:
        from paper.render import render
        output = render(root)
        print(f"Paper: {output.relative_to(root)}")
    print("Analysis: results/")


if __name__ == "__main__":
    main()
