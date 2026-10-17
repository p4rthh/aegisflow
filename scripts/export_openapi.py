"""Export OpenAPI schema for Google Stitch dashboard integration.

See PROJECT_ROADMAP.md Task 11.
"""

import json
from pathlib import Path
from aegisflow.api.main import app


def main():
    schema = app.openapi()
    out_file = Path("openapi.json")
    with open(out_file, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"OpenAPI schema successfully exported to {out_file} ({len(json.dumps(schema))} bytes)")


if __name__ == "__main__":
    main()
