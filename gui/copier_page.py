import tkinter as tk
from tkinter import ttk, messagebox
import threading
from db.database import fetch_databases, copy_database_logic

class CopierPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Page title
        title = ttk.Label(self, text="Database Copier", font=("Helvetica", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(30, 20))
        
        # Source Database selection
        ttk.Label(self, text="Select Source Database:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.db_combo = ttk.Combobox(self, state="readonly", font=("Helvetica", 10))
        self.db_combo.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Refresh list button
        self.refresh_btn = ttk.Button(self, text="Refresh", command=self.load_databases)
        self.refresh_btn.grid(row=1, column=2, padx=10, pady=5)
        
        # New Database name entry
        ttk.Label(self, text="New Database Name:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.new_db_entry = ttk.Entry(self, font=("Helvetica", 10))
        self.new_db_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # Copy button
        self.copy_btn = ttk.Button(self, text="Copy Database", command=self.start_copy)
        self.copy_btn.grid(row=3, column=0, columnspan=3, pady=20)
        
        # Progress bar and status label
        self.progress_bar = ttk.Progressbar(self, mode="determinate", maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.status_label = ttk.Label(self, text="", font=("Helvetica", 10))
        self.status_label.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="w")
        
        self.copy_thread = None
        
        # Reload databases when this frame is shown
        self.bind("<<ShowFrame>>", lambda e: self.load_databases())
    
    def load_databases(self):
        """Load the list of databases from the server."""
        credentials = self.controller.db_credentials
        if not credentials:
            return
        db_list = fetch_databases(credentials)
        self.db_combo['values'] = db_list
        if db_list:
            self.db_combo.current(0)
    
    def start_copy(self):
        src_db = self.db_combo.get()
        new_db = self.new_db_entry.get().strip()
        if not src_db:
            messagebox.showwarning("Input Error", "Please select a source database.")
            return
        if not new_db:
            messagebox.showwarning("Input Error", "Please enter a name for the new database.")
            return
        
        # Disable UI elements during the copy operation
        self.copy_btn.config(state="disabled")
        self.db_combo.config(state="disabled")
        self.new_db_entry.config(state="disabled")
        self.progress_bar['value'] = 0
        self.update_status("Starting database copy...")
        
        # Run the copy process in a background thread
        self.copy_thread = threading.Thread(target=self.do_copy, args=(src_db, new_db), daemon=True)
        self.copy_thread.start()
        self.after(500, self.update_progress)
    
    def update_progress(self):
        if self.copy_thread and self.copy_thread.is_alive():
            current_value = self.progress_bar['value']
            if current_value < 95:
                self.progress_bar['value'] += 5
            self.after(500, self.update_progress)
        else:
            self.progress_bar['value'] = 100
    
    def update_status(self, message):
        self.status_label.config(text=message)
    
    def do_copy(self, src_db, new_db):
        credentials = self.controller.db_credentials
        try:
            copy_database_logic(credentials, src_db, new_db, self.update_status)
            self.after(0, lambda: messagebox.showinfo("Success", f"Database '{new_db}' created as a copy of '{src_db}'."))
            self.after(0, self.load_databases)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Error copying database: {e}"))
            self.after(0, lambda: self.update_status("Error occurred during copy."))
        finally:
            self.after(0, lambda: self.copy_btn.config(state="normal"))
            self.after(0, lambda: self.db_combo.config(state="readonly"))
            self.after(0, lambda: self.new_db_entry.config(state="normal"))
