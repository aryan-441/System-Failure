
import random
from enemy import Enemy
from settings import WIDTH, HEIGHT


def create_random_enemy():

    side = random.choice(["top", "bottom", "left", "right"])

    if side == "top":
        x = random.randint(20, WIDTH - 20)
        y = 20

    elif side == "bottom":
        x = random.randint(20, WIDTH - 20)
        y = HEIGHT - 20

    elif side == "left":
        x = 20
        y = random.randint(20, HEIGHT - 20)

    else:
        x = WIDTH - 20
        y = random.randint(20, HEIGHT - 20)

    enemy_type = random.choices(
        ['normal', 'interceptor', 'ranger', 'bomber'],
        weights=[50, 20, 20, 10],
        k=1
    )[0]

    return Enemy(x, y, enemy_type)


class EnemySpawner:

    def __init__(self):
        self.spawn_timer = 0
        self.spawn_interval = 2.5
        self.difficulty_timer = 0
        self.pending_spawns = 0

    def update(self, dt, malfunction_active=False):
        self.spawn_timer += dt
        self.difficulty_timer += dt

        if self.difficulty_timer >= 30:
            self.difficulty_timer -= 30
            self.spawn_interval = max(1.8, round(self.spawn_interval - 0.1, 2))

        if self.pending_spawns > 0:
            return True

        current_interval = self.spawn_interval

        if malfunction_active:
            current_interval = self.spawn_interval * 1.6

        if self.spawn_timer >= current_interval:
            self.spawn_timer -= current_interval

            if malfunction_active:
                weights = [90, 10, 0]
            else:
                weights = [85, 15, 0]

            self.pending_spawns = random.choices(
                [1, 2, 3],
                weights=weights,
                k=1
            )[0]

            return True

        return False

    def spawn(self):
        if self.pending_spawns > 0:
            self.pending_spawns -= 1

        return create_random_enemy()
