import tkinter as tk
from tkinter import ttk
from db.database import fetch_databases, get_database_details

class DBManagementPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Set up custom styles using the provided color theme.
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("Custom.Treeview.Heading",
                        background="#181F67",
                        foreground="white",
                        font=("Helvetica", 12, "bold"))
        style.configure("Custom.Treeview",
                        font=("Helvetica", 10))
        style.map("Custom.Treeview.Heading", background=[("active", "#7BB837")])
        style.configure("Custom.Small.TButton",
                        background="#7BB837",
                        foreground="white",
                        font=("Helvetica", 8, "bold"),
                        padding=(2, 2))
        style.map("Custom.Small.TButton", background=[("active", "#6AA62F")])

        # Use an outer frame to center content responsively.
        outer_frame = ttk.Frame(self)
        outer_frame.pack(expand=True, fill="both")
        content_frame = ttk.Frame(outer_frame, padding=20)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Create two main frames: left for the database list, right for details.
        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")

        # Configure grid weights so both frames expand.
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Left Frame: Title, a small Refresh button, and the Treeview.
        left_header = ttk.Frame(left_frame)
        left_header.pack(fill="x")
        lbl_left = ttk.Label(left_header, text="Databases", font=("Helvetica", 14, "bold"), foreground="#181F67")
        lbl_left.pack(side="left", anchor="w")
        refresh_btn = ttk.Button(left_header, text="Refresh", command=self.load_databases, style="Custom.Small.TButton")
        refresh_btn.pack(side="right", anchor="e")

        # Create the Treeview to list databases.
        columns = ("Database",)
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", style="Custom.Treeview")
        self.tree.heading("Database", text="Database Name")
        self.tree.column("Database", anchor="w", width=300)
        self.tree.pack(fill="both", expand=True, pady=(5,0))

        # Add a vertical scrollbar for the Treeview.
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Bind selection event to update details panel.
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Right Frame: Title and details panel (using a Text widget).
        lbl_details = ttk.Label(right_frame, text="Database Details", font=("Helvetica", 14, "bold"), foreground="#181F67")
        lbl_details.pack(anchor="w")
        self.details_text = tk.Text(right_frame, width=40, height=15, wrap="word", font=("Helvetica", 10))
        self.details_text.pack(fill="both", expand=True, pady=(5, 0))
        self.details_text.config(state="disabled")

        # Reload databases whenever this frame is shown.
        self.bind("<<ShowFrame>>", lambda e: self.load_databases())

    def load_databases(self):
        """Load databases and display them in the treeview; clear the details panel."""
        # Clear existing items in the treeview.
        for item in self.tree.get_children():
            self.tree.delete(item)
        credentials = self.controller.db_credentials
        if not credentials:
            return
        dbs = fetch_databases(credentials)
        for db in dbs:
            self.tree.insert("", tk.END, values=(db,))
        # Clear details text.
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.config(state="disabled")

    def on_tree_select(self, event):
        """When a database is selected, display its details in the details panel."""
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        db_name = item['values'][0]
        credentials = self.controller.db_credentials
        details = get_database_details(credentials, db_name)
        # Format details as text.
        details_str = ""
        if details:
            for key, value in details.items():
                details_str += f"{key}: {value}\n"
        else:
            details_str = "No details available."
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, details_str)
        self.details_text.config(state="disabled")
