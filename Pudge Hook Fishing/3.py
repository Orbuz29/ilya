import arcade
import random
import math
import os
from enum import Enum

# ============================================================
#                     НАСТРОЙКИ
# ============================================================

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Pudge Hook Fishing"

PLAYER_SCALE = 0.35
FISH_SCALE = 0.25
HOOK_SCALE = 0.10

PLAYER_SPEED = 6
HOOK_SPEED = 12
FISH_SPEED_MIN = 1.5
FISH_SPEED_MAX = 3.5
FISH_SPEED_FAST = 10.0

HOOK_MAX_DISTANCE = 420
RECORD_FILE = "record.txt"

BACKGROUND_COLOR = arcade.color.DARK_SLATE_BLUE


# ============================================================
#                     ENUM
# ============================================================

class HookState(Enum):
    READY = 0
    FLYING = 1
    RETURNING = 2


# ============================================================
#                     УТИЛИТЫ
# ============================================================

def load_record():
    if not os.path.exists(RECORD_FILE):
        return 0
    with open(RECORD_FILE, "r") as f:
        return int(f.read())


def save_record(score):
    if score > load_record():
        with open(RECORD_FILE, "w") as f:
            f.write(str(score))


def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


# ============================================================
#                     РЫБА
# ============================================================

class Fish(arcade.Sprite):
    def __init__(self, level):
        super().__init__("fish.png", FISH_SCALE)
        self.level = level  # Уровень игры
        self.center_y = random.randint(80, 200)
        self.center_x = random.choice([0, SCREEN_WIDTH])
        # Скорость рыб в зависимости от уровня
        if self.level == 2:
            self.change_x = random.choice([-1, 1]) * random.uniform(FISH_SPEED_FAST, FISH_SPEED_FAST * 2)
        else:
            self.change_x = random.choice([-1, 1]) * random.uniform(FISH_SPEED_MIN, FISH_SPEED_MAX)
        self.caught = False

    def update(self, delta_time: float = 0):
        if not self.caught:
            self.center_x += self.change_x

        if self.center_x < -50 or self.center_x > SCREEN_WIDTH + 50:
            self.remove_from_sprite_lists()


# ============================================================
#                     ХУК
# ============================================================

class Hook(arcade.Sprite):
    def __init__(self):
        super().__init__("hook.png", HOOK_SCALE)
        self.state = HookState.READY
        self.start_x = 0
        self.start_y = 0
        self.caught_fish = None

    def fire(self, x, y):
        if self.state == HookState.READY:
            self.center_x = x
            self.center_y = y
            self.start_x = x
            self.start_y = y
            self.state = HookState.FLYING

    def update(self):
        delivered = False

        if self.state == HookState.FLYING:
            self.center_y -= HOOK_SPEED
            if distance(self.center_x, self.center_y,
                        self.start_x, self.start_y) >= HOOK_MAX_DISTANCE:
                self.state = HookState.RETURNING

        elif self.state == HookState.RETURNING:
            dx = self.start_x - self.center_x
            dy = self.start_y - self.center_y
            length = math.sqrt(dx ** 2 + dy ** 2)

            if length > 0:
                self.center_x += (dx / length) * HOOK_SPEED
                self.center_y += (dy / length) * HOOK_SPEED

            if length < HOOK_SPEED:
                self.state = HookState.READY
                if self.caught_fish:
                    self.caught_fish.remove_from_sprite_lists()
                    self.caught_fish = None
                    delivered = True

        return delivered


# ============================================================
#                     ИГРА
# ============================================================

