
import random
from enemy import Enemy
from settings import WIDTH, HEIGHT


def choose_enemy_type():
    return random.choices(
        ['normal', 'interceptor', 'ranger', 'bomber'],
        weights=[50, 20, 20, 10],
        k=1
    )[0]


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

    return Enemy(x, y, choose_enemy_type())


class EnemySpawner:

    def __init__(self, difficulty):
        self.spawn_timer = 0
        self.difficulty_timer = 0
        self.pending_spawns = 0

        self.single_interval = difficulty['single_interval']
        self.double_interval = difficulty['double_interval']

        self.min_single_interval = difficulty['min_single_interval']
        self.min_double_interval = difficulty['min_double_interval']

        self.difficulty_increase = difficulty['difficulty_increase']
        self.spawn_weights = difficulty['spawn_weights']

        self.batch_size = random.choices(
            [1, 2],
            weights=self.spawn_weights,
            k=1
        )[0]

    def update(self, dt, malfunction_active=False):
        self.spawn_timer += dt
        self.difficulty_timer += dt

        if self.difficulty_timer >= 30:
            self.difficulty_timer -= 30

            self.single_interval = max(
                self.min_single_interval,
                round(self.single_interval - self.difficulty_increase, 2)
            )

            self.double_interval = max(
                self.min_double_interval,
                round(self.double_interval - self.difficulty_increase, 2)
            )

        if self.pending_spawns > 0:
            return True

        if self.batch_size == 1:
            current_interval = self.single_interval
        else:
            current_interval = self.double_interval

        if malfunction_active:
            current_interval *= 1.3

        if self.spawn_timer >= current_interval:
            self.spawn_timer = 0
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
                weights=self.spawn_weights,
                k=1
            )[0]

        return enemy
