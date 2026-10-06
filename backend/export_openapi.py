import json
from pathlib import Path

from app.main import app


def export_openapi():
    spec = app.openapi()
    output_path = Path(__file__).parent / "openapi.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)
    print(f"Exported openapi.json to {output_path}")


if __name__ == "__main__":
    export_openapi()
