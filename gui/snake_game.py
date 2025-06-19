import tkinter as tk
import random


class SnakeGame(tk.Frame):
    def __init__(self, parent, width=300, height=200):
        super().__init__(parent)
        self.parent = parent
        self.width = width
        self.height = height
        self.score = 0
        self.high_score = 0
        self.running = False
        self.after_id = None
        self.snake_size = 12  # Slightly larger for better performance
        self.snake = []
        self.direction = "Right"
        self.food = None
        self.game_speed = 150  # Slower for better performance

        # Performance optimization: reduce update frequency
        self.last_direction_change = 0

        self.create_widgets()

    def create_widgets(self):
        """Create game widgets efficiently"""
        # Canvas with optimized settings
        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            bg="#2C3E50",
            highlightthickness=0,
            relief="flat",
            borderwidth=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # Score display
        self.score_label = tk.Label(
            self,
            text=f"Score: {self.score} | Best: {self.high_score}",
            font=("Segoe UI", 11, "bold"),
            fg="white",
            bg="#34495E",
            relief="flat",
        )
        self.score_label.pack(fill="x", ipady=5)

        # Start button
        self.start_button = tk.Button(
            self,
            text="🎮 Start Game",
            command=self.start_game,
            font=("Segoe UI", 12, "bold"),
            bg="#27AE60",
            fg="white",
            relief="flat",
            borderwidth=0,
            activebackground="#229954",
        )
        self.start_button.place(relx=0.5, rely=0.5, anchor="center")

        # Game over elements (created but hidden)
        self.game_over_elements = []

        # Bind keys efficiently
        self.bind_keys()

    def bind_keys(self):
        """Bind keyboard events efficiently"""
        # Use focus_set to ensure key events are captured
        self.focus_set()

        # Bind arrow keys and WASD
        keys = {
            "<Left>": "Left",
            "<a>": "Left",
            "<A>": "Left",
            "<Right>": "Right",
            "<d>": "Right",
            "<D>": "Right",
            "<Up>": "Up",
            "<w>": "Up",
            "<W>": "Up",
            "<Down>": "Down",
            "<s>": "Down",
            "<S>": "Down",
        }

        for key, direction in keys.items():
            self.bind(key, lambda e, d=direction: self.change_direction(d))

    def start_game(self):
        """Start or restart the game"""
        self.reset_game()
        self.running = True
        self.start_button.place_forget()
        self.clear_game_over()
        self.focus_set()  # Ensure focus for key events
        self.game_loop()

    def reset_game(self):
        """Reset game state efficiently"""
        # Clear canvas efficiently
        self.canvas.delete("all")

        # Reset game state
        center_x = (self.width // 2) // self.snake_size * self.snake_size
        center_y = (self.height // 2) // self.snake_size * self.snake_size
        self.snake = [(center_x, center_y)]
        self.direction = "Right"
        self.score = 0
        self.last_direction_change = 0

        self.update_score()
        self.spawn_food()
        self.draw_snake()

    def update_score(self):
        """Update score display efficiently"""
        if self.score > self.high_score:
            self.high_score = self.score
        self.score_label.config(text=f"Score: {self.score} | Best: {self.high_score}")

    def draw_snake(self):
        """Draw snake efficiently using rectangles"""
        self.canvas.delete("snake")

        for i, (x, y) in enumerate(self.snake):
            # Use different color for head
            color = "#2ECC71" if i == 0 else "#27AE60"
            self.canvas.create_rectangle(
                x,
                y,
                x + self.snake_size,
                y + self.snake_size,
                fill=color,
                outline="",
                tags="snake",
            )

    def spawn_food(self):
        """Spawn food at random valid location"""
        if self.food:
            self.canvas.delete(self.food)

        # Calculate grid positions for consistent placement
        max_x = (self.width - self.snake_size) // self.snake_size
        max_y = (self.height - self.snake_size) // self.snake_size

        # Ensure food doesn't spawn on snake
        attempts = 0
        while attempts < 20:  # Prevent infinite loop
            food_x = random.randint(0, max_x) * self.snake_size
            food_y = random.randint(0, max_y) * self.snake_size

            if (food_x, food_y) not in self.snake:
                break
            attempts += 1

        # Create food
        self.food = self.canvas.create_oval(
            food_x + 1,
            food_y + 1,
            food_x + self.snake_size - 1,
            food_y + self.snake_size - 1,
            fill="#E74C3C",
            outline="#C0392B",
            width=2,
            tags="food",
        )

    def change_direction(self, new_direction):
        """Change direction with debouncing"""
        if not self.running:
            return

        current_time = self.tk.call("clock", "milliseconds")
        if current_time - self.last_direction_change < 100:  # Debounce
            return

        # Prevent reverse direction
        opposites = {"Left": "Right", "Right": "Left", "Up": "Down", "Down": "Up"}
        if new_direction != opposites.get(self.direction):
            self.direction = new_direction
            self.last_direction_change = current_time

    def game_loop(self):
        """Main game loop with optimized performance"""
        if not self.running:
            return

        # Calculate new head position
        head_x, head_y = self.snake[0]
        moves = {
            "Left": (-self.snake_size, 0),
            "Right": (self.snake_size, 0),
            "Up": (0, -self.snake_size),
            "Down": (0, self.snake_size),
        }

        dx, dy = moves[self.direction]
        new_head = (head_x + dx, head_y + dy)

        # Check collisions
        if (
            new_head[0] < 0
            or new_head[0] >= self.width
            or new_head[1] < 0
            or new_head[1] >= self.height
            or new_head in self.snake
        ):
            self.game_over()
            return

        # Add new head
        self.snake.insert(0, new_head)

        # Check food collision
        food_coords = self.canvas.coords(self.food)
        if self.check_food_collision(new_head, food_coords):
            self.score += 1
            self.update_score()
            self.spawn_food()
            # Slightly increase speed
            self.game_speed = max(80, self.game_speed - 2)
        else:
            self.snake.pop()  # Remove tail

        # Redraw snake
        self.draw_snake()

        # Schedule next update
        self.after_id = self.after(self.game_speed, self.game_loop)

    def check_food_collision(self, head, food_coords):
        """Check if snake head touches food"""
        if len(food_coords) < 4:
            return False

        x, y = head
        x1, y1, x2, y2 = food_coords
        return (
            x < x2 and x + self.snake_size > x1 and y < y2 and y + self.snake_size > y1
        )

    def game_over(self):
        """Handle game over efficiently"""
        self.running = False
        self.pause()

        # Show game over message
        center_x, center_y = self.width // 2, self.height // 2

        # Background for text
        bg = self.canvas.create_rectangle(
            center_x - 80,
            center_y - 30,
            center_x + 80,
            center_y + 30,
            fill="#2C3E50",
            outline="#E74C3C",
            width=2,
            tags="gameover",
        )

        # Game over text
        text = self.canvas.create_text(
            center_x,
            center_y,
            text="Game Over!",
            fill="#E74C3C",
            font=("Segoe UI", 14, "bold"),
            tags="gameover",
        )

        self.game_over_elements = [bg, text]

        # Show restart button
        self.start_button.config(text="🔄 Play Again")
        self.start_button.place(relx=0.5, rely=0.7, anchor="center")

    def clear_game_over(self):
        """Clear game over elements"""
        for element in self.game_over_elements:
            self.canvas.delete(element)
        self.game_over_elements = []

    def pause(self):
        """Pause the game"""
        self.running = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

    def pause_game(self):
        """External pause method for compatibility"""
        self.pause()

    def generate_commentary(self, score):
        """Generate performance commentary"""
        comments = [
            (0, "🐌 Baby steps! Every expert was once a beginner."),
            (3, "🎯 Getting the hang of it! Keep practicing."),
            (7, "🚀 Nice moves! You're improving quickly."),
            (12, "🏆 Impressive! You've got real skills."),
            (20, "🔥 Outstanding! You're a snake charmer!"),
            (30, "🌟 Legendary! Are you sure you're human?"),
        ]

        for threshold, comment in reversed(comments):
            if score >= threshold:
                return comment
        return comments[0][1]  # Default to first comment
