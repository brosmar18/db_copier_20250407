import tkinter as tk
from tkinter import ttk, messagebox
import threading
from db import (
    fetch_databases,
    get_database_details,
    get_tables_for_database,
    get_columns_for_table,
    get_table_details,
    terminate_and_delete_database
)

class DBManagementPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_db = None         # Currently selected database name
        self.all_databases = []        # List of all databases
        self.all_items = []            # List of tables (or columns) for the left pane

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

        # Two main panes: left for databases, right for details and tables/fields.
        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)

        # === LEFT PANE: DATABASES ===
        left_header = ttk.Frame(left_frame)
        left_header.pack(fill="x")
        lbl_left = ttk.Label(left_header, text="Databases", font=("Helvetica", 14, "bold"), foreground="#181F67")
        lbl_left.pack(side="left", anchor="w")
        refresh_btn = ttk.Button(left_header, text="Refresh", command=self.load_databases, style="Custom.Small.TButton")
        refresh_btn.pack(side="right", anchor="e", padx=2, pady=2)
        delete_btn = ttk.Button(left_header, text="Delete", command=self.delete_selected_database, style="Delete.TButton")
        delete_btn.pack(side="right", anchor="e", padx=5, pady=2)

        self.db_search_var = tk.StringVar()
        db_search_frame = ttk.Frame(left_frame)
        db_search_frame.pack(fill="x", padx=2, pady=(2, 5))
        ttk.Label(db_search_frame, text="Search:", font=("Helvetica", 10)).pack(side="left")
        self.db_search_entry = ttk.Entry(db_search_frame, textvariable=self.db_search_var)
        self.db_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.db_search_entry.bind("<KeyRelease>", self.filter_databases)

        self.db_tree = ttk.Treeview(left_frame, columns=("Database",), show="headings", selectmode="extended")
        self.db_tree.heading("Database", text="Database Name")
        self.db_tree.column("Database", anchor="w", width=200)
        self.db_tree.pack(expand=True, fill="both", pady=5)
        self.db_tree.bind("<<TreeviewSelect>>", self.on_db_select)

        # === RIGHT PANE: DETAILS & TABLES/FIELDS ===
        # Upper part: Details text area.
        self.details_label = ttk.Label(right_frame, text="Details", font=("Helvetica", 14, "bold"), foreground="#181F67")
        self.details_label.grid(row=0, column=0, sticky="w")
        self.details_text = tk.Text(right_frame, wrap="word", font=("Helvetica", 10), height=6)
        self.details_text.grid(row=1, column=0, sticky="nsew", pady=(5, 5))
        self.details_text.config(state="disabled")
        right_frame.rowconfigure(1, weight=0)

        # Lower part: Search field and a frame that holds two side-by-side treeviews:
        # Left: List of tables; Right: List of fields for the selected table.
        self.item_search_var = tk.StringVar()
        item_search_frame = ttk.Frame(right_frame)
        item_search_frame.grid(row=2, column=0, sticky="ew", padx=2, pady=(2, 5))
        ttk.Label(item_search_frame, text="Search:", font=("Helvetica", 10)).pack(side="left")
        self.item_search_entry = ttk.Entry(item_search_frame, textvariable=self.item_search_var)
        self.item_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.item_search_entry.bind("<KeyRelease>", self.filter_items)

        # Header row for the tables/fields section.
        header_frame_right = ttk.Frame(right_frame)
        header_frame_right.grid(row=3, column=0, sticky="ew")
        self.right_label = ttk.Label(header_frame_right, text="Tables", font=("Helvetica", 14, "bold"), foreground="#181F67")
        self.right_label.pack(side="left", anchor="w")
        self.back_button = ttk.Button(header_frame_right, text="Refresh", command=self.back_to_tables, style="Custom.Small.TButton")
        self.back_button.pack(side="right", anchor="e")
        self.back_button.grid_remove()  # Initially hidden

        # Bottom frame: will hold two treeviews side by side.
        self.bottom_frame = ttk.Frame(right_frame)
        self.bottom_frame.grid(row=4, column=0, sticky="nsew", pady=(5, 0))
        right_frame.rowconfigure(4, weight=1)
        right_frame.columnconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(1, weight=1)

        # Left treeview: List of tables.
        self.item_tree = ttk.Treeview(self.bottom_frame, columns=("Item",), show="headings", style="Custom.Treeview")
        self.item_tree.heading("Item", text="Table Name")
        self.item_tree.column("Item", anchor="w", width=200)
        self.item_tree.grid(row=0, column=0, sticky="nsew")
        self.item_tree.bind("<<TreeviewSelect>>", self.on_item_select)
        # (We no longer use double-click to show fields because fields will be shown in the right box.)
        # Right treeview: List of fields (columns) for the selected table.
        self.fields_tree = ttk.Treeview(self.bottom_frame, columns=("Field",), show="headings", style="Custom.Treeview")
        self.fields_tree.heading("Field", text="Fields")
        self.fields_tree.column("Field", anchor="w", width=200)
        self.fields_tree.grid(row=0, column=1, sticky="nsew")

        self.bind("<<ShowFrame>>", lambda e: self.load_databases())

    def load_databases(self):
        """Load databases into the left treeview, clear search and details."""
        self.db_tree.delete(*self.db_tree.get_children())
        credentials = self.controller.db_credentials
        if not credentials:
            return
        dbs = fetch_databases(credentials)
        self.all_databases = sorted(dbs)
        for db in self.all_databases:
            self.db_tree.insert("", tk.END, values=(db,))
        self.db_search_var.set("")
        self.clear_details()
        self.back_button.grid_remove()
        self.right_label.config(text="Tables")
        self.item_search_var.set("")
        self.item_tree.delete(*self.item_tree.get_children())
        self.fields_tree.delete(*self.fields_tree.get_children())

    def clear_details(self):
        """Clear the details text and the fields tree."""
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.config(state="disabled")
        self.fields_tree.delete(*self.fields_tree.get_children())

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
        item = self.db_tree.item(selected[0])
        db_name = item['values'][0]
        self.current_db = db_name
        credentials = self.controller.db_credentials
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
        tables = get_tables_for_database(credentials, db_name)
        tables = sorted(tables)
        self.all_items = tables
        self.populate_items(self.all_items, header="Table Name")
        self.right_label.config(text="Tables")
        self.back_button.grid_remove()
        self.item_search_var.set("")
        self.fields_tree.delete(*self.fields_tree.get_children())

    def populate_items(self, items, header="Table Name"):
        """Populate the left treeview with items (tables)."""
        self.item_tree.delete(*self.item_tree.get_children())
        self.item_tree.heading("Item", text=header)
        for item in items:
            self.item_tree.insert("", tk.END, values=(item,))

    def filter_items(self, event):
        """Filter the tables based on the search term."""
        term = self.item_search_var.get().lower()
        filtered = [item for item in self.all_items if term in item.lower()]
        self.populate_items(filtered, header="Table Name")

    def on_item_select(self, event):
        """
        When a table is selected, update the details text with basic table info
        (table name and record count) and populate the fields_tree with the list of fields.
        """
        selected = self.item_tree.selection()
        if not selected:
            return
        item = self.item_tree.item(selected[0])
        table_name = item['values'][0]
        credentials = self.controller.db_credentials
        # Get basic table details (e.g., record count)
        table_details = get_table_details(credentials, self.current_db, table_name)
        details_str = ""
        if table_details:
            details_str += f"Table Name: {table_details.get('Table Name')}\n"
            details_str += f"Record Count: {table_details.get('Record Count')}\n"
        else:
            details_str += "No table details available.\n"
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, details_str)
        self.details_text.config(state="disabled")
        # Populate the fields_tree with columns.
        columns = get_columns_for_table(credentials, self.current_db, table_name)
        self.fields_tree.delete(*self.fields_tree.get_children())
        if columns:
            for col in sorted(columns):
                self.fields_tree.insert("", tk.END, values=(col,))
        else:
            self.fields_tree.insert("", tk.END, values=("No fields available",))

    def on_item_double_click(self, event):
        """
        Double-click behavior can be repurposed if needed.
        For now, we leave it empty since fields are automatically shown.
        """
        pass

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
        self.item_search_var.set("")
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
        self.fields_tree.delete(*self.fields_tree.get_children())

    def delete_selected_database(self):
        selected = self.db_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "No database selected for deletion.")
            return
        # Get all selected database names
        db_names = [self.db_tree.item(item)['values'][0] for item in selected]
        confirm = messagebox.askokcancel(
            "Confirm Deletion",
            f"WARNING: This will permanently delete the following databases:\n\n{', '.join(db_names)}\n\nThis action cannot be undone.\nDo you want to proceed?"
        )
        if not confirm:
            return
        def delete_database():
            credentials = self.controller.db_credentials
            for db_name in db_names:
                try:
                    terminate_and_delete_database(credentials, db_name)
                except Exception as e:
                    messagebox.showerror("Error", f"Error deleting database {db_name}: {e}")
            self.load_databases()
            messagebox.showinfo("Deletion Complete", "Database(s) have been deleted.")
        threading.Thread(target=delete_database, daemon=True).start()

