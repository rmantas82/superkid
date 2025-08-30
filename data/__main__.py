# -*- coding: utf-8 -*-
import random
import pygame

BACKGROUND_LAYERS = [
    ("bg_sky", 0.00),
    ("bg_clouds", 0.15),
    ("bg_mountains", 0.30),
    ("bg_hills", 0.45),
]

# --- Hearts UI ---
HEART_POS_Y = 5
HEART_EXTRA_GAP = 20

# --- Hero hitbox ---
HITBOX_W_RATIO = 0.44
HITBOX_H_RATIO = 0.86
HITBOX_X_OFFSET = 0
HITBOX_Y_OFFSET = 0

# --- Window ---
WIDTH, HEIGHT = 1280, 720
TITLE = "SuperKid"

# --- Runner ---
PLAYER_ANCHOR_X = int(WIDTH * 0.25)

# --- Ground ---
GROUND_Y = HEIGHT - 60
SPAWN_GAP_MIN = 250
SPAWN_GAP_MAX = 420
OBJECT_OFFSCREEN_CLEAN = 200

# Physics
GRAVITY = 1.0
MOVE = 6
JUMP = -40
MAX_FALL = 22

# Camera
cam_x = 0
VIEW_LEFT = int(WIDTH * 0.35)
VIEW_RIGHT = int(WIDTH * 0.65)

# Objects
coins = []
enemies = []
trees = []

# Hero animation
walk_frames = ["hero_walk1", "hero_walk2", "hero_walk3"]
current_walk_frame = 0
walk_timer = 0

# Actors
player = Actor("hero_idle", anchor=("center", "bottom"))
player.vx = 0
player.vy = 0

# Spawner
next_spawn_x = 0

# --- Config ---
RUNNER_MODE = True
RUN_SPEED = 6

# --- Enemigos posibles ---
# --- Enemigos posibles ---
ENEMY_IMAGES = [
    "enemies/enemy_1",
    "enemies/enemy_2"
]

# Correcciones verticales por enemigo (ajusta a ojo los valores)
ENEMY_OFFSETS_Y = {
    "enemies/enemy_1": -75,
    "enemies/enemy_2": -75
}

# --- Game state ---
score = 0
high_score = 0
INVULN_FRAMES = 60
invuln_timer = 0

# --- Hearts / Game Over ---
HEARTS_MAX = 3
lives = HEARTS_MAX
HEART_FLASH_FRAMES = 30
HEART_FLASH_PERIOD = 4
heart_flash_timer = 0
heart_flash_index = -1
GAME_OVER_FRAMES = 60
game_over_timer = 0

# --- Jump helpers ---
COYOTE_FRAMES = 6
BUFFER_FRAMES = 7
coyote = 0
jump_buffer = 0


