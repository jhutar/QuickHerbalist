import pygame
import random
import sys

# --- Inicializace Pygame ---
pygame.init()

# --- Nastavení obrazovky ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Běžec s Květinami")

# --- Barvy ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 150, 0) # Pro trávu
RED = (255, 0, 0)   # Pro kameny
YELLOW = (255, 255, 0) # Pro květiny
BLUE = (0, 0, 255) # Pro hráče

# --- Fonty ---
font = pygame.font.Font(None, 36)
game_over_font = pygame.font.Font(None, 72)

# --- Herní proměnné ---
game_speed = 5 # Počáteční rychlost
score = 0
distance = 0 # Vzdálenost "ušlá" hráčem
game_state = "RUNNING" # "RUNNING", "GAME_OVER"

# --- Třída Hráče ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # V reálné hře bys nahrával obrázky:
        # self.images = [
        #     pygame.image.load("hero1.png").convert_alpha(),
        #     pygame.image.load("hero2.png").convert_alpha(),
        #     pygame.image.load("hero3.png").convert_alpha(),
        #     pygame.image.load("hero4.png").convert_alpha()
        # ]
        # Pro simulaci použijeme obdélníky
        self.images = [
            pygame.Surface((50, 50)),
            pygame.Surface((50, 50)),
            pygame.Surface((50, 50)),
            pygame.Surface((50, 50))
        ]
        for img in self.images:
            img.fill(BLUE) # Vyplníme je modrou barvou

        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)
        self.animation_speed = 0.1 # Rychlost animace
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
    def __init__(self, x):
        super().__init__()
        # V reálné hře bys nahrával obrázek:
        # self.image = pygame.image.load("grass.png").convert_alpha()
        # Pro simulaci použijeme obdélník
        self.image = pygame.Surface((SCREEN_WIDTH, 50)) # Pás trávy
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = SCREEN_HEIGHT - 50 # Umístění trávy dole

    def update(self):
        self.rect.x -= game_speed
        if self.rect.right < 0:
            self.rect.x = SCREEN_WIDTH # Reset na pravý okraj

# --- Třída Květiny ---
class Flower(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # V reálné hře bys nahrával obrázek:
        # self.image = pygame.image.load("flower.png").convert_alpha()
        # Pro simulaci použijeme kruh
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA) # SRCALPHA pro průhlednost
        pygame.draw.circle(self.image, YELLOW, (15, 15), 15) # Žlutý kruh
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH + random.randint(50, 200) # Náhodná pozice za obrazovkou
        self.rect.y = random.randint(0, SCREEN_HEIGHT - self.rect.height)

    def update(self):
        self.rect.x -= game_speed
        if self.rect.right < 0:
            self.kill() # Odstraní se, pokud je mimo obrazovku

# --- Třída Kamene ---
class Stone(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # V reálné hře bys nahrával obrázek:
        # self.image = pygame.image.load("stone.png").convert_alpha()
        # Pro simulaci použijeme obdélník
        self.image = pygame.Surface((40, 40))
        self.image.fill(RED) # Červený obdélník
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH + random.randint(100, 300) # Náhodná pozice za obrazovkou
        self.rect.y = random.randint(0, SCREEN_HEIGHT - self.rect.height)

    def update(self):
        self.rect.x -= game_speed
        if self.rect.right < 0:
            self.kill() # Odstraní se, pokud je mimo obrazovku

# --- Skupiny sprajtů ---
all_sprites = pygame.sprite.Group()
flowers = pygame.sprite.Group()
stones = pygame.sprite.Group()
ground_tiles = pygame.sprite.Group()

# --- Vytvoření hráče ---
player = Player()
all_sprites.add(player)

# --- Vytvoření počátečních dlaždic země ---
for i in range(2): # Dvě dlaždice pro plynulý pohyb
    ground = Ground(i * SCREEN_WIDTH)
    all_sprites.add(ground)
    ground_tiles.add(ground)

# --- Časovače pro generování objektů ---
flower_spawn_event = pygame.USEREVENT + 1
pygame.time.set_timer(flower_spawn_event, 2000) # Květina každé 2 sekundy

stone_spawn_event = pygame.USEREVENT + 2
pygame.time.set_timer(stone_spawn_event, 3000) # Kámen každé 3 sekundy

# --- Hlavní herní smyčka ---
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == flower_spawn_event and game_state == "RUNNING":
            new_flower = Flower()
            all_sprites.add(new_flower)
            flowers.add(new_flower)
        if event.type == stone_spawn_event and game_state == "RUNNING":
            new_stone = Stone()
            all_sprites.add(new_stone)
            stones.add(new_stone)

    if game_state == "RUNNING":
        # --- Aktualizace ---
        all_sprites.update()

        # Zvýšení rychlosti hry a vzdálenosti
        game_speed += 0.001 # Postupné zrychlování
        distance += game_speed / 10 # Vzdálenost se zvyšuje s rychlostí

        # Kontrola kolizí s květinami
        flower_hits = pygame.sprite.spritecollide(player, flowers, True) # True = odstraní květinu
        for flower in flower_hits:
            score += 1

        # Kontrola kolizí s kameny
        stone_hits = pygame.sprite.spritecollide(player, stones, False) # False = neodstraní kámen
        if stone_hits:
            game_state = "GAME_OVER"

        # Zajištění plynulého pohybu země
        if ground_tiles.sprites()[0].rect.right < 0:
            ground_tiles.sprites()[0].rect.x = SCREEN_WIDTH
        if ground_tiles.sprites()[1].rect.right < 0:
            ground_tiles.sprites()[1].rect.x = SCREEN_WIDTH

        # --- Kreslení ---
        screen.fill(WHITE) # Vyplní pozadí bílou barvou

        # Kreslení země (trávy)
        for tile in ground_tiles:
            screen.blit(tile.image, tile.rect)

        all_sprites.draw(screen)

        # Zobrazení skóre a vzdálenosti
        score_text = font.render(f"Květiny: {score}", True, BLACK)
        distance_text = font.render(f"Vzdálenost: {int(distance)} m", True, BLACK)
        screen.blit(score_text, (10, 10))
        screen.blit(distance_text, (10, 50))

    elif game_state == "GAME_OVER":
        screen.fill(BLACK)
        game_over_text = game_over_font.render("KONEC HRY!", True, WHITE)
        final_score_text = font.render(f"Květiny: {score}", True, WHITE)
        final_distance_text = font.render(f"Ušlá vzdálenost: {int(distance)} m", True, WHITE)

        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        distance_rect = final_distance_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))

        screen.blit(game_over_text, game_over_rect)
        screen.blit(final_score_text, score_rect)
        screen.blit(final_distance_text, distance_rect)

    # --- Aktualizace displeje ---
    pygame.display.flip()

    # --- Omezení FPS ---
    clock.tick(60)

pygame.quit()
sys.exit()
