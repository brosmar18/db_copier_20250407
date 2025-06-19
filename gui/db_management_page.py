import tkinter as tk
from tkinter import ttk, messagebox
import threading
from db import (
    fetch_databases,
    get_database_details,
    get_tables_for_database,
    get_columns_for_table,
    get_table_details,
    terminate_and_delete_database,
    copy_database_logic,
)


class DBManagementPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_db = None
        self.all_databases = []
        self.all_items = []
        self.context_menu_db = None

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
            "Custom.Small.TButton",
            background="#7BB837",
            foreground="white",
            font=("Helvetica", 8, "bold"),
            padding=(2, 2),
        )
        style.map("Custom.Small.TButton", background=[("active", "#6AA62F")])
        style.configure(
            "Delete.TButton",
            background="#D9534F",
            foreground="white",
            font=("Helvetica", 10, "bold"),
            padding=(4, 4),
        )
        style.map("Delete.TButton", background=[("active", "#C9302C")])

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
            style="Custom.Small.TButton",
        ).pack(side="right", padx=2, pady=2)
        ttk.Button(
            left_header,
            text="Delete",
            command=self.delete_selected_database,
            style="Delete.TButton",
        ).pack(side="right", padx=5, pady=2)

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

        # --- CONTEXT MENU: clone and delete options ---
        self.db_context_menu = tk.Menu(
            self,
            tearoff=0,
            font=("Helvetica", 10),
            bg="white",
            fg="black",
            activebackground="#7BB837",
            activeforeground="white",
        )
        self.db_context_menu.add_command(
            label="🔁 Clone DB", command=self.clone_database
        )
        self.db_context_menu.add_separator()
        self.db_context_menu.add_command(
            label="🗑️ Delete DB", command=self.delete_database_from_context
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
            style="Custom.Small.TButton",
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

    def delete_selected_database(self):
        selected = self.db_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "No database selected for deletion.")
            return

        db_names = [self.db_tree.item(i)["values"][0] for i in selected]
        confirm = messagebox.askokcancel(
            "Confirm Deletion",
            f"WARNING: This will permanently delete:\n\n{', '.join(db_names)}\n\nThis action cannot be undone.\nProceed?",
        )
        if not confirm:
            return

        def worker():
            creds = self.controller.db_credentials
            errors = []
            for db in db_names:
                try:
                    terminate_and_delete_database(creds, db)
                except Exception as e:
                    errors.append(f"{db}: {e}")
            self.after(0, self.load_databases)
            if errors:
                self.after(
                    0, lambda: messagebox.showerror("Deletion Error", "\n".join(errors))
                )
            else:
                self.after(
                    0, lambda: messagebox.showinfo("Success", "Deleted successfully.")
                )

        threading.Thread(target=worker, daemon=True).start()

    # --- CONTEXT-MENU HANDLERS ---
    def show_db_context_menu(self, event):
        item = self.db_tree.identify_row(event.y)
        if not item:
            return
        self.db_tree.selection_set(item)
        self.context_menu_db = self.db_tree.item(item)["values"][0]
        try:
            self.db_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.db_context_menu.grab_release()

    def show_db_context_menu_keyboard(self, event):
        selected = self.db_tree.selection()
        if not selected:
            return
        item = selected[0]
        self.context_menu_db = self.db_tree.item(item)["values"][0]
        bbox = self.db_tree.bbox(item)
        if not bbox:
            return
        x = self.db_tree.winfo_rootx() + bbox[0] + bbox[2] // 2
        y = self.db_tree.winfo_rooty() + bbox[1] + bbox[3] // 2
        try:
            self.db_context_menu.tk_popup(x, y)
        finally:
            self.db_context_menu.grab_release()

    def clone_database(self):
        """Open dialog for naming and quantity of cloned DBs."""
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        default_name = f"{self.context_menu_db}_copy_{timestamp}"

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
            background="#7BB837",
            foreground="white",
            font=("Helvetica", 10, "bold"),
            padding=(10, 5),
            borderwidth=0,
            relief="flat",
        )
        style.map("DialogOK.TButton", background=[("active", "#6AA62F")])

        # Dialog Cancel button style (gray)
        style.configure(
            "DialogCancel.TButton",
            background="#939498",
            foreground="white",
            font=("Helvetica", 10, "bold"),
            padding=(10, 5),
            borderwidth=0,
            relief="flat",
        )
        style.map("DialogCancel.TButton", background=[("active", "#7A7A7A")])

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
        content_frame = ttk.Frame(dialog, style="Dialog.TFrame", padding=25)
        content_frame.pack(fill="both", expand=True)

        # Configure grid weights for proper expansion
        content_frame.columnconfigure(1, weight=1)

        # Layout with styled widgets
        ttk.Label(content_frame, text="New Database Name:", style="Dialog.TLabel").grid(
            row=0, column=0, padx=(0, 10), pady=(10, 5), sticky="w"
        )
        name_entry = ttk.Entry(
            content_frame, textvariable=name_var, width=35, style="Dialog.TEntry"
        )
        name_entry.grid(row=0, column=1, padx=(0, 10), pady=(10, 5), sticky="ew")

        ttk.Label(content_frame, text="Number of Copies:", style="Dialog.TLabel").grid(
            row=1, column=0, padx=(0, 10), pady=5, sticky="w"
        )
        copies_spin = ttk.Spinbox(
            content_frame,
            from_=1,
            to=100,
            textvariable=copies_var,
            width=5,
            style="Dialog.TSpinbox",
        )
        copies_spin.grid(row=1, column=1, padx=(0, 10), pady=5, sticky="w")

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

                    update_status(
                        f"Cloning {self.context_menu_db} to {current_name}..."
                    )
                    copy_database_logic(
                        credentials, self.context_menu_db, current_name, update_status
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
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(25, 15))

        ok_btn = ttk.Button(
            btn_frame, text="Clone Database", command=on_ok, style="DialogOK.TButton"
        )
        ok_btn.pack(side="left", padx=15)

        cancel_btn = ttk.Button(
            btn_frame, text="Cancel", command=on_cancel, style="DialogCancel.TButton"
        )
        cancel_btn.pack(side="right", padx=15)

        # Set minimum size and center the dialog
        dialog.minsize(500, 280)
        dialog.geometry("500x280")

        # Center dialog on parent window
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = (
            self.winfo_rooty()
            + (self.winfo_height() // 2)
            - (dialog.winfo_height() // 2)
        )
        dialog.geometry(f"+{x}+{y}")

        # Focus and wait
        name_entry.focus()
        dialog.wait_window()

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

    def delete_database_from_context(self):
        """Delete a single database from context menu with styled confirmation dialog"""
        db_name = self.context_menu_db
        if not db_name:
            return

        # Create custom confirmation dialog
        dialog = tk.Toplevel(self)
        dialog.title("⚠️ Delete Database")
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
            font=("Helvetica", 12, "bold"),
        )

        # Dialog Delete button style (red)
        style.configure(
            "DialogDelete.TButton",
            background="#D9534F",
            foreground="white",
            font=("Helvetica", 10, "bold"),
            padding=(15, 8),
            borderwidth=0,
            relief="flat",
        )
        style.map("DialogDelete.TButton", background=[("active", "#C9302C")])

        # Dialog Cancel button style (gray)
        style.configure(
            "DialogCancelWarning.TButton",
            background="#939498",
            foreground="white",
            font=("Helvetica", 10, "bold"),
            padding=(15, 8),
            borderwidth=0,
            relief="flat",
        )
        style.map("DialogCancelWarning.TButton", background=[("active", "#7A7A7A")])

        # Main content frame with styled background
        content_frame = ttk.Frame(dialog, style="Warning.TFrame", padding=30)
        content_frame.pack(fill="both", expand=True)

        # Warning icon and header
        ttk.Label(
            content_frame, text="⚠️ CRITICAL WARNING", style="WarningHeader.TLabel"
        ).pack(pady=(0, 15))

        # Warning message
        warning_text = (
            "You are about to permanently delete the following database:\n\n"
            "This action will:\n"
            "• Terminate all active connections\n"
            "• Permanently delete all data\n"
            "• Cannot be undone\n\n"
            "Are you absolutely sure you want to proceed?"
        )
        ttk.Label(
            content_frame, text=warning_text, style="Warning.TLabel", justify="center"
        ).pack(pady=(0, 10))

        # Database name highlight
        ttk.Label(content_frame, text=f'"{db_name}"', style="DatabaseName.TLabel").pack(
            pady=(0, 20)
        )

        # Button handlers
        def on_delete():
            dialog.destroy()
            self.perform_database_deletion(db_name)

        def on_cancel():
            dialog.destroy()

        # Buttons with styled frame
        btn_frame = ttk.Frame(content_frame, style="Warning.TFrame")
        btn_frame.pack(pady=(20, 0))

        delete_btn = ttk.Button(
            btn_frame,
            text="DELETE DATABASE",
            command=on_delete,
            style="DialogDelete.TButton",
        )
        delete_btn.pack(side="left", padx=20)

        cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            command=on_cancel,
            style="DialogCancelWarning.TButton",
        )
        cancel_btn.pack(side="right", padx=20)

        # Set minimum size and center the dialog
        dialog.minsize(450, 350)
        dialog.geometry("450x350")

        # Center dialog on parent window
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = (
            self.winfo_rooty()
            + (self.winfo_height() // 2)
            - (dialog.winfo_height() // 2)
        )
        dialog.geometry(f"+{x}+{y}")

        # Focus on cancel button by default (safer)
        cancel_btn.focus()
        dialog.wait_window()

    def perform_database_deletion(self, db_name):
        """Perform the actual database deletion in background thread"""

        def deletion_worker():
            credentials = self.controller.db_credentials
            try:
                terminate_and_delete_database(credentials, db_name)
                # Success - update UI on main thread
                self.after(0, lambda: self.finish_deletion_success(db_name))
            except Exception as e:
                # Error - show error message on main thread
                self.after(0, lambda: self.finish_deletion_error(db_name, str(e)))

        # Start deletion in background thread
        threading.Thread(target=deletion_worker, daemon=True).start()

    def finish_deletion_success(self, db_name):
        """Handle successful deletion completion"""
        messagebox.showinfo(
            "Deletion Complete", f"Database '{db_name}' has been successfully deleted."
        )
        # Refresh the database list to remove the deleted database
        self.load_databases()

    def finish_deletion_error(self, db_name, error_message):
        """Handle deletion error"""
        messagebox.showerror(
            "Deletion Error", f"Failed to delete database '{db_name}':\n{error_message}"
        )
