from typing import List
from arklib_loader import ArkItem

def build_giveitem_command(player_id: int, item: ArkItem,
                           qty: int, quality: int, is_bp: bool) -> str:
    bp_flag = 1 if is_bp else 0
    return (
        f"scriptcommand giveitemtoplayer {player_id} "
        f"{item.blueprint} {qty} {quality} {bp_flag}"
    )

def build_spawn_dino_command(eos_id: str, item: ArkItem,
                              level: int, breedable: bool) -> str:
    b_flag = "y" if breedable else "n"
    return (
        "scriptcommand SpawnDinoinBall "
        f"-p={eos_id} -t={item.blueprint} -l={level} -f=1 -i=1 -b={b_flag} -h=1"
    )

def build_single(item: ArkItem, **kwargs) -> List[str]:
    """Return list to keep interface consistent (breeding pairs may return >1)."""
    if item.section.lower() == "creatures":
        cmd = build_spawn_dino_command(
            eos_id=kwargs["eos_id"],
            item=item,
            level=int(kwargs.get("level", 150)),
            breedable=bool(kwargs.get("breedable", True)),
        )
        return [cmd]
    else:
        cmd = build_giveitem_command(
            player_id=int(kwargs["player_id"]),
            item=item,
            qty=int(kwargs.get("qty", 1)),
            quality=int(kwargs.get("quality", 1)),
            is_bp=bool(kwargs.get("is_bp", False)),
        )
        return [cmd]
