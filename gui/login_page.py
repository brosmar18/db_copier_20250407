import tkinter as tk
from tkinter import ttk, messagebox
from db import test_connection


class LoginPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Use an outer frame to center content responsively
        outer_frame = ttk.Frame(self)
        outer_frame.pack(expand=True, fill="both")
        content_frame = ttk.Frame(outer_frame)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Page Title with larger font
        label_title = ttk.Label(
            content_frame, 
            text="PostgreSQL Login", 
            font=("Segoe UI", 24, "bold")  # Increased from 16
        )
        label_title.grid(row=0, column=0, columnspan=2, pady=(40, 30))  # Increased padding

        # Use StringVar for each field with default values.
        self.host_var = tk.StringVar(value="localhost")
        self.port_var = tk.StringVar(value="5432")
        self.user_var = tk.StringVar(value="postgres")
        self.password_var = tk.StringVar()

        # Host field with larger fonts and padding
        ttk.Label(
            content_frame, 
            text="Host:", 
            font=("Segoe UI", 14, "bold")  # Increased font
        ).grid(row=1, column=0, padx=15, pady=12, sticky="w")  # Increased padding
        
        self.entry_host = ttk.Entry(
            content_frame, 
            textvariable=self.host_var,
            font=("Segoe UI", 14),  # Larger font
            width=25  # Adequate width
        )
        self.entry_host.grid(row=1, column=1, padx=15, pady=12)

        # Port field
        ttk.Label(
            content_frame, 
            text="Port:", 
            font=("Segoe UI", 14, "bold")
        ).grid(row=2, column=0, padx=15, pady=12, sticky="w")
        
        self.entry_port = ttk.Entry(
            content_frame, 
            textvariable=self.port_var,
            font=("Segoe UI", 14),
            width=25
        )
        self.entry_port.grid(row=2, column=1, padx=15, pady=12)

        # Username field
        ttk.Label(
            content_frame, 
            text="Username:", 
            font=("Segoe UI", 14, "bold")
        ).grid(row=3, column=0, padx=15, pady=12, sticky="w")
        
        self.entry_user = ttk.Entry(
            content_frame, 
            textvariable=self.user_var,
            font=("Segoe UI", 14),
            width=25
        )
        self.entry_user.grid(row=3, column=1, padx=15, pady=12)

        # Password field (user-entered)
        ttk.Label(
            content_frame, 
            text="Password:", 
            font=("Segoe UI", 14, "bold")
        ).grid(row=4, column=0, padx=15, pady=12, sticky="w")
        
        self.entry_password = ttk.Entry(
            content_frame, 
            textvariable=self.password_var, 
            show="*",
            font=("Segoe UI", 14),
            width=25
        )
        self.entry_password.grid(row=4, column=1, padx=15, pady=12)
        # Bind the Enter key to trigger connection
        self.entry_password.bind("<Return>", self.on_enter_pressed)

        # Connect button with improved styling
        style = ttk.Style()
        style.configure(
            "Login.TButton",
            font=("Segoe UI", 14, "bold"),
            padding=(30, 15),  # Larger button
            background="#3498DB",
            foreground="white"
        )
        
        button_connect = ttk.Button(
            content_frame, 
            text="Connect", 
            command=self.attempt_login,
            style="Login.TButton"
        )
        button_connect.grid(row=5, column=0, columnspan=2, pady=30)  # Increased padding

    def on_enter_pressed(self, event):
        self.attempt_login()

    def attempt_login(self):
        host = self.host_var.get().strip()
        port = self.port_var.get().strip()
        user = self.user_var.get().strip()
        password = self.password_var.get().strip()

        if not all([host, port, user, password]):
            messagebox.showerror("Error", "All fields are required.")
            return

        credentials = {"host": host, "port": port, "user": user, "password": password}

        # Test the connection using our database module.
        success, error_msg = test_connection(credentials)
        if success:
            self.controller.db_credentials = credentials
            # Directly proceed to the next page.
            self.controller.show_frame("DBManagementPage")
        else:
            messagebox.showerror(
                "Connection Failed", f"Connection Failed:\n{error_msg}"
            )