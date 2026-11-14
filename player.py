'''PLAYER CLASS'''
import pygame

from settings import PLAYER_SIZE, PLAYER_COLOUR, PLAYER_SPEED, WIDTH, HEIGHT

class Player:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x,y)
        self.speed = PLAYER_SPEED
        self.health = 5
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE) #playe rectangle
        self.rect.center = self.position
    def update(self,dt,keys):
        direction = pygame.Vector2(0,0)
       #keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y +=1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1
        if direction.length() > 0:
            direction = direction.normalize() #fixed bug--- diagonal movement was super fast before the normalise method
        self.position += direction * self.speed * dt

        #world boundary

        half = PLAYER_SIZE / 2
        self.position.x = max(half, min(WIDTH - half, self.position.x))
        self.position.y = max(half, min(HEIGHT - half, self.position.y))
        self.rect.center = self.position

    def draw(self, screen):
        pygame.draw.rect(screen, PLAYER_COLOUR, self.rect)
