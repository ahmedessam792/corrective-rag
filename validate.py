from __future__ import annotations

# ruff: noqa: E402, I001

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

from crag.validation import main


if __name__ == "__main__":
    raise SystemExit(main())
