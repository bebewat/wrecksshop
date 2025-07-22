from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import csv

@dataclass
class ArkItem:
    section: str
    name: str
    blueprint: str
    mod: str = ""

def load_ark_lib(csv_path: Path) -> Dict[str, List[ArkItem]]:
    """Load CleanArkData.csv and return items grouped by Section."""
    items_by_section: Dict[str, List[ArkItem]] = defaultdict(list)
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            section = (row.get("Section") or "").strip()
            name = (row.get("Name") or "").strip()
            blueprint = (row.get("Blueprint Path") or "").strip()
            mod = (row.get("Mod/DLC") or "").strip()
            if not (section and name and blueprint):
                continue
            items_by_section[section].append(ArkItem(section, name, blueprint, mod))
    return items_by_section
