import pygame
import random
from sys import exit

# Inicjalizacja Pygame
pygame.init()

# Konfiguracja ekranu
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mój Infinite Runner")

# Kolory
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
BLUE = (0, 100, 255)

# Zmienne gry
clock = pygame.time.Clock()
gravity = 0
score = 0
game_active = True

# Grupy sprite'ów (opcjonalnie, tu użyjemy prostych prostokątów dla jasności)
player_rect = pygame.Rect(80, 300, 50, 50)
obstacle_list = []

# Timer dla przeszkód
obstacle_timer = pygame.USEREVENT + 1
pygame.time.set_timer(obstacle_timer, 1500)  # Nowa przeszkoda co 1.5 sekundy

def move_obstacles(obstacles):
    if obstacles:
        for obstacle in obstacles:
            obstacle.x -= 5  # Prędkość przeszkód
        # Usuwamy przeszkody, które wyleciały za ekran
        obstacles = [obs for obs in obstacles if obs.x > -100]
        return obstacles
    return []

def check_collisions(player, obstacles):
    for obs in obstacles:
        if player.colliderect(obs):
            return False
    return True

# Pętla główna
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        
        if game_active:
            # Skok
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player_rect.bottom >= 350:
                    gravity = -20
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
            
            # Dodawanie przeszkód
            if event.type == obstacle_timer:
                obstacle_list.append(pygame.Rect(WIDTH, 300, 30, 50))
        else:
            # Restart gry
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_active = True
                obstacle_list.clear()
                player_rect.bottom = 350
                score = 0

    if game_active:
        # Tło
        screen.fill(WHITE)
        pygame.draw.line(screen, BLACK, (0, 350), (WIDTH, 350), 3)

        # Mechanika gracza (Grawitacja)
        gravity += 1
        player_rect.y += gravity
        if player_rect.bottom > 350:
            player_rect.bottom = 350

        pygame.draw.rect(screen, BLUE, player_rect)

        # Przeszkody
        obstacle_list = move_obstacles(obstacle_list)
        for obs in obstacle_list:
            pygame.draw.rect(screen, RED, obs)

        # Kolizje i punkty
        game_active = check_collisions(player_rect, obstacle_list)
        score += 1
        
        # Wyświetlanie wyniku
        font = pygame.font.SysFont("Arial", 30)
        score_surf = font.render(f"Score: {score // 10}", True, BLACK)
        screen.blit(score_surf, (10, 10))

    else:
        # Ekran końca gry
        screen.fill(BLACK)
        font = pygame.font.SysFont("Arial", 50)
        msg = font.render("GAME OVER! Press SPACE", True, WHITE)
        screen.blit(msg, (WIDTH // 2 - 250, HEIGHT // 2))

    pygame.display.update()
    clock.tick(60)  # 60 klatek na sekundę