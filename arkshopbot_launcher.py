import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk
import subprocess, os, json

# Paths
env_path = '.env'
shop_items_path = 'shop_items.json'
assets_dir = 'assets'
logo_path = os.path.join(assets_dir, 'logo.png')
icon_path = os.path.join(assets_dir, 'icon.png')

# Configuration fields
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
        # Set icon
        try:
            icon = tk.PhotoImage(file=icon_path)
            root.iconphoto(False, icon)
        except:
            pass
        # Header
        if os.path.exists(logo_path):
            img = tk.PhotoImage(file=logo_path)
            lbl = ttk.Label(root, image=img)
            lbl.image = img
            lbl.pack(pady=5)
        else:
            ttk.Label(root, text="ArkShopBot", font=('Segoe UI', 16, 'bold')).pack(pady=5)
        # Notebook
        self.nb = ttk.Notebook(root)
        self.nb.pack(expand=True, fill='both')
        self._build_config_tab()
        self._build_servers_tab()
        self._build_shop_tab()
        self._build_logs_tab()
        # Load data
        self._load_env()
        self._load_servers()
        self._load_shop_items()
        self.process = None

    def _build_config_tab(self):
        frame = ttk.Frame(self.nb); self.nb.add(frame, text='Configuration')
        self.config_entries = {}
        for i, (key, label) in enumerate(CONFIG_KEYS):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky='w', pady=2)
            entry = ttk.Entry(frame, width=40)
            entry.grid(row=i, column=1, pady=2)
            self.config_entries[key] = entry
        ttk.Button(frame, text='Save Settings', command=self._save_env).grid(row=len(CONFIG_KEYS), column=0, columnspan=2, pady=10)

    def _build_servers_tab(self):
        frame = ttk.Frame(self.nb); self.nb.add(frame, text='RCON Servers')
        cols = ('Name','Host','Port','Password')
        self.srv_tv = ttk.Treeview(frame, columns=cols, show='headings')
        for c in cols: self.srv_tv.heading(c, text=c)
        self.srv_tv.pack(expand=True, fill='both', pady=5)
        btnf = ttk.Frame(frame); btnf.pack()
        ttk.Button(btnf, text='Add', command=self._add_server).pack(side='left', padx=2)
        ttk.Button(btnf, text='Remove', command=self._remove_server).pack(side='left', padx=2)

    def _build_shop_tab(self):
        frame = ttk.Frame(self.nb); self.nb.add(frame, text='Shop Items')
        # Category
        ttk.Label(frame, text='Category').pack(anchor='w')
        self.cat_combo = ttk.Combobox(frame, values=[], state='readonly')
        self.cat_combo.pack(fill='x', padx=5, pady=2)
        ttk.Button(frame, text='Add Category', command=self._add_category).pack(pady=2)
        # Items tree
        cols = ('Name','Command','Price','Limit','Roles')
        self.item_tv = ttk.Treeview(frame, columns=cols, show='headings', selectmode='browse')
        for c in cols: self.item_tv.heading(c, text=c)
        self.item_tv.pack(expand=True, fill='both', pady=5)
        # Entry fields
        form = ttk.Frame(frame); form.pack(fill='x', pady=5)
        labels = ['Name','Command','Price']
        self.item_vars = {}
        for idx, lbl in enumerate(labels):
            ttk.Label(form, text=lbl).grid(row=0, column=idx, padx=2)
            entry = ttk.Entry(form, width=30)
            entry.grid(row=1, column=idx, padx=2)
            self.item_vars[lbl] = entry
        # Limit checkbox
        self.limit_var = tk.BooleanVar()
        ttk.Checkbutton(form, text='Limit', variable=self.limit_var).grid(row=1, column=len(labels), padx=2)
        # Roles entry and 'All' checkbox
        ttk.Label(form, text='Roles (comma-separated IDs)').grid(row=0, column=len(labels)+1, padx=2)
        self.roles_entry = ttk.Entry(form, width=30)
        self.roles_entry.grid(row=1, column=len(labels)+1, padx=2)
        self.all_var = tk.BooleanVar()
        ttk.Checkbutton(form, text='All', variable=self.all_var, command=self._on_all_roles).grid(row=1, column=len(labels)+2, padx=2)
        # Add button
        ttk.Button(frame, text='Add Item', command=self._on_add_item).pack(pady=5)

    def _build_logs_tab(self):
        frame = ttk.Frame(self.nb); self.nb.add(frame, text='Logs')
        self.log_box = scrolledtext.ScrolledText(frame, state='disabled', font=('Consolas',10))
        self.log_box.pack(expand=True, fill='both', pady=5)
        ttk.Button(frame, text='Save Log', command=self._save_log).pack(pady=5)

    def _load_env(self):
        self.servers=[]; self.categories=[]
        if os.path.exists(env_path):
            data = dict(l.strip().split('=',1) for l in open(env_path) if '=' in l)
            for k,e in self.config_entries.items(): e.insert(0, data.get(k,''))
            self.servers = json.loads(data.get('RCON_SERVERS','[]'))

    def _save_env(self):
        out = {k: e.get() for k,e in self.config_entries.items()}
        out['RCON_SERVERS'] = self.servers
        with open(env_path,'w') as f:
            for k,v in out.items(): f.write(f"{k}={v}\n")
        messagebox.showinfo('Saved','Settings saved!')
        self._log('Configuration saved.')

    def _load_servers(self):
        for s in self.servers:
            self.srv_tv.insert('', 'end', values=(s['name'],s['host'],s['port'],'*'*len(s['password'])))

    def _add_server(self): pass
    def _remove_server(self): pass

    def _load_shop_items(self):
        data = json.load(open(shop_items_path)) if os.path.exists(shop_items_path) else {}
        self.categories = list(data.keys())
        self.cat_combo['values'] = self.categories
        for cat, items in data.items():
            for itm in items:
                roles = 'all' if itm.get('roles')=='all' else ','.join(itm.get('roles',[]))
                self.item_tv.insert('', 'end', values=(itm['name'], itm['command'], itm['price'], itm['limit'], roles))

    def _add_category(self):
        name = simpledialog.askstring('Category','Enter category name:')
        if not name or name in self.categories: return
        self.categories.append(name)
        self.cat_combo['values'] = self.categories
        self._log(f"Category added: {name}")

    def _on_all_roles(self):
        if self.all_var.get(): self.roles_entry.delete(0, tk.END); self.roles_entry.insert(0, 'all')

    def _on_add_item(self):
        cat = self.cat_combo.get().strip()
        if not cat:
            messagebox.showerror('Error','Select a category')
            return
        name = self.item_vars['Name'].get().strip()
        cmd = self.item_vars['Command'].get().strip()
        price = self.item_vars['Price'].get().strip()
        limit = self.limit_var.get()
        roles = self.roles_entry.get().strip()
        # Validate price
        try: price_val = int(price)
        except: messagebox.showerror('Error','Price must be an integer'); return
        # Roles
        if roles=='all': roles_val = 'all'
        else: roles_val = [r.strip() for r in roles.split(',') if r.strip()]
        # Store
        itm = {'name':name,'command':cmd,'price':price_val,'limit':limit,'roles':roles_val}
        store = json.load(open(shop_items_path)) if os.path.exists(shop_items_path) else {}
        store.setdefault(cat,[]).append(itm)
        with open(shop_items_path,'w') as f: json.dump(store,f,indent=2)
        # Display
        roles_disp = 'all' if roles_val=='all' else ','.join(roles_val)
        self.item_tv.insert('', 'end', values=(name, cmd, price_val, limit, roles_disp))
        self._log(f"Item added: {name}")

    def _save_log(self):
        path = filedialog.asksaveasfilename(defaultextension='.txt')
        if path:
            open(path,'w').write(self.log_box.get('1.0','end'))
            messagebox.showinfo('Saved', f'Log saved to {path}')

    def _log(self, msg):
        self.log_box.configure(state='normal'); self.log_box.insert('end', msg+'\n'); self.log_box.configure(state='disabled')

    def start_bot(self):
        if self.process: return messagebox.showwarning('Running','Already running')
        self.process = subprocess.Popen(['python','Discord_Shop_System.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self._read_output()

    def _read_output(self):
        if self.process and self.process.poll() is None:
            line=self.process.stdout.readline()
            if line: self._log(line.strip())
            self.root.after(100, self._read_output)

if __name__=='__main__':
    root=tk.Tk()
    ArkShopBotLauncher(root)
    root.mainloop()
