import json
from pathlib import Path

from causa.ui.extraction_evaluation import run_keyword_extraction_evaluation


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    report = run_keyword_extraction_evaluation()
    output = root / "examples" / "keyword_extraction_report.json"
    output.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
