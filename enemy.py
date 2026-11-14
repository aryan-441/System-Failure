import pygame


class Enemy:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        self.rect = pygame.Rect(0, 0, 40, 40)
        self.rect.center = self.position
        self.speed = 100
        self.health = 3
        self.max_health = 3
        self.image = None
        self.ship_image = None
        self.is_boss = False
        self.last_hit = -1000
        self.hit_flash_timer = 0.0

    def update(self, dt, player_position):
        self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)
        direction = player_position - self.position

        if direction.length_squared() > 0:
            direction = direction.normalize()
            self.position += direction * self.speed * dt

        self.rect.center = self.position

    def take_damage(self, amount):
        self.health -= amount
        self.last_hit = pygame.time.get_ticks()
        self.hit_flash_timer = 0.17
        return self.health <= 0

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.rect)
        for index in range(self.max_health):
            colour = (255, 70, 80) if index < self.health else (65, 65, 80)
            pygame.draw.rect(
                screen, colour,
                (self.rect.x + index * 14, self.rect.y - 9, 12, 4)
            )
