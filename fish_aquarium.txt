import curses
import random
import time
import math
import requests
import threading
import RPi.GPIO as GPIO
from Adafruit_IO import Client

# --- Configuration ---
PUSHOVER_USER_KEY = Insert own info
PUSHOVER_APP_TOKEN = Insert own info

AIO_USERNAME = Insert own info
AIO_KEY = Insert own info
FEED_NAME = Insert own info

# GPIO Pins
TRIG = 21
ECHO = 20
LED_GREEN = 27
LED_YELLOW = 17
BUZZER = 4

# Global variables
current_dist = 100.0
sensor_reading_active = False
hand_in_range = False 

aio = Client(AIO_USERNAME, AIO_KEY)

def get_distance_with_timeout():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    pulse_start = time.time()
    pulse_end = time.time()
    start_timeout = time.time()

    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start - start_timeout > 0.05:
            return 100.0

    end_timeout = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end - end_timeout > 0.05:
            return 100.0

    return (pulse_end - pulse_start) * 17150

def sensor_thread_logic():
    global sensor_reading_active, current_dist
    try:
        current_dist = get_distance_with_timeout()
    finally:
        sensor_reading_active = False

def send_pushover_notification():
    url = "https://api.pushover.net/1/messages.json"
    data = {"token": PUSHOVER_APP_TOKEN, "user": PUSHOVER_USER_KEY, "message": "The fish are hungry!!!"}
    try: requests.post(url, data=data, timeout=5)
    except: pass

def background_adafruit_update(hunger_pct):
    try: aio.send(FEED_NAME, int(hunger_pct * 100))
    except: pass

FISH_TYPES = [("><>", "<><"), (">><>", "<><<"), (">((('>", "<')))><")]

class Fish:
    def __init__(self, max_y, max_x):
        self.right_shape, self.left_shape = random.choice(FISH_TYPES)
        self.direction = random.choice([-1, 1])
        self.shape = self.right_shape if self.direction == 1 else self.left_shape
        self.y = random.uniform(2, max_y - 3) 
        self.x = random.uniform(1, max_x - len(self.shape) - 1)
        self.speed = random.uniform(0.05, 0.12)
        self.last_move = time.time()
        self.target_y = self.y
        self.color = 1 
        self.depth = 3

    def update_shape(self):
        self.shape = self.right_shape if self.direction == 1 else self.left_shape

    def move(self, max_y, max_x, food_pellets):
        now = time.time()
        if now - self.last_move < self.speed: return
        self.last_move = now
        if food_pellets:
            target = min(food_pellets, key=lambda p: math.hypot(self.x - p.x, self.y - p.y))
            if self.x < target.x: self.direction = 1
            elif self.x > target.x: self.direction = -1
            if self.y < target.y: self.y += 0.3
            elif self.y > target.y: self.y -= 0.3
            self.update_shape()
        else:
            if abs(self.y - self.target_y) < 1: self.target_y = random.randint(3, max_y - 4)
            if self.y < self.target_y: self.y += 0.2
            elif self.y > self.target_y: self.y -= 0.2
        self.x += self.direction
        if self.x <= 0: self.direction = 1; self.update_shape()
        elif self.x >= max_x - len(self.shape): self.direction = -1; self.update_shape()

    def draw(self, stdscr):
        try: stdscr.addstr(int(self.y), int(self.x), self.shape, curses.color_pair(self.color))
        except curses.error: pass

class Food:
    def __init__(self, max_x):
        self.x = random.randint(2, max_x - 3)
        self.y = 1.0
        self.speed = random.uniform(0.1, 0.2)
        self.last_move = time.time()
        self.depth = 2

    def move(self, max_y):
        now = time.time()
        if now - self.last_move < self.speed: return False
        self.last_move = now
        self.y += 0.5
        return self.y >= max_y - 2

    def draw(self, stdscr):
        try: stdscr.addstr(int(self.y), int(self.x), "*", curses.color_pair(2))
        except curses.error: pass

class Seaweed:
    def __init__(self, max_y, x):
        self.x = x; self.max_y = max_y; self.height = random.randint(2, 5)
        self.offset = random.uniform(0, 5); self.depth = 1 
    def draw(self, stdscr):
        sway = int(math.sin(time.time() * 2 + self.offset) * 1.2)
        for i in range(self.height):
            char = "(" if (i + sway) % 2 == 0 else ")"
            try: stdscr.addstr(self.max_y - 2 - i, self.x + (sway if i > 1 else 0), char, curses.color_pair(5))
            except curses.error: pass

