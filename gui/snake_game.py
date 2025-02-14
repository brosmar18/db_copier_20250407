import tkinter as tk
import random

class SnakeGame(tk.Frame):
    def __init__(self, parent, width=300, height=200):
        super().__init__(parent)
        self.parent = parent
        self.width = width
        self.height = height
        self.score = 0
        self.high_score = 0  # Track top score
        self.running = False
        self.after_id = None
        self.snake_size = 10
        self.snake = []
        self.direction = "Right"
        self.food = None

        # Create canvas with dark background.
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg="#2C3E50", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.on_resize)

        # Scoreboard label (placed above the game field, outside of the canvas).
        self.score_label = tk.Label(self, text=f"Score: {self.score} | High Score: {self.high_score}", 
                                    font=("Helvetica", 12, "bold"), fg="white", bg="#34495E")
        self.score_label.pack(fill="x")  # Ensures it stays above the game field

        # Overlay Start Game button in the center.
        self.start_button = tk.Button(self, text="Start Game", command=self.start_game,
                                      font=("Helvetica", 14, "bold"), bg="#27AE60", fg="white")
        self.start_button.place(relx=0.5, rely=0.5, anchor="center")

        # Restart button (hidden initially).
        self.game_over_text_id = None
        self.restart_button = tk.Button(self, text="Restart Game", command=self.start_game,
                                        font=("Helvetica", 12, "bold"), bg="#E74C3C", fg="white")

        # Re-enable keyboard controls
        self.bind_all("<Left>", self.on_key_press)
        self.bind_all("<Right>", self.on_key_press)
        self.bind_all("<Up>", self.on_key_press)
        self.bind_all("<Down>", self.on_key_press)

    def on_resize(self, event):
        """Handles window resize events."""
        self.width = event.width
        self.height = event.height

    def start_game(self):
        """Resets and starts the game."""
        self.reset_game()
        self.running = True
        self.start_button.place_forget()  # Hide start button once game starts
        self.restart_button.place_forget()
        if self.game_over_text_id:
            self.canvas.delete(self.game_over_text_id)
            self.game_over_text_id = None
        self.game_loop()

    def reset_game(self):
        """Resets the game state."""
        self.canvas.delete("all")
        self.snake = [(self.width // 2, self.height // 2)]
        self.direction = "Right"
        self.score = 0
        self.update_score()
        self.draw_snake()
        self.spawn_food()

    def update_score(self):
        """Updates the score label and checks for a new high score."""
        if self.score > self.high_score:
            self.high_score = self.score
        self.score_label.config(text=f"Score: {self.score} | High Score: {self.high_score}")

    def draw_snake(self):
        """Draws the snake on the canvas."""
        self.canvas.delete("snake")
        for (x, y) in self.snake:
            self.canvas.create_rectangle(x, y, x + self.snake_size, y + self.snake_size,
                                         fill="#27AE60", tag="snake")

    def spawn_food(self):
        """Spawns food at a random location."""
        if self.food:
            self.canvas.delete(self.food)
        max_x = max(1, (self.width - self.snake_size) // self.snake_size)
        max_y = max(1, (self.height - self.snake_size) // self.snake_size)
        food_x = random.randint(0, max_x - 1) * self.snake_size
        food_y = random.randint(0, max_y - 1) * self.snake_size
        self.food = self.canvas.create_oval(food_x, food_y, food_x + self.snake_size, food_y + self.snake_size,
                                            fill="#E74C3C", tag="food")

    def on_key_press(self, event):
        """Handles user input for movement."""
        key = event.keysym
        if key == "Left" and self.direction != "Right":
            self.direction = "Left"
        elif key == "Right" and self.direction != "Left":
            self.direction = "Right"
        elif key == "Up" and self.direction != "Down":
            self.direction = "Up"
        elif key == "Down" and self.direction != "Up":
            self.direction = "Down"

    def game_loop(self):
        """Main game loop to update the snake movement."""
        if not self.running:
            return
        head_x, head_y = self.snake[0]
        if self.direction == "Left":
            head_x -= self.snake_size
        elif self.direction == "Right":
            head_x += self.snake_size
        elif self.direction == "Up":
            head_y -= self.snake_size
        elif self.direction == "Down":
            head_y += self.snake_size
        new_head = (head_x, head_y)

        # Check for collisions
        if head_x < 0 or head_x >= self.width or head_y < 0 or head_y >= self.height:
            self.game_over()
            return
        if new_head in self.snake:
            self.game_over()
            return

        self.snake = [new_head] + self.snake
        if self.food:
            food_coords = self.canvas.coords(self.food)
            if self.check_collision(new_head, food_coords):
                self.score += 1
                self.update_score()
                self.spawn_food()
            else:
                self.snake.pop()

        self.draw_snake()
        self.after_id = self.after(100, self.game_loop)

    def check_collision(self, head, food_coords):
        """Checks if the snake head collides with food."""
        x, y = head
        x1, y1, x2, y2 = food_coords
        return x >= x1 and x < x2 and y >= y1 and y < y2

    def game_over(self):
        """Handles game over state."""
        self.running = False
        self.pause()
        self.canvas.create_text(self.width//2, self.height//2, text="Game Over!", fill="red",
                                font=("Helvetica", 16, "bold"))
        self.restart_button.place(relx=0.5, rely=0.8, anchor="center")

    def pause(self):
        """Pauses the game."""
        self.running = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

    def pause_game(self):
        """External pause method."""
        self.pause()

    def generate_commentary(self, score):
        """Generates commentary based on the player's score."""
        if score < 3:
            return "Ouch! You barely moved!"
        elif score < 6:
            return "Not bad, but you can do better!"
        elif score < 10:
            return "Nice! Keep it up!"
        else:
            return "Incredible! You're a snake master!"
