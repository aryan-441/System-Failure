
import random
import math
import pygame
from pathlib import Path


class ShipSprites:

    def __init__(self):
        folder = Path(__file__).parent / "assets" / "images"

        enemy_folder = folder / "enemies"
        player_folder = folder / "player"

        # ONE SPRITE FOR EACH ENEMY TYPE
        self.normal_image = self.load_image(enemy_folder, "enemy_blue_3")
        self.interceptor_image = self.load_image(enemy_folder, "enemy_black_5")
        self.tank_image = self.load_image(enemy_folder / "new", "space_shooter_extension_ship_005_tank")
        self.ranger_image = self.load_image(enemy_folder, "enemy_extension_ship_003")
        self.bomber_image = self.load_image(enemy_folder / "new", "space_shooter_extension_ship_009_bomber")

        self.player_image = self.load_image(player_folder, "player_ship_blue")

        self.enemy_images = [
            self.normal_image,
            self.interceptor_image,
            self.tank_image,
            self.ranger_image,
            self.bomber_image
        ]

        self.boss_image = self.tank_image
        self.boss_chance = 0.5   #50 percent tank chance

        print("Enemy sprites loaded:", sum(image is not None for image in self.enemy_images))
        print("Tank sprite loaded:", self.tank_image is not None)
        print("Player sprite loaded:", self.player_image is not None)

    def load_image(self, folder, name):
        for extension in (".png", ".webp", ".jpg", ".jpeg"):
            path = folder / (name + extension)

            if path.exists():
                try:
                    return pygame.image.load(str(path)).convert_alpha()
                except (pygame.error, OSError):
                    print("Could not load:", path)

        return None

    def prepare_enemy(self, enemy, allow_boss=True):
        enemy.is_boss = False
        enemy.last_hit = -1000

        if enemy.enemy_type == 'interceptor':
            enemy.ship_image = self.interceptor_image

        elif enemy.enemy_type == 'ranger':
            enemy.ship_image = self.ranger_image

        elif enemy.enemy_type == 'bomber':
            enemy.ship_image = self.bomber_image

        elif enemy.enemy_type == 'tank':
            enemy.is_boss = True
            enemy.health = 6
            enemy.speed = 60
            enemy.rect.size = (60, 60)
            enemy.rect.center = enemy.position
            enemy.ship_image = self.tank_image

        elif allow_boss and self.tank_image is not None and random.random() < self.boss_chance:
            enemy.enemy_type = 'tank'
            enemy.is_boss = True
            enemy.health = 6
            enemy.speed = 60
            enemy.rect.size = (60, 60)
            enemy.rect.center = enemy.position
            enemy.ship_image = self.tank_image

        else:
            enemy.ship_image = self.normal_image

        enemy.max_health = enemy.health

    def draw_enemy(self, screen, enemy):
        image = enemy.ship_image

        if image is None:
            enemy.draw(screen)
            return

        scale = 1

        width = max(1, int(enemy.rect.width * scale))
        height = max(1, int(enemy.rect.height * scale))

        sprite = pygame.transform.smoothscale(image, (width, height))
        sprite_rect = sprite.get_rect(center=enemy.rect.center)

        if pygame.time.get_ticks() - enemy.last_hit < 120:
            sprite = sprite.copy()
            sprite.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGB_ADD)

        screen.blit(sprite, sprite_rect)

        bar_width = 12
        gap = 3
        total_width = enemy.max_health * bar_width + (enemy.max_health - 1) * gap

        start_x = enemy.rect.centerx - total_width // 2

        for i in range(enemy.max_health):
            colour = (255, 70, 80) if i < enemy.health else (65, 65, 80)

            pygame.draw.rect(
                screen,
                colour,
                (start_x + i * (bar_width + gap), sprite_rect.top - 10, bar_width, 5)
            )

    def draw_player(self, screen, player, mouse_pos):
        if self.player_image is None:
            player.draw(screen)
            return

        image = pygame.transform.smoothscale(
            self.player_image,
            (player.rect.width, player.rect.height)
        )

        direction = pygame.Vector2(mouse_pos) - player.position

        if direction.length_squared() > 0:
            angle = math.degrees(math.atan2(-direction.y, direction.x)) - 90
            image = pygame.transform.rotate(image, angle)

        rect = image.get_rect(center=player.rect.center)
        screen.blit(image, rect)