class Bubble:
    def __init__(self, max_y, max_x):
        self.x = random.randint(1, max_x - 2); self.y = max_y - 2; self.char = random.choice(['o', 'O', '.'])
        self.speed = random.uniform(0.05, 0.15); self.last_move = time.time(); self.depth = 0 
    def move(self):
        now = time.time()
        if now - self.last_move < self.speed: return
        self.last_move = now; self.y -= 1
    def draw(self, stdscr):
        try: stdscr.addstr(int(self.y), int(self.x), self.char, curses.color_pair(4))
        except curses.error: pass

def init_colors():
    curses.start_color(); curses.use_default_colors()
    Y, O, R, C, G = 226, 208, 196, 51, 46 if curses.COLORS >= 256 else (11, 10, 9, 14, 10)
    curses.init_pair(1, Y, -1); curses.init_pair(2, O, -1); curses.init_pair(3, R, -1); curses.init_pair(4, C, -1); curses.init_pair(5, G, -1)

def aquarium(stdscr):
    global sensor_reading_active, current_dist, hand_in_range
    GPIO.setmode(GPIO.BCM)
    for pin in [TRIG, LED_GREEN, LED_YELLOW, BUZZER]: GPIO.setup(pin, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    
    curses.curs_set(0); stdscr.nodelay(True); init_colors()
    
    max_y, max_x = stdscr.getmaxyx()
    fish_list = [Fish(max_y, max_x) for _ in range(10)]
    seaweed_list = [Seaweed(max_y, x) for x in range(2, max_x - 2, 4)]
    bubbles, food_pellets = [], []
    
    last_fed_time = last_iot_update = last_sensor_check = time.time()
    fed_feedback_start = 0
    hunger_duration = 30.0
    notification_sent = False

    try:
        while True:
            now = time.time()
            max_y, max_x = stdscr.getmaxyx()

            if now - last_sensor_check > 0.1 and not sensor_reading_active:
                sensor_reading_active = True
                threading.Thread(target=sensor_thread_logic, daemon=True).start()
                last_sensor_check = now

            # Feeding Trigger (10cm latch)
            if current_dist < 10.0:
                if not hand_in_range:
                    for _ in range(5): food_pellets.append(Food(max_x))
                    GPIO.output(LED_GREEN, True)
                    GPIO.output(BUZZER, True)
                    fed_feedback_start = now
                    hand_in_range = True
            else:
                hand_in_range = False

            # Turn off fed feedback after 0.5s
            if fed_feedback_start > 0 and now - fed_feedback_start > 0.5:
                GPIO.output(LED_GREEN, False)
                GPIO.output(BUZZER, False)
                fed_feedback_start = 0

            if stdscr.getch() == ord('q'): break
            
            elapsed = now - last_fed_time
            hunger_pct = min(1.0, elapsed / hunger_duration)
            is_hungry = hunger_pct >= 1.0

            # Hunger LED logic
            GPIO.output(LED_YELLOW, True if is_hungry else False)

            if now - last_iot_update > 5:
                threading.Thread(target=background_adafruit_update, args=(hunger_pct,), daemon=True).start()
                last_iot_update = now

            if is_hungry and not notification_sent:
                threading.Thread(target=send_pushover_notification, daemon=True).start()
                notification_sent = True 

            if random.random() < 0.1: bubbles.append(Bubble(max_y, max_x))
            for b in bubbles[:]: b.move(); (bubbles.remove(b) if b.y <= 1 else None)
            for p in food_pellets[:]: (food_pellets.remove(p) if p.move(max_y) else None)
            for f in fish_list:
                f.move(max_y, max_x, food_pellets)
                for p in food_pellets[:]:
                    if abs(f.x + len(f.shape)//2 - p.x) < 2 and abs(f.y - p.y) < 1.5:
                        if p in food_pellets:
                            food_pellets.remove(p)
                            last_fed_time = now
                            notification_sent = False 

            stdscr.erase()
            bar_width = 20
            filled_width = int(hunger_pct * bar_width)
            bar_str = "[" + "=" * filled_width + " " * (bar_width - filled_width) + "]"
            label = f" HUNGER: {int(hunger_pct * 100)}% "
            try: stdscr.addstr(0, (max_x // 2) - (len(bar_str + label) // 2), label + bar_str, curses.color_pair(3 if is_hungry else 2))
            except curses.error: pass

            for x in range(max_x):
                try: stdscr.addstr(1, x, "~", curses.color_pair(4))
                except curses.error: pass
            
            drawables = [(b.depth, b) for b in bubbles] + [(f.depth, f) for f in fish_list] + \
                        [(s.depth, s) for s in seaweed_list] + [(p.depth, p) for p in food_pellets]
            drawables.sort(key=lambda x: x[0])
            for _, obj in drawables: obj.draw(stdscr)
            
            stdscr.refresh()
            time.sleep(0.03)
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    curses.wrapper(aquarium)
