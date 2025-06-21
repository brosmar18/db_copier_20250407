import tkinter as tk
import random


class SnakeGame(tk.Frame):
    def __init__(self, parent, width=400, height=280):
        super().__init__(parent)
        self.parent = parent
        self.width = width
        self.height = height
        self.score = 0
        self.high_score = 0
        self.running = False
        self.after_id = None
        self.snake_size = 16
        self.snake = []
        self.direction = "Right"
        self.food = None
        self.game_speed = 180

        # Performance optimization
        self.last_direction_change = 0

        self.create_widgets()

    def create_widgets(self):
        """Create game widgets with new color scheme"""
        # Canvas with new color scheme
        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            bg="#181F67",  # New dark blue background
            highlightthickness=2,
            highlightbackground="#939498",  # New gray border
            relief="solid",
            borderwidth=1,
        )
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # Score display with new color scheme
        self.score_label = tk.Label(
            self,
            text=f"Score: {self.score} | Best: {self.high_score}",
            font=("Segoe UI", 13, "bold"),
            fg="white",
            bg="#939498",  # New gray background
            relief="flat",
            padx=15,
            pady=8
        )
        self.score_label.pack(fill="x")

        # Start button with new color scheme
        self.start_button = tk.Button(
            self,
            text="🎮 Start Game",
            command=self.start_game,
            font=("Segoe UI", 14, "bold"),
            bg="#7BB837",  # New green background
            fg="white",
            relief="flat",
            borderwidth=0,
            activebackground="#6FA02E",  # Darker green on hover
            padx=25,
            pady=12
        )
        self.start_button.place(relx=0.5, rely=0.5, anchor="center")

        # Game over elements
        self.game_over_elements = []

        # Bind keys
        self.bind_keys()

    def bind_keys(self):
        """Bind keyboard events efficiently"""
        self.focus_set()

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
        self.focus_set()
        self.game_loop()

    def reset_game(self):
        """Reset game state efficiently"""
        self.canvas.delete("all")

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
        """Draw snake with new color scheme"""
        self.canvas.delete("snake")

        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                # Head - bright green with darker border
                color = "#7BB837"  # New green
                outline = "#6FA02E"  # Darker green
            else:
                # Body - slightly darker green with border
                color = "#6FA02E"  # Darker green
                outline = "#5F8A26"  # Even darker green
            
            self.canvas.create_rectangle(
                x,
                y,
                x + self.snake_size,
                y + self.snake_size,
                fill=color,
                outline=outline,
                width=2,
                tags="snake",
            )

    def spawn_food(self):
        """Spawn food with new color scheme"""
        if self.food:
            self.canvas.delete(self.food)

        max_x = (self.width - self.snake_size) // self.snake_size
        max_y = (self.height - self.snake_size) // self.snake_size

        attempts = 0
        while attempts < 20:
            food_x = random.randint(0, max_x) * self.snake_size
            food_y = random.randint(0, max_y) * self.snake_size

            if (food_x, food_y) not in self.snake:
                break
            attempts += 1

        # Create food with better visibility - using a contrasting color
        self.food = self.canvas.create_oval(
            food_x + 2,
            food_y + 2,
            food_x + self.snake_size - 2,
            food_y + self.snake_size - 2,
            fill="#E74C3C",  # Keep red for good contrast against dark blue background
            outline="#C0392B",  # Darker red border
            width=3,
            tags="food",
        )

    def change_direction(self, new_direction):
        """Change direction with debouncing"""
        if not self.running:
            return

        current_time = self.tk.call("clock", "milliseconds")
        if current_time - self.last_direction_change < 120:
            return

        opposites = {"Left": "Right", "Right": "Left", "Up": "Down", "Down": "Up"}
        if new_direction != opposites.get(self.direction):
            self.direction = new_direction
            self.last_direction_change = current_time

    def game_loop(self):
        """Main game loop with optimized performance"""
        if not self.running:
            return

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

        self.snake.insert(0, new_head)

        # Check food collision
        food_coords = self.canvas.coords(self.food)
        if self.check_food_collision(new_head, food_coords):
            self.score += 1
            self.update_score()
            self.spawn_food()
            self.game_speed = max(100, self.game_speed - 3)
        else:
            self.snake.pop()

        self.draw_snake()
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
        """Handle game over with new color scheme"""
        self.running = False
        self.pause()

        center_x, center_y = self.width // 2, self.height // 2

        # Background for text with new colors
        bg = self.canvas.create_rectangle(
            center_x - 100,
            center_y - 40,
            center_x + 100,
            center_y + 40,
            fill="#181F67",  # New dark blue
            outline="#E74C3C",  # Keep red for visibility
            width=3,
            tags="gameover",
        )

        # Game over text
        text = self.canvas.create_text(
            center_x,
            center_y,
            text="Game Over!",
            fill="#E74C3C",  # Keep red for visibility
            font=("Segoe UI", 16, "bold"),
            tags="gameover",
        )

        self.game_over_elements = [bg, text]

        # Show restart button
        self.start_button.config(
            text="🔄 Play Again",
            font=("Segoe UI", 14, "bold"),
            bg="#7BB837",  # New green
            activebackground="#6FA02E",  # Darker green on hover
            padx=25,
            pady=12
        )
        self.start_button.place(relx=0.5, rely=0.75, anchor="center")

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
        """Generate performance commentary with updated thresholds"""
        comments = [
            (0, "🐌 Baby steps! Every expert was once a beginner."),
            (4, "🎯 Getting the hang of it! Keep practicing."),
            (8, "🚀 Nice moves! You're improving quickly."),
            (15, "🏆 Impressive! You've got real skills."),
            (25, "🔥 Outstanding! You're a snake charmer!"),
            (35, "🌟 Legendary! Are you sure you're human?"),
        ]

        for threshold, comment in reversed(comments):
            if score >= threshold:
                return comment
        return comments[0][1]