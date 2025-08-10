import pygame
import random
import sys
import gettext

# --- Inicializace lokalizace
gettext.bindtextdomain("base", "locales/")
gettext.textdomain("base")
_ = gettext.gettext

# --- Inicializace Pygame ---
pygame.init()

# --- Nastavení obrazovky ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(_("Quick Herbalist"))

# --- Barvy ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN1 = (0, 150, 0)  # Pro trávu
GREEN2 = (0, 130, 0)  # Pro trávu
GREEN3 = (0, 170, 0)  # Pro trávu
RED = (255, 0, 0)  # Pro kameny
YELLOW = (255, 255, 0)  # Pro květiny
BLUE = (0, 0, 255)  # Pro hráče

# --- Fonty ---
font = pygame.font.Font(None, 36)
game_over_font = pygame.font.Font(None, 72)

# --- Herní proměnné ---
game_speed = 3  # Počáteční rychlost
score = 0
distance = 0  # Vzdálenost "ušlá" hráčem
game_state = "MENU"


# --- Třída Hráče ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.images = [
            pygame.image.load("hero1.png").convert_alpha(),
            pygame.image.load("hero2.png").convert_alpha(),
            pygame.image.load("hero1.png").convert_alpha(),
            pygame.image.load("hero3.png").convert_alpha(),
        ]

        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 8, SCREEN_HEIGHT // 2)
        self.animation_speed = 0.1  # Rychlost animace
        self.last_update = pygame.time.get_ticks()

    def update(self):
        # Animace hráče
        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed * 1000:
            self.last_update = now
            self.index = (self.index + 1) % len(self.images)
            self.image = self.images[self.index]

        # Pohyb nahoru/dolů
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= 5
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += 5

        # Omezení pohybu na obrazovku
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT


class MovingSprite(pygame.sprite.Sprite):
    """Base class for sprite that is constatntly moving to the left in the game like grass, flowers or stones."""
    def __init__(self, image, x, y):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.rect_x_float = float(x)

    def update(self):
        self.rect_x_float -= game_speed
        self.rect.x = int(self.rect_x_float)
        if self.rect.right < 0:
            self.kill()


# --- Třída Země/Trávy ---
class Ground(MovingSprite):
    def __init__(self, x, y):
        image = pygame.image.load("grass.png").convert_alpha()
        super().__init__(image, x, y)


# --- Třída Květiny ---
class Flower(MovingSprite):
    def __init__(self):
        image = pygame.image.load(random.choice(["flower1.png"])).convert_alpha()
        x = SCREEN_WIDTH + random.randint(50, 200)
        y = random.randint(0, SCREEN_HEIGHT)
        super().__init__(image, x, y)


# --- Třída Kamene ---
class Stone(MovingSprite):
    def __init__(self):
        image = pygame.image.load("stone.png").convert_alpha()
        x = SCREEN_WIDTH + random.randint(100, 300)
        y = random.randint(0, SCREEN_HEIGHT)
        super().__init__(image, x, y)


