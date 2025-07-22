import csv
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

class ArkItem:
  section: str
  name: str
  blueprint: str

def load_ark_lib(csv_path: Path) -> dict[str, list[ArkItem]]:
  items_by_section: dict[str, list[ArkItem]] = defaultdict(list)
  with csv_path.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
      item = ArkItem(
        section=row["Section"]
        name=row["Name"]
        blueprint=row["Blueprint Path"]
        mod=row.get("Mod/DLC", "") or ""
      )
      items_by_section[item.section].append(item)
  return items_by_section
