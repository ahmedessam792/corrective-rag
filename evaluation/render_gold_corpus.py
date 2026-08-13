from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from win32com.client import DispatchEx


def _docx_to_pdf(word: object, source: Path, target: Path) -> None:
    document = word.Documents.Open(str(source.resolve()), ReadOnly=True)
    try:
        document.ExportAsFixedFormat(str(target.resolve()), 17)
    finally:
        document.Close(False)


def _render_pdf(source: Path, output: Path) -> list[Path]:
    document = fitz.open(source)
    pages = []
    output.mkdir(parents=True, exist_ok=True)
    for index, page in enumerate(document, start=1):
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        path = output / f"page-{index:03d}.png"
        pixmap.save(path)
        pages.append(path)
    document.close()
    return pages


def _contact_sheets(pages: list[tuple[str, Path]], output: Path, group: str) -> list[Path]:
    results = []
    width, height = 1850, 2350
    columns, rows = 3, 3
    cell_width, cell_height = width // columns, height // rows
    for sheet_index, start in enumerate(range(0, len(pages), columns * rows), start=1):
        sheet = Image.new("RGB", (width, height), "#d7dde5")
        draw = ImageDraw.Draw(sheet)
        for offset, (label, path) in enumerate(pages[start : start + columns * rows]):
            image = Image.open(path).convert("RGB")
            image.thumbnail((cell_width - 28, cell_height - 62))
            x = (offset % columns) * cell_width + (cell_width - image.width) // 2
            y = (offset // columns) * cell_height + 42
            sheet.paste(image, (x, y))
            draw.text((offset % columns * cell_width + 12, offset // columns * cell_height + 12), label, fill="#101828")
        target = output / f"contact-{group}-{sheet_index:02d}.png"
        sheet.save(target)
        results.append(target)
    return results


def render(corpus: Path, output: Path) -> Path:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    sources = [json.loads(line) for line in (corpus / "sources.jsonl").read_text(encoding="utf-8").splitlines()]
    word = DispatchEx("Word.Application")
    word.Visible = False
    records = []
    page_groups: dict[str, list[tuple[str, Path]]] = {"en": [], "ar": []}
    try:
        for source in sources:
            fixture = corpus / source["relative_path"]
            pdf = fixture if fixture.suffix.lower() == ".pdf" else output / "converted" / f"{fixture.stem}.pdf"
            if fixture.suffix.lower() == ".docx":
                pdf.parent.mkdir(parents=True, exist_ok=True)
                _docx_to_pdf(word, fixture, pdf)
            pages = _render_pdf(pdf, output / "pages" / source["source_id"])
            for page_index, page in enumerate(pages, start=1):
                page_groups[source["language"]].append((f"{fixture.name} p{page_index}", page))
            records.append(
                {
                    "source_id": source["source_id"],
                    "fixture": source["relative_path"],
                    "language": source["language"],
                    "pages": len(pages),
                    "rendered_pages": [path.relative_to(output).as_posix() for path in pages],
                }
            )
    finally:
        word.Quit()
    sheets = []
    for language, pages in page_groups.items():
        sheets.extend(_contact_sheets(pages, output, language))
    report = output / "render-report.json"
    report.write_text(
        json.dumps(
            {
                "corpus": str(corpus),
                "sources": records,
                "total_sources": len(records),
                "total_pages": sum(record["pages"] for record in records),
                "contact_sheets": [path.name for path in sheets],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the draft corpus for visual human review")
    parser.add_argument("--corpus", type=Path, default=Path("evaluation/corpora/crag-gold-v1-draft"))
    parser.add_argument("--output", type=Path, default=Path(".corpus-qa/rendered"))
    args = parser.parse_args()
    print(render(args.corpus, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
