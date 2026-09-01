import sys
import os
import math
import random
import shutil
import threading
import array
import tkinter as tk
from tkinter import filedialog, messagebox
import pygame

pygame.init()
pygame.font.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2)

WIDTH, HEIGHT = 980, 640
FPS = 60

COLOR_BG = (10, 10, 12)
COLOR_CARD = (18, 18, 20)
COLOR_CARD_BORDER = (35, 35, 40)
COLOR_GOLD = (250, 204, 21)
COLOR_GOLD_HOVER = (234, 179, 8)
COLOR_TEXT_MAIN = (255, 255, 255)
COLOR_TEXT_MUTED = (140, 140, 150)
COLOR_DANGER = (239, 68, 68)
COLOR_DANGER_HOVER = (220, 38, 38)

# ==========================================
# 1. Sound Generator Engine
# ==========================================
class SoundEngine:
    @staticmethod
    def generate_sound(freq, duration_ms, wave_type="sine", fade=True):
        sample_rate = 44100
        n_samples = int(sample_rate * (duration_ms / 1000.0))
        buf = array.array('h', [0] * n_samples)
        amplitude = 12000

        for i in range(n_samples):
            t = float(i) / sample_rate
            if wave_type == "sine":
                val = math.sin(2.0 * math.pi * freq * t)
            elif wave_type == "square":
                val = 1.0 if math.sin(2.0 * math.pi * freq * t) > 0 else -1.0

            if fade:
                env = 1.0 - (i / n_samples)
                val *= env

            buf[i] = int(val * amplitude)

        stereo = array.array('h', [0] * (n_samples * 2))
        for i in range(n_samples):
            stereo[i*2] = buf[i]
            stereo[i*2 + 1] = buf[i]

        sound = pygame.mixer.Sound(buffer=stereo)
        sound.set_volume(0.15)
        return sound

    def __init__(self):
        try:
            self.snd_click = self.generate_sound(580, 40, "sine")
            self.snd_success = self.generate_sound(880, 120, "sine")
            self.snd_undo = self.generate_sound(440, 90, "sine")
        except Exception:
            self.snd_click = self.snd_success = self.snd_undo = None

    def play_click(self):
        if self.snd_click: self.snd_click.play()

    def play_success(self):
        if self.snd_success: self.snd_success.play()

    def play_undo(self):
        if self.snd_undo: self.snd_undo.play()

# ==========================================
# 2. File Organizer & Undo Engine (Core Logic)
# ==========================================
class FileOrganizer:
    def __init__(self):
        self.selected_path = ""
        self.history = []
        self.last_stats = 0

    def select_folder(self):
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder = filedialog.askdirectory(title="Select Target Directory")
        root.destroy()
        if folder:
            self.selected_path = folder
            return folder
        return None

    def organize_async(self, progress_callback, completion_callback):
        def worker():
            if not self.selected_path or not os.path.exists(self.selected_path):
                completion_callback(False, "Invalid folder path!")
                return

            files = [f for f in os.listdir(self.selected_path) if os.path.isfile(os.path.join(self.selected_path, f))]
            total = len(files)
            
            if total == 0:
                completion_callback(False, "Selected folder is empty!")
                return

            self.history.clear()
            moved_count = 0

            for i, filename in enumerate(files):
                old_path = os.path.join(self.selected_path, filename)
                ext = os.path.splitext(filename)[1].replace(".", "").upper()
                
                if ext:
                    new_dir = os.path.join(self.selected_path, ext)
                    if not os.path.exists(new_dir):
                        os.makedirs(new_dir)
                    new_path = os.path.join(new_dir, filename)
                    shutil.move(old_path, new_path)
                    self.history.append((new_path, old_path))
                    moved_count += 1
                
                progress_callback((i + 1) / total)
                pygame.time.wait(25)

            self.last_stats = moved_count
            completion_callback(True, f"DONE! {moved_count} Files Organized")

        threading.Thread(target=worker, daemon=True).start()

    def undo_async(self, completion_callback):
        def worker():
            if not self.history:
                completion_callback(False, "No previous actions to undo!")
                return

            restored = 0
            for current_path, original_path in self.history:
                if os.path.exists(current_path):
                    shutil.move(current_path, original_path)
                    restored += 1
                    folder = os.path.dirname(current_path)
                    if os.path.exists(folder) and not os.listdir(folder):
                        os.rmdir(folder)

            self.history.clear()
            self.last_stats = 0
            completion_callback(True, f"RESTORED! {restored} Files Reverted")

        threading.Thread(target=worker, daemon=True).start()

