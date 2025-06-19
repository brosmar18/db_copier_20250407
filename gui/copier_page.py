import tkinter as tk
from tkinter import ttk, messagebox
import threading
from db import fetch_databases, copy_database_logic


class CopierPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.copy_thread = None
        self._widgets_created = False

        # Bind to show frame event for lazy loading
        self.bind("<<ShowFrame>>", self.on_show_frame)

    def create_widgets(self):
        """Create widgets lazily for better startup performance"""
        if self._widgets_created:
            return

        # Simple progress bar style
        style = ttk.Style(self)
        style.configure(
            "Copy.Horizontal.TProgressbar", troughcolor="#E8E8E8", background="#27AE60"
        )

        # Main container
        main_frame = ttk.Frame(self, padding=40)
        main_frame.pack(expand=True, fill="both")

        # Center content frame
        content_frame = ttk.Frame(main_frame)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title = ttk.Label(
            content_frame, text="Database Copier", font=("Segoe UI", 18, "bold")
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 30))

        # Source database selection
        ttk.Label(
            content_frame, text="Source Database:", font=("Segoe UI", 11, "bold")
        ).grid(row=1, column=0, padx=(0, 15), pady=10, sticky="w")

        self.db_combo = ttk.Combobox(
            content_frame, state="readonly", font=("Segoe UI", 11), width=35
        )
        self.db_combo.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

        # Refresh button
        self.refresh_btn = ttk.Button(
            content_frame, text="Refresh", command=self.refresh_databases
        )
        self.refresh_btn.grid(row=1, column=2, padx=(15, 0), pady=10)

        # New database name
        ttk.Label(
            content_frame, text="New Database Name:", font=("Segoe UI", 11, "bold")
        ).grid(row=2, column=0, padx=(0, 15), pady=10, sticky="w")

        self.new_db_entry = ttk.Entry(content_frame, font=("Segoe UI", 11), width=35)
        self.new_db_entry.grid(row=2, column=1, padx=5, pady=10, sticky="ew")

        # Copy button
        self.copy_btn = ttk.Button(
            content_frame,
            text="Copy Database",
            command=self.start_copy,
            style="Accent.TButton",
        )
        self.copy_btn.grid(row=3, column=0, columnspan=3, pady=20)

        # Progress section (initially hidden)
        self.progress_frame = ttk.Frame(content_frame)
        self.progress_frame.grid(
            row=4, column=0, columnspan=3, pady=(20, 0), sticky="ew"
        )

        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode="indeterminate",
            style="Copy.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(fill="x", pady=(0, 10))

        self.status_label = ttk.Label(
            self.progress_frame, text="", font=("Segoe UI", 10), foreground="#2C3E50"
        )
        self.status_label.pack()

        # Hide progress initially
        self.progress_frame.grid_remove()

        # Configure button style
        style.configure(
            "Accent.TButton",
            background="#3498DB",
            foreground="white",
            font=("Segoe UI", 11, "bold"),
            padding=(25, 10),
        )
        style.map("Accent.TButton", background=[("active", "#2980B9")])

        self._widgets_created = True

    def on_show_frame(self, event):
        """Handle frame show event"""
        if not self._widgets_created:
            self.create_widgets()
        self.load_databases_async()

    def load_databases_async(self):
        """Load databases asynchronously"""
        credentials = self.controller.db_credentials
        if not credentials:
            return

        def load_worker():
            try:
                db_list = sorted(fetch_databases(credentials))
                self.after(0, lambda: self.update_database_list(db_list))
            except Exception as e:
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "Error", f"Failed to load databases: {e}"
                    ),
                )

        threading.Thread(target=load_worker, daemon=True).start()

    def update_database_list(self, db_list):
        """Update database list on main thread"""
        self.db_combo["values"] = db_list
        if db_list:
            self.db_combo.current(0)

    def refresh_databases(self):
        """Refresh database list and reset form"""
        self.new_db_entry.delete(0, tk.END)
        self.hide_progress()
        self.load_databases_async()

    def start_copy(self):
        """Start database copy operation"""
        src_db = self.db_combo.get()
        new_db = self.new_db_entry.get().strip()

        # Validation
        if not src_db:
            messagebox.showwarning("Input Error", "Please select a source database.")
            return
        if not new_db:
            messagebox.showwarning(
                "Input Error", "Please enter a name for the new database."
            )
            return
        if src_db.lower() == new_db.lower():
            messagebox.showwarning(
                "Input Error", "New database name must be different from source."
            )
            return

        # Show progress and disable UI
        self.show_progress("Initializing database copy...")
        self.disable_ui()

        # Start copy operation
        self.copy_thread = threading.Thread(
            target=self.perform_copy, args=(src_db, new_db), daemon=True
        )
        self.copy_thread.start()

    def perform_copy(self, src_db, new_db):
        """Perform the copy operation in background"""
        credentials = self.controller.db_credentials

        try:
            copy_database_logic(credentials, src_db, new_db, self.update_status)
            self.after(0, lambda: self.copy_success(src_db, new_db))
        except Exception as e:
            self.after(0, lambda: self.copy_error(str(e)))

    def copy_success(self, src_db, new_db):
        """Handle successful copy"""
        self.hide_progress()
        self.enable_ui()
        messagebox.showinfo(
            "Success",
            f"Database '{new_db}' created successfully as a copy of '{src_db}'!",
        )

        # Refresh database list
        self.load_databases_async()

        # Clear new database name
        self.new_db_entry.delete(0, tk.END)

    def copy_error(self, error_message):
        """Handle copy error"""
        self.hide_progress()
        self.enable_ui()
        messagebox.showerror("Copy Error", f"Failed to copy database:\n{error_message}")

    def update_status(self, message):
        """Update status message from background thread"""
        self.after(0, lambda: self.status_label.config(text=message))

    def show_progress(self, message):
        """Show progress bar and status"""
        self.progress_frame.grid()
        self.progress_bar.start(8)  # Slower animation for better performance
        self.status_label.config(text=message)

    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.stop()
        self.progress_frame.grid_remove()

    def disable_ui(self):
        """Disable UI elements during operation"""
        self.copy_btn.config(state="disabled")
        self.db_combo.config(state="disabled")
        self.new_db_entry.config(state="disabled")
        self.refresh_btn.config(state="disabled")

    def enable_ui(self):
        """Re-enable UI elements after operation"""
        self.copy_btn.config(state="normal")
        self.db_combo.config(state="readonly")
        self.new_db_entry.config(state="normal")
        self.refresh_btn.config(state="normal")
