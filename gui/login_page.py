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

        # Page Title with larger font and new color
        label_title = ttk.Label(
            content_frame, 
            text="PostgreSQL Login", 
            font=("Segoe UI", 24, "bold"),
            foreground="#181F67"  # New dark blue
        )
        label_title.grid(row=0, column=0, columnspan=2, pady=(40, 30))

        # Use StringVar for each field with default values.
        self.host_var = tk.StringVar(value="localhost")
        self.port_var = tk.StringVar(value="5432")
        self.user_var = tk.StringVar(value="postgres")
        self.password_var = tk.StringVar()

        # Host field with larger fonts and new colors
        ttk.Label(
            content_frame, 
            text="Host:", 
            font=("Segoe UI", 14, "bold"),
            foreground="#181F67"  # New dark blue
        ).grid(row=1, column=0, padx=15, pady=12, sticky="w")
        
        self.entry_host = ttk.Entry(
            content_frame, 
            textvariable=self.host_var,
            font=("Segoe UI", 14),
            width=25
        )
        self.entry_host.grid(row=1, column=1, padx=15, pady=12)

        # Port field
        ttk.Label(
            content_frame, 
            text="Port:", 
            font=("Segoe UI", 14, "bold"),
            foreground="#181F67"  # New dark blue
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
            font=("Segoe UI", 14, "bold"),
            foreground="#181F67"  # New dark blue
        ).grid(row=3, column=0, padx=15, pady=12, sticky="w")
        
        self.entry_user = ttk.Entry(
            content_frame, 
            textvariable=self.user_var,
            font=("Segoe UI", 14),
            width=25
        )
        self.entry_user.grid(row=3, column=1, padx=15, pady=12)

        # Password field
        ttk.Label(
            content_frame, 
            text="Password:", 
            font=("Segoe UI", 14, "bold"),
            foreground="#181F67"  # New dark blue
        ).grid(row=4, column=0, padx=15, pady=12, sticky="w")
        
        self.entry_password = ttk.Entry(
            content_frame, 
            textvariable=self.password_var, 
            show="*",
            font=("Segoe UI", 14),
            width=25
        )
        self.entry_password.grid(row=4, column=1, padx=15, pady=12)
        self.entry_password.bind("<Return>", self.on_enter_pressed)

        # Connect button with comprehensive new color scheme styling
        style = ttk.Style()
        
        # Ensure the theme is set properly
        style.theme_use("clam")
        
        style.configure(
            "Login.TButton",
            font=("Segoe UI", 14, "bold"),
            padding=(30, 15),
            background="#7BB837",  # New green
            foreground="white",
            borderwidth=0,
            relief="flat",
            focuscolor="none",
            # Additional properties to ensure proper rendering
            compound="center",
            anchor="center"
        )
        style.map(
            "Login.TButton", 
            background=[
                ("active", "#6FA02E"),      # Darker green on hover
                ("pressed", "#5F8A26")      # Even darker green when pressed
            ],
            foreground=[("active", "white"), ("pressed", "white")],
            relief=[("pressed", "flat"), ("!pressed", "flat")]
        )
        
        button_connect = ttk.Button(
            content_frame, 
            text="Connect", 
            command=self.attempt_login,
            style="Login.TButton"
        )
        button_connect.grid(row=5, column=0, columnspan=2, pady=30)

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