# =========== HELPERS ===========
def hero_hitbox():
    w = int(player.width * HITBOX_W_RATIO)
    h = int(player.height * HITBOX_H_RATIO)
    left = int(player.centerx - w // 2 + HITBOX_X_OFFSET)
    top = int(player.bottom - h + HITBOX_Y_OFFSET)
    return Rect(left, top, w, h)


def draw_actor_centered_cam(a):
    x = int(a.x - cam_x - a.width // 2)
    y = int(a.y - a.height // 2)
    screen.blit(a.image, (x, y))


def draw_player_cam():
    x = int(player.x - cam_x - player.width // 2)
    y = int(player.bottom - player.height)
    screen.blit(player.image, (x, y))


def follow_camera():
    global cam_x
    if RUNNER_MODE:
        player.x = cam_x + PLAYER_ANCHOR_X
        return
    px = player.x - cam_x
    if px > VIEW_RIGHT:
        cam_x = player.x - VIEW_RIGHT
    elif px < VIEW_LEFT:
        cam_x = max(0, player.x - VIEW_LEFT)


# --- Background ---
def setup_background_image():
    global _scaled_bg, _bg_w, _bg_h
    try:
        bg = getattr(images, "background")
        iw, ih = bg.get_size()
        s = HEIGHT / ih
        new_size = (int(iw * s), int(ih * s))
        _scaled_bg = pygame.transform.smoothscale(bg, new_size)
        _bg_w, _bg_h = _scaled_bg.get_size()
    except:
        _scaled_bg = None
        _bg_w = _bg_h = 0


def draw_background_image():
    for name, parallax in BACKGROUND_LAYERS:
        try:
            bg = getattr(images, name)
            iw, ih = bg.get_size()
            scale = HEIGHT / ih
            new_w, new_h = int(iw * scale), int(ih * scale)
            bg_scaled = pygame.transform.scale(bg, (new_w, new_h))
            offset = int(-(cam_x * parallax)) % new_w
            y = HEIGHT - new_h
            x0 = -offset
            screen.surface.blit(bg_scaled, (x0, y))
            screen.surface.blit(bg_scaled, (x0 + new_w, y))
        except:
            pass


# --- World ---
def init_ground_world():
    global coins, enemies, trees, next_spawn_x, GROUND_Y
    coins = []
    enemies = []
    trees = []
    try:
        tile_h = images.bg_ground.get_height()
        GROUND_Y = HEIGHT
    except:
        GROUND_Y = HEIGHT - 60
    next_spawn_x = player.x + 300


def start_player():
    global next_spawn_x, cam_x, coins, enemies
    cam_x = 0
    player.vx = 0
    player.vy = 0
    player.midbottom = (cam_x + PLAYER_ANCHOR_X, HEIGHT)
    coins.clear()
    enemies.clear()
    next_spawn_x = cam_x + WIDTH + 300


# ============ Spawners ============
def spawn_tree(x):
    img = random.choice(["tree_1", "tree_2"])
    t = Actor(img, anchor=("center", "bottom"))
    t.midbottom = (x, HEIGHT - 120)
    trees.append(t)


def spawn_enemy(x, behavior="static"):
    img = random.choice(ENEMY_IMAGES)
    e = Actor(img, anchor=("center", "bottom"))
    offset_y = ENEMY_OFFSETS_Y.get(img, 0) # offset individual
    e.midbottom = (x, GROUND_Y + offset_y)
    e.behavior = behavior

    if behavior == "horizontal":
        e.min_x = x - random.randint(60, 120)
        e.max_x = x + random.randint(60, 120)
        e.vx = random.choice([-2, -1, 1, 2])
        e.vy = 0

    elif behavior == "vertical":
        e.base_y = GROUND_Y + ENEMY_OFFSETS_Y.get(img, 0)
        e.min_y = e.base_y - random.randint(40, 120)
        e.max_y = e.base_y
        e.vy = random.choice([-2, -1, 1, 2])
        e.vx = 0
        e.y = e.base_y

    else:  # static
        e.vx = 0
        e.vy = 0

    enemies.append(e)


def spawn_coin(x):
    c = Actor("coin")
    c.center = (x, HEIGHT - 100)
    coins.append(c)


last_enemy = False


def ensure_world_ahead():
    global next_spawn_x, last_enemy
    base = cam_x if RUNNER_MODE else player.x
    target_x = base + int(WIDTH * 1.5)

    if next_spawn_x < base + WIDTH:
        next_spawn_x = base + WIDTH

    while next_spawn_x < target_x:
        if not last_enemy and random.random() < 0.5:
            spawn_enemy(next_spawn_x, behavior=random.choice(["static", "vertical"]))
            last_enemy = True
        else:
            spawn_coin(next_spawn_x)
            last_enemy = False
        if random.random() < 0.25:
            spawn_tree(next_spawn_x + random.randint(100, 400))
        next_spawn_x += random.randint(SPAWN_GAP_MIN, SPAWN_GAP_MAX)

    left_limit = cam_x - OBJECT_OFFSCREEN_CLEAN
    coins[:]   = [c for c in coins   if c.right >= left_limit]
    enemies[:] = [e for e in enemies if e.right >= left_limit]
    trees[:]   = [t for t in trees   if t.right >= left_limit]


# --- Enemies update ---
def update_enemies():
    for e in enemies:
        if e.behavior == "horizontal":
            e.x += e.vx
            if e.left <= e.min_x or e.right >= e.max_x:
                e.vx *= -1
        elif e.behavior == "vertical":
            e.y += e.vy
            if e.y <= e.min_y or e.y >= e.max_y:
                e.vy *= -1


# --- Runner helpers ---
def runner_update_x():
    if RUNNER_MODE:
        global cam_x
        cam_x += RUN_SPEED
        player.x = cam_x + PLAYER_ANCHOR_X
    else:
        player.vx = (-MOVE if keyboard.left else 0) + (MOVE if keyboard.right else 0)
        player.x += player.vx


# --- Hero animation ---
def update_hero_image():
    global current_walk_frame, walk_timer
    if not on_ground():
        player.image = "hero_jump" if player.vy < 0 else "hero_fall"
    else:
        if RUNNER_MODE or player.vx != 0:
            walk_timer += 1
            if walk_timer >= 10:
                walk_timer = 0
                current_walk_frame = (current_walk_frame + 1) % len(walk_frames)
            player.image = walk_frames[current_walk_frame]
        else:
            player.image = "hero_idle"


# --- Hearts UI ---
HEART_POS_Y = 5
HEART_EXTRA_GAP = 20

def hearts_start_flash(index: int):
    global heart_flash_timer, heart_flash_index
    heart_flash_index = index
    heart_flash_timer = HEART_FLASH_FRAMES


def hearts_update():
    global heart_flash_timer, heart_flash_index
    if heart_flash_timer > 0:
        heart_flash_timer -= 1
        if heart_flash_timer <= 0:
            heart_flash_index = -1


def hearts_draw(y=HEART_POS_Y, extra_gap=HEART_EXTRA_GAP):
    """Corazones arriba-derecha."""
    try:
        heart_w = images.heart_full.get_width()
    except:
        heart_w = 32
    spacing = heart_w + extra_gap
    total_w = HEARTS_MAX * spacing - extra_gap
    x0 = WIDTH - total_w - 16   # margen de 16 px desde la derecha

    for i in range(HEARTS_MAX):
        img = "heart_full" if i < lives else "heart_empty"
        if game_over_timer > 0 and (game_over_timer // HEART_FLASH_PERIOD) % 2 == 0:
            continue
        if i == heart_flash_index and (heart_flash_timer // HEART_FLASH_PERIOD) % 2 == 0:
            continue
        screen.blit(img, (x0 + i * spacing, y))


# --- Core functions ---
def on_key_down(key):
    global jump_buffer
    if key == keys.SPACE:
        jump_buffer = BUFFER_FRAMES


def update():
    global coyote, jump_buffer, invuln_timer, lives, game_over_timer, score, high_score

    if game_over_timer > 0:
        game_over_timer -= 1
        if game_over_timer == 0:
            lives = HEARTS_MAX
            score = 0
            start_player()
        return

    if invuln_timer > 0:
        invuln_timer -= 1

    runner_update_x()

    # Gravedad
    player.vy = min(player.vy + GRAVITY, MAX_FALL)
    if player.vy < 0 and not keyboard.space:
        player.vy += 1.2  # caída rápida

    if on_ground():
        coyote = COYOTE_FRAMES
    else:
        coyote = max(coyote - 1, 0)

    if jump_buffer > 0 and coyote > 0:
        player.vy = JUMP
        jump_buffer = 0
        coyote = 0
    jump_buffer = max(jump_buffer - 1, 0)

    player.y += player.vy
    if player.vy >= 0 and player.bottom >= GROUND_Y:
        player.bottom = GROUND_Y
        player.vy = 0

    # colisiones con enemigos
    if invuln_timer == 0:
        for e in enemies:
            e_rect = Rect(e.left, e.top, e.width, e.height)
            if hero_hitbox().colliderect(e_rect):
                take_damage()
                break

    # colisiones con monedas
    taken_idx = []
    hb = hero_hitbox()
    for i, c in enumerate(coins):
        c_rect = Rect(c.left, c.top, c.width, c.height)
        if hb.colliderect(c_rect):
            score_add(1)
            if score > high_score:
                high_score = score
            taken_idx.append(i)
            try:
                sounds.coin.play()
            except:
                pass
    for i in reversed(taken_idx):
        coins.pop(i)

    update_enemies()
    follow_camera()
    ensure_world_ahead()

    if player.top > HEIGHT + 60:
        take_damage()

    update_hero_image()
    hearts_update()


def take_damage():
    global lives, invuln_timer, heart_flash_timer, heart_flash_index, game_over_timer
    if lives <= 0 or game_over_timer > 0:
        return
    lives -= 1
    invuln_timer = INVULN_FRAMES
    hearts_start_flash(lives)
    try:
        sounds.hit.play()
    except:
        pass
    if lives <= 0:
        heart_flash_index = -1
        heart_flash_timer = 0
        game_over_timer = GAME_OVER_FRAMES
    else:
        if player.bottom > GROUND_Y:
            player.bottom = GROUND_Y


def draw():
    draw_background_image()
    if hasattr(images, "bg_ground"):
        tile_w = images.bg_ground.get_width()
        tile_h = images.bg_ground.get_height()
        start_x = int((cam_x // tile_w - 2) * tile_w)
        end_x = int(cam_x + WIDTH + tile_w * 2)
        for x in range(start_x, end_x, tile_w):
            screen.blit("bg_ground", (x - cam_x, HEIGHT - tile_h))
    else:
        screen.draw.filled_rect(Rect(0, HEIGHT - 60, WIDTH, 60), (60, 48, 36))

    for t in trees:
        draw_actor_centered_cam(t)
    for c in coins:
        draw_actor_centered_cam(c)
    for e in enemies:
        draw_actor_centered_cam(e)

    if invuln_timer % 10 < 5 or game_over_timer > 0:
        draw_player_cam()

    # UI
    screen.draw.text(f"Points: {score}", (16, 48), color="yellow", fontsize=40)
    screen.draw.text(f"Max: {high_score}", (16, 12), color="white", fontsize=32)
    hearts_draw()


def on_ground():
    hb = hero_hitbox()
    foot = Rect(hb.left + 6, hb.bottom - 2, hb.width - 12, 4)
    ground_rect = Rect(-10**6, GROUND_Y - 2, 2 * 10**6, 4)
    return foot.colliderect(ground_rect)


def score_add(n):
    global score
    score += n


# ========= SETUP =========
setup_background_image()
init_ground_world()
start_player()
