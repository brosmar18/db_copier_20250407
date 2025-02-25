# restore_page.py
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

        # Set custom style for progress bar.
        style = ttk.Style(self)
        style.configure("Custom.Horizontal.TProgressbar",
                        troughcolor="#E0E0E0",
                        background="#7BB837",
                        thickness=20)

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

        # pg_restore directory input.
        ttk.Label(content_frame, text="Binary Path:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        # Default value is just the directory without 'pg_restore.exe'
        self.pg_restore_path_var = tk.StringVar(value=r"C:\Program Files\PostgreSQL\12\bin")
        self.pg_restore_path_entry = ttk.Entry(content_frame, textvariable=self.pg_restore_path_var, width=30)
        self.pg_restore_path_entry.grid(row=3, column=1, padx=5, pady=5)

        # Restore button.
        restore_btn = ttk.Button(content_frame, text="Restore Database", command=self.restore_database_action)
        restore_btn.grid(row=4, column=0, columnspan=3, pady=10)

        # Progress bar.
        self.progress_bar = ttk.Progressbar(content_frame, mode="determinate", maximum=100,
                                            style="Custom.Horizontal.TProgressbar")
        self.progress_bar.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.progress_bar.grid_remove()

        # Embed the Snake game.
        self.snake_game = SnakeGame(content_frame, width=300, height=200)
        self.snake_game.grid(row=6, column=0, columnspan=3, padx=10, pady=10)
        self.snake_game.grid_remove()  # Hidden initially

        # Back button.
        back_btn = ttk.Button(content_frame, text="Back", command=lambda: controller.show_frame("DBManagementPage"))
        back_btn.grid(row=7, column=0, columnspan=3, pady=5)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Backup Files", "*.backup"), ("All Files", "*.*")])
        if file_path:
            self.backup_file_var.set(file_path)

    def update_progress(self):
        if self.restore_thread and self.restore_thread.is_alive():
            current_value = self.progress_bar['value']
            if current_value < 95:
                self.progress_bar['value'] += 5
            self.after(500, self.update_progress)
        else:
            self.progress_bar['value'] = 100
            self.after(500, self.finish_progress)

    def finish_progress(self):
        self.progress_bar.grid_remove()
        self.progress_bar['value'] = 0
        self.snake_game.pause_game()  # Pause the snake game

        top_score = self.snake_game.high_score  # Get the high score
        commentary = self.snake_game.generate_commentary(top_score)
    
        message = f"Database restored successfully!\nYour top snake score: {top_score}\n{commentary}"
        messagebox.showinfo("Success", message)

    def restore_database_action(self):
        db_name = self.db_name_var.get().strip()
        backup_file = self.backup_file_var.get().strip()
        pg_restore_dir = self.pg_restore_path_var.get().strip()
        if not db_name:
            messagebox.showerror("Input Error", "Please enter a new database name.")
            return
        if not backup_file:
            messagebox.showerror("Input Error", "Please select a backup file.")
            return

        # Start progress bar and show snake game widget.
        self.progress_bar['value'] = 0
        self.progress_bar.grid()
        self.snake_game.grid()  # Ensure game widget is visible
        
        def run_restore():
            credentials = self.controller.db_credentials
            try:
                create_database(credentials, db_name)
                restore_database(credentials, db_name, backup_file, pg_restore_dir)
            except Exception as e:
                err = str(e)
                try:
                    terminate_and_delete_database(credentials, db_name)
                except Exception:
                    pass
                self.controller.after(0, lambda err=err: messagebox.showerror("Error", f"Restore failed: {err}"))
            finally:
                pass

        self.restore_thread = threading.Thread(target=run_restore, daemon=True)
        self.restore_thread.start()
        self.after(500, self.update_progress)
