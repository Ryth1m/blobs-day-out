import math
import random
import colorsys
import pygame
import array
from typing import Optional, Dict, Any, List

# ---------------------------------------------------------------------------
# Constants & Helpers
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 1280, 720
PLAYER_SPEED = 2.0

def hsv_to_rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
    return int(r * 255), int(g * 255), int(b * 255)

def darken(color, factor=0.65):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))

def lighten(color, factor=1.15):
    return (min(255, int(color[0] * factor)), min(255, int(color[1] * factor)), min(255, int(color[2] * factor)))

def clamp(val, lo, hi):
    return lo if val < lo else hi if val > hi else val

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)), int(lerp(c1[1], c2[1], t)), int(lerp(c1[2], c2[2], t)))

# ---------------------------------------------------------------------------
# Sound System
# ---------------------------------------------------------------------------
class SoundManager:
    def __init__(self):
        self.sounds: Dict[str, Any] = {}
        self._generate_all()
    
    def _make_sound(self, freq_env, duration, volume=0.2):
        sample_rate = 22050
        n = int(sample_rate * duration)
        buf = array.array('h')
        for i in range(n):
            t = i / sample_rate
            p = i / n
            freq, amp = freq_env(t, p)
            val = int(amp * 12000 * math.sin(2 * math.pi * freq * t))
            buf.append(clamp(val, -32767, 32767))
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(volume)
        return sound
    
    def _generate_all(self):
        def happy_env(t, p):
            freqs =[523, 659, 784]
            idx = min(2, int(p * 3))
            return freqs[idx], max(0, 1 - p * 1.5)
        self.sounds["happy"] = self._make_sound(happy_env, 0.3, 0.2)
        
        def sad_env(t, p):
            return 350 - p * 100, max(0, 1 - p * 1.2)
        self.sounds["sad"] = self._make_sound(sad_env, 0.4, 0.18)
        
        def pop_env(t, p):
            return 800 * (1 - p * 0.5), max(0, 1 - p * 8)
        self.sounds["pop"] = self._make_sound(pop_env, 0.08, 0.2)
        
        def munch_env(t, p):
            return 150 + random.random() * 100, max(0, 1 - p * 5) * 0.7
        self.sounds["munch"] = self._make_sound(munch_env, 0.1, 0.15)
        
        def bell_env(t, p):
            return 700 + math.sin(p * 15) * 80, max(0, 1 - p) * 0.6
        self.sounds["bell"] = self._make_sound(bell_env, 0.8, 0.15)
        
        random.seed(99)
        def splash_env(t, p):
            return 200 + random.random() * 300, max(0, 1 - p * 3) * 0.8
        self.sounds["splash"] = self._make_sound(splash_env, 0.15, 0.18)
        random.seed()
        
        def type_env(t, p):
            return 1200 - p * 400, max(0, 1 - p * 15)
        self.sounds["type"] = self._make_sound(type_env, 0.03, 0.08)
        
        def sparkle_env(t, p):
            return 1500 + math.sin(p * 20) * 200, max(0, 1 - p * 2) * 0.6
        self.sounds["sparkle"] = self._make_sound(sparkle_env, 0.25, 0.15)
        
        random.seed(77)
        def whoosh_env(t, p):
            return 300 + p * 200 + random.random() * 50, max(0, math.sin(p * math.pi)) * 0.5
        self.sounds["whoosh"] = self._make_sound(whoosh_env, 0.3, 0.12)
        random.seed()
        
        self.sounds["footsteps"] =[]
        for j in range(4):
            random.seed(j * 42)
            def foot_env(t, p, j=j):
                return 80 + j * 15 + random.random() * 40, max(0, 1 - p * 8) * 0.5
            self.sounds["footsteps"].append(self._make_sound(foot_env, 0.07, 0.1))
            random.seed()
    
    def play(self, name):
        if name == "footstep":
            random.choice(self.sounds["footsteps"]).play()
        elif name in self.sounds:
            self.sounds[name].play()