# ==========================================
# 3. UI Helpers & Toast Notifications
# ==========================================
class UIHelper:
    @staticmethod
    def draw_rounded_rect_with_shadow(surface, rect, color, radius=18, shadow_blur=15, shadow_offset=(0, 6)):
        shadow_surf = pygame.Surface((rect.w + shadow_blur * 2, rect.h + shadow_blur * 2), pygame.SRCALPHA)
        for i in range(shadow_blur, 0, -2):
            alpha = int(12 * (1 - i / shadow_blur))
            shadow_rect = pygame.Rect(shadow_blur - i + shadow_offset[0], shadow_blur - i + shadow_offset[1], rect.w + i*2, rect.h + i*2)
            pygame.draw.rect(shadow_surf, (0, 0, 0, alpha), shadow_rect, border_radius=radius + i//2)
        
        surface.blit(shadow_surf, (rect.x - shadow_blur, rect.y - shadow_blur))
        pygame.draw.rect(surface, color, rect, border_radius=radius)

class LampNotification:
    def __init__(self, cx, y, font):
        self.cx = cx
        self.y = y
        self.font = font
        self.text = ""
        self.alpha = 0.0
        self.target_alpha = 0.0
        self.timer = 0
        self.bg_color = COLOR_GOLD

    def show(self, text, duration_frames=180, is_error=False):
        self.text = text
        self.target_alpha = 255.0
        self.timer = duration_frames
        self.bg_color = COLOR_DANGER if is_error else COLOR_GOLD

    def update(self):
        if self.timer > 0:
            self.timer -= 1
            if self.timer == 0:
                self.target_alpha = 0.0
        self.alpha += (self.target_alpha - self.alpha) * 0.1

    def draw(self, surface):
        if self.alpha < 5: return

        txt_color = (255, 255, 255) if self.bg_color == COLOR_DANGER else (0, 0, 0)
        txt_surf = self.font.render(self.text, True, txt_color)
        w, h = txt_surf.get_width() + 36, txt_surf.get_height() + 16
        rect = pygame.Rect(self.cx - w // 2, self.y, w, h)

        popup_surf = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
        alpha_int = int(self.alpha)
        
        pygame.draw.rect(popup_surf, (*self.bg_color, alpha_int), (10, 10, w, h), border_radius=12)
        txt_surf.set_alpha(alpha_int)
        popup_surf.blit(txt_surf, (10 + (w - txt_surf.get_width()) // 2, 10 + (h - txt_surf.get_height()) // 2))

        surface.blit(popup_surf, (rect.x - 10, rect.y - 10))

# ==========================================
# 4. Particles & Reactive Lamp UI
# ==========================================
class Particle:
    def __init__(self, bounds_x, bounds_y):
        self.reset(bounds_x, bounds_y)

    def reset(self, bounds_x, bounds_y):
        self.x = random.uniform(bounds_x[0], bounds_x[1])
        self.y = random.uniform(bounds_y[0], bounds_y[1])
        self.size = random.uniform(1.2, 3.2)
        self.alpha = random.randint(80, 220)
        self.speed_y = random.uniform(-0.5, -0.1)
        self.speed_x = random.uniform(-0.15, 0.15)

    def update(self, bounds_x, bounds_y):
        self.y += self.speed_y
        self.x += self.speed_x
        self.alpha -= 0.4
        if self.alpha <= 0 or self.y < bounds_y[0]:
            self.reset(bounds_x, bounds_y)

class ReactiveLamp:
    def __init__(self, center_x, top_y):
        self.cx = center_x
        self.top_y = top_y
        self.lamp_y = top_y + 130
        self.state = "IDLE"
        self.current_glow = 0.25
        self.target_glow = 0.25
        self.pulse_timer = 0.0
        self.particles = [Particle((self.cx - 110, self.cx + 110), (self.lamp_y + 30, HEIGHT)) for _ in range(40)]

    def set_state(self, new_state):
        self.state = new_state
        if self.state == "IDLE": self.target_glow = 0.25
        elif self.state in ["READY", "PROCESSING"]: self.target_glow = 1.0

    def update(self):
        if self.state == "PROCESSING":
            self.pulse_timer += 0.08
            pulse = (math.sin(self.pulse_timer) + 1) / 2
            self.current_glow = 0.65 + (pulse * 0.35)
        else:
            self.current_glow += (self.target_glow - self.current_glow) * 0.07

        if self.current_glow > 0.1:
            for p in self.particles:
                p.update((self.cx - 130 * self.current_glow, self.cx + 130 * self.current_glow), (self.lamp_y + 30, HEIGHT))

    def draw(self, surface):
        pygame.draw.line(surface, (70, 70, 75), (self.cx, 0), (self.cx, self.lamp_y), 3)
        pygame.draw.arc(surface, (30, 30, 35), (self.cx - 55, self.lamp_y - 28, 110, 56), 0, math.pi, 0)

        if self.current_glow > 0.05:
            cone_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            points = [
                (self.cx - 25, self.lamp_y + 15),
                (self.cx + 25, self.lamp_y + 15),
                (self.cx + 220 * self.current_glow, HEIGHT),
                (self.cx - 220 * self.current_glow, HEIGHT)
            ]
            alpha_base = int(55 * self.current_glow)
            pygame.draw.polygon(cone_surf, (250, 204, 21, alpha_base), points)
            pygame.draw.polygon(cone_surf, (255, 230, 100, int(alpha_base * 0.5)), points)
            surface.blit(cone_surf, (0, 0))

            for p in self.particles:
                p_surf = pygame.Surface((int(p.size*2), int(p.size*2)), pygame.SRCALPHA)
                p_alpha = int(p.alpha * self.current_glow)
                pygame.draw.circle(p_surf, (250, 215, 60, p_alpha), (p.size, p.size), p.size)
                surface.blit(p_surf, (p.x, p.y))

        bulb_color = (int(250 * self.current_glow), int(204 * self.current_glow), int(21 * self.current_glow))
        pygame.draw.ellipse(surface, bulb_color, (self.cx - 40, self.lamp_y, 80, 22))

class SmoothButton:
    def __init__(self, x, y, w, h, text, callback, font, fg_color=COLOR_GOLD, hover_color=COLOR_GOLD_HOVER):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.font = font
        self.fg_color = fg_color
        self.hover_color = hover_color
        self.is_hovered = False
        self.enabled = True

    def draw(self, surface):
        color = self.hover_color if (self.is_hovered and self.enabled) else self.fg_color
        if not self.enabled: color = (35, 35, 40)

        UIHelper.draw_rounded_rect_with_shadow(surface, self.rect, color, radius=14, shadow_blur=10 if self.is_hovered else 6)
        text_color = (255, 255, 255) if color in [COLOR_DANGER, COLOR_DANGER_HOVER] else ((0, 0, 0) if (self.enabled and color in [self.fg_color, self.hover_color]) else (100, 100, 110))
        txt_surf = self.font.render(self.text, True, text_color)
        surface.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.enabled:
                self.callback()

# ==========================================
# 5. Main App Loop
# ==========================================
class App:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("vRMZ Smart File Organizer - Enterprise Edition")
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("Arial Black", 40)
        self.font_sub = pygame.font.SysFont("Helvetica", 13, bold=True)
        self.font_btn = pygame.font.SysFont("Helvetica", 15, bold=True)
        self.font_toast = pygame.font.SysFont("Helvetica", 14, bold=True)

        self.sound = SoundEngine()
        self.organizer = FileOrganizer()
        self.lamp = ReactiveLamp(center_x=230, top_y=0)
        self.notification = LampNotification(cx=230, y=280, font=self.font_toast)

        card_w, card_h = 400, 520
        card_x, card_y = 510, 55
        self.card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

        self.btn_browse = SmoothButton(card_x + 50, card_y + 160, 300, 50, "BROWSE FOLDER", self.on_browse, self.font_btn, fg_color=(45, 45, 50), hover_color=(60, 60, 68))
        self.btn_start = SmoothButton(card_x + 50, card_y + 290, 300, 55, "START ORGANIZING", self.on_start, self.font_btn, fg_color=COLOR_GOLD)
        self.btn_undo = SmoothButton(card_x + 50, card_y + 430, 300, 45, "↩ UNDO LAST ACTION", self.on_undo, self.font_btn, fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER)
        
        self.btn_start.enabled = False
        self.btn_undo.enabled = False
        self.progress_val = 0.0

    def on_browse(self):
        self.sound.play_click()
        folder = self.organizer.select_folder()
        if folder:
            self.btn_start.enabled = True
            self.lamp.set_state("READY")

    def on_start(self):
        self.sound.play_click()
        self.btn_start.enabled = False
        self.btn_browse.enabled = False
        self.btn_undo.enabled = False
        self.lamp.set_state("PROCESSING")

        def on_progress(val):
            self.progress_val = val

        def on_complete(success, msg):
            self.progress_val = 0.0
            self.btn_browse.enabled = True
            self.lamp.set_state("READY")
            
            if success:
                self.sound.play_success()
                self.notification.show(msg)
                self.btn_undo.enabled = True
            else:
                self.notification.show(msg, is_error=True)
                self.btn_start.enabled = True

        self.organizer.organize_async(on_progress, on_complete)

    def on_undo(self):
        self.sound.play_click()
        self.btn_undo.enabled = False
        self.btn_start.enabled = False
        self.btn_browse.enabled = False

        def on_undo_complete(success, msg):
            self.btn_browse.enabled = True
            if self.organizer.selected_path:
                self.btn_start.enabled = True

            if success:
                self.sound.play_undo()
                self.notification.show(msg)
            else:
                self.notification.show(msg, is_error=True)

        self.organizer.undo_async(on_undo_complete)

    def render(self):
        self.screen.fill(COLOR_BG)

        self.lamp.update()
        self.lamp.draw(self.screen)

        self.notification.update()
        self.notification.draw(self.screen)

        UIHelper.draw_rounded_rect_with_shadow(self.screen, self.card_rect, COLOR_CARD, radius=22, shadow_blur=20)
        pygame.draw.rect(self.screen, COLOR_CARD_BORDER, self.card_rect, width=1, border_radius=22)

        title_surf = self.font_title.render("vRMZ", True, COLOR_GOLD)
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.card_rect.centerx, self.card_rect.top + 60)))

        sub_surf = self.font_sub.render("SMART FILE ORGANIZER", True, COLOR_TEXT_MUTED)
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(self.card_rect.centerx, self.card_rect.top + 105)))

        path_text = self.organizer.selected_path if self.organizer.selected_path else "No directory selected"
        if len(path_text) > 32: path_text = "..." + path_text[-29:]
        path_surf = self.font_sub.render(path_text, True, COLOR_GOLD if self.organizer.selected_path else COLOR_TEXT_MUTED)
        self.screen.blit(path_surf, path_surf.get_rect(center=(self.card_rect.centerx, self.card_rect.top + 230)))

        pb_rect = pygame.Rect(self.card_rect.left + 50, self.card_rect.top + 260, 300, 10)
        pygame.draw.rect(self.screen, (35, 35, 40), pb_rect, border_radius=5)
        if self.progress_val > 0:
            pb_fill = pygame.Rect(pb_rect.left, pb_rect.top, int(pb_rect.width * self.progress_val), 10)
            pygame.draw.rect(self.screen, COLOR_GOLD, pb_fill, border_radius=5)

        self.btn_browse.draw(self.screen)
        self.btn_start.draw(self.screen)
        self.btn_undo.draw(self.screen)

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                self.btn_browse.handle_event(event)
                self.btn_start.handle_event(event)
                self.btn_undo.handle_event(event)

            self.render()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = App()
    app.run()