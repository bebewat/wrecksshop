import os
import json
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
from arklib_loader import load_ark_lib, ArkItem
import command_builders

# Paths
ENV_PATH = '.env'
SHOP_ITEMS_PATH = 'shop_items.json'
ASSETS_DIR = 'assets'
LOGO_PATH = os.path.join(ASSETS_DIR, 'logo.png')
ICON_PATH = os.path.join(ASSETS_DIR, 'icon.png')
# CSV data library path
CSV_REL_PATH = Path('data') / 'data/CleanArkData.csv'
ARK_DATA = load_ark_lib(CSV_REL_PATH)

# Config keys for .env
CONFIG_KEYS = [
    ('DISCORD_TOKEN', 'Discord Bot Token'),
    ('SHOP_LOG_CHANNEL_ID', 'Discord Log Channel ID'),
    ('TIP4SERV_SECRET', 'Tip4Serv Secret (optional)'),
    ('TIP4SERV_TOKEN', 'Tip4Serv Token (optional)'),
    ('REWARD_INTERVAL_MINUTES', 'Reward Interval (Minutes)'),
    ('REWARD_POINTS', 'Reward Amount (Points)')
]

class WrecksShopLauncher:
    def __init__(self, root):
        self.root = root
        root.title("WrecksShop Launcher")
        root.configure(bg='#f0f0f0')
        # Icon
        try:
            icon = tk.PhotoImage(file=ICON_PATH)
            root.iconphoto(False, icon)
        except Exception:
            pass
        # Header
        if os.path.exists(LOGO_PATH):
            img = tk.PhotoImage(file=LOGO_PATH)
            lbl = ttk.Label(root, image=img, background='#f0f0f0')
            lbl.image = img
            lbl.pack(pady=5)
        else:
            ttk.Label(root, text="WrecksShop", font=('Montserrat', 18, 'bold'), background='#f0f0f0').pack(pady=5)
        # Initialize data containers
        self.servers = []
        self.databases = []
        self.categories = []
        # Load existing config (populates categories)
        self._load_env()
        # Notebook styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook.Tab', font=('Montserrat', 10), padding=(10, 8), background='#e6e6fa', borderwidth=1)
        style.map('TNotebook.Tab', background=[('selected', '#d8bfd8')])
        # Tabs
        self.nb = ttk.Notebook(root)
        self.nb.pack(expand=True, fill='both', padx=10, pady=10)
        self._build_config_tab()
        self._build_servers_tab()
        self._build_databases_tab()
        self._build_shop_tab()
        self._build_library_tab()
        self._build_logs_tab()
        # Load remaining data
        self._load_servers()
        self._load_databases()
        self._load_shop_items()
        self._load_library_display()
        self.process = None

    def _build_config_tab(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text='Configuration')
        self.config_entries = {}
        for i, (key, label) in enumerate(CONFIG_KEYS):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky='w', pady=4)
            entry = ttk.Entry(frame, width=40)
            entry.grid(row=i, column=1, pady=4)
            self.config_entries[key] = entry
        ttk.Button(frame, text='Save Settings', command=self._save_env).grid(row=len(CONFIG_KEYS), column=0, columnspan=2, pady=10)

    def _build_servers_tab(self):
        frame = ttk.Frame(self.nb);
        self.nb.add(frame, text='RCON Servers')
        cols = ('Name','Host','Port','Password')
        self.srv_tv = ttk.Treeview(frame, columns=cols, show='headings')
        for c in cols: self.srv_tv.heading(c, text=c)
        self.srv_tv.pack(expand=True, fill='both', pady=5)
        btnf = ttk.Frame(frame); btnf.pack()
        ttk.Button(btnf, text='Add Server', command=self._add_server).pack(side='left', padx=5)
        ttk.Button(btnf, text='Remove Server', command=self._remove_server).pack(side='left', padx=5)

    def _build_databases_tab(self):
        frame = ttk.Frame(self.nb);
        self.nb.add(frame, text='SQL Databases')
        cols = ('Name','Host','Port','User','DB')
        self.db_tv = ttk.Treeview(frame, columns=cols, show='headings')
        for c in cols: self.db_tv.heading(c, text=c)
        self.db_tv.pack(expand=True, fill='both', pady=5)
        btnf = ttk.Frame(frame); btnf.pack()
        ttk.Button(btnf, text='Add DB', command=self._add_database).pack(side='left', padx=5)
        ttk.Button(btnf, text='Remove DB', command=self._remove_database).pack(side='left', padx=5)

    def _build_shop_tab(self):
        frame = ttk.Frame(self.nb);
        self.nb.add(frame, text='Shop Items')
        ttk.Label(frame, text='Category').pack(anchor='w', pady=4)
        self.cat_combo = ttk.Combobox(frame, values=self.categories, state='readonly')
        self.cat_combo.pack(fill='x', padx=5, pady=4)
        ttk.Button(frame, text='Add Category', command=self._add_category).pack(pady=4)
        cols = ('Name','Command','Price','Limit','Roles')
        self.item_tv = ttk.Treeview(frame, columns=cols, show='headings')
        for c in cols: self.item_tv.heading(c, text=c)
        self.item_tv.pack(expand=True, fill='both', pady=5)
        form = ttk.Frame(frame); form.pack(fill='x', pady=5)
        for idx, lbl in enumerate(['Name','Command','Price']):
            ttk.Label(form, text=lbl).grid(row=0, column=idx, padx=4)
            entry = ttk.Entry(form, width=30)
            entry.grid(row=1, column=idx, padx=4)
            setattr(self, f'{lbl.lower()}_entry', entry)
        self.limit_var = tk.BooleanVar()
        ttk.Checkbutton(form, text='Limit', variable=self.limit_var).grid(row=1, column=3, padx=4)
        ttk.Label(form, text='Roles (IDs)').grid(row=0, column=4, padx=4)
        self.roles_entry = ttk.Entry(form, width=30)
        self.roles_entry.grid(row=1, column=4, padx=4)
        self.all_var = tk.BooleanVar()
        ttk.Checkbutton(form, text='All', variable=self.all_var, command=self._on_all_roles).grid(row=1, column=5, padx=4)
        ttk.Button(frame, text='Add Item', command=self._on_add_item).pack(pady=5)

    def _build_library_tab(self):
        frame = ttk.Frame(self.nb);
        self.nb.add(frame, text='Data Library')
        cols = ('Name','Blueprint Path','Mod/DLC')
        self.lib_tv = ttk.Treeview(frame, columns=cols, show='headings')
        for c in cols: self.lib_tv.heading(c, text=c)
        self.lib_tv.pack(expand=True, fill='both', pady=5)
        ttk.Button(frame, text='Import Selection', command=self._on_lib_import).pack(pady=4)

    def _build_logs_tab(self):
        frame = ttk.Frame(self.nb);
        self.nb.add(frame, text='Logs')
        self.log_box = ScrolledText(frame, state='disabled', font=('Consolas',10))
        self.log_box.pack(expand=True, fill='both', pady=5)
        ttk.Button(frame, text='Save Log', command=self._save_log).pack(pady=5)

    def _load_env(self):
        if os.path.exists(ENV_PATH):
            data = dict(line.strip().split('=',1) for line in open(ENV_PATH) if '=' in line)
            for k,e in self.config_entries.items(): e.insert(0, data.get(k,''))
            self.servers = json.loads(data.get('RCON_SERVERS','[]'))
            self.databases = json.loads(data.get('SQL_DATABASES','[]'))
            if os.path.exists(SHOP_ITEMS_PATH):
                shop = json.load(open(SHOP_ITEMS_PATH))
                self.categories = list(shop.keys())

    def _save_env(self):
        out = {k: v.get() for k,v in self.config_entries.items()}
        out['RCON_SERVERS'] = self.servers
        out['SQL_DATABASES'] = self.databases
        with open(ENV_PATH,'w') as f:
            for k,v in out.items():
                val = json.dumps(v) if isinstance(v,list) else v
                f.write(f"{k}={val}\n")
        messagebox.showinfo('Saved','Configuration saved successfully.')
        self._log('Configuration saved.')

    def _load_servers(self):
        for s in self.servers:
            self.srv_tv.insert('', 'end', values=(s['name'],s['host'],s['port'],'*'*len(s['password'])))

    def _add_server(self):
        name = simpledialog.askstring('Server Name','Enter unique server name:')
        if not name: return
        host = simpledialog.askstring('Host','Enter RCON host/IP:')
        port = simpledialog.askinteger('Port','Enter RCON port:')
        pwd = simpledialog.askstring('Password','Enter RCON password:',show='*')
        srv = {'name':name,'host':host,'port':port,'password':pwd}
        self.servers.append(srv)
        self.srv_tv.insert('', 'end', values=(name,host,port,'*'*len(pwd)))
        self._log(f"Added server: {name}")

    def _remove_server(self):
        sel = self.srv_tv.selection()
        if sel:
            idx = self.srv_tv.index(sel)
            name = self.servers.pop(idx)['name']
            self.srv_tv.delete(sel)
            self._log(f"Removed server: {name}")

    def _load_databases(self):
        for db in self.databases:
            self.db_tv.insert('', 'end', values=(db['name'],db['host'],db['port'],db['user'],db['database']))

    def _add_database(self):
        name = simpledialog.askstring('DB Name','Enter unique DB name:')
        if not name: return
        host = simpledialog.askstring('Host','Enter DB host/IP:')
        port = simpledialog.askinteger('Port','Enter DB port:')
        user = simpledialog.askstring('User','Enter DB user:')
        pwd = simpledialog.askstring('Password','Enter DB password:',show='*')
        dbname = simpledialog.askstring('Database','Enter database name:')
        db = {'name':name,'host':host,'port':port,'user':user,'password':pwd,'database':dbname}
        self.databases.append(db)
        self.db_tv.insert('', 'end', values=(name,host,port,user,dbname))
        self._log(f"Added DB: {name}")

    def _remove_database(self):
        sel = self.db_tv.selection()
        if sel:
            idx = self.db_tv.index(sel)
            name = self.databases.pop(idx)['name']
            self.db_tv.delete(sel)
            self._log(f"Removed DB: {name}")

    def _load_shop_items(self):
        if os.path.exists(SHOP_ITEMS_PATH):
            data = json.load(open(SHOP_ITEMS_PATH))
            for cat,items in data.items():
                for itm in items:
                    roles = 'all' if itm.get('roles')=='all' else ','.join(itm.get('roles',[]))
                    self.item_tv.insert('', 'end', values=(itm['name'],itm['command'],itm['price'],itm['limit'],roles))
            self.cat_combo['values'] = self.categories

    def _add_category(self):
        name = simpledialog.askstring('Category','Enter category name:')
        if name and name not in self.categories:
            self.categories.append(name)
            self.cat_combo['values'] = self.categories
            self._log(f"Added category: {name}")

    def _on_all_roles(self):
        if self.all_var.get():
            self.roles_entry.delete(0,tk.END)
            self.roles_entry.insert(0,'all')

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
        try:
            price_val = int(price)
        except ValueError:
            messagebox.showerror('Error','Price must be an integer')
            return
        roles_val = 'all' if roles=='all' else [r.strip() for r in roles.split(',') if r.strip()]
        itm = {'name':name,'command':cmd,'price':price_val,'limit':limit,'roles':roles_val}
        store = json.load(open(SHOP_ITEMS_PATH)) if os.path.exists(SHOP_ITEMS_PATH) else {}
        store.setdefault(cat,[]).append(itm)
        with open(SHOP_ITEMS_PATH,'w') as f: json.dump(store,f,indent=2)
        role_disp = 'all' if roles_val=='all' else ','.join(roles_val)
        self.item_tv.insert('', 'end', values=(name,cmd,price_val,limit,role_disp))
        self._log(f"Added item: {name} in category {cat}")

    def _load_library_display(self):
        for section, items in ARK_DATA.items():
            for item in items:
                self.lib_tv.insert('', 'end', values=(item.name, item.blueprint, item.mod))

    def _on_lib_import(self):
        sel = self.lib_tv.selection()
        if not sel: return
        name, blueprint, mod = self.lib_tv.item(sel,'values')
        self.name_entry.delete(0,tk.END)
        self.name_entry.insert(0,name)
        cmd = command_builders.build_spawn_command(eos_id=mod, item=ArkItem(section='', name=name, blueprint=blueprint, mod=mod), level=1, breedable=False) if mod.lower().startswith('eos') else command_builders.build_spawn_command(eos_id='', item=ArkItem(section='', name=name, blueprint=blueprint, mod=mod), level=1, breedable=False)
        self.command_entry.delete(0,tk.END)
        self.command_entry.insert(0,cmd)
        self._log(f"Imported {name} from library")

    def _log(self, text):
        self.log_box.configure(state='normal')
        self.log_box.insert('end',text+"\n")
        self.log_box.configure(state='disabled')

    def _save_log(self):
        path = filedialog.asksaveasfilename(defaultextension='.txt')
        if path:
            with open(path,'w') as f: f.write(self.log_box.get('1.0','end'))
            messagebox.showinfo('Saved',f'Log saved to {path}')

    def start_bot(self):
        if self.process:
            messagebox.showwarning('Running','Bot is already running')
            return
        self.process = subprocess.Popen(['python','Discord_Shop_System.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self._read_output()

    def _read_output(self):
        if self.process.poll() is None:
            line = self.process.stdout.readline()
            if line: self._log(line.strip())
            self.root.after(100,self._read_output)

if __name__=='__main__':
    root = tk.Tk()
    WrecksShopLauncher(root)
    root.mainloop()
