import tkinter as tk
import random

class SimpleGame(tk.Frame):
    def __init__(self, parent, width=300, height=200):
        super().__init__(parent)
        self.width = width
        self.height = height
        self.score = 0
        self.game_running = False

        # Configure the canvas for the game.
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg="black")
        self.canvas.pack(fill="both", expand=True)
        
        # Scoreboard label.
        self.score_label = tk.Label(self, text=f"Score: {self.score}", font=("Helvetica", 12, "bold"),
                                     fg="white", bg="black")
        self.score_label.pack(pady=5)

        # Create the player's basket (a rectangle).
        self.basket_width = 60
        self.basket_height = 15
        self.basket = self.canvas.create_rectangle(
            self.width//2 - self.basket_width//2, 
            self.height - self.basket_height - 5,
            self.width//2 + self.basket_width//2, 
            self.height - 5,
            fill="blue"
        )

        # List to keep track of falling items.
        self.items = []
        self.fall_speed = 4  # pixels per update
        self.spawn_interval = 1500  # milliseconds between spawns
        self.update_interval = 50   # milliseconds for game update

        # Bind keyboard events.
        self.bind_all("<Left>", self.move_left)
        self.bind_all("<Right>", self.move_right)

    def start_game(self):
        """Start the game."""
        self.game_running = True
        self.score = 0
        self.score_label.config(text=f"Score: {self.score}")
        self.canvas.delete("all")
        # Redraw the basket.
        self.basket = self.canvas.create_rectangle(
            self.width//2 - self.basket_width//2, 
            self.height - self.basket_height - 5,
            self.width//2 + self.basket_width//2, 
            self.height - 5,
            fill="blue"
        )
        self.items.clear()
        self.spawn_item()
        self.update_game()

    def stop_game(self):
        """Stop the game."""
        self.game_running = False

    def spawn_item(self):
        """Spawn a new falling item (a circle) at a random horizontal position."""
        if not self.game_running:
            return
        x = random.randint(10, self.width - 10)
        item = self.canvas.create_oval(x - 10, 0, x + 10, 20, fill="red", outline="")
        self.items.append(item)
        # Schedule the next item spawn.
        self.after(self.spawn_interval, self.spawn_item)

    def update_game(self):
        """Update game state (move items, check for collisions, update score)."""
        if not self.game_running:
            return
        to_remove = []
        for item in self.items:
            self.canvas.move(item, 0, self.fall_speed)
            x1, y1, x2, y2 = self.canvas.coords(item)
            if y2 >= self.height:
                # Item has fallen out of view; remove it.
                self.canvas.delete(item)
                to_remove.append(item)
            elif self.check_collision(item, self.basket):
                # Item caught by basket.
                self.canvas.delete(item)
                to_remove.append(item)
                self.score += 1
                self.score_label.config(text=f"Score: {self.score}")
        for item in to_remove:
            if item in self.items:
                self.items.remove(item)
        self.after(self.update_interval, self.update_game)

    def check_collision(self, item, basket):
        """Return True if the item collides with the basket."""
        x1, y1, x2, y2 = self.canvas.coords(item)
        bx1, by1, bx2, by2 = self.canvas.coords(basket)
        return not (x2 < bx1 or x1 > bx2 or y2 < by1 or y1 > by2)

    def move_left(self, event):
        """Move the basket left."""
        self.canvas.move(self.basket, -20, 0)
        bx1, _, bx2, _ = self.canvas.coords(self.basket)
        if bx1 < 0:
            self.canvas.move(self.basket, -bx1, 0)

    def move_right(self, event):
        """Move the basket right."""
        self.canvas.move(self.basket, 20, 0)
        _, _, bx2, _ = self.canvas.coords(self.basket)
        if bx2 > self.width:
            self.canvas.move(self.basket, self.width - bx2, 0)
