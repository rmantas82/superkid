import random
import pygame

BACKGROUND_LAYERS = [
    ("bg_sky", 0.00),       # sky fixed
    ("bg_clouds", 0.15),    # clouds (slow)
    ("bg_mountains", 0.30), # far mountains
    ("bg_hills", 0.45),     # closer hills
]

# --- Hero hitbox ---
HITBOX_W_RATIO = 0.44
HITBOX_H_RATIO = 0.86
HITBOX_X_OFFSET = 0
HITBOX_Y_OFFSET = 0
DEBUG_HITBOX = False

# --- Window ---
WIDTH, HEIGHT = 1280, 720
TITLE = "SuperKid"

# --- Ground ---
GROUND_Y = HEIGHT - 60
SPAWN_GAP_MIN = 250
SPAWN_GAP_MAX = 420
OBJECT_OFFSCREEN_CLEAN = 200

# Background image
BACKGROUND_IMG = "background"
_scaled_bg = None

# Physics
GRAVITY = 1.0
MOVE = 6
JUMP = -30
MAX_FALL = 22

# Jump improvements
COYOTE_FRAMES = 6
BUFFER_FRAMES = 7
EXTRA_FALL = 1.2

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

coin_proto = Actor("coin")
enemy_proto = Actor("enemy")

# Spawner
next_spawn_x = 0

game_over_timer = 0        # cuenta atrás antes de reiniciar
GAME_OVER_FRAMES = 60      # 1 segundo a 60fps

