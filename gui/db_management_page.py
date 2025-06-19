import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sqlparse
from db import (
    fetch_databases,
    get_database_details,
    get_tables_for_database,
    get_columns_for_table,
    get_table_details,
    terminate_and_delete_database,
    copy_database_logic,
    rename_database,
    execute_sql_query,
)


class DBManagementPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_db = None
        self.all_databases = []
        self.all_items = []
        self.context_menu_dbs = []  # Changed to support multiple selections
        self.protected_databases = [
            "postgres",
            "template0",
            "template1",
        ]  # System databases to protect

        # --- Styles ---
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Custom.Treeview.Heading",
            background="#181F67",
            foreground="white",
            font=("Helvetica", 12, "bold"),
        )
        style.configure("Custom.Treeview", font=("Helvetica", 10))
        style.map("Custom.Treeview.Heading", background=[("active", "#7BB837")])
        style.configure(
            "Refresh.TButton",
            background="#7BB837",
            foreground="white",
            font=("Helvetica", 10, "bold"),
            padding=(8, 4),
            borderwidth=0,
            relief="flat",
        )
        style.map("Refresh.TButton", background=[("active", "#6AA62F")])

        # --- Layout ---
        outer_frame = ttk.Frame(self)
        outer_frame.pack(expand=True, fill="both", padx=10, pady=10)
        content_frame = ttk.Frame(outer_frame)
        content_frame.pack(expand=True, fill="both")

        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)

        # --- LEFT PANE: DATABASES ---
        left_header = ttk.Frame(left_frame)
        left_header.pack(fill="x")
        ttk.Label(
            left_header,
            text="Databases",
            font=("Helvetica", 14, "bold"),
            foreground="#181F67",
        ).pack(side="left", anchor="w")
        ttk.Button(
            left_header,
            text="Refresh",
            command=self.load_databases,
            style="Refresh.TButton",
        ).pack(side="right", padx=5, pady=5)

        # search
        self.db_search_var = tk.StringVar()
        db_search_frame = ttk.Frame(left_frame)
        db_search_frame.pack(fill="x", padx=2, pady=(2, 5))
        ttk.Label(db_search_frame, text="Search:", font=("Helvetica", 10)).pack(
            side="left"
        )
        self.db_search_entry = ttk.Entry(
            db_search_frame, textvariable=self.db_search_var
        )
        self.db_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.db_search_entry.bind("<KeyRelease>", self.filter_databases)

        # treeview
        self.db_tree = ttk.Treeview(
            left_frame, columns=("Database",), show="headings", selectmode="extended"
        )
        self.db_tree.heading("Database", text="Database Name")
        self.db_tree.column("Database", anchor="w", width=200)
        self.db_tree.pack(expand=True, fill="both", pady=5)
        self.db_tree.bind("<<TreeviewSelect>>", self.on_db_select)

        # --- CONTEXT MENU: dynamically updated based on selection ---
        self.db_context_menu = tk.Menu(
            self,
            tearoff=0,
            font=("Helvetica", 10),
            bg="white",
            fg="black",
            activebackground="#7BB837",
            activeforeground="white",
        )

        # bind right-click / ctrl+click / menu key
        self.db_tree.bind("<Button-3>", self.show_db_context_menu)
        self.db_tree.bind("<Control-Button-1>", self.show_db_context_menu)
        self.db_tree.bind("<Button-2>", self.show_db_context_menu)
        self.db_tree.bind("<App>", self.show_db_context_menu_keyboard)
        self.db_tree.bind("<Shift-F10>", self.show_db_context_menu_keyboard)

        # === RIGHT PANE: DETAILS & TABLES/FIELDS ===
        ttk.Label(
            right_frame,
            text="Details",
            font=("Helvetica", 14, "bold"),
            foreground="#181F67",
        ).grid(row=0, column=0, sticky="w")
        self.details_text = tk.Text(
            right_frame, wrap="word", font=("Helvetica", 10), height=6
        )
        self.details_text.grid(row=1, column=0, sticky="nsew", pady=(5, 5))
        self.details_text.config(state="disabled")
        right_frame.rowconfigure(1, weight=0)

        # Table/field search & header
        self.item_search_var = tk.StringVar()
        item_search_frame = ttk.Frame(right_frame)
        item_search_frame.grid(row=2, column=0, sticky="ew", padx=2, pady=(2, 5))
        ttk.Label(item_search_frame, text="Search:", font=("Helvetica", 10)).pack(
            side="left"
        )
        self.item_search_entry = ttk.Entry(
            item_search_frame, textvariable=self.item_search_var
        )
        self.item_search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.item_search_entry.bind("<KeyRelease>", self.filter_items)

        header_frame_right = ttk.Frame(right_frame)
        header_frame_right.grid(row=3, column=0, sticky="ew")
        self.right_label = ttk.Label(
            header_frame_right,
            text="Tables",
            font=("Helvetica", 14, "bold"),
            foreground="#181F67",
        )
        self.right_label.pack(side="left")
        self.back_button = ttk.Button(
            header_frame_right,
            text="Refresh",
            command=self.back_to_tables,
            style="Refresh.TButton",
        )
        self.back_button.pack(side="right")
        self.back_button.grid_remove()

        # Tables/fields trees
        self.bottom_frame = ttk.Frame(right_frame)
        self.bottom_frame.grid(row=4, column=0, sticky="nsew", pady=(5, 0))
        right_frame.rowconfigure(4, weight=1)
        right_frame.columnconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(1, weight=1)

        self.item_tree = ttk.Treeview(
            self.bottom_frame,
            columns=("Item",),
            show="headings",
            style="Custom.Treeview",
        )
        self.item_tree.heading("Item", text="Table Name")
        self.item_tree.column("Item", anchor="w", width=200)
        self.item_tree.grid(row=0, column=0, sticky="nsew")
        self.item_tree.bind("<<TreeviewSelect>>", self.on_item_select)

        self.fields_tree = ttk.Treeview(
            self.bottom_frame,
            columns=("Field",),
            show="headings",
            style="Custom.Treeview",
        )
        self.fields_tree.heading("Field", text="Fields")
        self.fields_tree.column("Field", anchor="w", width=200)
        self.fields_tree.grid(row=0, column=1, sticky="nsew")

        self.bind("<<ShowFrame>>", lambda e: self.load_databases())

    # --- Database loading/filtering/selection methods ---
    def load_databases(self):
        self.db_tree.delete(*self.db_tree.get_children())
        creds = self.controller.db_credentials
        if not creds:
            return
        self.all_databases = sorted(fetch_databases(creds))
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
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.config(state="disabled")
        self.fields_tree.delete(*self.fields_tree.get_children())

    def filter_databases(self, event):
        term = self.db_search_var.get().lower()
        filtered = [db for db in self.all_databases if term in db.lower()]
        self.db_tree.delete(*self.db_tree.get_children())
        for db in filtered:
            self.db_tree.insert("", tk.END, values=(db,))

    def on_db_select(self, event):
        selected = self.db_tree.selection()
        if not selected:
            return
        db_name = self.db_tree.item(selected[0])["values"][0]
        self.current_db = db_name
        creds = self.controller.db_credentials
        details = get_database_details(creds, db_name) or {}
        details_str = (
            "\n".join(f"{k}: {v}" for k, v in details.items())
            or "No details available."
        )
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, details_str)
        self.details_text.config(state="disabled")

        tables = sorted(get_tables_for_database(creds, db_name) or [])
        self.all_items = tables
        self.populate_items(tables, header="Table Name")
        self.right_label.config(text="Tables")
        self.back_button.grid_remove()
        self.item_search_var.set("")
        self.fields_tree.delete(*self.fields_tree.get_children())

    def populate_items(self, items, header="Table Name"):
        self.item_tree.delete(*self.item_tree.get_children())
        self.item_tree.heading("Item", text=header)
        for item in items:
            self.item_tree.insert("", tk.END, values=(item,))

    def filter_items(self, event):
        term = self.item_search_var.get().lower()
        filtered = [it for it in self.all_items if term in it.lower()]
        self.populate_items(filtered, header="Table Name")

    def on_item_select(self, event):
        selected = self.item_tree.selection()
        if not selected:
            return
        table_name = self.item_tree.item(selected[0])["values"][0]
        creds = self.controller.db_credentials
        td = get_table_details(creds, self.current_db, table_name) or {}
        details_str = (
            f"Table Name: {td.get('Table Name')}\nRecord Count: {td.get('Record Count')}\n"
            if td
            else "No table details available.\n"
        )
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, details_str)
        self.details_text.config(state="disabled")

        cols = sorted(get_columns_for_table(creds, self.current_db, table_name) or [])
        self.fields_tree.delete(*self.fields_tree.get_children())
        for col in cols:
            self.fields_tree.insert("", tk.END, values=(col,))
        if not cols:
            self.fields_tree.insert("", tk.END, values=("No fields available",))

    def back_to_tables(self):
        if not self.current_db:
            return
        creds = self.controller.db_credentials
        tables = sorted(get_tables_for_database(creds, self.current_db) or [])
        self.all_items = tables
        self.populate_items(tables, header="Table Name")
        self.right_label.config(text="Tables")
        self.back_button.grid_remove()
        self.item_search_var.set("")
        details = get_database_details(creds, self.current_db) or {}
        ds = (
            "\n".join(f"{k}: {v}" for k, v in details.items())
            or "No details available."
        )
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert(tk.END, ds)
        self.details_text.config(state="disabled")
        self.fields_tree.delete(*self.fields_tree.get_children())

    def is_protected_database(self, db_name):
        """Check if a database is protected from deletion"""
        return db_name.lower() in [db.lower() for db in self.protected_databases]

    def get_deletable_databases(self, db_names):
        """Filter out protected databases from a list"""
        return [db for db in db_names if not self.is_protected_database(db)]

    def get_protected_databases(self, db_names):
        """Get only protected databases from a list"""
        return [db for db in db_names if self.is_protected_database(db)]

    # --- CONTEXT-MENU HANDLERS ---
    def show_db_context_menu(self, event):
        item = self.db_tree.identify_row(event.y)
        if not item:
            return

        # If clicked item is not in current selection, select only it
        if item not in self.db_tree.selection():
            self.db_tree.selection_set(item)

        # Get all selected items
        selected_items = self.db_tree.selection()
        if not selected_items:
            return

        selected_dbs = [self.db_tree.item(i)["values"][0] for i in selected_items]
        self.context_menu_dbs = selected_dbs

        # Update menu labels based on selection count
        self.update_context_menu_labels(len(selected_dbs))

        try:
            self.db_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.db_context_menu.grab_release()

    def show_db_context_menu_keyboard(self, event):
        selected = self.db_tree.selection()
        if not selected:
            return

        selected_dbs = [self.db_tree.item(i)["values"][0] for i in selected]
        self.context_menu_dbs = selected_dbs

        # Update menu labels based on selection count
        self.update_context_menu_labels(len(selected_dbs))

        # Get position from first selected item
        item = selected[0]
        bbox = self.db_tree.bbox(item)
        if not bbox:
            return
        x = self.db_tree.winfo_rootx() + bbox[0] + bbox[2] // 2
        y = self.winfo_rooty() + bbox[1] + bbox[3] // 2
        try:
            self.db_context_menu.tk_popup(x, y)
        finally:
            self.db_context_menu.grab_release()

    def update_context_menu_labels(self, count):
        """Update context menu labels based on number of selected databases"""
        # Clear existing menu
        self.db_context_menu.delete(0, "end")

        # Check if any selected databases are deletable
        deletable_dbs = self.get_deletable_databases(self.context_menu_dbs)
        protected_dbs = self.get_protected_databases(self.context_menu_dbs)

        if count == 1:
            self.db_context_menu.add_command(
                label="🔁 Clone DB", command=self.clone_database
            )
            # Only show rename for non-protected databases
            if not self.is_protected_database(self.context_menu_dbs[0]):
                self.db_context_menu.add_command(
                    label="✏️ Rename DB", command=self.rename_database
                )
            self.db_context_menu.add_command(
                label="🔍 Query DB", command=self.open_query_interface
            )
            self.db_context_menu.add_separator()

            # Only show delete for non-protected databases
            if not self.is_protected_database(self.context_menu_dbs[0]):
                self.db_context_menu.add_command(
                    label="🗑️ Delete DB", command=self.delete_database_from_context
                )
            else:
                self.db_context_menu.add_command(
                    label="🔒 System DB (Protected)",
                    command=self.show_protection_message,
                )
        else:
            self.db_context_menu.add_command(
                label="🔁 Clone DB", command=self.clone_database
            )
            self.db_context_menu.add_separator()

            # Show delete option only if there are deletable databases
            if deletable_dbs:
                if protected_dbs:
                    # Some protected, some deletable
                    self.db_context_menu.add_command(
                        label=f"🗑️ Delete {len(deletable_dbs)} DBs",
                        command=self.delete_database_from_context,
                    )
                    self.db_context_menu.add_command(
                        label=f"🔒 {len(protected_dbs)} Protected",
                        command=self.show_protection_message,
                    )
                else:
                    # All deletable
                    self.db_context_menu.add_command(
                        label=f"🗑️ Delete {count} DBs",
                        command=self.delete_database_from_context,
                    )
            else:
                # All protected
                self.db_context_menu.add_command(
                    label=f"🔒 All {count} DBs Protected",
                    command=self.show_protection_message,
                )

    def clone_database(self):
        """Open dialog for naming and quantity of cloned DBs."""
        # Only allow cloning one database at a time
        if not self.context_menu_dbs:
            return

        if len(self.context_menu_dbs) > 1:
            messagebox.showwarning(
                "Clone Limitation",
                "Please select only one database to clone.\n"
                f"Currently selected: {len(self.context_menu_dbs)} databases",
            )
            return

        source_db = self.context_menu_dbs[0]

        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        default_name = f"{source_db}_copy_{timestamp}"

        dialog = tk.Toplevel(self)
        dialog.title("🔁 Clone Database")
        dialog.transient(self)
        dialog.grab_set()

        # Apply color schema to dialog
        dialog.configure(bg="#181F67")  # Navy blue background

        # Setup custom styles for this dialog
        style = ttk.Style()

        # Dialog-specific frame style
        style.configure("Dialog.TFrame", background="#181F67", relief="flat")

        # Dialog-specific label style
        style.configure(
            "Dialog.TLabel",
            background="#181F67",
            foreground="white",
            font=("Helvetica", 10),
        )

        # Dialog-specific entry style
        style.configure(
            "Dialog.TEntry",
            font=("Helvetica", 10),
            fieldbackground="white",
            borderwidth=1,
            relief="solid",
        )

        # Dialog-specific spinbox style
        style.configure(
            "Dialog.TSpinbox",
            font=("Helvetica", 10),
            fieldbackground="white",
            borderwidth=1,
            relief="solid",
        )

        # Dialog OK button style (green)
        style.configure(
            "DialogOK.TButton",
            background="#38A169",
            foreground="white",
            font=("Helvetica", 11, "bold"),
            padding=(20, 10),
            borderwidth=0,
            relief="flat",
        )
        style.map("DialogOK.TButton", background=[("active", "#2F855A")])

        # Dialog Cancel button style (gray)
        style.configure(
            "DialogCancel.TButton",
            background="#718096",
            foreground="white",
            font=("Helvetica", 11, "bold"),
            padding=(20, 10),
            borderwidth=0,
            relief="flat",
        )
        style.map("DialogCancel.TButton", background=[("active", "#4A5568")])

        # Progress bar style
        style.configure(
            "Dialog.Horizontal.TProgressbar",
            troughcolor="#E0E0E0",
            background="#7BB837",
            thickness=15,
        )

        # Variables
        name_var = tk.StringVar(value=default_name)
        copies_var = tk.IntVar(value=1)
        self.clone_in_progress = False

        # Main content frame with styled background
        content_frame = ttk.Frame(dialog, style="Dialog.TFrame", padding=35)
        content_frame.pack(fill="both", expand=True)

        # Configure grid weights for proper expansion
        content_frame.columnconfigure(1, weight=1)

        # Layout with styled widgets
        ttk.Label(content_frame, text="New Database Name:", style="Dialog.TLabel").grid(
            row=0, column=0, padx=(0, 15), pady=(15, 8), sticky="w"
        )
        name_entry = ttk.Entry(
            content_frame, textvariable=name_var, width=35, style="Dialog.TEntry"
        )
        name_entry.grid(row=0, column=1, padx=(0, 15), pady=(15, 8), sticky="ew")

        ttk.Label(content_frame, text="Number of Copies:", style="Dialog.TLabel").grid(
            row=1, column=0, padx=(0, 15), pady=(8, 15), sticky="w"
        )
        copies_spin = ttk.Spinbox(
            content_frame,
            from_=1,
            to=100,
            textvariable=copies_var,
            width=5,
            style="Dialog.TSpinbox",
        )
        copies_spin.grid(row=1, column=1, padx=(0, 15), pady=(8, 15), sticky="w")

        # Progress bar (initially hidden)
        progress_bar = ttk.Progressbar(
            content_frame, mode="indeterminate", style="Dialog.Horizontal.TProgressbar"
        )
        progress_bar.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        progress_bar.grid_remove()

        # Status label (initially hidden)
        status_label = ttk.Label(content_frame, text="", style="Dialog.TLabel")
        status_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        status_label.grid_remove()

        # Button handlers
        def update_status(message):
            """Update status label from background thread"""
            dialog.after(0, lambda: status_label.config(text=message))

        def perform_clone():
            """Perform the actual cloning operation"""
            new_name = name_var.get().strip() or default_name
            count = copies_var.get()
            credentials = self.controller.db_credentials

            try:
                for i in range(count):
                    if count == 1:
                        current_name = new_name
                    else:
                        current_name = f"{new_name}_{i+1:02d}"

                    update_status(f"Cloning {source_db} to {current_name}...")
                    copy_database_logic(
                        credentials, source_db, current_name, update_status
                    )

                # Success - update UI
                dialog.after(
                    0, lambda: self.finish_clone_success(dialog, count, new_name)
                )

            except Exception as e:
                # Error - show error message
                dialog.after(0, lambda: self.finish_clone_error(dialog, str(e)))

        def on_ok():
            if self.clone_in_progress:
                return

            new_name = name_var.get().strip() or default_name
            count = copies_var.get()

            if not new_name:
                messagebox.showwarning("Input Error", "Please enter a database name.")
                return

            # Disable buttons and show progress
            self.clone_in_progress = True
            ok_btn.config(state="disabled")
            cancel_btn.config(text="Close", state="disabled")
            name_entry.config(state="disabled")
            copies_spin.config(state="disabled")

            progress_bar.grid()
            progress_bar.start(10)
            status_label.grid()
            status_label.config(text="Starting clone operation...")

            # Start cloning in background thread
            clone_thread = threading.Thread(target=perform_clone, daemon=True)
            clone_thread.start()

        def on_cancel():
            if not self.clone_in_progress:
                dialog.destroy()

        # Buttons with styled frame
        btn_frame = ttk.Frame(content_frame, style="Dialog.TFrame")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(30, 15))

        ok_btn = ttk.Button(
            btn_frame, text="Clone", command=on_ok, style="DialogOK.TButton"
        )
        ok_btn.pack(side="left", padx=15)

        cancel_btn = ttk.Button(
            btn_frame, text="Cancel", command=on_cancel, style="DialogCancel.TButton"
        )
        cancel_btn.pack(side="right", padx=15)

        # Set size and center the dialog with smooth animation
        dialog.withdraw()  # Hide dialog initially
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (480 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (300 // 2)
        dialog.geometry(f"480x300+{x}+{y}")
        dialog.deiconify()  # Show dialog smoothly

        # Focus and wait
        name_entry.focus()
        dialog.wait_window()

    def rename_database(self):
        """Open dialog for renaming a database."""
        # Only allow renaming one database at a time
        if not self.context_menu_dbs:
            return

        if len(self.context_menu_dbs) > 1:
            messagebox.showwarning(
                "Rename Limitation",
                "Please select only one database to rename.\n"
                f"Currently selected: {len(self.context_menu_dbs)} databases",
            )
            return

        source_db = self.context_menu_dbs[0]

        # Check if database is protected
        if self.is_protected_database(source_db):
            messagebox.showwarning(
                "Protected Database",
                f"Cannot rename '{source_db}' because it is a protected system database.\n\n"
                "System databases (postgres, template0, template1) are critical for "
                "PostgreSQL operation and cannot be renamed.",
            )
            return

        dialog = tk.Toplevel(self)
        dialog.title("✏️ Rename Database")
        dialog.transient(self)
        dialog.grab_set()

        # Apply color schema to dialog
        dialog.configure(bg="#181F67")  # Navy blue background

        # Setup custom styles for this dialog
        style = ttk.Style()

        # Dialog-specific frame style
        style.configure("Rename.TFrame", background="#181F67", relief="flat")

        # Dialog-specific label style
        style.configure(
            "Rename.TLabel",
            background="#181F67",
            foreground="white",
            font=("Helvetica", 10),
        )

        # Dialog-specific entry style
        style.configure(
            "Rename.TEntry",
            font=("Helvetica", 10),
            fieldbackground="white",
            foreground="black",
            insertcolor="black",  # This makes the cursor visible
            selectbackground="#7BB837",
            selectforeground="white",
            borderwidth=1,
            relief="solid",
        )

        # Dialog OK button style (green)
        style.configure(
            "RenameOK.TButton",
            background="#38A169",
            foreground="white",
            font=("Helvetica", 11, "bold"),
            padding=(20, 10),
            borderwidth=0,
            relief="flat",
        )
        style.map("RenameOK.TButton", background=[("active", "#2F855A")])

        # Dialog Cancel button style (gray)
        style.configure(
            "RenameCancel.TButton",
            background="#718096",
            foreground="white",
            font=("Helvetica", 11, "bold"),
            padding=(20, 10),
            borderwidth=0,
            relief="flat",
        )
        style.map("RenameCancel.TButton", background=[("active", "#4A5568")])

        # Progress bar style
        style.configure(
            "Rename.Horizontal.TProgressbar",
            troughcolor="#E0E0E0",
            background="#7BB837",
            thickness=15,
        )

        # Variables
        new_name_var = tk.StringVar(value=source_db)
        self.rename_in_progress = False

        # Main content frame with styled background
        content_frame = ttk.Frame(dialog, style="Rename.TFrame", padding=35)
        content_frame.pack(fill="both", expand=True)

        # Configure grid weights for proper expansion
        content_frame.columnconfigure(1, weight=1)

        # Current database name (read-only)
        ttk.Label(content_frame, text="Current Name:", style="Rename.TLabel").grid(
            row=0, column=0, padx=(0, 15), pady=(15, 8), sticky="w"
        )
        current_name_entry = ttk.Entry(content_frame, width=35, style="Rename.TEntry")
        current_name_entry.insert(0, source_db)
        current_name_entry.config(state="readonly")
        current_name_entry.grid(
            row=0, column=1, padx=(0, 15), pady=(15, 8), sticky="ew"
        )

        # New database name entry
        ttk.Label(content_frame, text="New Name:", style="Rename.TLabel").grid(
            row=1, column=0, padx=(0, 15), pady=(8, 15), sticky="w"
        )
        new_name_entry = ttk.Entry(
            content_frame, textvariable=new_name_var, width=35, style="Rename.TEntry"
        )
        new_name_entry.grid(row=1, column=1, padx=(0, 15), pady=(8, 15), sticky="ew")

        # Progress bar (initially hidden)
        progress_bar = ttk.Progressbar(
            content_frame, mode="indeterminate", style="Rename.Horizontal.TProgressbar"
        )
        progress_bar.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        progress_bar.grid_remove()

        # Status label (initially hidden)
        status_label = ttk.Label(content_frame, text="", style="Rename.TLabel")
        status_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        status_label.grid_remove()

        # Button handlers
        def update_status(message):
            """Update status label from background thread"""
            dialog.after(0, lambda: status_label.config(text=message))

        def perform_rename():
            """Perform the actual rename operation"""
            new_name = new_name_var.get().strip()
            credentials = self.controller.db_credentials

            try:
                rename_database(credentials, source_db, new_name, update_status)

                # Success - update UI
                dialog.after(
                    0, lambda: self.finish_rename_success(dialog, source_db, new_name)
                )

            except Exception as e:
                # Error - show error message
                dialog.after(0, lambda: self.finish_rename_error(dialog, str(e)))

        def on_rename():
            if self.rename_in_progress:
                return

            new_name = new_name_var.get().strip()

            if not new_name:
                messagebox.showwarning(
                    "Input Error", "Please enter a new database name."
                )
                return

            if new_name == source_db:
                messagebox.showwarning(
                    "Input Error", "New name must be different from current name."
                )
                return

            # Disable buttons and show progress
            self.rename_in_progress = True
            rename_btn.config(state="disabled")
            cancel_btn.config(text="Close", state="disabled")
            current_name_entry.config(state="disabled")
            new_name_entry.config(state="disabled")

            progress_bar.grid()
            progress_bar.start(10)
            status_label.grid()
            status_label.config(text="Starting rename operation...")

            # Start renaming in background thread
            rename_thread = threading.Thread(target=perform_rename, daemon=True)
            rename_thread.start()

        def on_cancel():
            if not self.rename_in_progress:
                dialog.destroy()

        # Buttons with styled frame
        btn_frame = ttk.Frame(content_frame, style="Rename.TFrame")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(30, 15))

        rename_btn = ttk.Button(
            btn_frame, text="Rename", command=on_rename, style="RenameOK.TButton"
        )
        rename_btn.pack(side="left", padx=15)

        cancel_btn = ttk.Button(
            btn_frame, text="Cancel", command=on_cancel, style="RenameCancel.TButton"
        )
        cancel_btn.pack(side="right", padx=15)

        # Set size and center the dialog with smooth animation
        dialog.withdraw()  # Hide dialog initially
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (480 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (320 // 2)
        dialog.geometry(f"480x320+{x}+{y}")
        dialog.deiconify()  # Show dialog smoothly

        # Focus on new name entry and select all text for easy editing
        new_name_entry.focus()
        new_name_entry.select_range(0, tk.END)
        dialog.wait_window()

    def open_query_interface(self):
        """Open SQL query interface for the selected database."""
        if not self.context_menu_dbs:
            return

        if len(self.context_menu_dbs) > 1:
            messagebox.showwarning(
                "Query Limitation",
                "Please select only one database to query.\n"
                f"Currently selected: {len(self.context_menu_dbs)} databases",
            )
            return

        db_name = self.context_menu_dbs[0]

        # Create query interface window
        query_window = tk.Toplevel(self)
        query_window.title(f"🔍 SQL Query - {db_name}")
        query_window.transient(self)

        # Apply color schema
        query_window.configure(bg="#181F67")

        # Setup custom styles for query interface
        style = ttk.Style()

        # Query window specific styles
        style.configure("Query.TFrame", background="#181F67", relief="flat")

        style.configure(
            "Query.TLabel",
            background="#181F67",
            foreground="white",
            font=("Helvetica", 10),
        )

        style.configure(
            "QueryHeader.TLabel",
            background="#181F67",
            foreground="white",
            font=("Helvetica", 12, "bold"),
        )

        style.configure(
            "QueryExecute.TButton",
            background="#38A169",
            foreground="white",
            font=("Helvetica", 10, "bold"),
            padding=(15, 8),
            borderwidth=0,
            relief="flat",
        )
        style.map("QueryExecute.TButton", background=[("active", "#2F855A")])

        style.configure(
            "QueryClear.TButton",
            background="#718096",
            foreground="white",
            font=("Helvetica", 10, "bold"),
            padding=(15, 8),
            borderwidth=0,
            relief="flat",
        )
        style.map("QueryClear.TButton", background=[("active", "#4A5568")])

        style.configure(
            "QueryFormat.TButton",
            background="#805AD5",
            foreground="white",
            font=("Helvetica", 10, "bold"),
            padding=(15, 8),
            borderwidth=0,
            relief="flat",
        )
        style.map("QueryFormat.TButton", background=[("active", "#6B46C1")])

        style.configure(
            "Query.Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",
            font=("Helvetica", 9),
        )
        style.configure(
            "Query.Treeview.Heading",
            background="#181F67",
            foreground="white",
            font=("Helvetica", 10, "bold"),
        )
        style.map("Query.Treeview.Heading", background=[("active", "#7BB837")])

        # Main content frame
        main_frame = ttk.Frame(query_window, style="Query.TFrame")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Header with database name
        header_frame = ttk.Frame(main_frame, style="Query.TFrame")
        header_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            header_frame,
            text=f"SQL Query Interface - Database: {db_name}",
            style="QueryHeader.TLabel",
        ).pack(side="left")

        # SQL Editor Section
        editor_frame = ttk.Frame(main_frame, style="Query.TFrame")
        editor_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(editor_frame, text="SQL Query:", style="Query.TLabel").pack(
            anchor="w", pady=(0, 5)
        )

        # SQL text editor with scrollbar
        editor_container = ttk.Frame(editor_frame, style="Query.TFrame")
        editor_container.pack(fill="x")

        self.sql_text = tk.Text(
            editor_container,
            height=8,
            font=("Consolas", 11),
            bg="white",
            fg="black",
            insertbackground="black",
            selectbackground="#7BB837",
            selectforeground="white",
            wrap="none",
        )

        # Add scrollbars for SQL editor
        sql_scrollbar_v = ttk.Scrollbar(
            editor_container, orient="vertical", command=self.sql_text.yview
        )
        sql_scrollbar_h = ttk.Scrollbar(
            editor_container, orient="horizontal", command=self.sql_text.xview
        )
        self.sql_text.configure(
            yscrollcommand=sql_scrollbar_v.set, xscrollcommand=sql_scrollbar_h.set
        )

        self.sql_text.grid(row=0, column=0, sticky="nsew")
        sql_scrollbar_v.grid(row=0, column=1, sticky="ns")
        sql_scrollbar_h.grid(row=1, column=0, sticky="ew")

        editor_container.grid_rowconfigure(0, weight=1)
        editor_container.grid_columnconfigure(0, weight=1)

        # Button frame
        button_frame = ttk.Frame(main_frame, style="Query.TFrame")
        button_frame.pack(fill="x", pady=(10, 15))

        execute_btn = ttk.Button(
            button_frame,
            text="▶ Execute Query",
            command=lambda: self.execute_query(db_name, query_window),
            style="QueryExecute.TButton",
        )
        execute_btn.pack(side="left", padx=(0, 10))

        format_btn = ttk.Button(
            button_frame,
            text="✨ Format SQL",
            command=self.format_sql,
            style="QueryFormat.TButton",
        )
        format_btn.pack(side="left", padx=(0, 10))

        clear_btn = ttk.Button(
            button_frame,
            text="🗑 Clear",
            command=self.clear_query,
            style="QueryClear.TButton",
        )
        clear_btn.pack(side="left")

        # Results section
        results_frame = ttk.Frame(main_frame, style="Query.TFrame")
        results_frame.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Label(results_frame, text="Query Results:", style="Query.TLabel").pack(
            anchor="w", pady=(0, 5)
        )

        # Results treeview with scrollbars
        results_container = ttk.Frame(results_frame, style="Query.TFrame")
        results_container.pack(fill="both", expand=True)

        self.results_tree = ttk.Treeview(results_container, style="Query.Treeview")

        # Add scrollbars for results
        results_scrollbar_v = ttk.Scrollbar(
            results_container, orient="vertical", command=self.results_tree.yview
        )
        results_scrollbar_h = ttk.Scrollbar(
            results_container, orient="horizontal", command=self.results_tree.xview
        )
        self.results_tree.configure(
            yscrollcommand=results_scrollbar_v.set,
            xscrollcommand=results_scrollbar_h.set,
        )

        self.results_tree.grid(row=0, column=0, sticky="nsew")
        results_scrollbar_v.grid(row=0, column=1, sticky="ns")
        results_scrollbar_h.grid(row=1, column=0, sticky="ew")

        results_container.grid_rowconfigure(0, weight=1)
        results_container.grid_columnconfigure(0, weight=1)

        # Status bar
        status_frame = ttk.Frame(main_frame, style="Query.TFrame")
        status_frame.pack(fill="x")

        self.status_label = ttk.Label(
            status_frame, text="Ready to execute queries...", style="Query.TLabel"
        )
        self.status_label.pack(side="left")

        # Set window size and center it with smooth animation
        query_window.withdraw()  # Hide initially
        query_window.update_idletasks()

        # Large size for good data viewing
        window_width = 1100
        window_height = 750

        x = self.winfo_rootx() + (self.winfo_width() // 2) - (window_width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (window_height // 2)

        query_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        query_window.minsize(800, 600)  # Minimum size for usability
        query_window.deiconify()  # Show smoothly

        # Focus on SQL editor
        self.sql_text.focus()

    def execute_query(self, db_name, query_window):
        """Execute the SQL query in background thread."""
        sql_query = self.sql_text.get("1.0", tk.END).strip()

        if not sql_query:
            messagebox.showwarning(
                "Empty Query", "Please enter a SQL query to execute."
            )
            return

        # Disable execute button during execution
        for widget in query_window.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button) and "Execute" in child.cget(
                        "text"
                    ):
                        child.config(state="disabled")
                        break

        self.status_label.config(text="Executing query...")

        def query_worker():
            credentials = self.controller.db_credentials
            try:
                result = execute_sql_query(credentials, db_name, sql_query)
                query_window.after(
                    0, lambda: self.display_query_results(result, query_window)
                )
            except Exception as e:
                error_result = {
                    "success": False,
                    "message": f"Execution error: {str(e)}",
                    "execution_time_ms": 0,
                }
                query_window.after(
                    0, lambda: self.display_query_results(error_result, query_window)
                )

        threading.Thread(target=query_worker, daemon=True).start()

    def display_query_results(self, result, query_window):
        """Display query results in the treeview."""
        # Re-enable execute button
        for widget in query_window.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button) and "Execute" in child.cget(
                        "text"
                    ):
                        child.config(state="normal")
                        break

        # Clear previous results
        self.results_tree.delete(*self.results_tree.get_children())

        # Update status
        if result["success"]:
            status_text = (
                f"{result['message']} (Execution time: {result['execution_time_ms']}ms)"
            )
        else:
            status_text = result["message"]

        self.status_label.config(text=status_text)

        if not result["success"]:
            # Show error in results area
            self.results_tree["columns"] = ("Error",)
            self.results_tree["show"] = "headings"
            self.results_tree.heading("Error", text="Error Message")
            self.results_tree.column("Error", width=800)
            self.results_tree.insert("", tk.END, values=(result["message"],))
            return

        # Display results for successful queries
        if result["query_type"] == "SELECT" and result["columns"]:
            # Configure columns
            self.results_tree["columns"] = result["columns"]
            self.results_tree["show"] = "headings"

            # Set up column headers and widths
            for col in result["columns"]:
                self.results_tree.heading(col, text=col)
                self.results_tree.column(col, width=150, minwidth=100)

            # Insert data rows
            for row in result["rows"]:
                # Convert any None values to empty strings for display
                display_row = [str(val) if val is not None else "" for val in row]
                self.results_tree.insert("", tk.END, values=display_row)

        elif result["query_type"] == "MODIFICATION":
            # Show modification results
            self.results_tree["columns"] = ("Result",)
            self.results_tree["show"] = "headings"
            self.results_tree.heading("Result", text="Query Result")
            self.results_tree.column("Result", width=800)
            self.results_tree.insert("", tk.END, values=(result["message"],))

    def clear_query(self):
        """Clear the SQL editor."""
        self.sql_text.delete("1.0", tk.END)

    def format_sql(self):
        """Format and beautify the SQL in the editor."""
        try:
            # Get current SQL content
            current_sql = self.sql_text.get("1.0", tk.END).strip()

            if not current_sql:
                messagebox.showinfo(
                    "No SQL to Format", "Please enter some SQL code to format."
                )
                return

            # Format the SQL using sqlparse with enhanced formatting
            formatted_sql = sqlparse.format(
                current_sql,
                reindent=True,  # Proper indentation
                keyword_case="upper",  # SELECT, FROM, WHERE in uppercase
                identifier_case="lower",  # table_names, column_names in lowercase
                strip_comments=False,  # Keep -- comments
                indent_width=4,  # 4-space indentation for better readability
                wrap_after=60,  # Wrap lines after 60 characters
                comma_first=False,  # Comma at end of line, not beginning
                use_space_around_operators=True,  # Spaces around = < > operators
            )

            # Additional custom formatting for SELECT lists
            lines = formatted_sql.split("\n")
            formatted_lines = []
            in_select = False
            select_items = []

            for line in lines:
                stripped = line.strip()

                # Detect start of SELECT statement
                if stripped.upper().startswith("SELECT"):
                    in_select = True
                    # Check if SELECT is on same line as columns
                    if len(stripped) > 6:  # More than just "SELECT"
                        # Extract the part after SELECT
                        select_part = stripped[6:].strip()
                        formatted_lines.append("SELECT")
                        if select_part:
                            select_items.append(select_part)
                    else:
                        formatted_lines.append("SELECT")
                    continue

                # Detect end of SELECT clause
                elif in_select and any(
                    stripped.upper().startswith(keyword)
                    for keyword in [
                        "FROM",
                        "WHERE",
                        "GROUP BY",
                        "HAVING",
                        "ORDER BY",
                        "LIMIT",
                        "UNION",
                        "JOIN",
                        "INNER JOIN",
                        "LEFT JOIN",
                        "RIGHT JOIN",
                    ]
                ):
                    # Process accumulated SELECT items BEFORE adding the current line
                    if select_items:
                        formatted_lines.extend(self._format_select_items(select_items))
                        select_items = []
                    in_select = False
                    formatted_lines.append(line)  # Add the FROM/WHERE/etc line
                    continue

                # Accumulate SELECT items
                elif in_select:
                    if stripped:
                        select_items.append(stripped)
                    continue

                else:
                    formatted_lines.append(line)

            # Handle case where SELECT is at end of query
            if select_items:
                formatted_lines.extend(self._format_select_items(select_items))

            # Join back together
            final_formatted = "\n".join(formatted_lines)

            # Replace content with formatted version
            self.sql_text.delete("1.0", tk.END)
            self.sql_text.insert("1.0", final_formatted)

            # Update status
            if hasattr(self, "status_label"):
                self.status_label.config(text="SQL formatted successfully!")

        except Exception as e:
            messagebox.showerror("Format Error", f"Failed to format SQL:\n{str(e)}")

    def _format_select_items(self, items):
        """Helper method to format SELECT items with proper indentation."""
        formatted_items = []

        # Join all items and split by comma to handle multi-line cases
        all_items = " ".join(items)
        columns = [col.strip() for col in all_items.split(",") if col.strip()]

        for i, column in enumerate(columns):
            # Clean up the column (remove extra spaces, etc.)
            column = " ".join(column.split())

            # Add proper indentation and comma
            if i == len(columns) - 1:  # Last item, no comma
                formatted_items.append(f"    {column}")
            else:  # Add comma
                formatted_items.append(f"    {column},")

        return formatted_items

    def show_protection_message(self):
        """Show information about protected databases"""
        protected_list = ", ".join(self.get_protected_databases(self.context_menu_dbs))
        messagebox.showinfo(
            "Protected System Databases",
            f"The following databases are protected from modification:\n\n{protected_list}\n\n"
            "These are critical system databases required for PostgreSQL to function properly. "
            "They cannot be deleted, renamed, or modified to ensure system stability.",
        )

    def finish_clone_success(self, dialog, count, base_name):
        """Handle successful clone completion"""
        self.clone_in_progress = False
        if count == 1:
            message = f"Database '{base_name}' cloned successfully!"
        else:
            message = f"{count} database copies created successfully with base name '{base_name}'!"

        messagebox.showinfo("Clone Complete", message)
        dialog.destroy()

        # Refresh the database list to show the new databases
        self.load_databases()

    def finish_clone_error(self, dialog, error_message):
        """Handle clone operation error"""
        self.clone_in_progress = False
        messagebox.showerror(
            "Clone Error", f"Failed to clone database:\n{error_message}"
        )
        dialog.destroy()

    def finish_rename_success(self, dialog, old_name, new_name):
        """Handle successful rename completion"""
        self.rename_in_progress = False
        messagebox.showinfo(
            "Rename Complete",
            f"Database '{old_name}' has been successfully renamed to '{new_name}'!",
        )
        dialog.destroy()

        # Refresh the database list to show the renamed database
        self.load_databases()

    def finish_rename_error(self, dialog, error_message):
        """Handle rename operation error"""
        self.rename_in_progress = False
        messagebox.showerror(
            "Rename Error", f"Failed to rename database:\n{error_message}"
        )
        dialog.destroy()

    def delete_database_from_context(self):
        """Delete selected databases from context menu with styled confirmation dialog"""
        all_selected_dbs = self.context_menu_dbs
        if not all_selected_dbs:
            return

        # Filter out protected databases
        deletable_dbs = self.get_deletable_databases(all_selected_dbs)
        protected_dbs = self.get_protected_databases(all_selected_dbs)

        # If no databases can be deleted, show protection message
        if not deletable_dbs:
            self.show_protection_message()
            return

        # If some databases are protected, show warning about what will be deleted
        if protected_dbs:
            protected_list = ", ".join(protected_dbs)
            warning_result = messagebox.showwarning(
                "Protected Databases Detected",
                f"The following protected databases will be skipped:\n{protected_list}\n\n"
                f"Only {len(deletable_dbs)} database(s) will be deleted:\n{', '.join(deletable_dbs)}\n\n"
                "Do you want to continue with deleting the non-protected databases?",
                type=messagebox.OKCANCEL,
            )
            if warning_result != "ok":
                return

        # Use only deletable databases for the deletion dialog
        db_names = deletable_dbs

        # Create custom confirmation dialog
        dialog = tk.Toplevel(self)
        dialog.title("⚠️ Delete Database(s)")
        dialog.transient(self)
        dialog.grab_set()

        # Apply color schema to dialog
        dialog.configure(bg="#181F67")  # Navy blue background

        # Setup custom styles for this dialog
        style = ttk.Style()

        # Dialog-specific frame style
        style.configure("Warning.TFrame", background="#181F67", relief="flat")

        # Dialog-specific label style
        style.configure(
            "Warning.TLabel",
            background="#181F67",
            foreground="white",
            font=("Helvetica", 11),
        )

        # Warning header label style
        style.configure(
            "WarningHeader.TLabel",
            background="#181F67",
            foreground="#FFD700",  # Gold color for warning
            font=("Helvetica", 14, "bold"),
        )

        # Database name label style
        style.configure(
            "DatabaseName.TLabel",
            background="#181F67",
            foreground="#FF6B6B",  # Light red for emphasis
            font=("Helvetica", 11, "bold"),
        )

        # Dialog Delete button style (red)
        style.configure(
            "DialogDelete.TButton",
            background="#E53E3E",
            foreground="white",
            font=("Helvetica", 11, "bold"),
            padding=(20, 10),
            borderwidth=0,
            relief="flat",
        )
        style.map("DialogDelete.TButton", background=[("active", "#C53030")])

        # Dialog Cancel button style (gray)
        style.configure(
            "DialogCancelWarning.TButton",
            background="#718096",
            foreground="white",
            font=("Helvetica", 11, "bold"),
            padding=(20, 10),
            borderwidth=0,
            relief="flat",
        )
        style.map("DialogCancelWarning.TButton", background=[("active", "#4A5568")])

        # Main content frame with styled background
        content_frame = ttk.Frame(dialog, style="Warning.TFrame", padding=35)
        content_frame.pack(fill="both", expand=True)

        # Warning icon and header
        if len(db_names) == 1:
            header_text = "⚠️ Delete Database"
            warning_text = (
                "This will permanently delete the database and all its data.\n"
                "This action cannot be undone."
            )
        else:
            header_text = f"⚠️ Delete {len(db_names)} Databases"
            warning_text = (
                f"This will permanently delete {len(db_names)} databases and all their data.\n"
                "This action cannot be undone."
            )

        ttk.Label(content_frame, text=header_text, style="WarningHeader.TLabel").pack(
            pady=(0, 20)
        )

        # Database names highlight
        if len(db_names) == 1:
            ttk.Label(
                content_frame, text=f'"{db_names[0]}"', style="DatabaseName.TLabel"
            ).pack(pady=(0, 15))
        else:
            # Create a frame for multiple database names
            db_frame = ttk.Frame(content_frame, style="Warning.TFrame")
            db_frame.pack(pady=(0, 15))

            # Show database names in a more compact way
            if len(db_names) <= 3:
                for db_name in db_names:
                    ttk.Label(
                        db_frame, text=f'"{db_name}"', style="DatabaseName.TLabel"
                    ).pack()
            else:
                # For many databases, show first 2 and count
                for db_name in db_names[:2]:
                    ttk.Label(
                        db_frame, text=f'"{db_name}"', style="DatabaseName.TLabel"
                    ).pack()
                ttk.Label(
                    db_frame,
                    text=f"+ {len(db_names) - 2} more...",
                    style="DatabaseName.TLabel",
                ).pack()

        # Warning message
        ttk.Label(
            content_frame, text=warning_text, style="Warning.TLabel", justify="center"
        ).pack(pady=(0, 25))

        # Button handlers
        def on_delete():
            dialog.destroy()
            self.perform_multiple_database_deletion(db_names)

        def on_cancel():
            dialog.destroy()

        # Buttons with styled frame
        btn_frame = ttk.Frame(content_frame, style="Warning.TFrame")
        btn_frame.pack(pady=(15, 0))

        if len(db_names) == 1:
            delete_text = "Delete"
        else:
            delete_text = f"Delete All ({len(db_names)})"

        delete_btn = ttk.Button(
            btn_frame, text=delete_text, command=on_delete, style="DialogDelete.TButton"
        )
        delete_btn.pack(side="left", padx=15)

        cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            command=on_cancel,
            style="DialogCancelWarning.TButton",
        )
        cancel_btn.pack(side="right", padx=15)

        # Set minimum size and center the dialog
        min_height = 280 if len(db_names) <= 3 else 320
        dialog.minsize(420, min_height)

        # Center dialog on parent window BEFORE showing content
        dialog.withdraw()  # Hide dialog initially
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (420 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (min_height // 2)
        dialog.geometry(f"420x{min_height}+{x}+{y}")
        dialog.deiconify()  # Show dialog smoothly

        # Focus on cancel button by default (safer)
        cancel_btn.focus()
        dialog.wait_window()

    def perform_multiple_database_deletion(self, db_names):
        """Perform deletion of multiple databases in background thread"""

        def deletion_worker():
            credentials = self.controller.db_credentials
            errors = []
            successful_deletions = []

            for db_name in db_names:
                try:
                    terminate_and_delete_database(credentials, db_name)
                    successful_deletions.append(db_name)
                except Exception as e:
                    errors.append(f"{db_name}: {str(e)}")

            # Update UI on main thread
            self.after(
                0, lambda: self.finish_multiple_deletion(successful_deletions, errors)
            )

        # Start deletion in background thread
        threading.Thread(target=deletion_worker, daemon=True).start()

    def finish_multiple_deletion(self, successful_deletions, errors):
        """Handle completion of multiple database deletions"""
        # Refresh the database list
        self.load_databases()

        if errors and successful_deletions:
            # Partial success
            success_msg = f"Successfully deleted: {', '.join(successful_deletions)}"
            error_msg = f"Failed to delete:\n" + "\n".join(errors)
            messagebox.showwarning("Partial Success", f"{success_msg}\n\n{error_msg}")
        elif errors:
            # All failed
            error_msg = "Failed to delete databases:\n" + "\n".join(errors)
            messagebox.showerror("Deletion Error", error_msg)
        else:
            # All successful
            if len(successful_deletions) == 1:
                messagebox.showinfo(
                    "Deletion Complete",
                    f"Database '{successful_deletions[0]}' has been successfully deleted.",
                )
            else:
                messagebox.showinfo(
                    "Deletion Complete",
                    f"{len(successful_deletions)} databases have been successfully deleted.",
                )
