import csv
import io
from typing import List, Dict, Any


def convert_to_csv(logs: List[Dict[str, Any]]) -> str:
    if not logs:
        return ""

    output = io.StringIO()
    # Use lineterminator='\n' to ensure consistency across OS environments
    # quoting=csv.QUOTE_MINIMAL saves tokens by only quoting when absolutely necessary
    writer = csv.DictWriter(
        output,
        fieldnames=logs[0].keys(),
        lineterminator='\n',
        quoting=csv.QUOTE_MINIMAL
    )

    writer.writeheader()
    writer.writerows(logs)

    return output.getvalue().strip()  # .strip() removes trailing newlines
