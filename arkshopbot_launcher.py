import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog
import subprocess, os, json

CONFIG_KEYS = [
    ('DISCORD_TOKEN', 'Discord Bot Token'),
    ('SHOP_LOG_CHANNEL_ID', 'Shop Log Channel ID'),
    ('REWARD_INTERVAL_MINUTES', 'Reward Interval (Minutes)'),
    ('REWARD_POINTS', 'Reward Amount (Points)')
]

class ArkShopBotLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("ArkShopBot GUI Launcher")
        self.entries = {}

        # Basic config fields
        for i, (k, label) in enumerate(CONFIG_KEYS):
            tk.Label(root, text=label).grid(row=i, column=0, sticky='w')
            e = tk.Entry(root, width=40)
            e.grid(row=i, column=1, pady=2)
            self.entries[k] = e

        # Multi-server listbox
        tk.Label(root, text="RCON Servers").grid(row=len(CONFIG_KEYS), column=0, sticky='w')
        self.server_listbox = tk.Listbox(root, height=4)
        self.server_listbox.grid(row=len(CONFIG_KEYS), column=1, pady=2)
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=len(CONFIG_KEYS)+1, column=1)
        tk.Button(btn_frame, text="Add Server", command=self.add_server).pack(side='left')
        tk.Button(btn_frame, text="Edit Server", command=self.edit_server).pack(side='left')
        tk.Button(btn_frame, text="Remove Server", command=self.remove_server).pack(side='left')

        # Control buttons
        self.save_btn = tk.Button(root, text="Save Config", command=self.save_config)
        self.save_btn.grid(row=len(CONFIG_KEYS)+2, column=0, pady=10)
        self.start_btn = tk.Button(root, text="Start Bot", command=self.start_bot)
        self.start_btn.grid(row=len(CONFIG_KEYS)+2, column=1, pady=10)

        # Log viewer
        self.log_box = scrolledtext.ScrolledText(root, width=85, height=20, state='disabled')
        self.log_box.grid(row=len(CONFIG_KEYS)+3, column=0, columnspan=2, padx=10, pady=5)
        self.save_log_btn = tk.Button(root, text="Save Log to File", command=self.save_log)
        self.save_log_btn.grid(row=len(CONFIG_KEYS)+4, column=0, columnspan=2)

        self.process = None
        self.load_existing_config()

    def load_existing_config(self):
        # Load .env if exists
        if os.path.exists('.env'):
            env = dict(line.strip().split('=',1) for line in open('.env') if '=' in line)
            for k in self.entries:
                if k in env:
                    self.entries[k].insert(0, env[k])
            # Load RCON_SERVERS JSON
            servers = json.loads(env.get('RCON_SERVERS','[]'))
            for s in servers:
                self.server_listbox.insert(tk.END, f"{s['name']}|{s['host']}|{s['port']}|{s['password']}")

    def add_server(self):
        self.server_dialog()

    def edit_server(self):
        idx = self.server_listbox.curselection()
        if not idx: return
        data = self.server_listbox.get(idx)
        name, host, port, pwd = data.split('|')
        self.server_dialog(initial=(name,host,port,pwd), index=idx[0])

    def remove_server(self):
        idx = self.server_listbox.curselection()
        if idx:
            self.server_listbox.delete(idx)

    def server_dialog(self, initial=None, index=None):
        # Prompt user for server details
        name = simpledialog.askstring("Server Name", "Enter a unique server name:", initialvalue=(initial[0] if initial else ""))
        if not name: return
        host = simpledialog.askstring("RCON Host", "Enter RCON host/IP:", initialvalue=(initial[1] if initial else ""))
        port = simpledialog.askstring("RCON Port", "Enter RCON port:", initialvalue=(initial[2] if initial else ""))
        pwd  = simpledialog.askstring("RCON Password", "Enter RCON password:", show='*', initialvalue=(initial[3] if initial else ""))
        entry = f"{name}|{host}|{port}|{pwd}"
        if index is not None:
            self.server_listbox.delete(index)
            self.server_listbox.insert(index, entry)
        else:
            self.server_listbox.insert(tk.END, entry)

    def save_config(self):
        # Save .env
        servers = []
        for line in self.server_listbox.get(0, tk.END):
            name, host, port, pwd = line.split('|')
            servers.append({"name":name, "host":host, "port":int(port), "password":pwd})
        with open('.env', 'w') as f:
            for k,_ in CONFIG_KEYS:
                f.write(f"{k}={self.entries[k].get()}\n")
            f.write(f"RCON_SERVERS={json.dumps(servers)}\n")
        messagebox.showinfo("Saved", ".env file saved successfully.")

    def start_bot(self):
        if self.process:
            messagebox.showwarning("Bot Running", "Bot is already running.")
            return
        self.log_box.configure(state='normal')
        self.log_box.delete('1.0', tk.END)
        self.log_box.insert(tk.END, "Starting ArkShopBot...\n")
        self.log_box.configure(state='disabled')
        self.process = subprocess.Popen(['python', 'Discord_Shop_System.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.root.after(100, self.read_output)

    def read_output(self):
        if self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                self.log_box.configure(state='normal')
                self.log_box.insert(tk.END, line)
                self.log_box.yview(tk.END)
                self.log_box.configure(state='disabled')
            self.root.after(100, self.read_output)

    def save_log(self):
        log = self.log_box.get("1.0", tk.END)
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt")])
        if path:
            with open(path, 'w') as f:
                f.write(log)
            messagebox.showinfo("Saved", f"Log saved to {path}")

if __name__ == '__main__':
    root = tk.Tk()
    app = ArkShopBotLauncher(root)
    root.mainloop()
