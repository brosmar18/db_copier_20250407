import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from db import create_database, restore_database, terminate_and_delete_database

class RestorePage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        outer_frame = ttk.Frame(self)
        outer_frame.pack(expand=True, fill="both")
        content_frame = ttk.Frame(outer_frame, padding=20)
        content_frame.place(relx=0.5, rely=0.5, anchor="center")

        title = ttk.Label(content_frame, text="Restore Database", font=("Helvetica", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(20, 10))

        # New database name input.
        ttk.Label(content_frame, text="New Database Name:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.db_name_var = tk.StringVar()
        self.db_name_entry = ttk.Entry(content_frame, textvariable=self.db_name_var, width=30)
        self.db_name_entry.grid(row=1, column=1, padx=5, pady=5)

        # Backup file selection.
        ttk.Label(content_frame, text="Backup File:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.backup_file_var = tk.StringVar()
        self.backup_file_entry = ttk.Entry(content_frame, textvariable=self.backup_file_var, width=30)
        self.backup_file_entry.grid(row=2, column=1, padx=5, pady=5)
        browse_btn = ttk.Button(content_frame, text="Browse", command=self.browse_file)
        browse_btn.grid(row=2, column=2, padx=5, pady=5)

        # Restore button.
        restore_btn = ttk.Button(content_frame, text="Restore Database", command=self.restore_database_action)
        restore_btn.grid(row=3, column=0, columnspan=3, pady=10)

        # Progress bar (hidden initially)
        self.progress = ttk.Progressbar(content_frame, mode="indeterminate", length=300)
        self.progress.grid(row=4, column=0, columnspan=3, pady=5)
        self.progress.grid_remove()

        # Back button.
        back_btn = ttk.Button(content_frame, text="Back", command=lambda: controller.show_frame("DBManagementPage"))
        back_btn.grid(row=5, column=0, columnspan=3, pady=5)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Backup Files", "*.backup"), ("All Files", "*.*")])
        if file_path:
            self.backup_file_var.set(file_path)

    def reset_progress(self):
        self.progress.stop()
        self.progress.grid_remove()

    def restore_database_action(self):
        db_name = self.db_name_var.get().strip()
        backup_file = self.backup_file_var.get().strip()
        if not db_name:
            messagebox.showerror("Input Error", "Please enter a new database name.")
            return
        if not backup_file:
            messagebox.showerror("Input Error", "Please select a backup file.")
            return

        confirm = messagebox.askokcancel(
            "Confirm Restore",
            f"Are you sure you want to create a new database '{db_name}' and restore from:\n{backup_file}?"
        )
        if not confirm:
            return

        # Show and start the progress bar.
        self.progress.grid()
        self.progress.start(10)

        def run_restore():
            credentials = self.controller.db_credentials
            try:
                # Create new database.
                create_database(credentials, db_name)
                # Restore from backup.
                restore_database(credentials, db_name, backup_file)
                self.controller.after(0, lambda: messagebox.showinfo("Success", f"Database '{db_name}' restored successfully."))
            except Exception as e:
                err = str(e)
                # If restore fails, drop the created database.
                try:
                    terminate_and_delete_database(credentials, db_name)
                except Exception as drop_err:
                    pass
                self.controller.after(0, lambda err=err: messagebox.showerror("Error", f"Restore failed: {err}"))
            finally:
                self.controller.after(0, self.reset_progress)

        threading.Thread(target=run_restore, daemon=True).start()
