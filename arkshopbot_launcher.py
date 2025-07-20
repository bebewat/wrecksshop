import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess, os

CONFIG_KEYS = [
    ('DISCORD_TOKEN', 'Discord Bot Token'),
    ('RCON_HOST', 'RCON Host'),
    ('RCON_PORT', 'RCON Port'),
    ('RCON_PASSWORD', 'RCON Password'),
    ('SHOP_LOG_CHANNEL_ID', 'Shop Log Channel ID'),
    ('REWARD_INTERVAL_MINUTES', 'Reward Interval (Minutes)'),
    ('REWARD_POINTS', 'Reward Amount (Points)')
]

class ArkShopBotLauncher:
    def __init__(self, root):
        root.title("ArkShopBot GUI Launcher")
        self.entries = {}
        for i, (k, label) in enumerate(CONFIG_KEYS):
            tk.Label(root, text=label).grid(row=i, column=0, sticky='w')
            e = tk.Entry(root, width=40); e.grid(row=i, column=1)
            self.entries[k] = e

        tk.Button(root, text="Save Config", command=self.save_config).grid(row=len(CONFIG_KEYS), column=0)
        tk.Button(root, text="Start Bot", command=self.start_bot).grid(row=len(CONFIG_KEYS), column=1)

        self.log_box = scrolledtext.ScrolledText(root, width=85, height=20, state='disabled')
        self.log_box.grid(row=len(CONFIG_KEYS)+1, column=0, columnspan=2)
        tk.Button(root, text="Save Log", command=self.save_log).grid(row=len(CONFIG_KEYS)+2, column=0, columnspan=2)

        self.process = None

    def save_config(self):
        with open(".env", "w") as f:
            for k,_ in CONFIG_KEYS:
                f.write(f"{k}={self.entries[k].get()}\n")
        messagebox.showinfo("Saved", ".env saved")

    def start_bot(self):
        if self.process:
            messagebox.showwarning("Already running", "Bot is running")
            return
        self.log_box.configure(state='normal'); self.log_box.delete('1.0', tk.END)
        self.process = subprocess.Popen(
            ['python', 'Discord_Shop_System.py'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        self.root_after()

    def root_after(self):
        line = self.process.stdout.readline()
        if line:
            self.log_box.configure(state='normal')
            self.log_box.insert(tk.END, line); self.log_box.yview(tk.END)
            self.log_box.configure(state='disabled')
        if self.process.poll() is None:
            root.after(100, self.root_after)

    def save_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            with open(path, "w") as f:
                f.write(self.log_box.get("1.0", tk.END))
            messagebox.showinfo("Saved", f"Log saved to {path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ArkShopBotLauncher(root)
    root.mainloop()
