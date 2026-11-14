import pygame

class Enemy:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)

        self.rect = pygame.Rect(0, 0, 40, 40)
        self.rect.center = self.position

        self.speed = 100
        self.health = 3
        self.image = None
        self.last_hit = -1000

    def update(self, dt, player_position):
        direction = player_position - self.position

        if direction.length() > 0:
            direction = direction.normalize()
            self.position += direction * self.speed * dt

        self.rect.center = self.position

    def take_damage(self, amount):
        self.health -= amount

        self.last_hit = pygame.time.get_ticks()


        if self.health <= 0:
            return True
        else:
            return False

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.rect)

        if pygame.time.get_ticks() - self.last_hit < 120:
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 4)  #enemy flashes white after being hit

        for i in range(3): #3 health bars
            colour = (255, 70, 80) if i < self.health else (65, 65, 80)
            pygame.draw.rect(screen, colour, (self.rect.x + i * 14, self.rect.y - 9, 12, 4))
