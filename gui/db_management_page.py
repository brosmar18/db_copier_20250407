import tkinter as tk
from tkinter import ttk
from db.database import fetch_databases

class DBManagementPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        title = ttk.Label(self, text="Database Management", font=("Helvetica", 16, "bold"))
        title.pack(pady=(30, 20))
        
        # Listbox to display databases
        self.db_listbox = tk.Listbox(self, height=10, font=("Helvetica", 10))
        self.db_listbox.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Refresh button to reload the list
        self.refresh_btn = ttk.Button(self, text="Refresh List", command=self.load_databases)
        self.refresh_btn.pack(pady=10)
        
        # Reload databases whenever this frame is shown
        self.bind("<<ShowFrame>>", lambda e: self.load_databases())
    
    def load_databases(self):
        """Load databases and display them in the listbox."""
        self.db_listbox.delete(0, tk.END)
        credentials = self.controller.db_credentials
        if not credentials:
            return
        dbs = fetch_databases(credentials)
        for db in dbs:
            self.db_listbox.insert(tk.END, db)
