import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import scrolledtext
from tkinter import simpledialog
from tkinter import PhotoImage
from tkinter import ttk
import subprocess, os, json

# Attempt to load logo for header (PNG supported)
LOGO_PATH = os.path.join('assets','logo.png')
ICON_PATH = os.path.join('assets','icon.png')

CONFIG_KEYS = [
    ('DISCORD_TOKEN', 'Discord Bot Token'),
    ('SHOP_LOG_CHANNEL_ID', 'Shop Log Channel ID'),
    ('REWARD_INTERVAL_MINUTES', 'Reward Interval (Minutes)'),
    ('REWARD_POINTS', 'Reward Amount (Points)')
]

class ArkShopBotLauncher:
    def __init__(self, root):
        self.root = root
        root.title("ArkShopBot Launcher")
        # Set window icon
        try:
            icon_img = PhotoImage(file=ICON_PATH)
            root.iconphoto(False, icon_img)
        except:
            pass
        # Apply modern theme
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TNotebook.Tab', padding=[12, 8], font=('Segoe UI', 10))
        style.configure('Treeview', font=('Segoe UI', 10), rowheight=24)
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('TLabel', font=('Segoe UI', 10))

        # Header banner
        if os.path.exists(LOGO_PATH):
            try:
                banner = PhotoImage(file=LOGO_PATH)
                lbl = ttk.Label(root, image=banner)
                lbl.image = banner
                lbl.pack(pady=10)
            except:
                ttk.Label(root, text="ArkShopBot", font=('Segoe UI', 16, 'bold')).pack(pady=10)
        else:
            ttk.Label(root, text="ArkShopBot", font=('Segoe UI', 16, 'bold')).pack(pady=10)

        # Notebook for sections
        self.nb = ttk.Notebook(root)
        self.nb.pack(expand=True, fill='both', padx=10, pady=10)

        self._create_config_tab()
        self._create_servers_tab()
        self._create_shop_tab()
        self._create_logs_tab()

        # Load existing data
        self._load_config()
        self._load_servers()
        self._load_shop_items()

        # Process handle
        self.process = None

    def _create_config_tab(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text='Configuration')
        self.config_entries = {}
        for i, (key, label) in enumerate(CONFIG_KEYS):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky='w', pady=4)
            entry = ttk.Entry(frame, width=40)
            entry.grid(row=i, column=1, pady=4)
            self.config_entries[key] = entry
        ttk.Button(frame, text='Save Settings', command=self._save_config).grid(row=len(CONFIG_KEYS), column=0, columnspan=2, pady=10)

    def _create_servers_tab(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text='RCON Servers')
        cols = ('Name','Host','Port','Password')
        self.server_tv = ttk.Treeview(frame, columns=cols, show='headings', selectmode='browse')
        for c in cols:
            self.server_tv.heading(c, text=c)
        self.server_tv.pack(expand=True, fill='both', pady=(0,10))
        btn_frame = ttk.Frame(frame)
        btn_frame.pack()
        ttk.Button(btn_frame, text='Add', command=self._add_server).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Edit', command=self._edit_server).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Remove', command=self._remove_server).pack(side='left', padx=5)

    def _create_shop_tab(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text='Shop Items')
        cols = ('Name','Category','Price','Limit')
        self.shop_tv = ttk.Treeview(frame, columns=cols, show='headings', selectmode='browse')
        for c in cols:
            self.shop_tv.heading(c, text=c)
        self.shop_tv.pack(expand=True, fill='both', pady=(0,10))
        btn_frame = ttk.Frame(frame)
        btn_frame.pack()
        ttk.Button(btn_frame, text='Add', command=self._add_item).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Edit', command=self._edit_item).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Remove', command=self._remove_item).pack(side='left', padx=5)

    def _create_logs_tab(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text='Logs')
        self.log_box = scrolledtext.ScrolledText(frame, state='disabled', font=('Consolas', 10))
        self.log_box.pack(expand=True, fill='both')
        ttk.Button(frame, text='Save Log', command=self._save_log).pack(pady=5)

    # ---------- Config handlers ----------
    def _load_config(self):
        if os.path.exists('.env'):
            env = dict(l.strip().split('=',1) for l in open('.env') if '=' in l)
            for k, e in self.config_entries.items():
                if k in env: e.insert(0, env[k])
            self.servers = json.loads(env.get('RCON_SERVERS','[]'))
        else:
            self.servers = []

    def _save_config(self):
        with open('.env','w') as f:
            for k, e in self.config_entries.items():
                f.write(f"{k}={e.get()}\n")
            f.write(f"RCON_SERVERS={json.dumps(self.servers)}\n")
        messagebox.showinfo('Saved','Configuration saved successfully.')
        self._log('Configuration saved.')

    # ---------- Server handlers ----------
    def _load_servers(self):
        for s in getattr(self, 'servers', []):
            self.server_tv.insert('', 'end', values=(s['name'],s['host'],s['port'],'*'*len(s['password'])))

    def _add_server(self):
        data = self._server_dialog()
        if data:
            self.servers.append(data)
            self.server_tv.insert('', 'end', values=(data['name'],data['host'],data['port'],'*'*len(data['password'])))
            self._log(f"Server added: {data['name']}")

    def _edit_server(self):
        sel = self.server_tv.selection()
        if not sel: return
        idx = self.server_tv.index(sel)
        data = self.servers[idx]
        new = self._server_dialog(initial=data)
        if new:
            self.servers[idx] = new
            for i,v in enumerate((new['name'],new['host'],new['port'],'*'*len(new['password']))):
                self.server_tv.set(sel, i, v)
            self._log(f"Server edited: {new['name']}")

    def _remove_server(self):
        sel = self.server_tv.selection()
        if not sel: return
        idx = self.server_tv.index(sel)
        name = self.servers[idx]['name']
        del self.servers[idx]
        self.server_tv.delete(sel)
        self._log(f"Server removed: {name}")

    def _server_dialog(self, initial=None):
        dlg = simpledialog.Dialog(self.root, title='Server Details')
        # For brevity, implement similar to ItemDialog or reuse a custom dialog
        # Should return dict(name,host,port,password) or None
        return None  # placeholder

    # ---------- Shop handlers ----------
    def _load_shop_items(self):
        if os.path.exists('shop_items.json'):
            data = json.load(open('shop_items.json'))
            self.shop_items = data
            for cat, items in data.items():
                for itm in items:
                    self.shop_tv.insert('', 'end', values=(itm['name'],cat,itm['price'],itm['limit']))
        else:
            self.shop_items = {}

    def _add_item(self):
        from_file = simpledialog.askstring('Add Item', 'Paste item JSON:')
        try:
            itm = json.loads(from_file)
            cat = itm.get('category')
            if cat not in self.shop_items: self.shop_items[cat] = []
            self.shop_items[cat].append(itm)
            self.shop_tv.insert('', 'end', values=(itm['name'],cat,itm['price'],itm['limit']))
            self._log(f"Item added: {itm['name']}")
        except Exception as e:
            messagebox.showerror('Invalid JSON', f'{e}')

    def _edit_item(self):
        sel = self.shop_tv.selection()
        if not sel: return
        item = self.shop_tv.item(sel)
        name,cat,price,limit = item['values']
        # implement similar dialog to edit and refresh
        self._log(f"Item edit not implemented yet")

    def _remove_item(self):
        sel = self.shop_tv.selection()
        if not sel: return
        item = self.shop_tv.item(sel)
        name = item['values'][0]
        # remove from self.shop_items structure accordingly
        self.shop_tv.delete(sel)
        self._log(f"Item removed: {name}")

    # ---------- Log helpers ----------
    def _create_log(self):
        pass

    def _log(self, text):
        self.log_box.configure(state='normal')
        self.log_box.insert('end', f"{text}\n")
        self.log_box.configure(state='disabled')

    def _save_log(self):
        path = filedialog.asksaveasfilename(defaultextension='.txt')
        if path:
            with open(path,'w') as f:
                f.write(self.log_box.get('1.0','end'))
            messagebox.showinfo('Saved',f'Log saved to {path}')

    # ---------- Bot start ----------
    def start_bot(self):
        if self.process:
            return messagebox.showwarning('Already Running','Bot is already running')
        self.process = subprocess.Popen(['python','Discord_Shop_System.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.root.after(100, self._read_output)

    def _read_output(self):
        if self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                self.log_box.configure(state='normal')
                self.log_box.insert('end', line)
                self.log_box.see('end')
                self.log_box.configure(state='disabled')
            self.root.after(100, self._read_output)

if __name__=='__main__':
    root = tk.Tk()
    launcher = ArkShopBotLauncher(root)
    root.mainloop()