class Background(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.max_x_float = 0.0  # X axis of most right tile (it's left border)

    def add(self, *sprites):
        super().add(*sprites)

        # Update max_x_float if added sprite is more to the right
        for s in sprites:
            if s.rect_x_float > self.max_x_float:
                self.max_x_float = s.rect_x_float

    def update(self):
        super().update()

        # Tiles were just updated to move to the left, so move max_x_float as well
        self.max_x_float -= game_speed
        max_x = int(self.max_x_float)

        # Create new column of tiles if needed
        current_max_x = max_x
        if current_max_x <= SCREEN_WIDTH:
            first = iter(self).__next__()
            tile_width = first.rect.width
            tile_height = first.rect.height
            for row in range(int(SCREEN_HEIGHT / tile_height)):
                tile = Ground(current_max_x + tile_width, row * tile_height)
                self.add(tile)


# --- Skupiny sprajtů ---
flowers = pygame.sprite.Group()
stones = pygame.sprite.Group()
players = pygame.sprite.Group()
background = Background()

# --- Vytvoření hráče ---
player = Player()
players.add(player)

# --- Vytvoření počátečních dlaždic země ---
first = Ground(0, 0)
for row in range(int(SCREEN_HEIGHT / first.rect.height)):
    for col in range(int(SCREEN_WIDTH / first.rect.width)):
        tile = Ground(col * first.rect.width, row * first.rect.height)
        background.add(tile)

# --- Časovače pro generování objektů ---
flower_spawn_event = pygame.USEREVENT + 1
pygame.time.set_timer(flower_spawn_event, 1000)  # Květina každou 1 sekundu

stone_spawn_event_interval = 3000
stone_spawn_event = pygame.USEREVENT + 2
pygame.time.set_timer(
    stone_spawn_event, stone_spawn_event_interval, 1
)  # Kámen každé 3 sekundy a potom častěji

# --- Hlavní herní smyčka ---
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_state in ("QUIT",) and event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
            running = False
        if game_state in ("MENU", "RUNNING") and event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
            game_state = "QUIT"
        if game_state in ("MENU", "QUIT") and event.type == pygame.KEYDOWN and event.key == pygame.K_s:
            game_state = "RUNNING"
        if game_state in ("RUNNING",) and event.type == flower_spawn_event:
            new_flower = Flower()
            flowers.add(new_flower)
        if game_state in ("RUNNING",) and event.type == stone_spawn_event:
            new_stone = Stone()
            stones.add(new_stone)

            # Next stone will appear faster
            if stone_spawn_event_interval > 50:
                stone_spawn_event_interval -= random.randint(0, 50)
            pygame.time.set_timer(stone_spawn_event, stone_spawn_event_interval, 1)

    if game_state == "MENU":
        screen.fill(BLACK)
        title_text = font.render(_("Quick Herbalist"), True, WHITE)
        title_rect = title_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
        )
        start_text = font.render(_("Press 's' for start"), True, WHITE)
        start_rect = start_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
        )
        screen.blit(title_text, title_rect)
        screen.blit(start_text, start_rect)

    elif game_state == "RUNNING":
        # --- Aktualizace ---
        background.update()
        flowers.update()
        stones.update()
        players.update()

        # Zvýšení rychlosti hry a vzdálenosti
        game_speed += 0.001 # Postupné zrychlování
        distance += game_speed / 10  # Vzdálenost se zvyšuje s rychlostí

        # Kontrola kolizí s květinami
        flower_hits = pygame.sprite.spritecollide(
            player, flowers, True
        )  # True = odstraní květinu
        for flower in flower_hits:
            score += 1

        # Kontrola kolizí s kameny
        stone_hits = pygame.sprite.spritecollide(
            player, stones, False
        )  # False = neodstraní kámen
        if stone_hits:
            game_state = "GAME_OVER"

        # --- Kreslení ---
        screen.fill(WHITE)  # Vyplní pozadí bílou barvou
        background.draw(screen)
        flowers.draw(screen)
        stones.draw(screen)
        players.draw(screen)

        # Zobrazení skóre a vzdálenosti
        score_text = font.render(_("Collected: ") + str(score), True, BLACK)
        distance_text = font.render(_("Distance: ") + str(int(distance)), True, BLACK)
        screen.blit(score_text, (10, 10))
        screen.blit(distance_text, (10, 50))

    elif game_state == "BREWING":
        pass

    elif game_state == "QUIT":
        screen.fill(BLACK)
        title_text = font.render(_("Do you want to quit?"), True, WHITE)
        title_rect = title_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
        )
        start_text = font.render(_("Press 's' to continue"), True, WHITE)
        start_rect = start_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
        )
        quit_text = font.render(_("Press 'q' to quit"), True, WHITE)
        quit_rect = quit_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)
        )
        screen.blit(title_text, title_rect)
        screen.blit(start_text, start_rect)
        screen.blit(quit_text, quit_rect)

    elif game_state == "GAME_OVER":
        screen.fill(BLACK)
        game_over_text = game_over_font.render(_("GAME OVER!"), True, WHITE)
        final_score_text = font.render(_("Collected: ") + str(score), True, WHITE)
        final_distance_text = font.render(_("Distance: ") + str(int(distance)), True, WHITE)

        game_over_rect = game_over_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
        )
        score_rect = final_score_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)
        )
        distance_rect = final_distance_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)
        )

        screen.blit(game_over_text, game_over_rect)
        screen.blit(final_score_text, score_rect)
        screen.blit(final_distance_text, distance_rect)

    # --- Aktualizace displeje ---
    pygame.display.flip()

    # --- Omezení FPS ---
    clock.tick(60)

pygame.quit()
sys.exit()
