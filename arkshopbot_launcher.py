import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText
import subprocess, os, json
import pymysql  # For MariaDB connections

# Paths
env_path = '.env'
shop_items_path = 'shop_items.json'
assets_dir = 'assets'
logo_path = os.path.join(assets_dir, 'logo.png')
icon_path = os.path.join(assets_dir, 'icon.png')

# Configuration fields
CONFIG_KEYS = [
    ('DISCORD_TOKEN', 'Discord Bot Token'),
    ('SHOP_LOG_CHANNEL_ID', 'Discord Log Channel ID'),
    ('TIP4SERV_SECRET', 'Tip4Serv Secret (optional)'),
    ('TIP4SERV_TOKEN', 'Tip4Serv Token (optional)'),
    ('REWARD_INTERVAL_MINUTES', 'Reward Interval (Minutes)'),
    ('REWARD_POINTS', 'Reward Amount (Points)')
]

class ArkShopBotLauncher:
    def __init__(self, root):
        self.root = root
        root.title("ArkShopBot Launcher")
        root.configure(bg='#f0f0f0')  # light grey background
        # Set icon
        try:
            icon = tk.PhotoImage(file=icon_path)
            root.iconphoto(False, icon)
        except:
            pass
        # Header
        if os.path.exists(logo_path):
            img = tk.PhotoImage(file=logo_path)
            lbl = ttk.Label(root, image=img, background='#f0f0f0')
            lbl.image = img
            lbl.pack(pady=5)
        else:
            ttk.Label(root, text="ArkShopBot", font=('Montserrat', 18, 'bold'), background='#f0f0f0').pack(pady=5)
        # Notebook
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook.Tab', font=('Montserrat', 10), padding=(10, 8), background='#e6e6fa', borderwidth=1)
        style.map('TNotebook.Tab', background=[('selected', '#d8bfd8')])
        self.nb = ttk.Notebook(root)
        self.nb.pack(expand=True, fill='both', padx=10, pady=10)
        # Tabs
        self._build_config_tab()
        self._build_servers_tab()
        self._build_databases_tab()
        self._build_shop_tab()
        self._build_logs_tab()
        # Load data
        self.servers = []
        self.databases = []
        self.categories = []
        self._load_env()
        self._load_servers()
        self._load_databases()
        self._load_shop_items()
        self.process = None

    # Configuration Tab
    def _build_config_tab(self):
        frame = ttk.Frame(self.nb); self.nb.add(frame, text='Configuration')
        self.config_entries = {}
        for i, (key, label) in enumerate(CONFIG_KEYS):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky='w', pady=4)
            entry = ttk.Entry(frame, width=40)
            entry.grid(row=i, column=1, pady=4)
            self.config_entries[key] = entry
        ttk.Button(frame, text='Save Settings', command=self._save_env).grid(row=len(CONFIG_KEYS), column=0, columnspan=2, pady=10)

    # RCON Servers Tab
    def _build_servers_tab(self):
        frame = ttk.Frame(self.nb); self.nb.add(frame, text='RCON Servers')
        cols = ('Name','Host','Port','Password')
        self.srv_tv = ttk.Treeview(frame, columns=cols, show='headings')
        for c in cols: self.srv_tv.heading(c, text=c)
        self.srv_tv.pack(expand=True, fill='both', pady=5)
        btnf = ttk.Frame(frame); btnf.pack()
        ttk.Button(btnf, text='Add Server', command=self._add_server).pack(side='left', padx=5)
        ttk.Button(btnf, text='Remove Server', command=self._remove_server).pack(side='left', padx=5)

    # Databases Tab
    def _build_databases_tab(self):
        frame = ttk.Frame(self.nb); self.nb.add(frame, text='SQL Databases')
        cols = ('Name','Host','Port','User','DB')
        self.db_tv = ttk.Treeview(frame, columns=cols, show='headings')
        for c in cols: self.db_tv.heading(c, text=c)
        self.db_tv.pack(expand=True, fill='both', pady=5)
        btnf = ttk.Frame(frame); btnf.pack()
        ttk.Button(btnf, text='Add DB', command=self._add_database).pack(side='left', padx=5)
        ttk.Button(btnf, text='Remove DB', command=self._remove_database).pack(side='left', padx=5)

    # Shop Items Tab
    def _build_shop_tab(self):
        frame = ttk.Frame(self.nb); self.nb.add(frame, text='Shop Items')
        # Category
        ttk.Label(frame, text='Category').pack(anchor='w', pady=4)
        self.cat_combo = ttk.Combobox(frame, values=[], state='readonly')
        self.cat_combo.pack(fill='x', padx=5, pady=4)
        ttk.Button(frame, text='Add Category', command=self._add_category).pack(pady=4)
        # Items tree
        cols = ('Name','Command','Price','Limit','Roles')
        self.item_tv = ttk.Treeview(frame, columns=cols, show='headings')
        for c in cols: self.item_tv.heading(c, text=c)
        self.item_tv.pack(expand=True, fill='both', pady=5)
        # Entry fields
        form = ttk.Frame(frame); form.pack(fill='x', pady=5)
        for idx, lbl in enumerate(['Name','Command','Price']):
            ttk.Label(form, text=lbl).grid(row=0, column=idx, padx=4)
            entry = ttk.Entry(form, width=30)
            entry.grid(row=1, column=idx, padx=4)
            setattr(self, f'{lbl.lower()}_entry', entry)
        # Limit checkbox
        self.limit_var = tk.BooleanVar()
        ttk.Checkbutton(form, text='Limit', variable=self.limit_var).grid(row=1, column=3, padx=4)
        # Roles entry + all
        ttk.Label(form, text='Roles (IDs)').grid(row=0, column=4, padx=4)
        self.roles_entry = ttk.Entry(form, width=30)
        self.roles_entry.grid(row=1, column=4, padx=4)
        self.all_var = tk.BooleanVar()
        ttk.Checkbutton(form, text='All', variable=self.all_var, command=self._on_all_roles).grid(row=1, column=5, padx=4)
        ttk.Button(frame, text='Add Item', command=self._on_add_item).pack(pady=5)

    # Logs Tab
    def _build_logs_tab(self):
        frame = ttk.Frame(self.nb); self.nb.add(frame, text='Logs')
        self.log_box = ScrolledText(frame, state='disabled', font=('Consolas',10))
        self.log_box.pack(expand=True, fill='both', pady=5)
        ttk.Button(frame, text='Save Log', command=self._save_log).pack(pady=5)

    # Load/Save Env
    def _load_env(self):
        if os.path.exists(env_path):
            data = dict(line.strip().split('=',1) for line in open(env_path) if '=' in line)
            for k, e in self.config_entries.items(): e.insert(0, data.get(k, ''))
            self.servers = json.loads(data.get('RCON_SERVERS','[]'))
            self.databases = json.loads(data.get('SQL_DATABASES','[]'))

    def _save_env(self):
        out = {k: e.get() for k,e in self.config_entries.items()}
        out['RCON_SERVERS'] = self.servers
        out['SQL_DATABASES'] = self.databases
        with open(env_path,'w') as f:
            for k, v in out.items(): f.write(f"{k}={json.dumps(v) if isinstance(v, list) else v}\n")
        messagebox.showinfo('Saved','Configuration saved successfully.')
        self._log('Configuration saved.')

    # Server Handlers
    def _load_servers(self):
        for s in self.servers:
            self.srv_tv.insert('', 'end', values=(s['name'],s['host'],s['port'],'*'*len(s['password'])))

    def _add_server(self):
        dlg = simpledialog.askstring('Add Server','Enter JSON: {"name":"...","host":"...","port":...,"password":"..."}')
        try:
            s = json.loads(dlg)
            self.servers.append(s)
            self.srv_tv.insert('', 'end', values=(s['name'],s['host'],s['port'],'*'*len(s['password'])))
            self._log(f"Added server {s['name']}")
        except:
            messagebox.showerror('Error','Invalid JSON format')

    def _remove_server(self):
        sel = self.srv_tv.selection()
        if sel:
            idx = self.srv_tv.index(sel)
            name = self.servers.pop(idx)['name']
            self.srv_tv.delete(sel)
            self._log(f"Removed server {name}")

    # Database Handlers
    def _load_databases(self):
        for db in self.databases:
            self.db_tv.insert('', 'end', values=(db['name'],db['host'],db['port'],db['user'],db['database']))

    def _add_database(self):
        dlg = simpledialog.askstring('Add Database','Enter JSON: {"name":"...","host":"...","port":...,"user":"...","password":"...","database":"..."}')
        try:
            db = json.loads(dlg)
            self.databases.append(db)
            self.db_tv.insert('', 'end', values=(db['name'],db['host'],db['port'],db['user'],db['database']))
            self._log(f"Added DB {db['name']}")
        except:
            messagebox.showerror('Error','Invalid JSON format')

    def _remove_database(self):
        sel = self.db_tv.selection()
        if sel:
            idx = self.db_tv.index(sel)
            name = self.databases.pop(idx)['name']
            self.db_tv.delete(sel)
            self._log(f"Removed DB {name}")

    # Shop Items handlers
    def _load_shop_items(self):
        data = json.load(open(shop_items_path)) if os.path.exists(shop_items_path) else {}
        self.categories = list(data.keys())
        self.cat_combo['values'] = self.categories
        for cat, items in data.items():
            for itm in items:
                roles = 'all' if itm.get('roles')=='all' else ','.join(itm.get('roles',[]))
                self.item_tv.insert('', 'end', values=(itm['name'], itm['command'], itm['price'], itm['limit'], roles))

    def _add_category(self):
        name = simpledialog.askstring('Category','Enter category name:').strip()
        if name and name not in self.categories:
            self.categories.append(name)
            self.cat_combo['values'] = self.categories
            self._log(f"Added category {name}")

    def _on_all_roles(self):
        if self.all_var.get(): self.roles_entry.delete(0, tk.END); self.roles_entry.insert(0,'all')

    def _on_add_item(self):
        cat = self.cat_combo.get().strip()
        if not cat:
            messagebox.showerror('Error','Select a category')
            return
        name = self.name_entry.get().strip()
        cmd = self.command_entry.get().strip()
        price = self.price_entry.get().strip()
        limit = self.limit_var.get()
        roles = self.roles_entry.get().strip()
        # Validate price
        try: price_val = int(price)
        except: messagebox.showerror('Error','Price must be integer'); return
        roles_val = 'all' if roles=='all' else [r for r in roles.split(',') if r]
        itm = {'name':name,'command':cmd,'price':price_val,'limit':limit,'roles':roles_val}
        store = json.load(open(shop_items_path)) if os.path.exists(shop_items_path) else {}
        store.setdefault(cat,[]).append(itm)
        with open(shop_items_path,'w') as f: json.dump(store,f,indent=2)
        role_disp = 'all' if roles_val=='all' else ','.join(roles_val)
        self.item_tv.insert('', 'end', values=(name, cmd, price_val, limit, role_disp))
        self._log(f"Added item {name} in {cat}")

    # Logs
    def _save_log(self):
        path = filedialog.asksaveasfilename(defaultextension='.txt')
        if path:
            open(path,'w').write(self.log_box.get('1.0','end'))
            messagebox.showinfo('Saved',f'Log saved to {path}')

    def _log(self, text):
        self.log_box.configure(state='normal'); self.log_box.insert('end', text+'\n'); self.log_box.configure(state='disabled')

    # Start Bot
    def start_bot(self):
        if self.process: return messagebox.showwarning('Running','Already running')
        self.process = subprocess.Popen(['python','Discord_Shop_System.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self._read_output()

    def _read_output(self):
        if self.process.poll() is None:
            line = self.process.stdout.readline()
            if line: self._log(line.strip())
            self.root.after(100, self._read_output)

if __name__=='__main__':
    root = tk.Tk()
    tt = ArkShopBotLauncher(root)
    root.mainloop()