class GameView(arcade.View):
    def __init__(self, level=1):
        super().__init__()
        self.level = level
        self.score = 0
        self.timer = 60

        self.player_list = arcade.SpriteList()
        self.fish_list = arcade.SpriteList()
        self.hook_list = arcade.SpriteList()

        self.player = arcade.Sprite("pudge.png", PLAYER_SCALE)
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = 500
        self.player_list.append(self.player)

        self.hook = Hook()
        self.hook_list.append(self.hook)

        self.move_left = False
        self.move_right = False

        # Звуки
        self.sound_hook = arcade.load_sound("hook.wav")  # Звук для хука
        self.sound_catch = arcade.load_sound("catch.wav")  # Звук для поимки рыбы

    def spawn_fish(self):
        fish = Fish(self.level)
        self.fish_list.append(fish)

    def draw_chain(self):
        if self.hook.state != HookState.READY:
            segments = int(distance(
                self.player.center_x, self.player.center_y,
                self.hook.center_x, self.hook.center_y
            ) // 20)

            for i in range(segments):
                t = i / segments
                x = self.player.center_x + (self.hook.center_x - self.player.center_x) * t
                y = self.player.center_y + (self.hook.center_y - self.player.center_y) * t
                arcade.draw_circle_filled(x, y, 4, arcade.color.GRAY)

    def on_draw(self):
        self.clear()

        # ------------------------
        # Фон воды
        # ------------------------
        water_height = 230
        arcade.draw_lrbt_rectangle_filled(
            0, SCREEN_WIDTH,
            0, water_height,
            arcade.color.LIGHT_BLUE
        )

        # ------------------------
        # ВОЛНЫ
        # ------------------------
        wave_top = water_height
        wave_spacing_x = 60
        wave_spacing_y = 30
        wave_amplitude = 5
        wave_length = 0.05

        num_rows = wave_top // wave_spacing_y
        for row in range(num_rows):
            y_offset = row * wave_spacing_y
            for x in range(0, SCREEN_WIDTH, wave_spacing_x):
                start_y = y_offset + math.sin((x * wave_length) + self.timer) * wave_amplitude
                end_x = x + wave_spacing_x
                end_y = y_offset + math.sin((end_x * wave_length) + self.timer) * wave_amplitude
                arcade.draw_line(
                    x, start_y,
                    end_x, end_y,
                    arcade.color.SKY_BLUE,
                    2
                )

        # ------------------------
        # Игровые объекты
        # ------------------------
        self.player_list.draw()
        self.fish_list.draw()
        self.hook_list.draw()
        self.draw_chain()

        # ------------------------
        # Худ
        # ------------------------
        arcade.draw_text(f"Очки: {self.score}", 10, SCREEN_HEIGHT - 30,
                         arcade.color.WHITE, 16)
        arcade.draw_text(f"Время: {int(self.timer)}", 10, SCREEN_HEIGHT - 60,
                         arcade.color.WHITE, 16)

    def on_update(self, delta_time):
        self.timer -= delta_time
        if self.timer <= 0:
            save_record(self.score)
            self.window.show_view(GameOverView(self.score))
            return

        if random.random() < 0.02:
            self.spawn_fish()

        if self.move_left:
            self.player.center_x -= PLAYER_SPEED
        if self.move_right:
            self.player.center_x += PLAYER_SPEED

        self.player.center_x = max(30, min(SCREEN_WIDTH - 30, self.player.center_x))

        self.fish_list.update()

        delivered = self.hook.update()
        if delivered:
            self.score += 1

        if self.hook.state == HookState.FLYING and self.hook.caught_fish is None:
            hits = arcade.check_for_collision_with_list(self.hook, self.fish_list)
            if hits:
                fish = hits[0]
                fish.caught = True
                self.hook.caught_fish = fish
                self.hook.state = HookState.RETURNING
                arcade.play_sound(self.sound_catch)  # Звук при поимке рыбы

        if self.hook.caught_fish:
            self.hook.caught_fish.center_x = self.hook.center_x
            self.hook.caught_fish.center_y = self.hook.center_y

    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.move_left = True
        elif key == arcade.key.RIGHT:
            self.move_right = True
        elif key == arcade.key.SPACE:
            self.hook.fire(self.player.center_x, self.player.center_y)
            arcade.play_sound(self.sound_hook)  # Воспроизводим звук при запуске крючка
        elif key == arcade.key.ESCAPE:
            self.window.show_view(PauseView(self))

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.move_left = False
        elif key == arcade.key.RIGHT:
            self.move_right = False


# ============================================================
#                     ПАУЗА
# ============================================================

class PauseView(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view

    def on_draw(self):
        self.clear()
        arcade.draw_text("ПАУЗА", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40,
                          arcade.color.WHITE, 40, anchor_x="center")
        arcade.draw_text("ESC — Продолжить", SCREEN_WIDTH//2, SCREEN_HEIGHT//2,
                          arcade.color.GRAY, 20, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(self.game_view)


# ============================================================
#                     GAME OVER
# ============================================================

class GameOverView(arcade.View):
    def __init__(self, score):
        super().__init__()
        self.score = score

    def on_draw(self):
        self.clear()
        arcade.draw_text("GAME OVER", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60,
                          arcade.color.RED, 40, anchor_x="center")
        arcade.draw_text(f"Очки: {self.score}", SCREEN_WIDTH//2, SCREEN_HEIGHT//2,
                          arcade.color.WHITE, 24, anchor_x="center")
        arcade.draw_text("ENTER — В меню", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60,
                          arcade.color.GRAY, 18, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            self.window.show_view(MenuView())


# ============================================================
#                     МЕНЮ
# ============================================================

class MenuView(arcade.View):
    def on_draw(self):
        self.clear()
        arcade.draw_text("PUDGE FISHING", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100,
                          arcade.color.ORANGE, 40, anchor_x="center")
        arcade.draw_text("ENTER — Играть", SCREEN_WIDTH//2, SCREEN_HEIGHT//2,
                          arcade.color.WHITE, 22, anchor_x="center")
        arcade.draw_text(f"Рекорд: {load_record()}",
                          SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50,
                          arcade.color.GRAY, 18, anchor_x="center")
        arcade.draw_text("ESC — Закрыть игру", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100,
                          arcade.color.RED, 18, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            self.window.show_view(LevelSelectView())  # Переход к выбору уровня
        elif key == arcade.key.ESCAPE:
            arcade.close_window()  # Закрыть игру


# ============================================================
#                     ЭКРАН ВЫБОРА УРОВНЯ
# ============================================================

class LevelSelectView(arcade.View):
    def on_draw(self):
        self.clear()
        arcade.draw_text("Выберите уровень", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100,
                          arcade.color.ORANGE, 40, anchor_x="center")
        arcade.draw_text("1 — Обычный уровень", SCREEN_WIDTH//2, SCREEN_HEIGHT//2,
                          arcade.color.WHITE, 22, anchor_x="center")
        arcade.draw_text("2 — Уровень с быстрыми рыбами", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50,
                          arcade.color.WHITE, 22, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.NUM_1:
            self.window.show_view(GameView(level=1))  # обычный уровень
        elif key == arcade.key.NUM_2:
            self.window.show_view(GameView(level=2))  # уровень с быстрыми рыбами


# ============================================================
#                     ЗАПУСК
# ============================================================

window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
window.show_view(MenuView())
arcade.run()