def hero_hitbox():
    w = int(player.width * HITBOX_W_RATIO)
    h = int(player.height * HITBOX_H_RATIO)
    left = int(player.centerx - w // 2 + HITBOX_X_OFFSET)
    top = int(player.bottom - h + HITBOX_Y_OFFSET)
    return Rect(left, top, w, h)


def hero_hitbox_cam():
    hb = hero_hitbox()
    return Rect(hb.left - cam_x, hb.top, hb.width, hb.height)


# --- Camera ---
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
    px = player.x - cam_x
    if px > VIEW_RIGHT:
        cam_x = player.x - VIEW_RIGHT
    elif px < VIEW_LEFT:
        cam_x = max(0, player.x - VIEW_LEFT)


# --- Background ---
def setup_background_image():
    global _scaled_bg, _bg_w, _bg_h
    try:
        bg = getattr(images, BACKGROUND_IMG)
        iw, ih = bg.get_size()
        s = HEIGHT / ih
        new_size = (int(iw * s), int(ih * s))
        _scaled_bg = pygame.transform.smoothscale(bg, new_size)
        _bg_w, _bg_h = _scaled_bg.get_size()
    except Exception as e:
        print("Background error:", e)
        _scaled_bg = None
        _bg_w = _bg_h = 0


PARALLAX = 0.30


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
        except Exception as e:
            print("Layer error", name, ":", e)


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
    player.midbottom = (120, HEIGHT)
    player.vx = 0
    player.vy = 0
    cam_x = 0
    coins.clear()
    enemies.clear()
    next_spawn_x = player.x + 300


def spawn_tree(x):
    img = random.choice(["tree_1", "tree_2"])
    t = Actor(img, anchor=("center", "bottom"))
    offset = 120   # sube los arboles N pixeles (ajusta al gusto)
    t.midbottom = (x, HEIGHT - offset)
    trees.append(t)


def spawn_enemy(x):
    e = Actor("enemy")
    e.midbottom = (x, HEIGHT)
    e.min_x = x - random.randint(60, 120)
    e.max_x = x + random.randint(60, 120)
    e.vx = random.choice([-2, -1, 1, 2])
    enemies.append(e)


def spawn_coin(x):
    c = Actor("coin")
    c.center = (x, HEIGHT - 100)
    coins.append(c)


last_enemy = False


def ensure_world_ahead():
    global next_spawn_x, last_enemy
    target_x = player.x + int(WIDTH * 1.5)
    while next_spawn_x < target_x:
        if not last_enemy and random.random() < 0.5:
            spawn_enemy(next_spawn_x)
            last_enemy = True
        else:
            spawn_coin(next_spawn_x)
            last_enemy = False

        if random.random() < 0.25:
            spawn_tree(next_spawn_x + random.randint(100, 400))

        next_spawn_x += random.randint(SPAWN_GAP_MIN, SPAWN_GAP_MAX)

    left_limit = cam_x - OBJECT_OFFSCREEN_CLEAN
    coins[:] = [c for c in coins if c.right >= left_limit]
    enemies[:] = [e for e in enemies if e.right >= left_limit]
    trees[:] = [t for t in trees if t.right >= left_limit]


# --- Hero animation ---
def update_hero_image():
    global current_walk_frame, walk_timer
    if not on_ground():
        player.image = "hero_jump" if player.vy < 0 else "hero_fall"
    elif player.vx != 0:
        walk_timer += 1
        if walk_timer >= 10:
            walk_timer = 0
            current_walk_frame = (current_walk_frame + 1) % len(walk_frames)
        player.image = walk_frames[current_walk_frame]
    else:
        player.image = "hero_idle"


setup_background_image()
init_ground_world()
start_player()

# --- Game state ---
score = 0
coyote = 0
jump_buffer = 0
INVULN_FRAMES = 60  # ~1 segundo a 60fps

# --- Hearts UI state/consts ---
HEARTS_MAX = 3
lives = HEARTS_MAX

invuln_timer = 0

HEART_FLASH_FRAMES = 30   # ~0.5s a 60fps
HEART_FLASH_PERIOD = 4    # alterna visible cada 4 frames
heart_flash_timer = 0
heart_flash_index = -1    # -1 = ninguno


def on_key_down(key):
    global jump_buffer
    if key == keys.SPACE:
        jump_buffer = BUFFER_FRAMES


# --- Hearts helpers ---
def hearts_start_flash(index: int):
    """Empieza el parpadeo del corazón que acaba de vaciarse (index 0..HEARTS_MAX-1)."""
    global heart_flash_timer, heart_flash_index
    heart_flash_index = index
    heart_flash_timer = HEART_FLASH_FRAMES


def hearts_update():
    """Actualiza el temporizador de parpadeo del corazón vacío."""
    global heart_flash_timer, heart_flash_index
    if heart_flash_timer > 0:
        heart_flash_timer -= 1
        if heart_flash_timer <= 0:
            heart_flash_index = -1


def hearts_draw(x0=16, y=90, extra_gap=12):
    try:
        heart_w = images.heart_full.get_width()
    except:
        heart_w = 32
    spacing = heart_w + extra_gap

    for i in range(HEARTS_MAX):
        img = "heart_full" if i < lives else "heart_empty"

        # Si estamos en game over → todos vacíos parpadean
        if game_over_timer > 0 and (game_over_timer // HEART_FLASH_PERIOD) % 2 == 0:
            continue

        # Parpadeo normal del último corazón perdido
        if i == heart_flash_index and (heart_flash_timer // HEART_FLASH_PERIOD) % 2 == 0:
            continue

        screen.blit(img, (x0 + i * spacing, y))


def update():
    global coyote, jump_buffer, invuln_timer, lives

    # Invulnerabilidad tras daño
    if invuln_timer > 0:
        invuln_timer -= 1

    # --- Movimiento lateral ---
    player.vx = (-MOVE if keyboard.left else 0) + (MOVE if keyboard.right else 0)

    # --- Gravedad + salto variable ---
    player.vy = min(player.vy + GRAVITY, MAX_FALL)
    if player.vy < 0 and not keyboard.space:
        player.vy += EXTRA_FALL

    # --- Coyote / Buffer ---
    if on_ground():
        coyote = COYOTE_FRAMES
    else:
        coyote = max(coyote - 1, 0)

    if jump_buffer > 0 and coyote > 0:
        player.vy = JUMP
        jump_buffer = 0
        coyote = 0
    jump_buffer = max(jump_buffer - 1, 0)

    # --- Movimiento y colisiones ---
    player.x += player.vx
    if player.left < 0:
        player.left = 0
        if player.vx < 0:
            player.vx = 0

    player.y += player.vy
    hb = hero_hitbox()
    if player.vy >= 0 and hb.bottom >= GROUND_Y:
        player.bottom = GROUND_Y
        player.vy = 0

    # --- Enemigos ---
    for e in enemies:
        e.x += e.vx
        if e.left <= e.min_x or e.right >= e.max_x:
            e.vx *= -1

    # --- Daño del héroe ---
    if invuln_timer == 0:   # solo si no está invulnerable
        for e in enemies:
            e_rect = Rect(e.left, e.top, e.width, e.height)
            if hero_hitbox().colliderect(e_rect):
                take_damage()
                break

    # --- Monedas ---
    taken_idx = []
    hb = hero_hitbox()
    for i, c in enumerate(coins):
        c_rect = Rect(c.left, c.top, c.width, c.height)
        if hb.colliderect(c_rect):
            score_add(1)
            taken_idx.append(i)
            try:
                sounds.coin.play()
            except:
                pass
    for i in reversed(taken_idx):
        coins.pop(i)

    follow_camera()
    ensure_world_ahead()

    if player.top > HEIGHT + 60:
        take_damage()   # caer también quita vida

    update_hero_image()
    hearts_update()
	
	# Fase de game over
    global game_over_timer, lives, score
    if game_over_timer > 0:
        game_over_timer -= 1
        if game_over_timer == 0:
            # Ahora sí, reinicio completo
            lives = HEARTS_MAX
            score = 0
            start_player()

def take_damage():
    global lives, invuln_timer, score, heart_flash_timer, heart_flash_index, game_over_timer

    if lives <= 0 or game_over_timer > 0:
        return  # seguridad

    lives -= 1
    invuln_timer = INVULN_FRAMES

    # Corazón que pasa de lleno a vacío
    hearts_start_flash(lives)

    try:
        sounds.hit.play()
    except:
        pass

    if lives <= 0:
        # No reiniciamos aún → activamos animación de game over
        heart_flash_index = -1
        heart_flash_timer = 0
        game_over_timer = GAME_OVER_FRAMES


def draw():
    draw_background_image()

    # Suelo
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

    # Héroe parpadeando si está invulnerable
    if invuln_timer % 10 < 5:
        draw_player_cam()

    screen.draw.text("LEFT/RIGHT move | SPACE jump",
                     (16, 12), color="white", fontsize=32)
    screen.draw.text(f"Points: {score}", (16, 48), color="yellow", fontsize=40)

    # UI: corazones (llenos/vacíos con parpadeo del último perdido)
    hearts_draw(x0=16, y=90, extra_gap=20)


def on_ground():
    hb = hero_hitbox()
    foot = Rect(hb.left + 6, hb.bottom - 2, hb.width - 12, 4)
    ground_rect = Rect(-10**6, GROUND_Y - 2, 2 * 10**6, 4)
    return foot.colliderect(ground_rect)


def score_add(n):
    global score
    score += n


def dist(a, b):
    ax, ay = a
    bx, by = b
    dx, dy = ax - bx, ay - by
    return (dx * dx + dy * dy) ** 0.5