# ---------------------------------------------------------------------------
# Typing Text System
# ---------------------------------------------------------------------------
class TypingText:
    def __init__(self, sounds: SoundManager):
        self.text = ""
        self.display_text = ""
        self.char_index = 0
        self.timer = 0
        self.char_delay = 2
        self.active = False
        self.duration = 0
        self.sounds = sounds
    
    def show(self, text: str, duration: int = 180):
        self.text = text
        self.display_text = ""
        self.char_index = 0
        self.timer = 0
        self.active = True
        self.duration = duration
    
    def update(self):
        if not self.active: return
        
        if self.char_index < len(self.text):
            self.timer += 1
            if self.timer >= self.char_delay:
                self.timer = 0
                self.display_text += self.text[self.char_index]
                self.char_index += 1
                if self.char_index > 0 and self.text[self.char_index - 1] not in " \n":
                    self.sounds.play("type")
        else:
            self.duration -= 1
            if self.duration <= 0:
                self.active = False
    
    def draw(self, screen: pygame.Surface, x: int, y: int, font: pygame.font.Font):
        if not self.active or not self.display_text: return
        
        text_surf = font.render(self.display_text, True, (55, 45, 40))
        pad = 14
        bub_w = text_surf.get_width() + pad * 2
        bub_h = text_surf.get_height() + pad * 2
        bub_x = clamp(x - bub_w // 2, 10, WIDTH - bub_w - 10)
        bub_y = max(10, y - bub_h - 25)
        
        pygame.draw.ellipse(screen, (255, 252, 245), (bub_x - 5, bub_y - 3, bub_w + 10, bub_h + 6))
        pygame.draw.ellipse(screen, (180, 165, 140), (bub_x - 5, bub_y - 3, bub_w + 10, bub_h + 6), 2)
        pygame.draw.circle(screen, (255, 252, 245), (x - 8, y - 12), 7)
        pygame.draw.circle(screen, (180, 165, 140), (x - 8, y - 12), 7, 1)
        pygame.draw.circle(screen, (255, 252, 245), (x - 15, y - 2), 5)
        pygame.draw.circle(screen, (180, 165, 140), (x - 15, y - 2), 5, 1)
        
        screen.blit(text_surf, (bub_x + pad, bub_y + pad))
        if self.char_index < len(self.text) and pygame.time.get_ticks() % 400 < 200:
            pygame.draw.rect(screen, (80, 70, 60), (bub_x + pad + text_surf.get_width() + 2, bub_y + pad, 2, text_surf.get_height()))

# ---------------------------------------------------------------------------
# Blob Class
# ---------------------------------------------------------------------------
class Blob:
    EXPRESSIONS =["happy", "confused", "sad", "excited", "thinking", "focus", "proud", "neutral", "surprised", "sleepy"]
    
    def __init__(self, x=400, y=300, cfg: Optional[Dict[str, Any]] = None):
        self.x = float(x)
        self.y = float(y)
        self.coins = 0
        self.cfg: Dict[str, Any] = {"hue": 0.08, "eyes": 2, "outline": 3, "size_factor": 5.5}
        if cfg: self.cfg.update(cfg)
        
        self.speed = PLAYER_SPEED
        self.vx = self.speed
        self.z = 0.0
        self.vz = 0.0
        self.is_jumping = False
        self.landing_timer = 0
        self.walk_cycle = 0.0
        self.is_walking = True
        
        self.expression = "happy"
        self.expr_timer = 0
        self.default_expression = "happy"
        self.blink_timer = random.randint(100, 180)
        self.is_blinking = False
        self.blink_duration = 8
        
        self.held_item: Optional[str] = None
        self.held_item_state: Dict[str, Any] = {}
        
        self.look_up = False
        self.look_up_timer = 0
        self.sitting = False
        
        self.angle = 0.0
        self.extra_stretch_x = 0.0
        self.extra_stretch_y = 0.0
        self.shake = 0
    
    def set_expression(self, expr: str, duration: int = 0):
        if expr in self.EXPRESSIONS:
            self.expression = expr
            self.expr_timer = duration
    
    def set_default_expression(self, expr: str):
        if expr in self.EXPRESSIONS:
            self.default_expression = expr
            self.expression = expr
    
    def update(self):
        if self.is_blinking:
            self.blink_timer -= 1
            if self.blink_timer <= 0:
                self.is_blinking = False
                self.blink_timer = random.randint(100, 180)
        else:
            self.blink_timer -= 1
            if self.blink_timer <= 0:
                self.is_blinking = True
                self.blink_timer = self.blink_duration
        
        if self.expr_timer > 0:
            self.expr_timer -= 1
            if self.expr_timer <= 0:
                self.expression = self.default_expression
        
        self.is_walking = abs(self.vx) > 0.1 and not self.sitting
        if self.is_walking:
            self.walk_cycle += abs(self.vx) * 0.1
        
        if self.look_up_timer > 0:
            self.look_up_timer -= 1
            self.look_up = True
        else:
            self.look_up = False
        
        if self.is_jumping:
            self.vz += 0.7
            self.z += self.vz
            if self.z >= 0:
                self.z = 0
                self.vz = 0
                self.is_jumping = False
                self.landing_timer = 10
        elif self.landing_timer > 0:
            self.landing_timer -= 1
    
    def jump(self):
        if not self.is_jumping and self.landing_timer == 0 and not self.sitting:
            self.vz = -10
            self.is_jumping = True
    
    def hold_item(self, item_type: str, **kwargs):
        self.held_item = item_type
        self.held_item_state = kwargs
    
    def drop_item(self):
        self.held_item = None
        self.held_item_state = {}
    
    def draw(self, screen):
        hue = self.cfg["hue"]
        rad = int(12.0 * self.cfg["size_factor"])
        
        sx = int(self.x) + random.randint(-self.shake, self.shake)
        sy = int(self.y) + random.randint(-self.shake, self.shake)
        
        body_col = hsv_to_rgb(hue, 0.35, 0.95)
        walk_bob = math.sin(self.walk_cycle) * 5 if self.is_walking else 0
        
        shadow_scale = max(0.4, 1.0 - abs(self.z) / 120)
        shadow_w = int(rad * 1.8 * shadow_scale)
        shadow_h = int(rad * 0.5 * shadow_scale)
        shadow_surf = pygame.Surface((shadow_w + 4, shadow_h + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, int(35 * shadow_scale)), (2, 2, shadow_w, shadow_h))
        screen.blit(shadow_surf, (sx - shadow_w // 2, sy + int(rad * 0.5)))
        
        blob_surf = pygame.Surface((rad * 3, rad * 3), pygame.SRCALPHA)
        cx, cy = int(rad * 1.5), int(rad * 1.5)
        
        pygame.draw.circle(blob_surf, body_col, (cx, cy), rad)
        pygame.draw.circle(blob_surf, darken(body_col, 0.5), (cx, cy), rad, self.cfg["outline"])
        pygame.draw.circle(blob_surf, lighten(body_col, 1.1), (cx, cy), max(1, rad - 4), 1)
        
        gloss = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(gloss, (255, 255, 255, 50), (int(rad * 0.3), int(rad * 0.15), int(rad * 0.65), int(rad * 0.35)))
        blob_surf.blit(gloss, (cx - rad, cy - rad))
        
        self._draw_eyes(blob_surf, cx, cy, rad, body_col)
        
        t = pygame.time.get_ticks()
        stretch_x = 1.0 + math.sin(t / 300) * 0.02 + self.extra_stretch_x
        stretch_y = 1.0 - math.sin(t / 300) * 0.01 + self.extra_stretch_y
        
        if self.is_walking:
            ws = math.sin(self.walk_cycle * 2) * 0.05
            stretch_x += ws
            stretch_y -= ws * 0.5
        if self.sitting:
            stretch_x += 0.1
            stretch_y -= 0.1
        if self.is_jumping:
            vs = min(0.18, abs(self.vz) * 0.012)
            stretch_y += vs
            stretch_x -= vs * 0.5
        elif self.landing_timer > 0:
            f = math.sin((10 - self.landing_timer) / 10 * math.pi)
            stretch_x += f * 0.18
            stretch_y -= f * 0.18
            
        new_w = max(1, int(rad * 3 * stretch_x))
        new_h = max(1, int(rad * 3 * stretch_y))
        scaled = pygame.transform.smoothscale(blob_surf, (new_w, new_h))
        
        rotated = pygame.transform.rotate(scaled, self.angle)
        
        base_y = sy + rad + self.z + walk_bob
        blit_x = sx - rotated.get_width() // 2
        blit_y = base_y - int(new_h * (2.5 / 3.0)) - (rotated.get_height() - new_h)//2
        screen.blit(rotated, (blit_x, int(blit_y)))
        
        if self.held_item is not None:
            self._draw_held_item(screen, sx, sy + self.z + walk_bob, rad)
    
    def _draw_held_item(self, screen, x, y, rad):
        item = self.held_item
        state = self.held_item_state
        if item == "icecream": self._draw_icecream(screen, x + rad + 12, y - rad // 2, state.get("bites", 0))
        elif item == "flower": self._draw_flower(screen, x + rad + 8, y - rad // 2)
        elif item == "balloon": self._draw_balloon(screen, x + rad, y - rad, state.get("color", (255, 100, 120)))
        elif item == "umbrella": self._draw_umbrella(screen, x, y - rad * 2, state.get("color", (255, 100, 100)))
        elif item == "coffee": self._draw_coffee(screen, x + rad + 10, y - rad // 3)
        elif item == "book": self._draw_book(screen, x + rad + 8, y - rad // 3)
        elif item == "camera": self._draw_camera(screen, x + rad + 5, y - rad // 2)
        elif item == "apple": self._draw_apple(screen, x + rad + 8, y - rad // 3)
        elif item == "fishing_rod": self._draw_fishing_rod(screen, x + rad + 5, y - rad)
        elif item == "scarf": self._draw_scarf(screen, x, y + rad // 4, rad)
    
    def _draw_icecream(self, screen, x, y, bites=0):
        cone = (220, 180, 120)
        pygame.draw.polygon(screen, cone,[(x - 14, y), (x + 14, y), (x, y + 45)])
        pygame.draw.polygon(screen, darken(cone, 0.8),[(x - 14, y), (x + 14, y), (x, y + 45)], 2)
        for i in range(4): pygame.draw.line(screen, darken(cone, 0.85), (x - 12 + i * 5, y + 5), (x - 4 + i * 5, y + 38), 1)
        colors =[(255, 180, 200), (180, 130, 90), (255, 255, 200)]
        for i in range(max(0, 3 - bites)):
            sy = y - 12 - i * 20
            pygame.draw.circle(screen, colors[i], (x, sy), 18 - i * 2)
            pygame.draw.circle(screen, lighten(colors[i], 1.2), (x - 5, sy - 5), 6)
    
    def _draw_flower(self, screen, x, y):
        pygame.draw.line(screen, (80, 150, 70), (x, y), (x, y + 40), 3)
        pygame.draw.ellipse(screen, (90, 170, 80), (x - 8, y + 15, 10, 6))
        pygame.draw.ellipse(screen, (90, 170, 80), (x, y + 25, 10, 6))
        for i in range(6):
            ang = i * 60
            px = x + int(math.cos(math.radians(ang)) * 14)
            py = y + int(math.sin(math.radians(ang)) * 14)
            pygame.draw.circle(screen, (255, 180, 200), (px, py), 9)
        pygame.draw.circle(screen, (255, 220, 100), (x, y), 8)
    
    def _draw_balloon(self, screen, x, y, color):
        sway = math.sin(pygame.time.get_ticks() / 300) * 10
        bx, by = x + sway, y - 90
        pygame.draw.line(screen, (150, 150, 155), (x, y + 35), (bx + 5, by + 45), 2)
        pygame.draw.ellipse(screen, color, (bx - 18, by, 46, 55))
        pygame.draw.ellipse(screen, lighten(color, 1.3), (bx - 8, by + 8, 14, 18))
        pygame.draw.polygon(screen, color,[(bx + 3, by + 53), (bx + 13, by + 53), (bx + 8, by + 62)])
    
    def _draw_umbrella(self, screen, x, y, color):
        # Stick — top to bottom
        pygame.draw.line(screen, (120, 85, 60), (x, y), (x, y + 52), 4)
        # Hook at bottom — arc that starts exactly where stick ends
        pygame.draw.arc(screen, (120, 85, 60), (x - 10, y + 44, 20, 18), math.pi, 2 * math.pi, 4)
        # Canopy
        pygame.draw.ellipse(screen, color, (x - 55, y - 38, 110, 45))
        pygame.draw.ellipse(screen, lighten(color, 1.15), (x - 35, y - 32, 30, 22))
        # Canopy edge scallops
        for i in range(5):
            scal_x = x - 44 + i * 22
            pygame.draw.arc(screen, darken(color, 0.85), (scal_x, y + 3, 22, 12), math.pi, 2 * math.pi, 2)
    
    def _draw_coffee(self, screen, x, y):
        pygame.draw.rect(screen, (255, 255, 250), (x - 12, y, 26, 32), border_radius=4)
        pygame.draw.rect(screen, (220, 215, 210), (x - 12, y, 26, 32), 2, border_radius=4)
        pygame.draw.ellipse(screen, (110, 80, 55), (x - 9, y + 5, 20, 10))
        pygame.draw.arc(screen, (220, 215, 210), (x + 10, y + 8, 14, 16), -1.5, 1.5, 3)
        t = pygame.time.get_ticks() / 200
        for i in range(3):
            steam_y = y - 8 - (t + i * 4) % 18
            steam_x = x + 1 + math.sin(t + i * 2) * 5
            alpha = max(0, 160 - int((y - steam_y) * 12))
            if alpha > 0:
                steam = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(steam, (255, 255, 255, alpha // 2), (5, 5), 4)
                screen.blit(steam, (int(steam_x) - 5, int(steam_y) - 5))
    
    def _draw_book(self, screen, x, y):
        bob = math.sin(pygame.time.get_ticks() / 150) * 3
        y += bob
        pygame.draw.rect(screen, (180, 80, 80), (x - 15, y, 30, 38), border_radius=2)
        pygame.draw.rect(screen, (160, 65, 65), (x - 15, y, 30, 38), 2, border_radius=2)
        pygame.draw.rect(screen, (255, 250, 240), (x - 12, y + 3, 24, 32))
        for i in range(4): pygame.draw.line(screen, (200, 195, 185), (x - 10, y + 8 + i * 7), (x + 10, y + 8 + i * 7), 1)
    
    def _draw_camera(self, screen, x, y):
        pygame.draw.rect(screen, (60, 60, 65), (x - 18, y, 36, 26), border_radius=4)
        pygame.draw.rect(screen, (50, 50, 55), (x - 18, y, 36, 26), 2, border_radius=4)
        pygame.draw.circle(screen, (40, 40, 45), (x, y + 14), 10)
        pygame.draw.circle(screen, (80, 120, 160), (x, y + 14), 7)
        pygame.draw.circle(screen, (120, 160, 200), (x - 2, y + 12), 3)
        pygame.draw.rect(screen, (70, 70, 75), (x - 8, y - 6, 16, 8), border_radius=2)
    
    def _draw_apple(self, screen, x, y):
        pygame.draw.circle(screen, (220, 60, 60), (x, y + 12), 14)
        pygame.draw.circle(screen, (255, 100, 100), (x - 4, y + 8), 5)
        pygame.draw.line(screen, (100, 70, 50), (x, y - 2), (x + 2, y + 4), 3)
        pygame.draw.ellipse(screen, (100, 170, 80), (x + 2, y - 6, 10, 6))
    
    def _draw_fishing_rod(self, screen, x, y):
        pygame.draw.line(screen, (140, 100, 60), (x, y + 50), (x + 60, y - 30), 4)
        pygame.draw.line(screen, (180, 180, 185), (x + 60, y - 30), (x + 65, y + 20), 1)
    
    def _draw_scarf(self, screen, x, y, rad):
        color = (220, 80, 80)
        dark = darken(color, 0.82)
        sway = math.sin(pygame.time.get_ticks() / 200) * 8
        # Main wrap around the lower body
        pygame.draw.ellipse(screen, color, (x - rad + 2, y - 8, (rad - 2) * 2, 18))
        pygame.draw.ellipse(screen, dark, (x - rad + 2, y - 8, (rad - 2) * 2, 18), 2)
        # Highlight stripe
        pygame.draw.ellipse(screen, lighten(color, 1.2), (x - rad + 6, y - 5, (rad - 6) * 2, 8))
        # Tail hanging down, swaying
        pygame.draw.rect(screen, color, (x + rad // 2 - 6, y + 6, 11, 28), border_radius=3)
        pygame.draw.polygon(screen, dark, [
            (x + rad // 2 - 6, y + 30),
            (x + rad // 2 + 5, y + 30),
            (x + rad // 2 + 5 + sway, y + 48),
            (x + rad // 2 - 6 + sway, y + 48)
        ])
    
    def _draw_eyes(self, surf, cx, cy, size, body_col):
        look_y = -0.5 if self.look_up else 0
        fcx, fcy = cx + int(size * 0.35), cy + int(look_y * size * 0.2)
        sep, eye_r = size * 0.28, max(5, int(size * 0.18))
        pupil_r = max(3, int(eye_r * 0.5))
        eyes =[(int(fcx - sep), fcy), (int(fcx + sep), fcy)]
        WHITE, BLACK = (255, 255, 255), (30, 30, 35)
        
        if self.is_blinking:
            for ex, ey in eyes: pygame.draw.line(surf, BLACK, (ex - eye_r, int(ey)), (ex + eye_r, int(ey)), 2)
            return
        
        pox, poy = int(eye_r * 0.3), int(look_y * eye_r * 0.5)
        expr = self.expression
        
        if expr in["neutral", "focus"]:
            for ex, ey in eyes:
                pygame.draw.circle(surf, WHITE, (ex, int(ey)), eye_r)
                pygame.draw.circle(surf, BLACK, (ex, int(ey)), eye_r, 2)
                pygame.draw.circle(surf, BLACK, (ex + pox, int(ey + poy)), pupil_r)
                pygame.draw.circle(surf, WHITE, (ex - int(eye_r * 0.2), int(ey - eye_r * 0.2)), max(1, int(eye_r * 0.18)))
        
        elif expr == "happy":
            for ex, ey in eyes:
                pygame.draw.circle(surf, WHITE, (ex, int(ey)), eye_r)
                pygame.draw.circle(surf, BLACK, (ex, int(ey)), eye_r, 2)
                pygame.draw.circle(surf, BLACK, (ex + pox, int(ey + poy)), pupil_r)
                bot = int(ey + eye_r * 0.3)
                pygame.draw.rect(surf, body_col, (ex - eye_r - 2, bot, eye_r * 2 + 4, eye_r))
                pygame.draw.line(surf, darken(body_col, 0.5), (ex - eye_r, bot), (ex + eye_r, bot), 2)
        
        elif expr == "sad":
            for i, (ex, ey) in enumerate(eyes):
                pygame.draw.circle(surf, WHITE, (ex, int(ey)), eye_r)
                pygame.draw.circle(surf, BLACK, (ex, int(ey)), eye_r, 2)
                pygame.draw.circle(surf, BLACK, (ex + pox, int(ey + poy + 2)), pupil_r)
                iy, oy = int(ey - eye_r * 0.5), int(ey + eye_r * 0.1)
                pts =[(ex - eye_r - 2, int(ey - eye_r - 2)), (ex + eye_r + 2, int(ey - eye_r - 2)), (ex + eye_r + 2, iy), (ex - eye_r - 2, oy)] if i == 0 else[(ex - eye_r - 2, int(ey - eye_r - 2)), (ex + eye_r + 2, int(ey - eye_r - 2)), (ex + eye_r + 2, oy), (ex - eye_r - 2, iy)]
                pygame.draw.polygon(surf, body_col, pts)
                pygame.draw.line(surf, darken(body_col, 0.5), pts[2], pts[3], 2)
        
        elif expr in["excited", "surprised"]:
            er, pr = int(eye_r * 1.2), max(2, int(pupil_r * 0.6))
            for ex, ey in eyes:
                pygame.draw.circle(surf, WHITE, (ex, int(ey)), er)
                pygame.draw.circle(surf, BLACK, (ex, int(ey)), er, 2)
                pygame.draw.circle(surf, BLACK, (ex, int(ey)), pr)
                pygame.draw.circle(surf, WHITE, (ex - int(er * 0.25), int(ey - er * 0.25)), max(1, int(er * 0.22)))
        
        elif expr == "thinking":
            for ex, ey in eyes:
                pygame.draw.circle(surf, WHITE, (ex, int(ey)), eye_r)
                pygame.draw.circle(surf, BLACK, (ex, int(ey)), eye_r, 2)
                pygame.draw.circle(surf, BLACK, (ex + int(eye_r * 0.3), int(ey - eye_r * 0.3)), pupil_r)
                ty = int(ey - eye_r * 0.35)
                pygame.draw.rect(surf, body_col, (ex - eye_r - 2, int(ey - eye_r - 2), eye_r * 2 + 4, ty - int(ey - eye_r)))
                pygame.draw.line(surf, darken(body_col, 0.5), (ex - eye_r, ty), (ex + eye_r, ty), 2)
        
        elif expr == "proud":
            for ex, ey in eyes: pygame.draw.arc(surf, BLACK, (ex - eye_r, int(ey - eye_r // 2), eye_r * 2, eye_r), 0, math.pi, 2)
        
        elif expr == "sleepy":
            for ex, ey in eyes: pygame.draw.line(surf, BLACK, (ex - eye_r, int(ey + 2)), (ex + eye_r, int(ey + eye_r * 0.2)), 3)
        
        elif expr == "confused":
            for i, (ex, ey) in enumerate(eyes):
                pygame.draw.circle(surf, WHITE, (ex, int(ey)), eye_r)
                pygame.draw.circle(surf, BLACK, (ex, int(ey)), eye_r, 2)
                pygame.draw.circle(surf, BLACK, (ex + pox, int(ey + poy)), pupil_r)
                ty = int(ey - eye_r * 0.1) if i == 0 else int(ey - eye_r * 0.6)
                rh = ty - int(ey - eye_r - 2)
                if rh > 0:
                    pygame.draw.rect(surf, body_col, (ex - eye_r - 2, int(ey - eye_r - 2), eye_r * 2 + 4, rh))
                    pygame.draw.line(surf, darken(body_col, 0.5), (ex - eye_r, ty), (ex + eye_r, ty), 2)
    
    def get_head_pos(self):
        size = 12.0 * self.cfg["size_factor"]
        wb = math.sin(self.walk_cycle) * 5 if self.is_walking else 0
        return int(self.x), int(self.y + self.z + wb - size * 1.2)

# ---------------------------------------------------------------------------
# Event System (Advanced Animations)
# ---------------------------------------------------------------------------
class Event:
    def __init__(self, etype: str, duration: int):
        self.type = etype
        self.duration = duration
        self.timer = 0
        self.phase = 0
        self.data: Dict[str, Any] = {}
    def update(self):
        self.timer += 1
        return self.timer < self.duration

class EventManager:
    def __init__(self, blob: Blob, sounds: SoundManager, typing_text: TypingText):
        self.blob = blob
        self.sounds = sounds
        self.typing = typing_text
        self.event: Optional[Event] = None
        self.cooldown = 60
        self.particles: List[Dict[str, Any]] =[]
        self.night_alpha = 0.0
        
        self.events =[
            ("icecream", 15), ("butterfly", 10), ("flower", 15), ("coin", 12),
            ("balloon", 10), ("rain", 7), ("sleepy", 8), ("coffee", 10),
            ("bird_poop", 4), ("trip", 5), ("sing", 8), ("leaf_head", 8),
            ("rainbow", 5), ("squirrel", 8), ("apple", 8), ("photo", 7),
            ("gift", 6), ("shooting_star", 6), ("frog", 7), ("fishing", 6),
            ("puddle", 8), ("cold", 6), ("book", 8), ("bee", 15),
            ("sit_rest", 7), ("dandelion", 9), ("acorn", 8),
        ]
    
    def update(self):
        for p in self.particles:
            p["y"] += p.get("vy", 0)
            p["x"] += p.get("vx", 0)
            p["vy"] = p.get("vy", 0) + p.get("gravity", 0)
            p["life"] -= 1
        self.particles =[p for p in self.particles if p["life"] > 0]
        
        if self.event and self.event.type == "shooting_star":
            if self.event.timer < 60: self.night_alpha = min(200.0, self.night_alpha + 3.5)
            elif self.event.duration - self.event.timer < 60: self.night_alpha = max(0.0, self.night_alpha - 3.5)
        else:
            self.night_alpha = max(0.0, self.night_alpha - 2.0)
        
        if self.event:
            if not self.event.update(): self._end_event()
            else: self._process_event()
            return
            
        if self.cooldown > 0:
            self.cooldown -= 1
            return
            
        if random.random() < 0.006:
            r = random.uniform(0, sum(w for _, w in self.events))
            cumul = 0
            for etype, weight in self.events:
                cumul += weight
                if r <= cumul:
                    self._start_event(etype)
                    break
    
    def _start_event(self, etype: str):
        e = Event(etype, 300)
        
        # We explicitly map ALL data attributes here to prevent KeyErrors
        if etype == "icecream":
            e.duration = 700
            e.data["truck_x"] = -300.0          # starts OFF LEFT edge
            e.data["truck_speed"] = 4.0
            outcome = random.choice(["eat", "drop", "miss"])
            e.data["outcome"] = outcome          # "eat" / "drop" / "miss"
            e.data["bites"] = 0
            e.data["drop_done"] = False
            self.sounds.play("bell")
            self.typing.show("Is that... an ice cream truck?!", 120)
            self.blob.set_expression("surprised", 80)
        elif etype == "butterfly":
            e.duration = 350
            e.data["x"], e.data["y"], e.data["landed"] = WIDTH + 100, -50, False
            self.blob.look_up_timer, self.blob.expression = 250, "excited"
            self.typing.show("A butterfly!")
        elif etype == "flower":
            e.duration, e.data["x"], e.data["picked"], e.data["scale"] = 400, WIDTH + 100, False, 0.0
            self.blob.set_expression("neutral", 60)
        elif etype == "coin":
            e.duration, e.data["x"], e.data["collected"], e.data["y_off"] = 300, WIDTH + 100, False, 0
        elif etype == "balloon":
            e.duration = 450
            e.data["has"], e.data["fly_away"] = False, random.random() < 0.3
            e.data["color"] = random.choice([(255, 100, 120), (100, 180, 255), (255, 220, 100), (180, 255, 180)])
            e.data["x"], e.data["y"] = WIDTH + 100, self.blob.y - 40
        elif etype == "rain":
            e.duration, e.data["drops"], e.data["has_umbrella"] = 550,[], False
            e.data["umbrella_color"] = random.choice([(255, 100, 100), (100, 150, 255), (255, 200, 100)])
            self.blob.set_expression("surprised", 80)
            self.typing.show("Oh no, rain!")
        elif etype == "sleepy":
            e.duration = 350
            self.blob.vx = self.blob.speed * 0.2
            self.blob.set_expression("sleepy", 300)
            self.typing.show("*yaaawn* So sleepy...")
        elif etype == "coffee":
            e.duration = 350
            self.blob.hold_item("coffee")
            self.blob.set_expression("happy", 120)
            self.typing.show("Coffee time!")
            self.sounds.play("happy")
        elif etype == "bird_poop":
            e.duration, e.data["poop_y"], e.data["hit"], e.data["scale"] = 220, -100, False, 1.0
        elif etype == "trip":
            e.duration = 180
            self.blob.set_expression("surprised", 40)
        elif etype == "sing":
            e.duration, e.data["notes"] = 300,[]
            self.blob.set_expression("happy", 250)
            self.typing.show("~ La la laaa ~")
        elif etype == "leaf_head":
            e.duration, e.data["leaf_y"], e.data["leaf_x"], e.data["on_head"] = 250, -100, WIDTH + 100, False
        elif etype == "rainbow":
            e.duration, e.data["alpha"], e.data["scale"] = 400, 0, 0.8
            self.blob.look_up_timer = 300
            self.blob.set_expression("excited", 200)
            self.typing.show("Wow! A rainbow!")
            self.sounds.play("sparkle")
        elif etype == "squirrel":
            e.duration, e.data["x"], e.data["y"] = 250, WIDTH + 100, self.blob.y + 10
        elif etype == "apple":
            e.duration, e.data["falling"], e.data["y"], e.data["vy"], e.data["bounces"] = 280, True, -100, 0, 0
            e.data["x"] = WIDTH + 50
            e.data["rot_angle"] = 0
            self.blob.look_up_timer = 100
        elif etype == "photo":
            e.duration, e.data["flash"], e.data["polaroid_y"] = 250, 0, -100
            self.blob.hold_item("camera")
            self.blob.set_expression("happy", 150)
            self.typing.show("Selfie time!")
        elif etype == "gift":
            e.duration, e.data["opened"], e.data["x"] = 350, False, WIDTH + 100
        elif etype == "shooting_star":
            e.duration, e.data["x"], e.data["y"] = 450, WIDTH + 200, -50
            self.blob.look_up_timer = 350
            self.blob.set_expression("excited", 150)
            self.typing.show("A shooting star! Make a wish!")
        elif etype == "frog":
            e.duration, e.data["x"], e.data["y"] = 280, WIDTH + 100, self.blob.y + 20
            e.data["jumped"], e.data["jump_frame"] = False, 0
        elif etype == "fishing":
            e.duration, e.data["caught"], e.data["bobber_y"], e.data["rings"] = 450, False, 0,[]
            self.blob.hold_item("fishing_rod")
            self.blob.vx = 0
            self.blob.sitting = True
            self.blob.set_expression("focus", 300)
            self.typing.show("Let's try fishing...")
        elif etype == "puddle":
            e.duration, e.data["splashed"], e.data["ripple"], e.data["x"] = 250, False, 0, WIDTH + 100
        elif etype == "cold":
            e.duration, e.data["has_scarf"] = 350, False
            self.blob.set_expression("sad", 80)
            self.typing.show("Brrr... so cold...")
        elif etype == "book":
            e.duration = 380
            e.data["chapter"] = 0
            self.blob.hold_item("book")
            self.blob.set_expression("focus", 300)
            self.typing.show("Reading while walking~")
        elif etype == "bee":
            e.duration, e.data["x"], e.data["y"], e.data["phase_ang"] = 400, WIDTH + 100, self.blob.y - 80, 0.0
        elif etype == "sit_rest":
            e.duration = 400
            self.blob.vx = 0
            self.blob.sitting = True
            self.blob.set_expression("happy", 350)
            self.typing.show("Time for a little rest~")
        elif etype == "dandelion":
            e.duration, e.data["blown"], e.data["seeds"], e.data["x"] = 280, False,[], WIDTH + 100
        elif etype == "acorn":
            e.duration, e.data["y"], e.data["hit"], e.data["rot"], e.data["x"] = 220, -50, False, 0, WIDTH + 100
            self.blob.look_up_timer = 80
        
        self.event = e
    
    def _process_event(self):
        e = self.event
        if e is None: return
        p = e.timer / e.duration if e.duration > 0 else 1
        
        if e.type == "icecream":
            outcome = e.data["outcome"]

            if e.phase == 0:
                # Truck drives in from left
                e.data["truck_x"] += e.data["truck_speed"]
                if e.data["truck_x"] >= self.blob.x - 200:
                    e.phase, e.timer = 1, 0
                    self.typing.show("Wait for me!")
                    self.blob.set_expression("excited", 100)

            elif e.phase == 1:
                # Blob runs toward truck (which keeps moving right at reduced speed)
                e.data["truck_speed"] = 1.5
                e.data["truck_x"] += e.data["truck_speed"]
                self.blob.vx = self.blob.speed * 2.5

                if outcome == "miss":
                    # Truck speeds away after a moment
                    if e.timer > 40:
                        e.data["truck_speed"] = 6.0
                        e.phase, e.timer = 5, 0
                        self.typing.show("Wait! Come back...")
                        self.blob.set_expression("sad", 150)
                else:
                    # Blob catches up
                    if e.data["truck_x"] <= self.blob.x + 120:
                        self.blob.vx = 0
                        e.data["truck_speed"] = 0
                        e.phase, e.timer = 2, 0

            elif e.phase == 2:
                # At the window — ordering
                e.data["truck_x"] += self.blob.vx
                if e.timer == 10:
                    if self.blob.coins > 0:
                        self.typing.show("One ice cream! *pays coin*")
                        self.blob.coins -= 1
                        self.sounds.play("sparkle")
                    else:
                        self.typing.show("One ice cream, please!")
                if e.timer == 60:
                    self.sounds.play("pop")
                    self.blob.hold_item("icecream", bites=0)
                    self.blob.set_expression("happy", 200)
                    self.typing.show("Yay! So yummy!")
                if e.timer == 130:
                    e.phase, e.timer = 3, 0

            elif e.phase == 3:
                # Truck drives off right, blob walks and eats
                e.data["truck_speed"] = 3.0
                e.data["truck_x"] += e.data["truck_speed"]
                if e.timer > 20:
                    self.blob.vx = self.blob.speed

                if outcome == "drop":
                    # Drop at 50 frames in
                    if e.timer == 50 and not e.data["drop_done"]:
                        e.data["drop_done"] = True
                        self.blob.drop_item()
                        self.blob.set_expression("sad", 150)
                        self.typing.show("Nooo! I dropped it!")
                        self.sounds.play("splash")
                else:
                    # Eat it bite by bite
                    if e.timer > 40 and e.timer % 55 == 0 and e.data["bites"] < 3:
                        e.data["bites"] += 1
                        self.blob.held_item_state["bites"] = e.data["bites"]
                        self.sounds.play("munch")
                        if e.data["bites"] >= 3:
                            self.blob.drop_item()
                            self.blob.set_expression("happy", 120)
                            self.typing.show("Delicious!!")

            elif e.phase == 5:
                # Truck drove away — blob gives up
                e.data["truck_x"] += e.data["truck_speed"]
                if e.timer > 30:
                    self.blob.vx = self.blob.speed
                if e.timer > 130:
                    e.phase = 6
                    
        elif e.type == "flower":
            if e.phase == 0:
                e.data["x"] -= self.blob.vx
                e.data["scale"] = min(1.0, e.data["scale"] + 0.05)
                if e.data["x"] <= self.blob.x + 30:
                    e.phase, self.blob.vx, e.timer = 1, 0, 0
                    self.blob.set_expression("surprised", 80)
                    self.typing.show("Oh, a flower!")
            elif e.phase == 1:
                e.data["x"] -= self.blob.vx
                if e.timer > 100:
                    e.phase, e.data["picked"] = 2, True
                    self.blob.set_expression("happy", 100)
                    self.blob.hold_item("flower")
                    self.sounds.play("pop")
                    self.typing.show("So pretty!")
            elif e.phase == 2:
                if e.timer > 250: self.blob.vx = self.blob.speed
                    
        elif e.type == "coin":
            e.data["y_off"] = math.sin(e.timer / 8) * 6
            if e.phase == 0:
                e.data["x"] -= self.blob.vx
                if e.data["x"] <= self.blob.x + 60:
                    e.phase, self.blob.vx, e.timer = 1, 0, 0
                    self.blob.set_expression("surprised", 60)
                    self.typing.show("Ooh, shiny!")
            elif e.phase == 1:
                e.data["x"] -= self.blob.vx
                if e.timer > 40 and not e.data["collected"]:
                    e.data["collected"] = True
                    self.blob.coins += 1
                    self.sounds.play("happy")
                    self.blob.jump()
                    for _ in range(12):
                        self.particles.append({"x": e.data["x"], "y": self.blob.y + 20, "vx": random.uniform(-4, 4), "vy": random.uniform(-6, -2), "gravity": 0.25, "life": 45, "type": "sparkle", "color": (255, 230, 100)})
                if e.timer > 100:
                    self.blob.vx = self.blob.speed
                    e.phase = 2
                    
        elif e.type == "bee":
            if e.phase == 0:
                e.data["x"] -= (self.blob.vx + 2.5)
                e.data["y"] += math.sin(e.timer * 0.1) * 2
                if e.data["x"] <= self.blob.x + 80:
                    e.phase, self.blob.vx = 1, 0
                    self.blob.set_expression("surprised", 100)
                    self.typing.show("Oh! A little bee!")
            elif e.phase == 1:
                e.data["phase_ang"] += 0.06
                e.data["x"] = self.blob.x + math.cos(e.data["phase_ang"]) * 60
                e.data["y"] = self.blob.y - 40 + math.sin(e.data["phase_ang"] * 2) * 30
                self.blob.look_up = e.data["y"] < self.blob.y - 60
                if e.data["phase_ang"] > math.pi * 4:
                    e.phase, self.blob.vx = 2, self.blob.speed
                    self.typing.show("Bye bye bee~")
                    self.blob.set_expression("happy", 100)
            elif e.phase == 2:
                e.data["x"] += 4
                e.data["y"] -= 2
                
        elif e.type == "butterfly":
            if e.phase == 0:
                e.data["x"] -= (self.blob.vx + 1.5)
                e.data["y"] += math.sin(e.timer * 0.05) * 1.5
                if e.data["x"] <= self.blob.x + 60: e.phase = 1
            elif e.phase == 1:
                t = e.timer / 40
                e.data["x"] = self.blob.x + 60 + math.sin(t * 2) * 60
                e.data["y"] = self.blob.y - 70 + math.cos(t * 1.5) * 40
                if p > 0.55 and not e.data["landed"]:
                    e.data["landed"] = True
                    e.data["x"], e.data["y"] = self.blob.x + 25, self.blob.y - 85
                    self.blob.set_expression("proud", 120)
                    self.typing.show("It landed on me!")
                
        elif e.type == "balloon":
            if e.phase == 0:
                e.data["x"] -= self.blob.vx
                e.data["y"] += math.sin(e.timer * 0.1) * 0.5
                if e.data["x"] <= self.blob.x + 40:
                    e.phase, e.data["has"] = 1, True
                    self.blob.hold_item("balloon", color=e.data["color"])
                    self.blob.set_expression("happy", 120)
                    self.sounds.play("pop")
                    self.typing.show("A balloon!")
            elif e.phase == 1:
                if e.data["fly_away"] and p > 0.6:
                    e.phase = 2
                    self.blob.drop_item()
                    e.data["fly_y"], e.data["fly_x"] = self.blob.y - 90, self.blob.x + 40
                    self.blob.set_expression("sad", 120)
                    self.typing.show("Oh no, it flew away...")
                    self.sounds.play("sad")
            elif e.phase == 2:
                e.data["fly_y"] -= 2.5
                e.data["fly_x"] += math.sin(e.timer * 0.05) * 2 - self.blob.vx
                
        elif e.type == "rain":
            if random.random() < 0.4: e.data["drops"].append({"x": random.randint(-50, WIDTH + 100), "y": -10, "speed": random.uniform(12, 18)})
            for d in e.data["drops"]:
                d["y"] += d["speed"]
                d["x"] -= 2.5
                if d["y"] > HEIGHT - 100 and random.random() < 0.3:
                    self.particles.append({"x": d["x"], "y": HEIGHT - 100, "vx": random.uniform(-1, 1), "vy": random.uniform(-2, -1), "gravity": 0.2, "life": 15, "type": "water", "color": (160, 190, 230)})
            e.data["drops"] =[d for d in e.data["drops"] if d["y"] <= HEIGHT]
            if p > 0.22 and not e.data["has_umbrella"]:
                e.data["has_umbrella"] = True
                self.blob.hold_item("umbrella", color=e.data["umbrella_color"])
                self.blob.set_expression("happy", 120)
                self.typing.show("Phew, umbrella!")
                
        elif e.type == "sleepy":
            if p < 0.85:
                # Staggered walking - small side-to-side drift
                self.blob.x += math.sin(e.timer * 0.08) * 0.4
                # Bigger zzz particles, varying sizes
                if random.random() < 0.06:
                    size_factor = random.uniform(0.6, 1.4)
                    self.particles.append({"x": self.blob.x + random.randint(-15, 25), "y": self.blob.y - 45, "vx": random.uniform(-0.3, 0.6), "vy": random.uniform(-1.8, -0.6), "gravity": 0, "life": int(70 * size_factor), "type": "zzz", "color": (195, 195, 255), "scale": size_factor})
            else:
                self.blob.vx = self.blob.speed
                self.blob.set_expression("happy", 60)
                if e.phase == 0:
                    e.phase = 1
                    self.typing.show("Okay, I'm awake now!")
                    
        elif e.type == "coffee":
            if p > 0.45 and e.phase == 0:
                e.phase = 1
                self.blob.set_expression("excited", 120)
                self.blob.vx = self.blob.speed * 1.6
                self.blob.shake = 3
                self.typing.show("ENERGY!!! ⚡⚡")
                self.sounds.play("sparkle")
            if e.phase == 1:
                if random.random() < 0.12:
                    self.particles.append({"x": self.blob.x + random.uniform(-10, 10), "y": self.blob.y - random.randint(5, 40), "vx": random.uniform(-2, 2), "vy": random.uniform(-3, -1), "gravity": 0.05, "life": 28, "type": "sparkle", "color": random.choice([(255, 210, 80), (255, 170, 50), (255, 255, 150)])})
                # Speed lines behind blob
                if random.random() < 0.3:
                    self.particles.append({"x": self.blob.x - 30, "y": self.blob.y - random.randint(10, 50), "vx": random.uniform(-5, -3), "vy": 0, "gravity": 0, "life": 12, "type": "speed_line", "color": (255, 240, 180)})
            # Caffeine crash near end
            if p > 0.82 and e.phase == 1:
                e.phase = 2
                self.blob.vx = self.blob.speed * 0.5
                self.blob.shake = 0
                self.blob.set_expression("sleepy", 80)
                self.typing.show("...crash... zzzz")
            if e.phase == 2:
                self.blob.vx = lerp(self.blob.vx, self.blob.speed, 0.02)
                
        elif e.type == "bird_poop":
            if not e.data["hit"]:
                e.data["poop_y"] += 12
                e.data["scale"] = max(0.2, 1.0 - e.data["poop_y"] / 200)
                if e.data["poop_y"] > -20:
                    e.data["hit"] = True
                    self.blob.set_expression("sad", 180)
                    self.typing.show("Ewww! Gross!")
                    self.sounds.play("splash")
                    for _ in range(8): self.particles.append({"x": self.blob.x, "y": self.blob.y - 20, "vx": random.uniform(-2, 2), "vy": random.uniform(-3, -1), "gravity": 0.2, "life": 20, "type": "water", "color": (230, 230, 230)})
            # Draw a little bird offscreen top
            bx2 = int(self.blob.x + 10)
            by2 = max(20, int(HEIGHT // 5 - e.data["poop_y"] * 0.3))
                    
        elif e.type == "trip":
            if p > 0.25 and e.phase == 0:
                e.phase = 1
                self.blob.jump()
                self.blob.vx = self.blob.speed * 2
                e.data["skid_x"] = self.blob.x
            if e.phase == 1:
                self.blob.angle += 18
                if p > 0.45:
                    e.phase = 2
                    self.blob.angle = 0
                    self.blob.vx = self.blob.speed
                    self.blob.set_expression("sad", 100)
                    self.typing.show("Oops! I tripped...")
                    for _ in range(10):
                        self.particles.append({"x": self.blob.x, "y": self.blob.y + 30, "vx": random.uniform(-3, 3), "vy": random.uniform(-3, -0.5), "gravity": 0.15, "life": 35, "type": "dust", "color": (175, 155, 115)})
                    for i in range(6):
                        ang = i * 60
                        self.particles.append({"x": self.blob.x, "y": self.blob.y - 50, "vx": math.cos(math.radians(ang)) * 2.5, "vy": math.sin(math.radians(ang)) * 2.5 - 1, "gravity": 0.05, "life": 50, "type": "star_dizzy", "color": (255, 220, 80)})
            if e.phase == 2 and p < 0.85:
                self.blob.angle = math.sin(e.timer * 0.3) * (4 * (1 - p / 0.85))
                    
        elif e.type == "sing":
            if random.random() < 0.1: e.data["notes"].append({"x": self.blob.x + random.randint(-15, 35), "y": self.blob.y - 90, "vx": random.uniform(-0.3, 0.8), "vy": random.uniform(-1.8, -1), "note": random.choice(["♪", "♫", "♬"]), "color": random.choice([(255, 180, 200), (180, 220, 255), (255, 220, 150), (200, 255, 200)]), "life": 1.0})
            for n in e.data["notes"]:
                n["x"] += n["vx"] + math.sin(n["y"] * 0.05) * 1.5
                n["y"] += n["vy"]
                n["life"] -= 0.01
            e.data["notes"] = [n for n in e.data["notes"] if n["life"] > 0]
            
        elif e.type == "leaf_head":
            if not e.data["on_head"]:
                e.data["leaf_x"] -= (self.blob.vx + 1)
                e.data["leaf_y"] += 2.5
                if e.data["leaf_y"] > -25 and abs(e.data["leaf_x"] - self.blob.x) < 40:
                    e.data["on_head"] = True
                    self.blob.set_expression("confused", 100)
                    self.typing.show("Huh? Something on my head?")
            elif p > 0.75 and e.phase == 0:
                e.phase = 1
                self.blob.set_expression("happy", 60)
                self.typing.show("I'll keep it!")
                
        elif e.type == "rainbow":
            e.data["scale"] = lerp(e.data["scale"], 1.0, 0.02)
            if p < 0.2: e.data["alpha"] = int(p / 0.2 * 180)
            elif p > 0.8: e.data["alpha"] = int((1 - p) / 0.2 * 180)
            else: e.data["alpha"] = int(180 + math.sin(e.timer * 0.05) * 20)
            
        elif e.type == "squirrel":
            e.data["x"] -= (self.blob.vx + 2.0)
            # Bouncing hop motion
            hop_cycle = abs(math.sin(e.timer * 0.35))
            e.data["y"] = self.blob.y + 12 - hop_cycle * 18
            # Pause and look at blob when nearby
            if abs(e.data["x"] - self.blob.x) < 80 and e.phase == 0:
                e.phase = 1
                e.data["x"] -= 0  # stop
                self.blob.set_expression("happy", 80)
                self.typing.show("Oh! A squirrel!")
            if e.phase == 1:
                e.data["x"] -= 0.3  # very slow creep
                if e.timer % 120 == 60:
                    self.blob.set_expression("excited", 60)
                    self.typing.show("So fluffy!!")
            if e.data["x"] < self.blob.x - 130 and e.phase <= 1:
                e.phase = 2
                self.typing.show("Bye bye, little friend!")
            if e.phase == 2:
                e.data["x"] -= (self.blob.vx + 4.0)
                
        elif e.type == "apple":
            e.data["x"] -= self.blob.vx
            if e.data["falling"]:
                if e.data["x"] <= self.blob.x + 60:
                    e.data["vy"] += 0.4
                    e.data["y"] += e.data["vy"]
                    if e.data["y"] > -10 and e.data["bounces"] == 0:
                        e.data["y"], e.data["vy"], e.data["bounces"] = -10, -5, 1
                        self.sounds.play("pop")
                        self.blob.extra_stretch_y = -0.2
                    elif e.data["y"] > 10 and e.data["bounces"] == 1:
                        e.data["falling"] = False
                        self.blob.hold_item("apple")
                        self.blob.set_expression("happy", 150)
                        self.typing.show("An apple! Lucky!")
            else:
                self.blob.extra_stretch_y = lerp(self.blob.extra_stretch_y, 0, 0.1)
                
        elif e.type == "photo":
            if p > 0.5 and e.data["flash"] == 0:
                e.data["flash"] = 30
                self.sounds.play("pop")
            if e.data["flash"] > 0: e.data["flash"] -= 1
            if p > 0.6: e.data["polaroid_y"] += 2
            if p > 0.75 and e.phase == 0:
                e.phase = 1
                self.blob.set_expression("proud", 80)
                self.typing.show("Great photo!")
                
        elif e.type == "gift":
            if e.phase == 0:
                e.data["x"] -= self.blob.vx
                if e.data["x"] <= self.blob.x + 80:
                    e.phase, self.blob.vx, e.timer = 1, 0, 0
                    self.blob.set_expression("surprised", 80)
                    self.typing.show("A present?!")
            elif e.phase == 1:
                if e.timer > 100 and not e.data["opened"]:
                    e.data["opened"] = True
                    self.blob.set_expression("excited", 150)
                    self.typing.show("Yay! I love surprises!")
                    self.sounds.play("sparkle")
                    for _ in range(25): self.particles.append({"x": e.data["x"], "y": self.blob.y - 10, "vx": random.uniform(-5, 5), "vy": random.uniform(-8, -2), "gravity": 0.2, "life": 60, "type": "confetti", "color": random.choice([(255, 100, 150), (100, 200, 255), (255, 220, 100), (150, 255, 150)])})
                if e.timer > 250:
                    self.blob.vx = self.blob.speed
                    
        elif e.type == "shooting_star":
            if e.timer > 50:
                e.data["x"] -= 16
                e.data["y"] += 4
                # Dense trail - 5 particles per frame, different sizes
                for _ in range(5):
                    self.particles.append({
                        "x": e.data["x"] + random.randint(-6, 6),
                        "y": e.data["y"] + random.randint(-6, 6),
                        "vx": random.uniform(0.5, 2.5),
                        "vy": random.uniform(-0.5, 0.5),
                        "gravity": 0,
                        "life": random.randint(10, 22),
                        "type": "star_trail",
                        "color": random.choice([(255, 255, 220), (200, 225, 255), (255, 240, 180)])
                    })
                
        elif e.type == "frog":
            if e.phase == 0:
                e.data["x"] -= self.blob.vx
                if e.data["x"] <= self.blob.x + 120:
                    e.phase, e.timer, self.blob.vx = 1, 0, 0
                    self.typing.show("Ribbit! A frog!")
            elif e.phase == 1:
                if e.timer > 50 and not e.data["jumped"]:
                    e.data["jumped"], e.data["jump_frame"] = True, 0
                if e.data["jumped"]:
                    e.data["jump_frame"] += 1
                    if e.data["jump_frame"] < 30:
                        e.data["x"] -= 5
                        e.data["y"] = self.blob.y + 20 - math.sin((e.data["jump_frame"] / 30) * math.pi) * 40
                if e.timer > 150:
                    self.blob.vx = self.blob.speed
                    self.blob.set_expression("happy", 80)
                    self.typing.show("Hop hop hop!")
                    e.phase = 2
            elif e.phase == 2:
                e.data["x"] -= self.blob.vx
                
        elif e.type == "fishing":
            e.data["bobber_y"] = math.sin(e.timer / 15) * 4
            if random.random() < 0.02 and not e.data["caught"]: e.data["rings"].append({"r": 0, "max": random.randint(15, 30)})
            for r in e.data["rings"]: r["r"] += 0.5
            e.data["rings"] =[r for r in e.data["rings"] if r["r"] < r["max"]]
            
            if p > 0.65 and not e.data["caught"]:
                e.data["caught"] = True
                self.blob.set_expression("excited", 150)
                self.typing.show("I caught something!")
                self.sounds.play("splash")
                for _ in range(15): self.particles.append({"x": self.blob.x + 75, "y": self.blob.y + 35, "vx": random.uniform(-3, 3), "vy": random.uniform(-6, -2), "gravity": 0.3, "life": 30, "type": "water", "color": (150, 200, 255)})
                
        elif e.type == "puddle":
            e.data["ripple"] = max(0, e.data["ripple"] - 0.5)
            if e.phase == 0:
                e.data["x"] -= self.blob.vx
                if e.data["x"] <= self.blob.x + 50:
                    e.phase, e.data["splashed"], e.data["ripple"] = 1, True, 20
                    self.blob.jump()
                    self.blob.set_expression("happy", 120)
                    self.sounds.play("splash")
                    for _ in range(15): self.particles.append({"x": e.data["x"], "y": self.blob.y + 30, "vx": random.uniform(-5, 5), "vy": random.uniform(-6, -2), "gravity": 0.3, "life": 35, "type": "water", "color": (150, 200, 255)})
                    self.typing.show("Puddle! Jump jump!")
            elif e.phase == 1:
                e.data["x"] -= self.blob.vx
                
        elif e.type == "cold":
            if not e.data["has_scarf"]:
                self.blob.shake = 1
                # Breath puffs
                if random.random() < 0.06:
                    self.particles.append({"x": self.blob.x + 38, "y": self.blob.y - 35, "vx": random.uniform(0.3, 1.2), "vy": random.uniform(-0.8, -0.2), "gravity": -0.02, "life": 55, "type": "breath", "color": (220, 235, 255)})
                # Chill sparkles
                if random.random() < 0.04:
                    self.particles.append({"x": self.blob.x + random.randint(-30, 30), "y": self.blob.y - random.randint(10, 50), "vx": random.uniform(-0.3, 0.3), "vy": random.uniform(-0.5, 0.5), "gravity": 0, "life": 40, "type": "chill", "color": (180, 210, 255)})
            else:
                self.blob.shake = 0
            if p > 0.35 and not e.data["has_scarf"]:
                e.data["has_scarf"] = True
                self.blob.hold_item("scarf")
                self.blob.set_expression("happy", 150)
                self.typing.show("Nice and warm now!")
                self.sounds.play("happy")
                
        elif e.type == "sit_rest":
            if e.phase == 0 and e.timer == 80:
                self.typing.show("Ahh, so peaceful~")
            elif e.phase == 0 and e.timer == 200:
                self.blob.set_expression("sleepy", 80)
                self.typing.show("*yawwwn*")
                for _ in range(3):
                    self.particles.append({"x": self.blob.x + 25, "y": self.blob.y - 30, "vx": random.uniform(0.2, 0.8), "vy": random.uniform(-1.2, -0.4), "gravity": 0, "life": 70, "type": "zzz", "color": (210, 210, 255)})
            if p > 0.85 and e.phase == 0:
                e.phase = 1
                self.blob.sitting = False
                self.blob.vx = self.blob.speed
                self.blob.set_expression("happy", 80)
                self.typing.show("Alright, let's go!")
                
        elif e.type == "dandelion":
            if e.phase == 0:
                e.data["x"] -= self.blob.vx
                if e.data["x"] <= self.blob.x + 80:
                    e.phase, e.timer, self.blob.vx = 1, 0, 0
                    self.blob.set_expression("surprised", 60)
            elif e.phase == 1:
                if e.timer > 40 and not e.data["blown"]:
                    e.data["blown"] = True
                    self.sounds.play("whoosh")
                    for _ in range(25): e.data["seeds"].append({"x": e.data["x"], "y": self.blob.y - 40, "vx": random.uniform(1.5, 5), "vy": random.uniform(-3, 1), "sway": random.uniform(0, 6.28)})
                    self.blob.set_expression("happy", 100)
                    self.typing.show("A dandelion! *blow*")
                if e.timer > 150:
                    self.blob.vx = self.blob.speed
                    e.phase = 2
            elif e.phase == 2:
                e.data["x"] -= self.blob.vx
            for s in e.data["seeds"]:
                s["x"] += s["vx"]
                s["y"] += s["vy"] + math.sin(e.timer * 0.1 + s["sway"]) * 0.5
                
        elif e.type == "acorn":
            e.data["x"] -= self.blob.vx
            if e.data["x"] <= self.blob.x + 20:
                if not e.data["hit"]:
                    e.data["y"] += 8
                    e.data["rot"] += 15
                    if e.data["y"] > -5:
                        e.data["hit"] = True
                        self.blob.set_expression("surprised", 80)
                        self.typing.show("Ouch! An acorn!")
                        self.sounds.play("pop")
                        self.blob.extra_stretch_y = -0.3
                else:
                    self.blob.extra_stretch_y = lerp(self.blob.extra_stretch_y, 0, 0.1)
                    e.data["y"] -= 2
                    e.data["rot"] -= 10

        elif e.type == "book":
            # Story reactions at key points
            if p > 0.25 and e.data["chapter"] == 0:
                e.data["chapter"] = 1
                self.blob.set_expression("thinking", 80)
                self.typing.show("Hmm, interesting...")
            elif p > 0.5 and e.data["chapter"] == 1:
                e.data["chapter"] = 2
                self.blob.set_expression("surprised", 80)
                self.typing.show("No way!! O_O")
                self.sounds.play("pop")
            elif p > 0.75 and e.data["chapter"] == 2:
                e.data["chapter"] = 3
                self.blob.set_expression("happy", 80)
                self.typing.show("What a good book!")
                # Confetti celebration
                for _ in range(10):
                    self.particles.append({"x": self.blob.x + random.randint(-20, 60), "y": self.blob.y - 30, "vx": random.uniform(-2, 2), "vy": random.uniform(-4, -1), "gravity": 0.15, "life": 50, "type": "confetti", "color": random.choice([(255, 200, 100), (200, 240, 180), (180, 210, 255)])})
    
    def _end_event(self):
        e = self.event
        if e is None: return
        if self.blob.held_item is not None: self.blob.drop_item()
        
        self.blob.vx = self.blob.speed
        self.blob.sitting = False
        self.blob.shake = 0
        self.blob.angle = 0
        self.blob.extra_stretch_x = 0
        self.blob.extra_stretch_y = 0
        
        self.blob.set_default_expression("happy")
        self.event = None
        self.cooldown = random.randint(120, 240)
    
    def draw_behind(self, screen):
        e = self.event
        if e is None: return
        
        if e.type == "sit_rest":
            # Draw a mossy log for the blob to sit on
            lx = int(self.blob.x)
            ly = int(self.blob.y + 20)
            # Log shadow
            sh = pygame.Surface((90, 18), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 35), (0, 0, 90, 18))
            screen.blit(sh, (lx - 45, ly + 6))
            # Log body
            pygame.draw.rect(screen, (130, 90, 55), (lx - 42, ly - 12, 84, 26), border_radius=12)
            pygame.draw.rect(screen, darken((130, 90, 55), 0.75), (lx - 42, ly - 12, 84, 26), 2, border_radius=12)
            # End grain circles
            for end_x in [lx - 37, lx + 37]:
                pygame.draw.circle(screen, (155, 110, 65), (end_x, ly), 12)
                pygame.draw.circle(screen, (110, 75, 45), (end_x, ly), 12, 2)
                pygame.draw.circle(screen, (175, 130, 80), (end_x, ly), 6)
                pygame.draw.circle(screen, (110, 75, 45), (end_x, ly), 6, 1)
            # Moss patches
            for mx in [lx - 20, lx + 5, lx + 22]:
                pygame.draw.ellipse(screen, (80, 140, 70), (mx, ly - 13, 14, 7))
                pygame.draw.ellipse(screen, (65, 120, 58), (mx, ly - 13, 14, 7), 1)
            # Bark lines
            for bx2 in range(-30, 32, 12):
                pygame.draw.line(screen, darken((130, 90, 55), 0.82), (lx + bx2, ly - 10), (lx + bx2, ly + 12), 1)

        elif e.type == "trip" and e.phase >= 2:
            # Skid marks on path
            if "skid_x" in e.data:
                skid_fade = min(1.0, (e.timer - e.duration * 0.45) / 30)
                for i in range(3):
                    sx2 = int(e.data["skid_x"] + i * 8 - 8)
                    sy2 = HEIGHT - 88
                    skid_s = pygame.Surface((18, 6), pygame.SRCALPHA)
                    pygame.draw.ellipse(skid_s, (120, 105, 80, int(80 * (1 - skid_fade))), (0, 0, 18, 6))
                    screen.blit(skid_s, (sx2, sy2))

        if e.type == "icecream":
            tx, ty = int(e.data["truck_x"]), int(HEIGHT - 95)
            # Only draw if on screen
            if tx < WIDTH + 20 and tx > -200:
                # Shadow
                pygame.draw.ellipse(screen, (0, 0, 0, 35), (tx - 5, ty + 2, 160, 18))
                # Truck body (faces right — service window on right side)
                pygame.draw.rect(screen, (255, 248, 255), (tx, ty - 112, 145, 105), border_radius=14)
                pygame.draw.rect(screen, (210, 225, 255), (tx, ty - 57, 145, 50), border_radius=10)
                # Pink/white stripes on top
                for i in range(7):
                    col = (255, 120, 145) if i % 2 == 0 else (255, 255, 255)
                    pygame.draw.rect(screen, col, (tx + 5 + i * 19, ty - 117, 19, 16), border_radius=3)
                # Driver window (left side)
                pygame.draw.rect(screen, (45, 45, 55), (tx + 8, ty - 82, 48, 40), border_radius=5)
                pygame.draw.rect(screen, (160, 210, 240), (tx + 11, ty - 79, 20, 18), border_radius=3)
                # Service window (right side — where blob buys from)
                pygame.draw.rect(screen, (155, 210, 245), (tx + 95, ty - 92, 42, 42), border_radius=5)
                pygame.draw.rect(screen, (130, 185, 215), (tx + 95, ty - 92, 42, 42), 2, border_radius=5)
                # Popsicle sign on top right
                sign = pygame.Surface((28, 40), pygame.SRCALPHA)
                pygame.draw.rect(sign, (255, 180, 210), (4, 0, 20, 28), border_radius=8)
                pygame.draw.rect(sign, darken((255, 180, 210), 0.8), (4, 0, 20, 28), 2, border_radius=8)
                pygame.draw.rect(sign, (220, 165, 100), (12, 24, 4, 14))
                screen.blit(sign, (tx + 108, ty - 115))
                # Undercarriage
                pygame.draw.rect(screen, (215, 220, 220), (tx, ty - 10, 145, 8))
                # Wheels
                wheel_rot = e.data["truck_x"] * 0.08
                for wx in [tx + 25, tx + 115]:
                    pygame.draw.circle(screen, (35, 35, 40), (wx, ty - 3), 19)
                    pygame.draw.circle(screen, (185, 185, 195), (wx, ty - 3), 9)
                    pygame.draw.line(screen, (110, 110, 115),
                                     (wx + int(math.cos(wheel_rot)*8), ty-3 + int(math.sin(wheel_rot)*8)),
                                     (wx - int(math.cos(wheel_rot)*8), ty-3 - int(math.sin(wheel_rot)*8)), 2)
                    pygame.draw.line(screen, (110, 110, 115),
                                     (wx + int(math.cos(wheel_rot+1.57)*8), ty-3 + int(math.sin(wheel_rot+1.57)*8)),
                                     (wx - int(math.cos(wheel_rot+1.57)*8), ty-3 - int(math.sin(wheel_rot+1.57)*8)), 2)
                # Jingle bell on top
                bell_bob = int(math.sin(e.timer * 0.4) * 4)
                pygame.draw.circle(screen, (255, 220, 80), (tx + 72, ty - 125 + bell_bob), 7)
                pygame.draw.circle(screen, (200, 165, 40), (tx + 72, ty - 125 + bell_bob), 7, 2)
                pygame.draw.circle(screen, (255, 240, 150), (tx + 70, ty - 128 + bell_bob), 3)
                # Dropped ice cream splat on ground (outcome==drop after dropped)
                if e.data.get("drop_done"):
                    splat_x = int(self.blob.x + 30)
                    splat_y = HEIGHT - 88
                    for col2, off in [((255,180,200),0),((200,150,100),8),((255,255,200),-8)]:
                        pygame.draw.ellipse(screen, col2, (splat_x - 20 + off, splat_y - 5, 28, 12))
                
        elif e.type == "rainbow" and e.data["alpha"] > 0:
            rs = pygame.Surface((WIDTH, 320), pygame.SRCALPHA)
            colors = [(255, 50, 50), (255, 145, 0), (255, 230, 0), (80, 210, 80), (30, 130, 255), (120, 50, 220)]
            scale = e.data["scale"]
            alpha = e.data["alpha"]
            pulse = int(math.sin(e.timer * 0.06) * 18)
            for i, c in enumerate(colors):
                arc_r = int((260 + i * 22) * scale)
                arc_a = min(255, alpha + pulse - i * 8)
                thick = max(1, int((14 - i * 1.5) * scale))
                # Draw arc as a series of thick dots for smoothness
                for deg in range(0, 181, 2):
                    rad_ang = math.radians(deg)
                    ax = WIDTH // 2 + int(math.cos(rad_ang) * arc_r)
                    ay = 300 - int(math.sin(rad_ang) * arc_r)
                    if 0 <= ax < WIDTH and 0 <= ay < 320:
                        dot = pygame.Surface((thick * 2, thick * 2), pygame.SRCALPHA)
                        pygame.draw.circle(dot, (*c, max(0, arc_a)), (thick, thick), thick)
                        rs.blit(dot, (ax - thick, ay - thick))
            screen.blit(rs, (0, 0))

        elif e.type == "photo" and e.data["polaroid_y"] > -50:
            py = int(e.data["polaroid_y"])
            px = int(self.blob.x + 25)
            # Gentle rotation as it falls
            pol_rot = math.sin(e.timer * 0.04) * 8
            pol = pygame.Surface((54, 62), pygame.SRCALPHA)
            # White frame
            pygame.draw.rect(pol, (255, 255, 252), (0, 0, 54, 62), border_radius=3)
            pygame.draw.rect(pol, (220, 215, 205), (0, 0, 54, 62), 2, border_radius=3)
            # Photo area (little scene inside)
            pygame.draw.rect(pol, (145, 200, 235), (4, 4, 46, 34))  # sky
            pygame.draw.ellipse(pol, (220, 210, 90), (32, 6, 16, 16))  # sun
            pygame.draw.rect(pol, (95, 150, 90), (4, 28, 46, 10))  # ground
            # Little blob face in photo
            pygame.draw.circle(pol, (255, 200, 100), (22, 22), 9)
            pygame.draw.circle(pol, darken((255, 200, 100), 0.5), (22, 22), 9, 1)
            pygame.draw.circle(pol, (30, 30, 30), (25, 22), 3)  # eyes
            # Bottom label area
            pygame.draw.rect(pol, (250, 248, 240), (4, 40, 46, 18))
            rotated = pygame.transform.rotate(pol, pol_rot)
            screen.blit(rotated, (px - rotated.get_width()//2, py - rotated.get_height()//2))
            
    def draw(self, screen, fonts):
        for p in self.particles:
            alpha = int(255 * min(1.0, p["life"] / 30))
            px, py = int(p["x"]), int(p["y"])
            if p["type"] == "sparkle":
                # Twinkling star shape
                size = max(2, int(5 * p["life"] / 50))
                sp = pygame.Surface((size*4, size*4), pygame.SRCALPHA)
                sc = (*p["color"], min(255, alpha + 40))
                for ang in range(0, 360, 45):
                    ex2 = size*2 + int(math.cos(math.radians(ang)) * size * 1.8)
                    ey2 = size*2 + int(math.sin(math.radians(ang)) * size * 1.8)
                    pygame.draw.line(sp, sc, (size*2, size*2), (ex2, ey2), 1)
                pygame.draw.circle(sp, sc, (size*2, size*2), size)
                screen.blit(sp, (px - size*2, py - size*2))
            elif p["type"] == "confetti":
                piece = pygame.Surface((10, 5), pygame.SRCALPHA)
                pygame.draw.rect(piece, (*p["color"], min(255, alpha)), (0, 0, 10, 5), border_radius=1)
                tumble_angle = (p["life"] * 12) % 360
                rotated = pygame.transform.rotate(piece, tumble_angle)
                screen.blit(rotated, (px - rotated.get_width()//2, py - rotated.get_height()//2))
            elif p["type"] == "water":
                ws = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(ws, (*p["color"], min(200, alpha)), (4, 4), 3)
                screen.blit(ws, (px - 4, py - 4))
            elif p["type"] == "zzz":
                z_scale = p.get("scale", 1.0) * (0.5 + (p["life"] / 70) * 0.8)
                z_font = fonts["ui"]
                z_surf = z_font.render("z", True, p["color"])
                z_surf = pygame.transform.smoothscale(z_surf, (max(1, int(z_surf.get_width() * z_scale)), max(1, int(z_surf.get_height() * z_scale))))
                z_surf.set_alpha(min(255, alpha))
                screen.blit(z_surf, (px - z_surf.get_width()//2, py - z_surf.get_height()//2))
            elif p["type"] == "dust":
                ds = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(ds, (*p["color"], min(180, alpha)), (5, 5), max(1, int(4 * p["life"] / 35)))
                screen.blit(ds, (px - 5, py - 5))
            elif p["type"] == "breath":
                r = max(2, int(6 * (1 - p["life"] / 55)))
                bs3 = pygame.Surface((r*3, r*3), pygame.SRCALPHA)
                pygame.draw.circle(bs3, (*p["color"], max(0, alpha // 2)), (r, r), r)
                screen.blit(bs3, (px - r, py - r))
            elif p["type"] == "chill":
                # Tiny snowflake
                cs3 = pygame.Surface((10, 10), pygame.SRCALPHA)
                for cang in range(0, 360, 60):
                    ex3 = 5 + int(math.cos(math.radians(cang)) * 4)
                    ey3 = 5 + int(math.sin(math.radians(cang)) * 4)
                    pygame.draw.line(cs3, (*p["color"], min(200, alpha)), (5, 5), (ex3, ey3), 1)
                screen.blit(cs3, (px - 5, py - 5))
            elif p["type"] == "star_dizzy":
                ss3 = pygame.Surface((14, 14), pygame.SRCALPHA)
                spin_ang = (60 - p["life"]) * 5  # rotates as it ages
                for sang2 in range(0, 360, 72):
                    ex3 = 7 + int(math.cos(math.radians(sang2 + spin_ang)) * 5)
                    ey3 = 7 + int(math.sin(math.radians(sang2 + spin_ang)) * 5)
                    pygame.draw.circle(ss3, (*p["color"], min(255, alpha)), (ex3, ey3), 2)
                screen.blit(ss3, (px - 7, py - 7))
            elif p["type"] == "speed_line":
                line_len = int(20 * p["life"] / 12)
                ls3 = pygame.Surface((line_len + 2, 4), pygame.SRCALPHA)
                pygame.draw.line(ls3, (*p["color"], min(200, alpha * 2)), (0, 2), (line_len, 2), 2)
                screen.blit(ls3, (px, py - 2))
            elif p["type"] == "page":
                # Little white page that tumbles and fades
                pg = pygame.Surface((10, 13), pygame.SRCALPHA)
                pygame.draw.rect(pg, (*p["color"], min(200, alpha)), (0, 0, 10, 13), border_radius=1)
                for li in range(3):
                    pygame.draw.line(pg, (180, 170, 150, min(150, alpha)), (2, 3 + li * 4), (8, 3 + li * 4), 1)
                page_rot = (60 - p["life"]) * 8
                pg_r = pygame.transform.rotate(pg, page_rot)
                screen.blit(pg_r, (px - pg_r.get_width()//2, py - pg_r.get_height()//2))
                
        e = self.event
        if e is None: return
        
        if e.type == "flower" and not e.data.get("picked"):
            fx, fy, s = int(e.data["x"]), int(self.blob.y + 45), e.data["scale"]
            stem_h = int(34 * s)
            # Stem
            pygame.draw.line(screen, (80, 155, 70), (fx, fy), (fx + int(3*s), fy - stem_h), 3)
            # Leaf
            pygame.draw.ellipse(screen, (90, 170, 80), (fx - int(10*s), fy - int(stem_h*0.55), int(12*s), int(6*s)))
            # Petals (animate open: scale them by s so they grow in)
            petal_cols = [(255, 180, 205), (255, 160, 195), (255, 200, 215)]
            for i in range(6):
                ang = i * 60 + e.timer * 0.5  # slow spin
                pr = 11 * s
                px2 = fx + int(math.cos(math.radians(ang)) * 12 * s)
                py2 = (fy - stem_h) + int(math.sin(math.radians(ang)) * 12 * s)
                pygame.draw.circle(screen, petal_cols[i % 3], (int(px2), int(py2)), int(pr))
                pygame.draw.circle(screen, darken(petal_cols[i % 3], 0.8), (int(px2), int(py2)), int(pr), 1)
            # Center
            pygame.draw.circle(screen, (255, 225, 90), (fx, fy - stem_h), int(7*s))
            pygame.draw.circle(screen, (220, 190, 60), (fx, fy - stem_h), int(7*s), 1)
            
        elif e.type == "coin" and not e.data.get("collected"):
            cx, cy = int(e.data["x"]), int(self.blob.y + 35 + e.data["y_off"])
            # 3D spinning coin
            spin = math.cos(e.timer * 0.12)
            coin_w = max(2, abs(spin) * 18)
            shade = (200, 165, 40) if spin > 0 else (255, 220, 80)
            pygame.draw.ellipse(screen, shade, (cx - coin_w, cy - 18, coin_w * 2, 36))
            if abs(spin) > 0.3:
                pygame.draw.ellipse(screen, (255, 240, 140), (cx - max(1, coin_w - 4), cy - 14, max(2, (coin_w - 4) * 2), 28))
            pygame.draw.ellipse(screen, darken(shade, 0.7), (cx - coin_w, cy - 18, coin_w * 2, 36), 2)
            # Orbit sparkle ring
            for si in range(4):
                sang = e.timer * 0.1 + si * (math.pi / 2)
                sx2 = cx + int(math.cos(sang) * 26)
                sy2 = cy + int(math.sin(sang) * 12)
                sp = pygame.Surface((8, 8), pygame.SRCALPHA)
                salpha = int(120 + 100 * math.sin(e.timer * 0.2 + si))
                pygame.draw.circle(sp, (255, 240, 120, salpha), (4, 4), 3)
                screen.blit(sp, (sx2 - 4, sy2 - 4))
            
        elif e.type == "bee":
            bx, by = int(e.data["x"]), int(e.data["y"])
            wa = math.sin(e.timer * 0.8) * 6
            # Rotation: face direction of movement
            if e.phase == 1:
                # Orbiting — face tangent direction
                ang = e.data["phase_ang"]
                # velocity direction is perpendicular to radius, i.e. tangent
                dx_vel = -math.sin(ang) * 60
                dy_vel = math.cos(ang * 2) * 30 * 2  # approximate
                rot = -math.degrees(math.atan2(dy_vel, dx_vel))
            elif e.phase == 2:
                rot = -20  # flying away up-right
            else:
                rot = 180  # approaching from right, facing left
            bs = pygame.Surface((44, 28), pygame.SRCALPHA)
            # Wings (translucent, flap up/down)
            pygame.draw.ellipse(bs, (220, 240, 255, 160), (8, 4 - abs(int(wa)), 14, 9))
            pygame.draw.ellipse(bs, (220, 240, 255, 160), (22, 4 - abs(int(wa)), 14, 9))
            # Body stripes
            pygame.draw.ellipse(bs, (255, 205, 50), (10, 10, 24, 14))
            for stripe in range(3):
                sy2 = 11 + stripe * 4
                pygame.draw.rect(bs, (40, 35, 30), (11, sy2, 22, 2))
            # Stinger
            pygame.draw.polygon(bs, (80, 65, 45), [(32, 17), (38, 16), (32, 19)])
            # Head
            pygame.draw.circle(bs, (40, 35, 30), (12, 17), 6)
            pygame.draw.circle(bs, (220, 220, 80), (10, 15), 2)
            pygame.draw.circle(bs, (220, 220, 80), (14, 15), 2)
            rotated = pygame.transform.rotate(bs, rot)
            screen.blit(rotated, (bx - rotated.get_width()//2, by - rotated.get_height()//2))

        elif e.type == "butterfly":
            bx, by = int(e.data["x"]), int(e.data["y"])
            flap_speed = 0.35 if e.data["landed"] else 0.7
            wa = math.sin(e.timer * flap_speed) * 0.9
            wing_cols = [(255, 155, 210), (255, 195, 120)]
            spot_cols = [(200, 90, 155), (195, 135, 50)]
            for i, (dx, wc, sc) in enumerate([(-16, wing_cols[0], spot_cols[0]), (16, wing_cols[1], spot_cols[1])]):
                ws = pygame.Surface((38, 32), pygame.SRCALPHA)
                pygame.draw.ellipse(ws, wc, (2, 0, 28, 22))
                pygame.draw.ellipse(ws, darken(wc, 0.75), (2, 0, 28, 22), 2)
                pygame.draw.ellipse(ws, wc, (5, 16, 22, 14))
                pygame.draw.ellipse(ws, darken(wc, 0.75), (5, 16, 22, 14), 1)
                pygame.draw.circle(ws, sc, (14, 9), 4)
                pygame.draw.circle(ws, (255, 255, 255), (14, 9), 2)
                pygame.draw.circle(ws, sc, (20, 18), 3)
                flip = 1 if i == 0 else -1
                rot = pygame.transform.rotate(ws, wa * 50 * flip)
                screen.blit(rot, (bx + dx - rot.get_width()//2 + (5 if i == 1 else -5), by - rot.get_height()//2))
            pygame.draw.ellipse(screen, (55, 40, 35), (bx - 3, by - 12, 7, 22))
            pygame.draw.circle(screen, (55, 40, 35), (bx, by - 13), 4)
            for adx in [-1, 1]:
                ax_end, ay_end = bx + adx * 8, by - 24
                pygame.draw.line(screen, (55, 40, 35), (bx, by - 14), (ax_end, ay_end), 1)
                glow = pygame.Surface((10, 10), pygame.SRCALPHA)
                ga = int(160 + math.sin(e.timer * 0.4 + adx) * 60)
                pygame.draw.circle(glow, (*wing_cols[0 if adx < 0 else 1], ga), (5, 5), 4)
                screen.blit(glow, (ax_end - 5, ay_end - 5))
        
        elif e.type == "balloon":
            if e.phase == 0:
                bx, by, color = e.data["x"], e.data["y"], e.data["color"]
                sway = math.sin(e.timer * 0.1) * 5
                pygame.draw.line(screen, (150, 150, 155), (int(bx), int(by + 35)), (int(bx + 5), int(by + 100)), 2)
                pygame.draw.ellipse(screen, color, (int(bx - 23 + sway), int(by - 20), 46, 55))
                pygame.draw.ellipse(screen, lighten(color, 1.3), (int(bx - 10 + sway), int(by - 10), 14, 18))
            elif e.phase == 2:
                by = e.data["fly_y"]
                bx = e.data.get("fly_x", self.blob.x)
                color = e.data["color"]
                # String curves as it drifts
                string_sway = math.sin(e.timer * 0.08) * 12
                cp_x = int(bx + string_sway * 0.5)
                cp_y = int(by + 60)
                # Draw curved string with line segments
                for seg in range(8):
                    t0, t1 = seg / 8, (seg + 1) / 8
                    def bezier(t):
                        return (int((1-t)**2 * bx + 2*(1-t)*t*cp_x + t**2*(bx + string_sway)),
                                int((1-t)**2 * (by + 35) + 2*(1-t)*t*cp_y + t**2*(by + 100)))
                    pygame.draw.line(screen, (150, 150, 155), bezier(t0), bezier(t1), 1)
                sway2 = math.sin(e.timer * 0.1) * 10
                pygame.draw.ellipse(screen, color, (int(bx - 23 + sway2), int(by - 20), 46, 55))
                pygame.draw.ellipse(screen, lighten(color, 1.3), (int(bx - 10 + sway2), int(by - 10), 14, 18))
        
        elif e.type == "rain":
            for d in e.data["drops"]:
                dx2, dy2 = int(d["x"]), int(d["y"])
                # Streak length proportional to speed
                streak = int(d["speed"] * 0.8)
                alpha = min(220, 120 + int(d["speed"] * 4))
                rs = pygame.Surface((6, streak + 4), pygame.SRCALPHA)
                pygame.draw.line(rs, (160, 195, 235, alpha), (1, 0), (3, streak), 2)
                screen.blit(rs, (dx2 - 2, dy2 - streak // 2))
        
        elif e.type == "sing":
            for n in e.data["notes"]:
                note_alpha = int(255 * min(1.0, n["life"] * 1.5))
                # Scale note up as it rises
                note_scale = 0.7 + (1.0 - n["life"]) * 0.5
                ns = fonts["note"].render(n["note"], True, n["color"])
                if note_scale != 1.0:
                    ns = pygame.transform.smoothscale(ns, (max(1, int(ns.get_width() * note_scale)), max(1, int(ns.get_height() * note_scale))))
                ns_a = ns.copy()
                ns_a.set_alpha(note_alpha)
                screen.blit(ns_a, (int(n["x"]), int(n["y"])))
        
        elif e.type == "leaf_head":
            if not e.data["on_head"]:
                lx, ly = e.data["leaf_x"], e.data["leaf_y"] + self.blob.y
                rot = math.sin(e.timer * 0.12) * 35
            else:
                walk_bob = math.sin(self.blob.walk_cycle) * 4 if self.blob.is_walking else 0
                lx = self.blob.x + 16
                ly = self.blob.y - 80 + walk_bob
                rot = 12 + math.sin(e.timer * 0.18) * 6  # gentle sway on head
            # Draw a nicer leaf with veins
            ls = pygame.Surface((28, 28), pygame.SRCALPHA)
            leaf_col = (190, 135, 55)
            pygame.draw.polygon(ls, leaf_col, [(14, 2), (26, 14), (14, 26), (2, 14)])
            pygame.draw.polygon(ls, darken(leaf_col, 0.75), [(14, 2), (26, 14), (14, 26), (2, 14)], 1)
            # Center vein
            pygame.draw.line(ls, darken(leaf_col, 0.65), (14, 3), (14, 25), 1)
            # Side veins
            for vy in [8, 13, 18]:
                spread = int((14 - abs(vy - 14)) * 0.6)
                pygame.draw.line(ls, darken(leaf_col, 0.65), (14, vy), (14 - spread, vy + 2), 1)
                pygame.draw.line(ls, darken(leaf_col, 0.65), (14, vy), (14 + spread, vy + 2), 1)
            rotated = pygame.transform.rotate(ls, rot)
            screen.blit(rotated, (int(lx) - rotated.get_width()//2, int(ly) - rotated.get_height()//2))
            
        elif e.type == "squirrel":
            sx, sy = int(e.data["x"]), int(e.data["y"])
            hop_cycle = abs(math.sin(e.timer * 0.35))
            # Squash on land, stretch in air
            sq_x = 1.0 + (1 - hop_cycle) * 0.18
            sq_y = 1.0 - (1 - hop_cycle) * 0.15
            looking_at_blob = e.phase == 1
            # Tail (multiple layers, animated curl)
            tail_curl = math.sin(e.timer * 0.25) * (10 if not looking_at_blob else 20)
            for ti in range(5):
                tc = 0.6 + ti * 0.08
                t_col = (int(175 * tc), int(115 * tc), int(65 * tc))
                ty2 = sy - 28 - ti * 3 + int(tail_curl * ti / 3)
                tw2, th2 = int((22 - ti) * sq_x), int((18 + ti * 2) * sq_y)
                pygame.draw.ellipse(screen, t_col, (sx - 38 + ti * 2, ty2, tw2, th2))
            # Body
            bw, bh = int(28 * sq_x), int(20 * sq_y)
            pygame.draw.ellipse(screen, (160, 100, 55), (sx - bw//2, sy - bh//2 - 2, bw, bh))
            pygame.draw.ellipse(screen, (230, 190, 150), (sx - 6, sy - bh//2, 12, bh - 4))
            # Head (faces toward blob if looking)
            hx = sx + (14 if not looking_at_blob else 10)
            pygame.draw.circle(screen, (160, 100, 55), (hx, sy - 8), 11)
            # Ear (perked up when alert)
            ear_h = -28 if looking_at_blob else -26
            pygame.draw.polygon(screen, (160, 100, 55), [(hx - 6, sy - 17), (hx - 2, sy + ear_h), (hx + 4, sy - 17)])
            pygame.draw.polygon(screen, (220, 165, 120), [(hx - 4, sy - 18), (hx - 1, sy + ear_h + 4), (hx + 2, sy - 18)])
            # Eye
            eye_x = hx + (4 if not looking_at_blob else 0)
            pygame.draw.circle(screen, (30, 25, 20), (eye_x + 4, sy - 10), 3)
            pygame.draw.circle(screen, (255, 255, 255), (eye_x + 3, sy - 11), 1)
            # Nose
            pygame.draw.circle(screen, (60, 35, 30), (hx + 8, sy - 6), 2)
            # Cheek puff when looking at blob
            if looking_at_blob:
                pygame.draw.ellipse(screen, lighten((160, 100, 55), 1.1), (hx + 2, sy - 9, 10, 7))
            # Legs
            for lx2, phase2 in [(-6, 0), (6, math.pi)]:
                leg_bob = int(hop_cycle * 5)
                pygame.draw.ellipse(screen, (140, 85, 45), (sx + lx2 - 4, sy + 8 - leg_bob, 8, 10))
            
        elif e.type == "apple" and e.data["falling"]:
            ay, ax = int(self.blob.y + e.data["y"]), int(e.data["x"])
            # Spin as it falls
            fall_rot = e.data.get("rot_angle", 0)
            e.data["rot_angle"] = fall_rot + 4
            ap = pygame.Surface((34, 34), pygame.SRCALPHA)
            # Body
            pygame.draw.circle(ap, (225, 60, 60), (17, 20), 13)
            pygame.draw.circle(ap, (255, 100, 100), (13, 15), 5)  # highlight
            pygame.draw.circle(ap, darken((225, 60, 60), 0.75), (17, 20), 13, 2)
            # Stem
            pygame.draw.line(ap, (100, 70, 50), (17, 7), (18, 13), 3)
            # Leaf
            pygame.draw.ellipse(ap, (90, 170, 75), (18, 4, 12, 7))
            pygame.draw.ellipse(ap, (65, 130, 55), (18, 4, 12, 7), 1)
            # Indentation
            pygame.draw.circle(ap, darken((225, 60, 60), 0.85), (17, 7), 3)
            rotated = pygame.transform.rotate(ap, fall_rot)
            screen.blit(rotated, (ax - rotated.get_width()//2, ay - rotated.get_height()//2))
            
        elif e.type == "photo" and e.data["flash"] > 0:
            # Full white flash that fades
            flash_alpha = int(e.data["flash"] / 30 * 255)
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 255, 255, flash_alpha))
            screen.blit(fs, (0, 0))
            # Vignette ring at peak flash
            if e.data["flash"] > 22:
                vg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.rect(vg, (255, 255, 255, 60), (0, 0, WIDTH, HEIGHT))
                screen.blit(vg, (0, 0))
            
        elif e.type == "gift" and not e.data["opened"]:
            gx, gy = e.data["x"], self.blob.y + 10
            wobble = math.sin(e.timer * 0.8) * 5 if (e.timer > 100 and e.phase == 1) else 0
            # Shadow
            gs_shadow = pygame.Surface((60, 16), pygame.SRCALPHA)
            pygame.draw.ellipse(gs_shadow, (0, 0, 0, 40), (0, 0, 60, 16))
            screen.blit(gs_shadow, (int(gx) - 27, int(gy) + 30))
            gs = pygame.Surface((56, 56), pygame.SRCALPHA)
            # Box body
            pygame.draw.rect(gs, (255, 100, 130), (4, 18, 48, 36), border_radius=4)
            pygame.draw.rect(gs, darken((255, 100, 130), 0.8), (4, 18, 48, 36), 2, border_radius=4)
            # Shading on box
            pygame.draw.rect(gs, lighten((255, 100, 130), 1.2), (6, 20, 22, 14), border_radius=2)
            # Vertical ribbon
            pygame.draw.rect(gs, (255, 220, 100), (24, 18, 8, 36))
            # Horizontal ribbon
            pygame.draw.rect(gs, (255, 220, 100), (4, 28, 48, 8))
            # Lid
            pygame.draw.rect(gs, (255, 145, 165), (2, 8, 52, 12), border_radius=3)
            pygame.draw.rect(gs, darken((255, 145, 165), 0.8), (2, 8, 52, 12), 2, border_radius=3)
            # Bow loops
            pygame.draw.circle(gs, (255, 220, 100), (20, 8), 8)
            pygame.draw.circle(gs, (255, 220, 100), (36, 8), 8)
            pygame.draw.circle(gs, (200, 165, 60), (20, 8), 8, 2)
            pygame.draw.circle(gs, (200, 165, 60), (36, 8), 8, 2)
            pygame.draw.circle(gs, (255, 240, 160), (28, 8), 5)  # Bow center
            rotated = pygame.transform.rotate(gs, wobble)
            screen.blit(rotated, (int(gx) - rotated.get_width()//2, int(gy) - 25 - rotated.get_height()//2))
            
        elif e.type == "frog":
            fx, fy = int(e.data["x"]), int(e.data["y"])
            sq_x, sq_y = 1.0, 1.0
            jf = e.data.get("jump_frame", 0)
            if e.data.get("jumped"):
                t_jump = jf / 30.0
                sq_y = 1.0 + math.sin(t_jump * math.pi) * 0.5   # stretches up during leap
                sq_x = 1.0 - math.sin(t_jump * math.pi) * 0.25
            # Pre-jump wind-up squash
            elif e.phase == 1 and not e.data.get("jumped") and e.timer % 60 > 40:
                sq_y = 0.7; sq_x = 1.3
            fw = int(44 * sq_x); fh = int(44 * sq_y)
            fs = pygame.Surface((fw, fh), pygame.SRCALPHA)
            scx, scy = fw // 2, fh // 2
            # Body
            pygame.draw.ellipse(fs, (85, 168, 85), (scx - 16, scy - 6, 32, 22))
            pygame.draw.ellipse(fs, (110, 195, 100), (scx - 10, scy - 4, 20, 12))  # belly highlight
            # Head
            pygame.draw.ellipse(fs, (85, 168, 85), (scx - 12, scy - 18, 24, 20))
            # Eyes (bulging)
            for edx in [-7, 7]:
                pygame.draw.circle(fs, (200, 230, 90), (scx + edx, scy - 18), 7)
                pygame.draw.circle(fs, (30, 30, 30), (scx + edx + 1, scy - 18), 3)
                pygame.draw.circle(fs, (255, 255, 255), (scx + edx - 1, scy - 20), 1)
            # Smile
            pygame.draw.arc(fs, (50, 120, 50), (scx - 8, scy - 14, 16, 8), math.pi, 2 * math.pi, 2)
            # Back legs
            leg_spread = 1.0 + math.sin(t_jump * math.pi) * 0.6 if e.data.get("jumped") else 1.0
            for lx in [-1, 1]:
                lbx = scx + lx * int(14 * leg_spread)
                pygame.draw.ellipse(fs, (70, 145, 70), (lbx - 5, scy + 12, 10, 6))
            screen.blit(fs, (fx - fw // 2, fy - fh // 2))
            
        elif e.type == "fishing":
            bx = int(self.blob.x + 75)
            by = int(self.blob.y + 35 + e.data["bobber_y"])
            rod_tip_x = int(self.blob.x + 65)
            rod_tip_y = int(self.blob.y - 10)
            # Fishing line (slight curve)
            mid_x = (rod_tip_x + bx) // 2 + 15
            mid_y = (rod_tip_y + by) // 2 + 20
            for seg in range(10):
                t0, t1 = seg / 10, (seg + 1) / 10
                lx0 = int((1-t0)**2 * rod_tip_x + 2*(1-t0)*t0*mid_x + t0**2*bx)
                ly0 = int((1-t0)**2 * rod_tip_y + 2*(1-t0)*t0*mid_y + t0**2*by)
                lx1 = int((1-t1)**2 * rod_tip_x + 2*(1-t1)*t1*mid_x + t1**2*bx)
                ly1 = int((1-t1)**2 * rod_tip_y + 2*(1-t1)*t1*mid_y + t1**2*by)
                pygame.draw.line(screen, (200, 200, 205), (lx0, ly0), (lx1, ly1), 1)
            # Water rings expanding out from bobber
            for r in e.data["rings"]:
                ring_alpha = max(0, int(180 - r["r"] * 6))
                rs2 = pygame.Surface((int(r["r"]*3)+4, int(r["r"]*1.5)+4), pygame.SRCALPHA)
                pygame.draw.ellipse(rs2, (160, 210, 240, ring_alpha),
                                    (0, 0, int(r["r"]*3), int(r["r"]*1.5)), 1)
                screen.blit(rs2, (bx - int(r["r"]*1.5) - 2, by - int(r["r"]*0.75) - 2))
            if e.data["caught"]:
                # Fish drawn at bobber
                fs2 = pygame.Surface((40, 20), pygame.SRCALPHA)
                pygame.draw.ellipse(fs2, (100, 160, 210), (0, 4, 32, 14))
                pygame.draw.polygon(fs2, (80, 140, 190), [(28, 0), (40, 10), (28, 20)])
                pygame.draw.circle(fs2, (30, 30, 40), (8, 10), 3)
                pygame.draw.ellipse(fs2, (140, 200, 240), (4, 6, 16, 6))  # shine
                screen.blit(fs2, (bx - 18, by - 8))
            else:
                # Bobber: white top, red bottom, floating
                pygame.draw.circle(screen, (255, 255, 255), (bx, by - 3), 6)
                pygame.draw.circle(screen, (230, 60, 60), (bx, by + 3), 6)
                pygame.draw.circle(screen, darken((230, 60, 60), 0.7), (bx, by), 12, 1)
                pygame.draw.circle(screen, (255, 255, 255), (bx - 2, by - 5), 2)  # glint
                
        elif e.type == "puddle":
            px, py = int(e.data["x"]), int(self.blob.y + 35)
            # Puddle base with depth gradient
            for layer, (w, h, alpha) in enumerate([(70, 22, 180), (55, 16, 140), (35, 10, 100)]):
                ps2 = pygame.Surface((w, h), pygame.SRCALPHA)
                color = (110 + layer * 15, 155 + layer * 15, 210 - layer * 5, alpha)
                pygame.draw.ellipse(ps2, color, (0, 0, w, h))
                screen.blit(ps2, (px - w//2, py - h//2))
            # Shimmer highlight
            shimmer = abs(math.sin(e.timer * 0.15))
            sh = pygame.Surface((28, 8), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (220, 240, 255, int(shimmer * 130)), (0, 0, 28, 8))
            screen.blit(sh, (px - 20, py - 6))
            # Expanding ripple
            if e.data["ripple"] > 0:
                rip_r = e.data["ripple"]
                rip_s = pygame.Surface((int(rip_r*3)+4, int(rip_r*1.4)+4), pygame.SRCALPHA)
                rip_alpha = max(0, int(180 * rip_r / 20))
                pygame.draw.ellipse(rip_s, (200, 230, 255, rip_alpha),
                                    (0, 0, int(rip_r*3), int(rip_r*1.4)), 2)
                screen.blit(rip_s, (px - int(rip_r*1.5)-2, py - int(rip_r*0.7)-2))
            
        elif e.type == "dandelion":
            dx, dy = int(e.data["x"]), int(self.blob.y + 5)
            # Stem with slight bend
            bend = math.sin(e.timer * 0.08) * 3
            pygame.draw.line(screen, (100, 160, 80), (dx, dy + 35), (dx + int(bend), dy), 3)
            pygame.draw.ellipse(screen, (90, 170, 80), (dx - 6, dy + 15, 12, 6))
            if not e.data["blown"]:
                # Fluffy seed head - radiating spokes
                for ang in range(0, 360, 18):
                    rad_ang = math.radians(ang + e.timer * 0.5)
                    spoke_len = 13 + math.sin(rad_ang * 3) * 2
                    ex2 = dx + int(math.cos(rad_ang) * spoke_len)
                    ey2 = dy - 5 + int(math.sin(rad_ang) * spoke_len)
                    pygame.draw.line(screen, (220, 220, 220), (dx, dy - 5), (ex2, ey2), 1)
                    pygame.draw.circle(screen, (255, 255, 255), (ex2, ey2), 2)
                # Center
                pygame.draw.circle(screen, (240, 220, 80), (dx, dy - 5), 4)
            else:
                # Stubble after blown
                for ang in range(0, 360, 36):
                    rad_ang = math.radians(ang)
                    ex2 = dx + int(math.cos(rad_ang) * 5)
                    ey2 = dy - 5 + int(math.sin(rad_ang) * 5)
                    pygame.draw.line(screen, (190, 185, 170), (dx, dy - 5), (ex2, ey2), 1)
            for s in e.data.get("seeds", []):
                # Seed with parachute line
                sx2, sy2 = int(s["x"]), int(s["y"])
                pygame.draw.line(screen, (210, 210, 200), (sx2, sy2), (sx2, sy2 - 7), 1)
                pygame.draw.circle(screen, (255, 255, 255), (sx2, sy2 - 7), 3)
                pygame.draw.circle(screen, (220, 215, 180), (sx2, sy2), 2)
                
        elif e.type == "acorn":
            ax, ay = int(e.data["x"]), int(self.blob.y + e.data["y"])
            ac = pygame.Surface((28, 32), pygame.SRCALPHA)
            # Nut body
            pygame.draw.ellipse(ac, (175, 130, 70), (4, 10, 20, 20))
            pygame.draw.ellipse(ac, lighten((175, 130, 70), 1.25), (6, 12, 10, 10))  # shine
            pygame.draw.ellipse(ac, darken((175, 130, 70), 0.75), (4, 10, 20, 20), 2)
            # Cap (textured)
            pygame.draw.ellipse(ac, (110, 80, 45), (2, 4, 24, 14))
            pygame.draw.ellipse(ac, (130, 95, 55), (2, 4, 24, 14), 2)
            for hatch in range(3):
                pygame.draw.line(ac, (90, 65, 35), (4 + hatch * 7, 6), (4 + hatch * 7, 14), 1)
            # Stem
            pygame.draw.line(ac, (90, 65, 35), (14, 2), (14, 6), 3)
            rotated = pygame.transform.rotate(ac, e.data["rot"])
            screen.blit(rotated, (ax - rotated.get_width()//2, ay - rotated.get_height()//2))

        elif e.type == "bird_poop":
            bx2 = int(self.blob.x + 10)
            # Little bird near top of screen
            bird_y = max(30, 80 - int(e.data["poop_y"] * 0.2))
            bs2 = pygame.Surface((28, 18), pygame.SRCALPHA)
            pygame.draw.ellipse(bs2, (70, 65, 60), (4, 4, 18, 12))  # body
            pygame.draw.circle(bs2, (70, 65, 60), (22, 6), 6)        # head
            pygame.draw.circle(bs2, (30, 30, 30), (25, 5), 2)        # eye
            pygame.draw.polygon(bs2, (200, 160, 60), [(26, 6), (28, 4), (28, 8)])  # beak
            # Wing flap
            wing_y = int(math.sin(e.timer * 0.6) * 3)
            pygame.draw.ellipse(bs2, (55, 50, 45), (6, wing_y, 14, 7))
            screen.blit(bs2, (bx2 - 14, bird_y - 9))
            # Warning shadow on ground (before hit)
            if not e.data["hit"]:
                warn_alpha = int(60 + 80 * (e.data["poop_y"] / 200))
                warn_r = max(4, int(18 - e.data["poop_y"] * 0.05))
                ws2 = pygame.Surface((warn_r * 3, warn_r), pygame.SRCALPHA)
                pygame.draw.ellipse(ws2, (30, 30, 30, warn_alpha), (0, 0, warn_r * 3, warn_r))
                screen.blit(ws2, (bx2 - warn_r - warn_r // 2, int(self.blob.y + 32)))
                # Falling poop droplet
                py2 = int(HEIGHT // 5 + e.data["poop_y"] * 0.8)
                if py2 < int(self.blob.y - 40):
                    pd = pygame.Surface((12, 16), pygame.SRCALPHA)
                    pygame.draw.ellipse(pd, (240, 240, 235), (1, 4, 10, 10))
                    pygame.draw.polygon(pd, (240, 240, 235), [(6, 0), (2, 5), (10, 5)])
                    screen.blit(pd, (bx2 - 6, py2 - 8))
            else:
                # Poop splat on blob
                splat_x, splat_y = bx2 + 15, int(self.blob.y - 62)
                splat = pygame.Surface((22, 14), pygame.SRCALPHA)
                pygame.draw.ellipse(splat, (242, 242, 237), (0, 2, 22, 10))
                pygame.draw.ellipse(splat, (242, 242, 237), (6, 0, 10, 14))
                screen.blit(splat, (splat_x - 11, splat_y - 7))

        elif e.type == "cold":
            # Frost crystals floating around blob when cold
            if not e.data.get("has_scarf"):
                for i in range(4):
                    ang = e.timer * 0.04 + i * (math.pi / 2)
                    cr = 55 + math.sin(e.timer * 0.08 + i) * 10
                    cx2 = int(self.blob.x + math.cos(ang) * cr)
                    cy2 = int(self.blob.y - 35 + math.sin(ang) * 20)
                    cs4 = pygame.Surface((14, 14), pygame.SRCALPHA)
                    cry_alpha = int(140 + math.sin(e.timer * 0.1 + i) * 60)
                    for ca in range(0, 360, 60):
                        ex4 = 7 + int(math.cos(math.radians(ca)) * 5)
                        ey4 = 7 + int(math.sin(math.radians(ca)) * 5)
                        pygame.draw.line(cs4, (185, 215, 255, cry_alpha), (7, 7), (ex4, ey4), 1)
                    pygame.draw.circle(cs4, (210, 235, 255, cry_alpha), (7, 7), 2)
                    screen.blit(cs4, (cx2 - 7, cy2 - 7))

        elif e.type == "sleepy":
            p2 = e.timer / e.duration if e.duration > 0 else 1
            if p2 < 0.85:
                # Heavy eyelid overlay — semi-transparent dark band from top
                droop = int(p2 * 0.4 * HEIGHT * 0.35)
                if droop > 0:
                    droop_s = pygame.Surface((WIDTH, droop), pygame.SRCALPHA)
                    droop_alpha = int(p2 * 90)
                    droop_s.fill((15, 10, 25, droop_alpha))
                    screen.blit(droop_s, (0, 0))
                    # Bottom droop too
                    screen.blit(droop_s, (0, HEIGHT - droop))

        elif e.type == "coffee" and e.phase == 1:
            # Energized screen edge glow — warm amber pulse
            pulse = abs(math.sin(e.timer * 0.18))
            eg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for ei in range(3):
                thick = 18 + ei * 12
                ea = int(pulse * (35 - ei * 10))
                if ea > 0:
                    pygame.draw.rect(eg, (255, 200, 80, ea), (ei * 6, ei * 6, WIDTH - ei * 12, HEIGHT - ei * 12), thick)
            screen.blit(eg, (0, 0))

        elif e.type == "sit_rest":
            p2 = e.timer / e.duration if e.duration > 0 else 1
            if 0.1 < p2 < 0.85:
                # Peaceful ambient sparkles drifting up around resting blob
                if random.random() < 0.08:
                    self.particles.append({"x": self.blob.x + random.randint(-40, 40), "y": self.blob.y + 10, "vx": random.uniform(-0.3, 0.3), "vy": random.uniform(-0.8, -0.3), "gravity": 0, "life": 80, "type": "sparkle", "color": random.choice([(200, 240, 180), (180, 220, 255), (255, 230, 180)])})

        elif e.type == "book":
            # Occasional page-turn particle and floating word snippets
            if random.random() < 0.03:
                self.particles.append({"x": self.blob.x + 45, "y": self.blob.y - 30, "vx": random.uniform(0.5, 1.5), "vy": random.uniform(-1.5, -0.5), "gravity": 0.02, "life": 55, "type": "page", "color": (240, 235, 215)})
            # Subtle focus glow around blob when reading
            p2 = e.timer / e.duration if e.duration > 0 else 1
            glow_alpha = int(30 + math.sin(e.timer * 0.05) * 15)
            fg = pygame.Surface((130, 130), pygame.SRCALPHA)
            pygame.draw.ellipse(fg, (255, 240, 200, glow_alpha), (0, 0, 130, 90))
            screen.blit(fg, (int(self.blob.x) - 65, int(self.blob.y) - 80))

    def draw_night_layer(self, screen):
        e = self.event
        if e is None or e.type != "shooting_star": return
        
        # Background stars
        rng = random.Random(77)
        for _ in range(60):
            sx2 = rng.randint(0, WIDTH)
            sy2 = rng.randint(0, HEIGHT // 2)
            twinkle = int(120 + math.sin(e.timer * 0.07 + sx2 * 0.05) * 80)
            star_s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(star_s, (255, 255, 220, twinkle), (3, 3), 2)
            screen.blit(star_s, (sx2 - 3, sy2 - 3))
        
        # Star trail particles
        for p in self.particles:
            if p["type"] == "star_trail":
                alpha = clamp(int(255 * p["life"] / 20), 0, 255)
                r = max(1, int(3 * p["life"] / 20))
                ts = pygame.Surface((r * 4 + 2, r * 4 + 2), pygame.SRCALPHA)
                pygame.draw.circle(ts, (p["color"][0], p["color"][1], p["color"][2], alpha), (r * 2 + 1, r * 2 + 1), r)
                screen.blit(ts, (int(p["x"]) - r * 2 - 1, int(p["y"]) - r * 2 - 1))
                
        sx, sy = int(e.data["x"]), int(e.data["y"])
        # Outer glow
        glow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 255, 180, 60), (20, 20), 18)
        pygame.draw.circle(glow, (255, 255, 220, 120), (20, 20), 12)
        screen.blit(glow, (sx - 20, sy - 20))
        # Core
        pygame.draw.circle(screen, (255, 255, 220), (sx, sy), 6)
        pygame.draw.circle(screen, (255, 255, 255), (sx - 1, sy - 1), 3)

# ---------------------------------------------------------------------------
# Forest Scene (Cozy Hills Upgrade)
# ---------------------------------------------------------------------------
class ForestScene:
    def __init__(self):
        self.scroll = 0.0
        self.time = 0
        
        random.seed(42)
        self.far_trees =[{"x": i * 90 + random.randint(-25, 25), "h": random.randint(220, 320), "w": random.randint(35, 55)} for i in range(35)]
        self.mid_trees =[{"x": i * 110 + random.randint(-35, 35), "h": random.randint(280, 400), "w": random.randint(45, 75)} for i in range(30)]
        self.ground =[{"x": i * 70 + random.randint(-25, 25), "type": random.choice(["bush", "flowers", "mushroom", "rock", "grass", "fern"]), "size": random.uniform(0.6, 1.15)} for i in range(50)]
        self.particles: List[Dict[str, Any]] =[{"x": random.randint(0, WIDTH), "y": random.randint(80, HEIGHT - 180), "phase": random.uniform(0, 6.28), "size": random.randint(2, 4)} for _ in range(25)]
        self.leaves =[{"x": random.randint(0, WIDTH * 2), "y": random.randint(-50, HEIGHT), "rot": random.uniform(0, 360), "speed": random.uniform(0.25, 0.9), "sway": random.uniform(0, 6.28), "color": random.choice([(185, 110, 55), (210, 160, 60), (160, 190, 85), (230, 135, 50)])} for _ in range(14)]
        self.clouds =[{"x": random.randint(0, WIDTH), "y": random.randint(40, 150), "w": random.randint(80, 180), "speed": random.uniform(0.15, 0.4)} for _ in range(6)]
        self.birds =[{"x": random.randint(-200, WIDTH), "y": random.randint(60, 180), "speed": random.uniform(1.5, 3), "wing": random.uniform(0, 6.28)} for _ in range(4)]
        random.seed()
        
        self.sky_colors =[(155, 200, 240), (200, 225, 248), (230, 240, 250)]
        self.far_col = (80, 120, 95)
        self.mid_col = (60, 100, 70)
        self.ground_col = (95, 140, 85)
        self.path_col = (180, 155, 120)
        
        self.sky_surf = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            t = y / HEIGHT
            c = lerp_color(self.sky_colors[0], self.sky_colors[1], t * 2) if t < 0.5 else lerp_color(self.sky_colors[1], self.sky_colors[2], (t - 0.5) * 2)
            pygame.draw.line(self.sky_surf, c, (0, y), (WIDTH, y))
            
    def update(self, speed):
        self.time += 1
        self.scroll += speed
        for p in self.particles:
            p["x"] += math.sin(self.time / 50 + p["phase"]) * 0.4
            p["y"] += math.cos(self.time / 70 + p["phase"]) * 0.25
        for leaf in self.leaves:
            leaf["y"] += leaf["speed"]
            leaf["x"] += math.sin(self.time / 25 + leaf["sway"]) * 0.9 - speed * 0.4
            leaf["rot"] += random.uniform(-1.5, 1.5)
            if leaf["y"] > HEIGHT - 70:
                leaf["y"], leaf["x"] = -15, random.randint(int(self.scroll), int(self.scroll) + WIDTH)
        for cloud in self.clouds:
            cloud["x"] += cloud["speed"]
            if cloud["x"] > WIDTH + 100: cloud["x"] = -cloud["w"] - 50
        for bird in self.birds:
            bird["x"] += bird["speed"]
            bird["wing"] += 0.25
            if bird["x"] > WIDTH + 100: bird["x"], bird["y"] = -50, random.randint(60, 180)
            
    def draw(self, screen):
        screen.blit(self.sky_surf, (0, 0))
        sun_x = WIDTH - 100 - int(self.scroll * 0.01)
        pygame.draw.circle(screen, (255, 252, 230), (sun_x, 85), 55)
        pygame.draw.circle(screen, (255, 255, 245), (sun_x - 10, 75), 35)
        
        for c in self.clouds:
            cs = pygame.Surface((int(c["w"]), 60), pygame.SRCALPHA)
            pygame.draw.ellipse(cs, (255, 255, 255, 200), (0, 20, c["w"], 35))
            pygame.draw.ellipse(cs, (255, 255, 255, 200), (int(c["w"] * 0.15), 5, int(c["w"] * 0.5), 40))
            pygame.draw.ellipse(cs, (255, 255, 255, 200), (int(c["w"] * 0.4), 10, int(c["w"] * 0.45), 35))
            screen.blit(cs, (int(c["x"]), int(c["y"])))
        
        for b in self.birds:
            bx, by = int(b["x"]), int(b["y"])
            wy = int(math.sin(b["wing"]) * 6)
            pygame.draw.line(screen, (50, 45, 45), (bx, by), (bx - 10, by + wy), 2)
            pygame.draw.line(screen, (50, 45, 45), (bx, by), (bx + 10, by + wy), 2)
            
        hill_bg = (85, 125, 100)
        for i in range(-1, 3):
            hx = i * 800 - int(self.scroll * 0.05) % 800
            pygame.draw.ellipse(screen, hill_bg, (hx, HEIGHT - 220, 1000, 400))
        
        for t in self.far_trees:
            x = (t["x"] - self.scroll * 0.08) % (len(self.far_trees) * 90) - 50
            self._tree(screen, x, HEIGHT - 110, t["h"], t["w"], self.far_col, distant=True)
            
        hill_mid = (75, 115, 85)
        for i in range(-1, 3):
            hx = i * 600 - int(self.scroll * 0.15) % 600
            pygame.draw.ellipse(screen, hill_mid, (hx, HEIGHT - 160, 800, 300))
            
        for t in self.mid_trees:
            x = (t["x"] - self.scroll * 0.3) % (len(self.mid_trees) * 110) - 70
            self._tree(screen, x, HEIGHT - 90, t["h"], t["w"], self.mid_col)
            
        pygame.draw.rect(screen, self.ground_col, (0, HEIGHT - 100, WIDTH, 100))
        pygame.draw.ellipse(screen, self.ground_col, (-100, HEIGHT - 140, WIDTH + 200, 100))
        
        pygame.draw.ellipse(screen, self.path_col, (-35, HEIGHT - 65, WIDTH + 70, 65))
        pygame.draw.ellipse(screen, lighten(self.path_col, 1.08), (-15, HEIGHT - 55, WIDTH + 30, 40))
        for i in range(25):
            px = (i * 55 + int(self.scroll * 0.6) + 20) % WIDTH
            py = HEIGHT - 50 + math.sin(i * 1.3) * 12
            pygame.draw.ellipse(screen, darken(self.path_col, 0.88), (px, int(py), 14, 6))
            
        for obj in self.ground:
            x = (obj["x"] - self.scroll * 0.55) % (len(self.ground) * 70) - 40
            s = obj["size"]
            base_y = HEIGHT - 90
            if obj["type"] == "bush":
                for i in range(4): pygame.draw.circle(screen, (65, 125, 75), (int(x + (i - 1.5) * 10 * s), int(base_y - 6 * s + abs(i - 1.5) * 4)), int(12 * s))
            elif obj["type"] == "flowers":
                colors =[(255, 185, 205), (255, 225, 155), (205, 185, 255)]
                for i in range(3):
                    fx = x + (i - 1) * 9 * s
                    pygame.draw.line(screen, (85, 145, 75), (int(fx), base_y + 5), (int(fx), base_y - int(8 * s)), 2)
                    pygame.draw.circle(screen, colors[i], (int(fx), base_y - int(8 * s) - 2), int(5 * s))
                    pygame.draw.circle(screen, (255, 225, 105), (int(fx), base_y - int(8 * s) - 2), int(2 * s))
            elif obj["type"] == "mushroom":
                pygame.draw.rect(screen, (245, 235, 215), (int(x - 4 * s), base_y - int(8 * s), int(8 * s), int(10 * s)), border_radius=2)
                pygame.draw.ellipse(screen, (205, 75, 75), (int(x - 11 * s), base_y - 5 - int(12 * s), int(22 * s), int(12 * s)))
                pygame.draw.circle(screen, (255, 255, 255), (int(x - 4 * s), base_y - 2 - int(10 * s)), int(2 * s))
            elif obj["type"] == "rock":
                pygame.draw.polygon(screen, (125, 120, 110),[(x - 12 * s, base_y + 2), (x - 10 * s, base_y - 6 * s), (x + 8 * s, base_y - 8 * s), (x + 12 * s, base_y + 2)])
            elif obj["type"] == "grass":
                for i in range(5): pygame.draw.line(screen, (85, 155, 85), (int(x + (i - 2) * 3.5 * s), base_y + 2), (int(x + (i - 2) * 1.5), base_y - int(10 * s)), 2)
            elif obj["type"] == "fern":
                for i in range(7):
                    fy = base_y + 2 - i * 4 * s
                    lw = (7 - i) * 2.5 * s
                    pygame.draw.line(screen, (70, 140, 80), (int(x - lw), int(fy)), (int(x), int(fy - 3)), 2)
                    pygame.draw.line(screen, (70, 140, 80), (int(x + lw), int(fy)), (int(x), int(fy - 3)), 2)
                    
        for p in self.particles:
            alpha = int(100 + 80 * math.sin(self.time / 35 + p["phase"]))
            ps = pygame.Surface((p["size"] * 2 + 4, p["size"] * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ps, (255, 255, 220, alpha), (p["size"] + 2, p["size"] + 2), p["size"])
            screen.blit(ps, (int(p["x"]) - p["size"] - 2, int(p["y"]) - p["size"] - 2))
        for leaf in self.leaves:
            lx = leaf["x"] - self.scroll * 0.25
            if -20 < lx < WIDTH + 20:
                ls = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.polygon(ls, leaf["color"],[(8, 1), (14, 8), (8, 15), (2, 8)])
                pygame.draw.line(ls, darken(leaf["color"], 0.7), (8, 2), (8, 14), 1)
                rot = pygame.transform.rotate(ls, leaf["rot"])
                screen.blit(rot, (int(lx) - rot.get_width()//2, int(leaf["y"]) - rot.get_height()//2))
                
    def _tree(self, screen, x, base, h, w, color, distant=False):
        tw, th = w // 4, h // 3
        pygame.draw.rect(screen, (100, 85, 70) if distant else (80, 60, 45), (int(x - tw//2), int(base - th), tw, th))
        for i in range(3 if distant else 4):
            ly = base - th - i * (h // 5)
            lw, lh = w - i * (w // 6), h // 4
            lc = lighten(color, 1.0 + i * 0.05) if i % 2 == 0 else color
            pygame.draw.polygon(screen, lc,[(int(x), int(ly - lh)), (int(x - lw // 2), int(ly)), (int(x + lw // 2), int(ly))])

# ---------------------------------------------------------------------------
# Main Game
# ---------------------------------------------------------------------------
def run_game():
    pygame.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Relaxing Forest Walk")
    clock = pygame.time.Clock()
    
    fonts = {
        "ui": pygame.font.SysFont("arial", 18, bold=True),
        "small": pygame.font.SysFont("arial", 14),
        "bubble": pygame.font.SysFont("arial", 20),
        "note": pygame.font.SysFont("arial", 26),
    }
    
    sounds = SoundManager()
    forest = ForestScene()
    blob = Blob(x=WIDTH // 2, y=HEIGHT - 55)
    typing = TypingText(sounds)
    events = EventManager(blob, sounds, typing)
    
    footstep_timer = 0
    running = True
    
    while running:
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                elif event.key == pygame.K_SPACE: blob.jump()
        
        blob.update()
        forest.update(blob.vx)
        events.update()
        typing.update()
        
        if blob.is_walking:
            footstep_timer += 1
            if footstep_timer >= 22:
                sounds.play("footstep")
                footstep_timer = 0
        
        forest.draw(screen)
        events.draw_behind(screen)
        blob.draw(screen)
        events.draw(screen, fonts)
        
        if typing.active:
            hx, hy = blob.get_head_pos()
            typing.draw(screen, hx, hy, fonts["bubble"])
            
        if events.night_alpha > 0:
            dark_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dark_surf.fill((10, 15, 35, int(events.night_alpha)))
            screen.blit(dark_surf, (0, 0))
            events.draw_night_layer(screen)

        # Cold event: frost vignette around edges
        if events.event and events.event.type == "cold" and not events.event.data.get("has_scarf"):
            frost_strength = min(1.0, events.event.timer / 60)
            frost = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for fi in range(4):
                thick = 30 + fi * 20
                falpha = int(frost_strength * (60 - fi * 12))
                if falpha > 0:
                    pygame.draw.rect(frost, (200, 225, 255, falpha), (fi * 8, fi * 8, WIDTH - fi * 16, HEIGHT - fi * 16), thick)
            screen.blit(frost, (0, 0))

        # Coffee event: speed lines at edges when energized
        if events.event and events.event.type == "coffee" and events.event.phase == 1:
            for _ in range(2):
                ly2 = random.randint(0, HEIGHT)
                llen = random.randint(60, 160)
                lalpha = random.randint(30, 80)
                ls2 = pygame.Surface((llen, 3), pygame.SRCALPHA)
                pygame.draw.line(ls2, (255, 235, 150, lalpha), (0, 1), (llen, 1), 2)
                screen.blit(ls2, (0, ly2))
            
        ui = pygame.Surface((WIDTH, 32), pygame.SRCALPHA)
        ui.fill((0, 0, 0, 50))
        screen.blit(ui, (0, 0))
        
        screen.blit(fonts["ui"].render("Relaxing Forest Walk", True, (255, 255, 255)), (18, 6))
        mood = fonts["small"].render(f"Mood: {blob.expression}", True, (225, 225, 230))
        screen.blit(mood, (WIDTH - mood.get_width() - 18, 8))
        
        if blob.coins > 0:
            coin_txt = fonts["small"].render(f"x {blob.coins}", True, (255, 220, 100))
            pygame.draw.circle(screen, (255, 210, 60), (WIDTH - coin_txt.get_width() - 42, 34), 7)
            pygame.draw.circle(screen, (200, 160, 40), (WIDTH - coin_txt.get_width() - 42, 34), 7, 1)
            screen.blit(coin_txt, (WIDTH - coin_txt.get_width() - 18, 28))
            
        hint = fonts["small"].render("Space: Jump  |  ESC: Exit  |  Just relax and watch~", True, (210, 210, 215))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 22))
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    run_game()