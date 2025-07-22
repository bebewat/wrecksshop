from typing import Iterable, Dict, Any, List
from arklib_loader import ArkItem
from command_builders import build_single, build_spawn_dino_command

ALLOWED_BATCH_CATEGORIES = {
    "starter kits", "base kits", "consumables",
    "breeding pairs", "structures", "armor",
}

def build_batch(batch_entries: Iterable[Dict[str, Any]], joiner: str = "\n") -> str:
    """
    batch_entries: iterable of dicts, each with:
      - category: str
      - items: list[ArkItem]
      - params: dict (shared defaults for that entry)
      - per_item_params: list[dict] (overrides per item)

    Special case: category == "Breeding Pairs" (case-insensitive) => spawn two dinos/item (male/female).
    Expected keys per pair: eos_id_m, eos_id_f, level_m, level_f, breedable_m, breedable_f
    """
    all_cmds: List[str] = []

    for entry in batch_entries:
        category = (entry.get("category") or "").lower()
        items: List[ArkItem] = entry.get("items", [])
        shared = entry.get("params", {}) or {}
        overrides = entry.get("per_item_params", []) or [None] * len(items)

        if category == "breeding pairs":
            for idx, item in enumerate(items):
                p = {**shared, **(overrides[idx] or {})}
                cmd_m = build_spawn_dino_command(
                    eos_id=p["eos_id_m"],
                    item=item,
                    level=int(p.get("level_m", p.get("level", 150))),
                    breedable=bool(p.get("breedable_m", True)),
                )
                cmd_f = build_spawn_dino_command(
                    eos_id=p["eos_id_f"],
                    item=item,
                    level=int(p.get("level_f", p.get("level", 150))),
                    breedable=bool(p.get("breedable_f", True)),
                )
                all_cmds.extend([cmd_m, cmd_f])
        else:
            for idx, item in enumerate(items):
                p = {**shared, **(overrides[idx] or {})}
                all_cmds.extend(build_single(item, **p))

    return joiner.join(all_cmds)
