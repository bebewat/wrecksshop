import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import json
import sys
from pathlib import Path

from arklib_loader import load_ark_lib, ArkItem
from command_builders import build_single
from batch_builder import build_batch
from paths import resource_path

APP_TITLE = "WrecksShop"
CSV_REL_PATH = "data/CleanArkData.csv"  # adjust if different

# ---------------------- Load Data ---------------------- #
ARKLIB_PATH = resource_path(CSV_REL_PATH)
ARK_DATA = load_ark_lib(ARKLIB_PATH)  # dict[section] -> list[ArkItem]

# Helper lookups
def get_sections():
    return sorted(ARK_DATA.keys())

def get_items_for_section(section: str):
    return ARK_DATA.get(section, [])

def find_item(section: str, name: str) -> ArkItem | None:
    for it in ARK_DATA.get(section, []):
        if it.name == name:
            return it
    return None

# ---------------------- GUI ---------------------- #
class WrecksShopGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1000x720")

        self._build_widgets()

    def _build_widgets(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # Tabs
        self.single_tab = ttk.Frame(nb)
        self.batch_tab = ttk.Frame(nb)
        nb.add(self.single_tab, text="Single Command")
        nb.add(self.batch_tab, text="Batch Builder")

        self._build_single_tab(self.single_tab)
        self._build_batch_tab(self.batch_tab)

    # ---------- Single Tab ---------- #
    def _build_single_tab(self, parent: ttk.Frame):
        # Section + Item selection
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Section:").grid(row=0, column=0, sticky="w")
        self.section_var = tk.StringVar()
        self.section_combo = ttk.Combobox(top, textvariable=self.section_var, state="readonly", values=get_sections())
        self.section_combo.grid(row=0, column=1, sticky="we", padx=5)
        self.section_combo.bind("<<ComboboxSelected>>", self.on_section_change)

        ttk.Label(top, text="Item:").grid(row=1, column=0, sticky="w")
        self.item_var = tk.StringVar()
        self.item_combo = ttk.Combobox(top, textvariable=self.item_var, state="readonly")
        self.item_combo.grid(row=1, column=1, sticky="we", padx=5)
        self.item_combo.bind("<<ComboboxSelected>>", self.on_item_select)

        top.columnconfigure(1, weight=1)

        # Frames for params
        self.item_frame = ttk.LabelFrame(parent, text="Item Params")
        self.creature_frame = ttk.LabelFrame(parent, text="Creature Params")

        # Item params
        ip = self.item_frame
        ttk.Label(ip, text="Player ID:").grid(row=0, column=0, sticky="e")
        self.player_id_var = tk.StringVar(value="0")
        ttk.Entry(ip, textvariable=self.player_id_var, width=12).grid(row=0, column=1, sticky="w")

        ttk.Label(ip, text="Qty:").grid(row=1, column=0, sticky="e")
        self.qty_var = tk.StringVar(value="1")
        ttk.Entry(ip, textvariable=self.qty_var, width=8).grid(row=1, column=1, sticky="w")

        ttk.Label(ip, text="Quality:").grid(row=2, column=0, sticky="e")
        self.quality_var = tk.StringVar(value="1")
        ttk.Entry(ip, textvariable=self.quality_var, width=8).grid(row=2, column=1, sticky="w")

        self.is_bp_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ip, text="Is Blueprint?", variable=self.is_bp_var).grid(row=3, column=0, columnspan=2, sticky="w")

        for i in range(2):
            ip.columnconfigure(i, weight=0)

        # Creature params
        cp = self.creature_frame
        ttk.Label(cp, text="EOS ID:").grid(row=0, column=0, sticky="e")
        self.eos_id_var = tk.StringVar()
        ttk.Entry(cp, textvariable=self.eos_id_var, width=30).grid(row=0, column=1, sticky="w")

        ttk.Label(cp, text="Level:").grid(row=1, column=0, sticky="e")
        self.level_var = tk.StringVar(value="150")
        ttk.Entry(cp, textvariable=self.level_var, width=8).grid(row=1, column=1, sticky="w")

        self.breedable_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(cp, text="Breedable", variable=self.breedable_var).grid(row=2, column=0, columnspan=2, sticky="w")

        for i in range(2):
            cp.columnconfigure(i, weight=0)

        # place frames (hidden first)
        self.item_frame.pack(fill="x", padx=10, pady=5)
        self.creature_frame.pack(fill="x", padx=10, pady=5)
        self.hide_item_fields()
        self.hide_creature_fields()

        # Build button + output
        btn = ttk.Button(parent, text="Build Command", command=self.build_single_command)
        btn.pack(padx=10, pady=5, anchor="w")

        self.output_box = ScrolledText(parent, height=10, wrap="none")
        self.output_box.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------- Batch Tab ---------- #
    def _build_batch_tab(self, parent: ttk.Frame):
        # Simple version: user pastes JSON, we build. (You can extend with a table later.)
        info = ("Paste batch JSON below or build a UI table later.\n"
                "Structure: [ {\n  'category': 'Starter Kits',\n  'items': [ {'section': 'Weapons', 'name': 'Longneck Rifle'}, ...],\n  'params': {...},\n  'per_item_params': [{...}, {...}]\n} ]")
        ttk.Label(parent, text=info, justify="left").pack(anchor="w", padx=10, pady=5)

        self.batch_text = ScrolledText(parent, height=18, wrap="none")
        self.batch_text.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Button(parent, text="Build Batch", command=self.build_batch_commands).pack(padx=10, pady=5, anchor="w")

        self.batch_output = ScrolledText(parent, height=10, wrap="none")
        self.batch_output.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------- Callbacks ---------- #
    def on_section_change(self, event=None):
        section = self.section_var.get()
        items = get_items_for_section(section)
        self.item_combo["values"] = [i.name for i in items]
        self.item_combo.set("")
        self.hide_item_fields()
        self.hide_creature_fields()

    def on_item_select(self, event=None):
        section = self.section_var.get()
        name = self.item_var.get()
        item = find_item(section, name)
        if not item:
            return
        if item.section.lower() == "creatures":
            self.show_creature_fields()
            self.hide_item_fields()
        else:
            self.show_item_fields()
            self.hide_creature_fields()

    # ---------- Builders ---------- #
    def build_single_command(self):
        section = self.section_var.get()
        name = self.item_var.get()
        item = find_item(section, name)
        if not item:
            messagebox.showerror("Error", "Item not found")
            return
        try:
            if item.section.lower() == "creatures":
                params = {
                    "eos_id": self.eos_id_var.get().strip(),
                    "level": int(self.level_var.get()),
                    "breedable": bool(self.breedable_var.get()),
                }
            else:
                params = {
                    "player_id": int(self.player_id_var.get()),
                    "qty": int(self.qty_var.get()),
                    "quality": int(self.quality_var.get()),
                    "is_bp": bool(self.is_bp_var.get()),
                }
            cmds = build_single(item, **params)
            self.output_box.delete("1.0", "end")
            self.output_box.insert("end", "\n".join(cmds))
        except Exception as e:
            messagebox.showerror("Build Error", str(e))

    def build_batch_commands(self):
        text = self.batch_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty", "Provide batch JSON")
            return
        try:
            raw_entries = json.loads(text)
            # Convert item dicts to ArkItem objects
            entries = []
            for entry in raw_entries:
                cat = entry.get("category", "")
                items_conf = entry.get("items", [])
                items: list[ArkItem] = []
                for ic in items_conf:
                    sec = ic["section"]
                    nm = ic["name"]
                    it = find_item(sec, nm)
                    if it:
                        items.append(it)
                e2 = {
                    "category": cat,
                    "items": items,
                    "params": entry.get("params", {}),
                    "per_item_params": entry.get("per_item_params", []),
                }
                entries.append(e2)
            cmds = build_batch(entries)
            self.batch_output.delete("1.0", "end")
            self.batch_output.insert("end", cmds)
        except Exception as e:
            messagebox.showerror("Batch Error", str(e))

    # ---------- Show/Hide helpers ---------- #
    def show_item_fields(self):
        self.item_frame.pack(fill="x", padx=10, pady=5)

    def hide_item_fields(self):
        self.item_frame.pack_forget()

    def show_creature_fields(self):
        self.creature_frame.pack(fill="x", padx=10, pady=5)

    def hide_creature_fields(self):
        self.creature_frame.pack_forget()


if __name__ == "__main__":
    app = WrecksShopGUI()
    app.mainloop()
