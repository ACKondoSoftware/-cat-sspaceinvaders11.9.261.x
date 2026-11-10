#!/usr/bin/env python3
# cat's space invaders 0.1.1.1
# single file / pygame / files = off / 160x192 atari-style playfield @ 60 fps
# pip install pygame ; python cats_space_invaders.py
import sys
import random
import array
import pygame

TITLE = "Space Invaders Classic - AC Kondo 0.1.1.1"
W, H = 160, 192          # 2600-style playfield
SX, SY = 4, 3            # wide pixels, like the real thing
FPS = 60
RATE = 22050

BLACK = (0, 0, 0)
WHITE = (236, 236, 236)
GREY = (142, 142, 142)
GREEN = (92, 186, 92)
GROUND = (110, 156, 66)
ORANGE = (214, 132, 60)
YELLOW = (220, 212, 72)
RED = (212, 82, 74)
PINK = (214, 112, 176)
PURPLE = (150, 96, 214)
BLUE = (84, 138, 210)
CYAN = (88, 196, 196)
ROW_COLORS = [YELLOW, ORANGE, PINK, PURPLE, BLUE, CYAN]
ROW_POINTS = [30, 25, 20, 15, 10, 5]

# ----------------------------------------------------------------- 3x5 font
FONT = {
    "A": "010101111101101", "B": "110101110101110", "C": "011100100100011",
    "D": "110101101101110", "E": "111100110100111", "F": "111100110100100",
    "G": "011100101101011", "H": "101101111101101", "I": "111010010010111",
    "J": "001001001101010", "K": "101101110101101", "L": "100100100100111",
    "M": "101111111101101", "N": "110101101101101", "O": "010101101101010",
    "P": "110101110100100", "Q": "010101101110011", "R": "110101110101101",
    "S": "011100010001110", "T": "111010010010010", "U": "101101101101111",
    "V": "101101101101010", "W": "101101111111101", "X": "101101010101101",
    "Y": "101101010010010", "Z": "111001010100111",
    "0": "111101101101111", "1": "010110010010111", "2": "110001010100111",
    "3": "110001010001110", "4": "101101111001001", "5": "111100110001110",
    "6": "011100111101111", "7": "111001010010010", "8": "111101111101111",
    "9": "111101111001110",
    ".": "000000000000010", ",": "000000000010100", "'": "010010000000000",
    "-": "000000111000000", ":": "000010000010000", "!": "010010010000010",
    "(": "001010010010001", ")": "100010010010100", "/": "001001010100100",
    ">": "100010001010100", "=": "000111000111000", "?": "110001010000010",
    " ": "000000000000000",
}
_text_cache = {}


