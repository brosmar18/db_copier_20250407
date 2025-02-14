import tkinter as tk
from tkinter import ttk, messagebox
import threading
from db import (fetch_databases, get_database_details, get_tables_for_database,
                get_columns_for_table, get_table_details, terminate_and_delete_database)

class DBManagementPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_db = None  # Currently selected database name
        self.in_columns_view = False  # Flag to indicate if we're showing columns
        self.all_databases = []  # Full list of databases
        self.all_items = []      # Full list of tables (or columns)

        # Set up custom styles using your color theme.
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
        # New style for delete button.
        style.configure("Delete.TButton",
                        background="#D9534F",
                        foreground="white",
                        font=("Helvetica", 10, "bold"),
                        padding=(4, 4))
        style.map("Delete.TButton", background=[("active", "#C9302C")])

        # Outer container
        outer_frame = ttk.Frame(self)
        outer_frame.pack(expand=True, fill="both", padx=10, pady=10)
        content_frame = ttk.Frame(outer_frame)
        content_frame.pack(expand=True, fill="both")

        # Two main panes: left for databases, right for details and tables/columns.
        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)

        # === LEFT PANE ===
        # Header with label, Refresh, and Delete Selected buttons.
        left_header = ttk.Frame(left_frame)
        left_header.pack(fill="x")
        lbl_left = ttk.Label(left_header, text="Databases", font=("Helvetica", 14, "bold"), foreground="#181F67")
        lbl_left.pack(side="left", anchor="w")
        refresh_btn = ttk.Button(left_header, text="Refresh", command=self.load_databases, style="Custom.Small.TButton")
        refresh_btn.pack(side="right", anchor="e", padx=2, pady=2)
        delete_btn = ttk.Button(left_header, text="Delete", command=self.delete_selected_databases, style="Delete.TButton")
        delete_btn.pack(side="right", anchor="e", padx=5, pady=2)

        # Search field for databases.
        self.db_search_var = tk.StringVar()
        db_search_frame = ttk.Frame(left_frame)
        db_search_frame.pack(fill="x", padx=2, pady=(2, 5))
        ttk.Label(db_search_frame, text="Search:", font=("Helvetica", 10)).pack(side="left")
        self.db_search_entry = ttk.Entry(db_search_frame, textvariable=self.db_search_var)
        self.db_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.db_search_entry.bind("<KeyRelease>", self.filter_databases)

        # Treeview for database list (allowing multiple selection).
        self.db_tree = ttk.Treeview(left_frame, columns=("Database",), show="headings", style="Custom.Treeview", selectmode="extended")
        self.db_tree.heading("Database", text="Database Name")
        self.db_tree.column("Database", anchor="w", width=200)
        self.db_tree.pack(expand=True, fill="both", pady=5)
        self.db_tree.bind("<<TreeviewSelect>>", self.on_db_select)

        # === RIGHT PANE ===
        # Top: Details section.
        self.details_label = ttk.Label(right_frame, text="Details", font=("Helvetica", 14, "bold"), foreground="#181F67")
        self.details_label.grid(row=0, column=0, sticky="w")
        self.details_text = tk.Text(right_frame, wrap="word", font=("Helvetica", 10), height=6)
        self.details_text.grid(row=1, column=0, sticky="nsew", pady=(5, 5))
        self.details_text.config(state="disabled")

        # Search field for tables/columns.
        self.item_search_var = tk.StringVar()
        item_search_frame = ttk.Frame(right_frame)
        item_search_frame.grid(row=2, column=0, sticky="ew", padx=2, pady=(2, 5))
        ttk.Label(item_search_frame, text="Search:", font=("Helvetica", 10)).pack(side="left")
        self.item_search_entry = ttk.Entry(item_search_frame, textvariable=self.item_search_var)
        self.item_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.item_search_entry.bind("<KeyRelease>", self.filter_items)

        # Header for tables/columns section with a Back button.
        header_frame_right = ttk.Frame(right_frame)
        header_frame_right.grid(row=3, column=0, sticky="ew")
        self.right_label = ttk.Label(header_frame_right, text="Tables", font=("Helvetica", 14, "bold"), foreground="#181F67")
        self.right_label.pack(side="left", anchor="w")
        self.back_button = ttk.Button(header_frame_right, text="Back", command=self.back_to_tables, style="Custom.Small.TButton")
        self.back_button.pack(side="right", anchor="e")
        self.back_button.grid_remove()  # Hide initially

        # Treeview for tables/columns.
        self.item_tree = ttk.Treeview(right_frame, columns=("Item",), show="headings", style="Custom.Treeview")
        self.item_tree.heading("Item", text="Table Name")
        self.item_tree.column("Item", anchor="w", width=200)
        self.item_tree.grid(row=4, column=0, sticky="nsew", pady=(5, 0))
        self.item_tree.bind("<Double-1>", self.on_item_double_click)
        self.item_tree.bind("<<TreeviewSelect>>", self.on_item_select)
        right_frame.rowconfigure(4, weight=1)
        right_frame.columnconfigure(0, weight=1)

        self.bind("<<ShowFrame>>", lambda e: self.load_databases())

    def load_databases(self):
        """Load databases into the left treeview, clear search and details."""
        for item in self.db_tree.get_children():
            self.db_tree.delete(item)
        credentials = self.controller.db_credentials
        if not credentials:
            return
        dbs = fetch_databases(credentials)
        self.all_databases = sorted(dbs)
        for db in self.all_databases:
            self.db_tree.insert("", tk.END, values=(db,))
        self.db_search_var.set("")
        self.clear_details()
        self.in_columns_view = False
        self.back_button.grid_remove()
        self.right_label.config(text="Tables")
        self.item_search_var.set("")
        self.item_tree.delete(*self.item_tree.get_children())

    def clear_details(self):
        """Clear the details and tables/columns views."""
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.config(state="disabled")
        for item in self.item_tree.get_children():
            self.item_tree.delete(item)

    def filter_databases(self, event):
        """Filter the database list based on the search term."""
        term = self.db_search_var.get().lower()
        filtered = [db for db in self.all_databases if term in db.lower()]
        self.db_tree.delete(*self.db_tree.get_children())
        for db in filtered:
            self.db_tree.insert("", tk.END, values=(db,))

    def on_db_select(self, event):
        """When a database is selected, update details and show its tables."""
        selected = self.db_tree.selection()
        if not selected:
            return
        # For multiple selections, use the first one for details.
        item = self.db_tree.item(selected[0])
        db_name = item['values'][0]
        self.current_db = db_name
        credentials = self.controller.db_credentials

        # Display database details.
        details = get_database_details(credentials, db_name)
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

        # Display list of tables.
        tables = get_tables_for_database(credentials, db_name)
        tables = sorted(tables)
        self.all_items = tables
        self.populate_items(self.all_items, header="Table Name")
        self.right_label.config(text="Tables")
        self.in_columns_view = False
        self.back_button.grid_remove()
        self.item_search_var.set("")

    def populate_items(self, items, header="Table Name"):
        """Populate the item tree with items (tables or columns)."""
        self.item_tree.delete(*self.item_tree.get_children())
        self.item_tree.heading("Item", text=header)
        for item in items:
            self.item_tree.insert("", tk.END, values=(item,))

    def filter_items(self, event):
        """Filter tables/columns based on the search term."""
        term = self.item_search_var.get().lower()
        filtered = [item for item in self.all_items if term in item.lower()]
        header = "Column Name" if self.in_columns_view else "Table Name"
        self.populate_items(filtered, header=header)

    def on_item_select(self, event):
        """When a table is selected (single-click), update details with its info."""
        if self.in_columns_view:
            return
        selected = self.item_tree.selection()
        if not selected:
            return
        item = self.item_tree.item(selected[0])
        table_name = item['values'][0]
        credentials = self.controller.db_credentials
        table_details = get_table_details(credentials, self.current_db, table_name)
        details_str = ""
        if table_details:
            for key, value in table_details.items():
                details_str += f"{key}: {value}\n"
        else:
            details_str = "No details available for this table."
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, details_str)
        self.details_text.config(state="disabled")

    def on_item_double_click(self, event):
        """When a table is double-clicked, show its columns."""
        if self.in_columns_view:
            return
        selected = self.item_tree.selection()
        if not selected:
            return
        item = self.item_tree.item(selected[0])
        table_name = item['values'][0]
        credentials = self.controller.db_credentials
        columns = get_columns_for_table(credentials, self.current_db, table_name)
        columns = sorted(columns)
        self.all_items = columns
        self.populate_items(columns, header="Column Name")
        self.right_label.config(text=f"Columns in '{table_name}'")
        self.back_button.grid()  # Show back button
        self.in_columns_view = True
        self.item_search_var.set("")

    def back_to_tables(self):
        """Return to the tables view for the current database."""
        if not self.current_db:
            return
        credentials = self.controller.db_credentials
        tables = get_tables_for_database(credentials, self.current_db)
        tables = sorted(tables)
        self.all_items = tables
        self.populate_items(tables, header="Table Name")
        self.right_label.config(text="Tables")
        self.back_button.grid_remove()
        self.in_columns_view = False
        self.item_search_var.set("")
        # Optionally, reset details to database details.
        details = get_database_details(credentials, self.current_db)
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

    def delete_selected_databases(self):
        """Terminate sessions and delete the selected databases after confirmation."""
        selected = self.db_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "No database selected for deletion.")
            return
        
        db_names = [self.db_tree.item(item)['values'][0] for item in selected]
        confirm = messagebox.askokcancel(
            "Confirm Deletion",
            f"WARNING: This will permanently delete the following database(s):\n\n" +
            "\n".join(db_names) +
            "\n\nThis action cannot be undone.\nDo you want to proceed?"
        )
        if not confirm:
            return
        
        def delete_databases():
            credentials = self.controller.db_credentials
            for db_name in db_names:
                try:
                    terminate_and_delete_database(credentials, db_name)
                except Exception as e:
                    messagebox.showerror("Error", f"Error deleting database {db_name}: {e}")
            self.load_databases()
            messagebox.showinfo("Deletion Complete", "Selected database(s) have been deleted.")
        
        threading.Thread(target=delete_databases, daemon=True).start()
