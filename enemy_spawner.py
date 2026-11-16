
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
        self.pending_spawns = 0

        self.batch_size = random.choices(
            [1, 2],
            weights=[75, 25],
            k=1
        )[0]

        self.spawn_interval = 1.0 if self.batch_size == 1 else 1.5

    def update(self, dt, malfunction_active=False):
        self.spawn_timer += dt

        if self.pending_spawns > 0:
            return True

        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer -= self.spawn_interval
            self.pending_spawns = self.batch_size
            return True

        return False

    def spawn(self):
        if self.pending_spawns > 0:
            self.pending_spawns -= 1

        enemy = create_random_enemy()

        if self.pending_spawns == 0:
            self.batch_size = random.choices(
                [1, 2],
                weights=[75, 25],
                k=1
            )[0]

            self.spawn_interval = 1.0 if self.batch_size == 1 else 1.5

        return enemy
