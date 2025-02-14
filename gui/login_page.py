import tkinter as tk
from tkinter import ttk, messagebox
from db.database import test_connection

class LoginPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Page title
        self.label_title = ttk.Label(self, text="PostgreSQL Login", font=("Helvetica", 16, "bold"))
        self.label_title.grid(row=0, column=0, columnspan=2, pady=(30, 20))
        
        # Host field (default: localhost)
        ttk.Label(self, text="Host:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_host = ttk.Entry(self)
        self.entry_host.grid(row=1, column=1, padx=10, pady=5)
        self.entry_host.insert(0, "localhost")
        
        # Port field (default: 5432)
        ttk.Label(self, text="Port:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.entry_port = ttk.Entry(self)
        self.entry_port.grid(row=2, column=1, padx=10, pady=5)
        self.entry_port.insert(0, "5432")
        
        # Username field (default: postgres)
        ttk.Label(self, text="Username:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.entry_user = ttk.Entry(self)
        self.entry_user.grid(row=3, column=1, padx=10, pady=5)
        self.entry_user.insert(0, "postgres")
        
        # Password field (user-entered)
        ttk.Label(self, text="Password:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.entry_password = ttk.Entry(self, show="*")
        self.entry_password.grid(row=4, column=1, padx=10, pady=5)
        
        # Connect button
        self.button_connect = ttk.Button(self, text="Connect", command=self.attempt_login)
        self.button_connect.grid(row=5, column=0, columnspan=2, pady=20)
    
    def attempt_login(self):
        host = self.entry_host.get().strip()
        port = self.entry_port.get().strip()
        user = self.entry_user.get().strip()
        password = self.entry_password.get().strip()
        
        if not all([host, port, user, password]):
            messagebox.showerror("Error", "All fields are required.")
            return
        
        credentials = {
            "host": host,
            "port": port,
            "user": user,
            "password": password
        }
        
        # Test the connection using our database module
        if test_connection(credentials):
            self.controller.db_credentials = credentials
            messagebox.showinfo("Success", "Connected to PostgreSQL successfully!")
            # Proceed to the Copier page after a successful login
            self.controller.show_frame("CopierPage")
        else:
            messagebox.showerror("Connection Failed", "Could not connect to PostgreSQL. Check credentials.")
