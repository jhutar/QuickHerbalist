import pygame
import random
import sys

# --- Inicializace Pygame ---
pygame.init()

# --- Nastavení obrazovky ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Rychlá bylinkářka")

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
game_state = "RUNNING"  # "RUNNING", "GAME_OVER"


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
        self.rect.center = (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)
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


# --- Třída Země/Trávy ---
class Ground(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("grass.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x -= game_speed
        if self.rect.right < 0:
            self.kill()  # Odstraní se, pokud je mimo obrazovku


# --- Třída Květiny ---
class Flower(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load(random.choice(["flower1.png"])).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH + random.randint(
            50, 200
        )  # Náhodná pozice za obrazovkou
        self.rect.y = random.randint(0, SCREEN_HEIGHT - self.rect.height)

    def update(self):
        self.rect.x -= game_speed
        if self.rect.right < 0:
            self.kill()  # Odstraní se, pokud je mimo obrazovku


# --- Třída Kamene ---
class Stone(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("stone.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH + random.randint(
            100, 300
        )  # Náhodná pozice za obrazovkou
        self.rect.y = random.randint(0, SCREEN_HEIGHT - self.rect.height)

    def update(self):
        self.rect.x -= game_speed
        if self.rect.right < 0:
            self.kill()  # Odstraní se, pokud je mimo obrazovku


class Background(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.max_x = 0  # X axis of most right tile (it's left border)

    def add(self, *sprites):
        super().add(*sprites)

        # Update max_x if added sprite is more to the right
        for s in sprites:
            if s.rect.x > self.max_x:
                self.max_x = s.rect.x

    def update(self):
        super().update()

        # Tiles were just updated to move to the left, so move max_x as well
        self.max_x -= game_speed

        ###print("Max: ", max([s.rect.x for s in self.sprites()]), " vs. ", self.max_x, " (", len(self), ")")

        # Create new column of tiles if needed
        current_max_x = self.max_x
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
        if event.type == flower_spawn_event and game_state == "RUNNING":
            new_flower = Flower()
            flowers.add(new_flower)
        if event.type == stone_spawn_event and game_state == "RUNNING":
            new_stone = Stone()
            stones.add(new_stone)

            # Next stone will appear faster
            if stone_spawn_event_interval > 50:
                stone_spawn_event_interval -= random.randint(0, 50)
            pygame.time.set_timer(stone_spawn_event, stone_spawn_event_interval, 1)

    if game_state == "RUNNING":
        # --- Aktualizace ---
        background.update()
        flowers.update()
        stones.update()
        players.update()

        # Zvýšení rychlosti hry a vzdálenosti
        ###game_speed += 0.001 # Postupné zrychlování   FIXME
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
        score_text = font.render(f"Květiny: {score}", True, BLACK)
        distance_text = font.render(f"Vzdálenost: {int(distance)} m", True, BLACK)
        screen.blit(score_text, (10, 10))
        screen.blit(distance_text, (10, 50))

    elif game_state == "GAME_OVER":
        screen.fill(BLACK)
        game_over_text = game_over_font.render("KONEC HRY!", True, WHITE)
        final_score_text = font.render(f"Květiny: {score}", True, WHITE)
        final_distance_text = font.render(f"Vzdálenost: {int(distance)} m", True, WHITE)

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
