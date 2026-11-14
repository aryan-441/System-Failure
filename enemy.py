import pygame

class Enemy:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)

        self.rect = pygame.Rect(0, 0, 40, 40)
        self.rect.center = self.position

        self.speed = 100
        self.health = 3
        self.image = None

    def update(self, dt, player_position):
        direction = player_position - self.position

        if direction.length() > 0:
            direction = direction.normalize()
            self.position += direction * self.speed * dt

        self.rect.center = self.position

    def take_damage(self, amount):
        self.health -= amount

        if self.health <= 0:
            return True
        else:
            return False

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.rect)
