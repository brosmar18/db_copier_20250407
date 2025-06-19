import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from db import create_database, restore_database, terminate_and_delete_database
from gui.snake_game import SnakeGame


class RestorePage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.restore_thread = None
        self._widgets_created = False

        # Bind to show frame event for lazy loading
        self.bind("<<ShowFrame>>", self.on_show_frame)

    def create_widgets(self):
        """Create widgets lazily for better startup performance"""
        if self._widgets_created:
            return

        # Setup styles
        style = ttk.Style(self)
        style.configure(
            "Restore.Horizontal.TProgressbar",
            troughcolor="#E8E8E8",
            background="#3498DB",
        )

        # Main container
        main_frame = ttk.Frame(self, padding=30)
        main_frame.pack(expand=True, fill="both")

        # Content frame (centered)
        content_frame = ttk.Frame(main_frame)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title = ttk.Label(
            content_frame, text="Database Restore", font=("Segoe UI", 18, "bold")
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 30))

        # Form fields
        self.create_form_fields(content_frame)

        # Action buttons
        self.create_action_buttons(content_frame)

        # Progress section (initially hidden)
        self.create_progress_section(content_frame)

        # Snake game (initially hidden)
        self.snake_game = SnakeGame(content_frame, width=350, height=250)
        self.snake_game.grid(row=7, column=0, columnspan=3, pady=20)
        self.snake_game.grid_remove()

        # Navigation button
        back_btn = ttk.Button(
            content_frame,
            text="← Back to Management",
            command=lambda: self.controller.show_frame("DBManagementPage"),
            style="Secondary.TButton",
        )
        back_btn.grid(row=8, column=0, columnspan=3, pady=15)

        # Configure button styles
        style.configure(
            "Primary.TButton",
            background="#3498DB",
            foreground="white",
            font=("Segoe UI", 11, "bold"),
            padding=(20, 10),
        )
        style.configure(
            "Secondary.TButton",
            background="#95A5A6",
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(15, 8),
        )
        style.map("Primary.TButton", background=[("active", "#2980B9")])

        self._widgets_created = True

    def create_form_fields(self, parent):
        """Create form input fields"""
        # Database name
        ttk.Label(
            parent, text="New Database Name:", font=("Segoe UI", 11, "bold")
        ).grid(row=1, column=0, sticky="e", padx=(0, 15), pady=12)

        self.db_name_var = tk.StringVar()
        self.db_name_entry = ttk.Entry(
            parent, textvariable=self.db_name_var, font=("Segoe UI", 11), width=35
        )
        self.db_name_entry.grid(row=1, column=1, padx=5, pady=12, sticky="ew")

        # Backup file
        ttk.Label(parent, text="Backup File:", font=("Segoe UI", 11, "bold")).grid(
            row=2, column=0, sticky="e", padx=(0, 15), pady=12
        )

        self.backup_file_var = tk.StringVar()
        self.backup_file_entry = ttk.Entry(
            parent, textvariable=self.backup_file_var, font=("Segoe UI", 11), width=35
        )
        self.backup_file_entry.grid(row=2, column=1, padx=5, pady=12, sticky="ew")

        browse_btn = ttk.Button(parent, text="Browse...", command=self.browse_file)
        browse_btn.grid(row=2, column=2, padx=(15, 0), pady=12)

        # PostgreSQL binary path
        ttk.Label(
            parent, text="PostgreSQL Bin Path:", font=("Segoe UI", 11, "bold")
        ).grid(row=3, column=0, sticky="e", padx=(0, 15), pady=12)

        self.pg_restore_path_var = tk.StringVar(
            value=r"C:\Program Files\PostgreSQL\12\bin"
        )
        self.pg_restore_path_entry = ttk.Entry(
            parent,
            textvariable=self.pg_restore_path_var,
            font=("Segoe UI", 11),
            width=35,
        )
        self.pg_restore_path_entry.grid(row=3, column=1, padx=5, pady=12, sticky="ew")

    def create_action_buttons(self, parent):
        """Create action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, columnspan=3, pady=25)

        self.restore_btn = ttk.Button(
            button_frame,
            text="🗄️ Restore Database",
            command=self.start_restore,
            style="Primary.TButton",
        )
        self.restore_btn.pack(side="left", padx=10)

        clear_btn = ttk.Button(
            button_frame,
            text="Clear Form",
            command=self.clear_form,
            style="Secondary.TButton",
        )
        clear_btn.pack(side="left", padx=10)

    def create_progress_section(self, parent):
        """Create progress display section"""
        self.progress_frame = ttk.Frame(parent)
        self.progress_frame.grid(row=5, column=0, columnspan=3, pady=20, sticky="ew")

        # Progress label
        self.progress_label = ttk.Label(
            self.progress_frame, text="Restore Progress:", font=("Segoe UI", 11, "bold")
        )
        self.progress_label.pack(anchor="w", pady=(0, 8))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode="indeterminate",
            style="Restore.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(fill="x", pady=(0, 10))

        # Status label
        self.status_label = ttk.Label(
            self.progress_frame, text="", font=("Segoe UI", 10), foreground="#2C3E50"
        )
        self.status_label.pack(anchor="w")

        # Entertainment message
        self.entertainment_label = ttk.Label(
            self.progress_frame,
            text="🎮 Enjoy the snake game while waiting!",
            font=("Segoe UI", 10, "italic"),
            foreground="#7F8C8D",
        )
        self.entertainment_label.pack(anchor="w", pady=(10, 0))

        # Hide initially
        self.progress_frame.grid_remove()

    def on_show_frame(self, event):
        """Handle frame show event"""
        if not self._widgets_created:
            self.create_widgets()

    def browse_file(self):
        """Browse for backup file"""
        file_types = [
            ("PostgreSQL Backup Files", "*.backup"),
            ("SQL Files", "*.sql"),
            ("All Files", "*.*"),
        ]

        file_path = filedialog.askopenfilename(
            title="Select Database Backup File", filetypes=file_types
        )

        if file_path:
            self.backup_file_var.set(file_path)

    def clear_form(self):
        """Clear all form fields"""
        self.db_name_var.set("")
        self.backup_file_var.set("")
        self.hide_progress()

    def start_restore(self):
        """Start the restore operation"""
        # Validate inputs
        db_name = self.db_name_var.get().strip()
        backup_file = self.backup_file_var.get().strip()
        pg_restore_dir = self.pg_restore_path_var.get().strip()

        if not db_name:
            messagebox.showerror("Input Error", "Please enter a database name.")
            return
        if not backup_file:
            messagebox.showerror("Input Error", "Please select a backup file.")
            return

        # Show progress and start game
        self.show_progress("Initializing restore operation...")
        self.disable_ui()

        # Show snake game for entertainment
        self.snake_game.grid()

        # Start restore in background
        self.restore_thread = threading.Thread(
            target=self.perform_restore,
            args=(db_name, backup_file, pg_restore_dir),
            daemon=True,
        )
        self.restore_thread.start()

    def perform_restore(self, db_name, backup_file, pg_restore_dir):
        """Perform restore operation in background"""
        credentials = self.controller.db_credentials

        try:
            # Update status
            self.update_status("Creating new database...")
            create_database(credentials, db_name)

            self.update_status("Restoring data from backup...")
            restore_database(credentials, db_name, backup_file, pg_restore_dir)

            # Success
            self.after(0, lambda: self.restore_success(db_name))

        except Exception as e:
            # Cleanup on error
            try:
                terminate_and_delete_database(credentials, db_name)
            except:
                pass  # Ignore cleanup errors

            self.after(0, lambda: self.restore_error(str(e)))

    def restore_success(self, db_name):
        """Handle successful restore"""
        self.hide_progress()
        self.enable_ui()

        # Get snake game score
        score = self.snake_game.high_score
        commentary = self.snake_game.generate_commentary(score)

        # Show success message with game stats
        message = (
            f"Database '{db_name}' restored successfully! 🎉\n\n"
            f"🐍 Your snake game score: {score}\n"
            f"{commentary}"
        )

        messagebox.showinfo("Restore Complete", message)

        # Reset form
        self.clear_form()
        self.snake_game.grid_remove()

    def restore_error(self, error_message):
        """Handle restore error"""
        self.hide_progress()
        self.enable_ui()
        self.snake_game.grid_remove()

        messagebox.showerror(
            "Restore Failed", f"Database restore failed:\n\n{error_message}"
        )

    def update_status(self, message):
        """Update status from background thread"""
        self.after(0, lambda: self.status_label.config(text=message))

    def show_progress(self, initial_message):
        """Show progress section"""
        self.progress_frame.grid()
        self.progress_bar.start(8)  # Gentle animation
        self.status_label.config(text=initial_message)

    def hide_progress(self):
        """Hide progress section"""
        self.progress_bar.stop()
        self.progress_frame.grid_remove()

    def disable_ui(self):
        """Disable form controls during operation"""
        self.restore_btn.config(state="disabled")
        self.db_name_entry.config(state="disabled")
        self.backup_file_entry.config(state="disabled")
        self.pg_restore_path_entry.config(state="disabled")

    def enable_ui(self):
        """Re-enable form controls after operation"""
        self.restore_btn.config(state="normal")
        self.db_name_entry.config(state="normal")
        self.backup_file_entry.config(state="normal")
        self.pg_restore_path_entry.config(state="normal")