def render(text, color, scale=1):
    key = (text, color, scale)
    s = _text_cache.get(key)
    if s is None:
        text = text.upper()
        s = pygame.Surface((max(1, len(text) * 4 * scale), 5 * scale), pygame.SRCALPHA)
        for i, ch in enumerate(text):
            bits = FONT.get(ch, FONT["?"])
            for b, v in enumerate(bits):
                if v == "1":
                    s.fill(color, (i * 4 * scale + (b % 3) * scale, (b // 3) * scale, scale, scale))
        _text_cache[key] = s
    return s


def text(surf, msg, x, y, color=WHITE, scale=1, center=False):
    s = render(msg, color, scale)
    if center:
        x = (W - (s.get_width() - scale)) // 2
    surf.blit(s, (x, y))


# ------------------------------------------------------------------ sprites
# Classic arcade-inspired invader silhouettes: squid, crab, octopus.
# Two animation frames for each type, with no external image assets.
SQUID_A = ["...XX...", "..XXXX..", ".XXXXXX.", "XX.XX.XX", "XXXXXXXX", "..X..X..", ".X.XX.X.", "X......X"]
SQUID_B = ["...XX...", "..XXXX..", ".XXXXXX.", "XX.XX.XX", "XXXXXXXX", ".X.XX.X.", "X.X..X.X", "..X..X.."]
CRAB_A = [".X....X.", "..X..X..", ".XXXXXX.", "XX.XX.XX", "XXXXXXXX", "X.XXXX.X", "X.X..X.X", "..X..X.."]
CRAB_B = [".X....X.", "X.X..X.X", "X.XXXX.X", "XXXXXXXX", "XX.XX.XX", ".XXXXXX.", "..X..X..", ".X....X."]
OCTOPUS_A = ["..XXXX..", ".XXXXXX.", "XXXXXXXX", "XX.XX.XX", "XXXXXXXX", "..X..X..", ".X.XX.X.", "X.X..X.X"]
OCTOPUS_B = ["..XXXX..", ".XXXXXX.", "XXXXXXXX", "XX.XX.XX", "XXXXXXXX", ".X.XX.X.", "X..XX..X", "..X..X.."]
BOOM = ["X..X..X.", ".X....X.", "..X..X..", "XX....XX", "..X..X..", ".X....X.", "X..X...X", "........"]
SHIP = ["...X...", "..XXX..", "..XXX..", "XXXXXXX", "XXXXXXX"]
SHIP_X = ["X..X..X", ".X...X.", "..X.X..", ".XXXXX.", "XX.X.XX"]
UFO = ["...XXX...", "..XXXXX..", ".XXXXXXX.", "XXXXXXXXX", "XX.X.X.XX"]


def sprite(rows, color):
    s = pygame.Surface((len(rows[0]), len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == "X":
                s.set_at((x, y), color)
    return s


# -------------------------------------------------------------------- sound
class Snd:
    """TIA-flavoured square + polynomial-noise beeps, synthesized at boot."""

    def __init__(self):
        self.s = {}
        init = pygame.mixer.get_init()
        self.ok = bool(init)
        if not self.ok:
            return
        self.ch = init[2]
        mk = self._tone
        self.s["shoot"] = mk(980, 260, 130)
        self.s["hit"] = mk(1900, 380, 150, noise=True)
        self.s["die"] = mk(700, 50, 700, vol=0.4, noise=True)
        self.s["ufohit"] = mk(1400, 180, 260)
        self.s["ufo0"] = mk(620, 620, 50, vol=0.18)
        self.s["ufo1"] = mk(830, 830, 50, vol=0.18)
        self.s["move"] = mk(440, 440, 35, vol=0.25)
        self.s["select"] = mk(660, 1320, 110, vol=0.3)
        self.s["wave"] = mk(330, 990, 300, vol=0.3)
        for i, f in enumerate((110, 98, 87, 78)):
            self.s["m%d" % i] = mk(f, f, 70, vol=0.45)

    def _tone(self, f0, f1, ms, vol=0.3, noise=False):
        n = int(RATE * ms / 1000)
        buf = array.array("h")
        amp = int(32767 * vol)
        phase, lfsr = 0.0, 0x1FF
        for i in range(n):
            f = f0 + (f1 - f0) * i / n
            phase += f / RATE
            if phase >= 1.0:
                phase -= 1.0
                if noise:  # 9-bit poly counter clocked at the tone rate
                    bit = (lfsr ^ (lfsr >> 4)) & 1
                    lfsr = (lfsr >> 1) | (bit << 8)
            if noise:
                v = amp if lfsr & 1 else -amp
            else:
                v = amp if phase < 0.5 else -amp
            if n - i < 200:
                v = v * (n - i) // 200
            for _ in range(self.ch):
                buf.append(v)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def play(self, name):
        if self.ok:
            self.s[name].play()


# --------------------------------------------------------------------- game
COLS, ROWS = 6, 6
CELL_W, CELL_H = 16, 11
PLAYER_Y = 172
SHIELD_Y = 146
MENU = ["PLAY GAME", "HELP", "ABOUT", "COPYRIGHT", "EXIT"]

HELP_TEXT = [
    "LEFT / RIGHT OR A / D    MOVE",
    "SPACE                    FIRE",
    "P                       PAUSE",
    "ESC                      MENU",
    "",
    "ONE SHOT ON SCREEN AT A TIME.",
    "TOP ROWS SCORE MORE.",
    "THE UFO IS WORTH 100.",
    "BUNKERS BLOCK ENEMY FIRE.",
    "DON'T LET THEM LAND.",
]
ABOUT_TEXT = [
    "SPACE INVADERS",
    "VERSION 0.1.1.1",
    "",
    "SINGLE FILE PYTHON + PYGAME",
    "160X192 PLAYFIELD, WIDE PIXELS",
    "60 FPS FIXED-STEP ENGINE",
    "SQUARE + POLY NOISE BEEPS",
    "SYNTHESIZED AT BOOT",
    "FILES = OFF",
]
COPYRIGHT_TEXT = [
    "(C) 2026 A.C HOLDINGS",
    "TEAM FLAMES",
    "",
    "ARCADE-STYLE PIXEL SPRITES",
    "DRAWN IN PYTHON AT RUNTIME.",
    "",
    "A FAN TRIBUTE. NOT AFFILIATED",
    "WITH OR ENDORSED BY TAITO",
    "OR ATARI.",
]


class Game:
    def __init__(self, snd):
        self.snd = snd
        self.invader_sprites = [(sprite(a, c), sprite(b, c)) for (a, b), c in zip([(SQUID_A, SQUID_B)] + [(CRAB_A, CRAB_B)] * 2 + [(OCTOPUS_A, OCTOPUS_B)] * 3, ROW_COLORS)]
        self.boom = sprite(BOOM, WHITE)
        self.ship = sprite(SHIP, GREEN)
        self.ship_x = sprite(SHIP_X, ORANGE)
        self.ufo_spr = (sprite(UFO, RED), pygame.transform.flip(sprite(UFO, RED), True, False))
        self.state = "menu"
        self.sel = 0
        self.tick = 0
        self.hi = 0
        self.score = 0
        self.lives = 3
        self.wave = 0
        self.paused = False
        self.running = True
        self.new_wave()

    # ---- setup
    def new_game(self):
        self.score, self.lives, self.wave = 0, 3, 0
        self.paused = False
        self.new_wave()
        self.state = "play"

    def new_wave(self):
        self.inv = [[True] * COLS for _ in range(ROWS)]
        self.ix = 36
        self.iy = 24 + min(self.wave, 5) * 6
        self.idir = 1
        self.frame = 0
        self.step_t = 0
        self.note = 0
        self.shot = None
        self.bombs = []
        self.booms = []
        self.px = W / 2 - 3
        self.dead_t = 0
        self.ufo = None
        self.ufo_t = FPS * random.randint(10, 18)
        self.sh = set()
        for bx in (28, 72, 116):
            for y in range(9):
                for x in range(16):
                    if y < 2 and (x < 2 - y or x > 13 + y):
                        continue
                    if y >= 6 and 5 <= x <= 10:
                        continue
                    self.sh.add((bx + x, SHIELD_Y + y))

    # ---- helpers
    def alive(self):
        return [(r, c) for r in range(ROWS) for c in range(COLS) if self.inv[r][c]]

    def inv_rect(self, r, c):
        return pygame.Rect(self.ix + c * CELL_W, self.iy + r * CELL_H, 8, 8)

    def erode(self, cx, cy):
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if random.random() < 0.7:
                    self.sh.discard((cx + dx, cy + dy))

    def hit_shield(self, x, y, h):
        x = int(x)
        for yy in range(int(y), int(y) + h):
            if (x, yy) in self.sh:
                self.erode(x, yy)
                return True
        return False

    def kill_player(self, final=False):
        self.snd.play("die")
        self.lives = 0 if final else self.lives - 1
        self.dead_t = 100
        self.bombs = []
        self.shot = None

    # ---- input
    def key(self, k):
        if self.state == "menu":
            if k in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(MENU)
                self.snd.play("move")
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(MENU)
                self.snd.play("move")
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.snd.play("select")
                item = MENU[self.sel]
                if item == "PLAY GAME":
                    self.new_game()
                elif item == "EXIT":
                    self.running = False
                else:
                    self.state = item.lower()
            elif k == pygame.K_ESCAPE:
                self.running = False
        elif self.state in ("help", "about", "copyright", "over"):
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
                self.snd.play("select")
                self.state = "menu"
        elif self.state == "play":
            if k == pygame.K_ESCAPE:
                self.hi = max(self.hi, self.score)
                self.state = "menu"
            elif k == pygame.K_p:
                self.paused = not self.paused
                self.snd.play("move")

    # ---- simulation: one call = one 1/60 s frame
    def update(self, keys):
        self.tick += 1
        if self.state != "play" or self.paused:
            return
        self.booms = [[x, y, t - 1] for x, y, t in self.booms if t > 1]

        if self.dead_t:
            self.dead_t -= 1
            if self.dead_t == 0:
                if self.lives <= 0:
                    self.hi = max(self.hi, self.score)
                    self.state = "over"
                else:
                    self.px = W / 2 - 3
            return

        # player
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.px = max(4, self.px - 1.5)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.px = min(W - 11, self.px + 1.5)
        if keys[pygame.K_SPACE] and self.shot is None:
            self.shot = [int(self.px) + 3, PLAYER_Y - 4]
            self.snd.play("shoot")

        alive = self.alive()
        n = len(alive)

        # invader march: fewer invaders = shorter step interval
        self.step_t += 1
        if self.step_t >= max(2, 2 + n * 28 // 36 - min(self.wave, 4) * 2):
            self.step_t = 0
            lo = min(c for _, c in alive)
            hi = max(c for _, c in alive)
            nx = self.ix + 2 * self.idir
            if nx + lo * CELL_W < 4 or nx + hi * CELL_W + 8 > W - 4:
                self.iy += 6
                self.idir = -self.idir
            else:
                self.ix = nx
            self.frame ^= 1
            self.snd.play("m%d" % self.note)
            self.note = (self.note + 1) & 3
            bottom = self.iy + max(r for r, _ in alive) * CELL_H + 8
            if bottom >= SHIELD_Y and self.sh:
                rects = [self.inv_rect(r, c) for r, c in alive]
                self.sh = {p for p in self.sh if not any(q.collidepoint(p) for q in rects)}
            if bottom >= PLAYER_Y:
                self.kill_player(final=True)
                return

        # player shot
        if self.shot:
            self.shot[1] -= 4
            sx, sy = self.shot
            if sy < 10:
                self.shot = None
            elif self.hit_shield(sx, sy, 4):
                self.shot = None
            else:
                r4 = pygame.Rect(sx, sy, 1, 4)
                if self.ufo and r4.colliderect(pygame.Rect(self.ufo[0], 13, 9, 5)):
                    self.booms.append([int(self.ufo[0]), 12, 14])
                    self.ufo = None
                    self.shot = None
                    self.score += 100
                    self.snd.play("ufohit")
                else:
                    for r, c in alive:
                        if r4.colliderect(self.inv_rect(r, c)):
                            self.inv[r][c] = False
                            self.booms.append([self.ix + c * CELL_W, self.iy + r * CELL_H, 10])
                            self.score += ROW_POINTS[r]
                            self.shot = None
                            self.snd.play("hit")
                            n -= 1
                            break

        if n == 0:
            self.wave += 1
            self.snd.play("wave")
            self.new_wave()
            return

        # bombs
        if len(self.bombs) < 2 + min(self.wave, 2) and random.random() < 0.02 + 0.005 * min(self.wave, 6):
            c = random.choice(sorted({c for _, c in alive}))
            r = max(r for r in range(ROWS) if self.inv[r][c])
            self.bombs.append([self.ix + c * CELL_W + 4, float(self.iy + r * CELL_H + 8)])
        speed = min(2.0, 1.2 + 0.1 * self.wave)
        prect = pygame.Rect(int(self.px), PLAYER_Y, 7, 5)
        keep = []
        for b in self.bombs:
            b[1] += speed
            if b[1] > PLAYER_Y + 6 or self.hit_shield(b[0], b[1], 4):
                continue
            if prect.colliderect(pygame.Rect(b[0], int(b[1]), 1, 4)):
                self.kill_player()
                return
            keep.append(b)
        self.bombs = keep

        # bonus UFO
        if self.ufo:
            self.ufo[0] += self.ufo[1] * 0.8
            if self.tick % 8 == 0:
                self.snd.play("ufo%d" % ((self.tick // 8) & 1))
            if self.ufo[0] < -10 or self.ufo[0] > W + 2:
                self.ufo = None
        else:
            self.ufo_t -= 1
            if self.ufo_t <= 0 and self.iy > 22:
                d = random.choice((-1, 1))
                self.ufo = [-9.0 if d > 0 else float(W), d]
                self.ufo_t = FPS * random.randint(14, 24)

    # ---- drawing
    def draw(self, s):
        s.fill(BLACK)
        getattr(self, "draw_" + self.state)(s)

    def draw_menu(self, s):
        text(s, "CLASSIC", 0, 18, YELLOW, 2, center=True)
        text(s, "SPACE INVADERS", 0, 32, GREEN, 2, center=True)
        text(s, "0.1.1.1", 0, 46, GREY, center=True)
        f = (self.tick // 30) & 1
        for i in range(6):
            s.blit(self.invader_sprites[i][f], (36 + i * 16 + (4 if f else 0), 60))
        for i, item in enumerate(MENU):
            y = 86 + i * 12
            on = i == self.sel
            if on and (self.tick // 15) & 1 == 0:
                text(s, ">", 46, y, YELLOW)
            text(s, item, 54, y, WHITE if on else GREY)
        text(s, "HI %05d" % self.hi, 0, 156, ORANGE, center=True)
        s.fill(GROUND, (0, 180, W, 2))
        text(s, "UP/DOWN + ENTER", 0, 184, GREY, center=True)

    def _page(self, s, title, lines):
        text(s, title, 0, 14, YELLOW, 2, center=True)
        for i, ln in enumerate(lines):
            text(s, ln, 0, 40 + i * 10, WHITE, center=True)
        s.fill(GROUND, (0, 180, W, 2))
        text(s, "PRESS ENTER", 0, 184, GREY, center=True)

    def draw_help(self, s):
        self._page(s, "HELP", HELP_TEXT)

    def draw_about(self, s):
        self._page(s, "ABOUT", ABOUT_TEXT)

    def draw_copyright(self, s):
        self._page(s, "COPYRIGHT", COPYRIGHT_TEXT)

    def draw_play(self, s):
        text(s, "%05d" % self.score, 8, 3, GREEN, 1)
        text(s, "HI %05d" % max(self.hi, self.score), 0, 3, ORANGE, center=True)
        text(s, "W%d" % (self.wave + 1), W - 20, 3, GREY)
        for r in range(ROWS):
            spr = self.invader_sprites[r][self.frame]
            for c in range(COLS):
                if self.inv[r][c]:
                    s.blit(spr, (self.ix + c * CELL_W, self.iy + r * CELL_H))
        for x, y, _ in self.booms:
            s.blit(self.boom, (x, y))
        if self.ufo:
            s.blit(self.ufo_spr[0 if self.ufo[1] > 0 else 1], (int(self.ufo[0]), 13))
        for p in self.sh:
            s.set_at(p, ORANGE)
        if self.dead_t:
            if (self.dead_t // 6) & 1:
                s.blit(self.ship_x, (int(self.px), PLAYER_Y))
        else:
            s.blit(self.ship, (int(self.px), PLAYER_Y))
        if self.shot:
            s.fill(WHITE, (self.shot[0], self.shot[1], 1, 4))
        for b in self.bombs:
            s.fill(YELLOW, (b[0], int(b[1]), 1, 4))
        s.fill(GROUND, (0, 180, W, 2))
        for i in range(max(0, self.lives - 1)):
            s.blit(self.ship, (8 + i * 10, 185))
        if self.paused:
            text(s, "PAUSED", 0, 90, WHITE, 2, center=True)

    def draw_over(self, s):
        self.draw_play(s)
        s.fill(BLACK, (24, 78, 112, 36))
        text(s, "GAME OVER", 0, 82, RED, 2, center=True)
        text(s, "SCORE %05d" % self.score, 0, 96, WHITE, center=True)
        text(s, "PRESS ENTER", 0, 105, GREY, center=True)


def main():
    try:
        pygame.mixer.pre_init(RATE, -16, 1, 256)
    except pygame.error:
        pass
    pygame.init()
    screen = pygame.display.set_mode((W * SX, H * SY))
    pygame.display.set_caption(TITLE)
    pygame.mouse.set_visible(False)
    surf = pygame.Surface((W, H)).convert()
    clock = pygame.time.Clock()
    game = Game(Snd())
    while game.running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                game.running = False
            elif e.type == pygame.KEYDOWN:
                game.key(e.key)
        game.update(pygame.key.get_pressed())
        game.draw(surf)
        pygame.transform.scale(surf, screen.get_size(), screen)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
