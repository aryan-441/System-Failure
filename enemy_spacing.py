import pygame


def separate_enemies(enemies, width, height):
    """Push overlapping enemies apart and keep them inside the play area."""
    for index, enemy_a in enumerate(enemies):
        for enemy_b in enemies[index + 1:]:
            difference = enemy_b.position - enemy_a.position
            distance = difference.length()

            radius_a = max(enemy_a.rect.width, enemy_a.rect.height) * 0.55
            radius_b = max(enemy_b.rect.width, enemy_b.rect.height) * 0.55
            minimum_distance = radius_a + radius_b

            if distance >= minimum_distance:
                continue

            if distance < 0.001:
                difference = pygame.Vector2(
                    1 if index % 2 == 0 else -1, 0
                )
                distance = 1

            movement = (
                difference / distance
                * (minimum_distance - distance)
                * 0.5
            )
            enemy_a.position -= movement
            enemy_b.position += movement

            for enemy in (enemy_a, enemy_b):
                half_width = enemy.rect.width / 2
                half_height = enemy.rect.height / 2
                enemy.position.x = max(
                    half_width, min(width - half_width, enemy.position.x)
                )
                enemy.position.y = max(
                    half_height, min(height - half_height, enemy.position.y)
                )
                enemy.rect.center = enemy.position
