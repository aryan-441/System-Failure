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

    if random.random() < 0.33:
        return Enemy(x,y,"interceptor")
    return Enemy(x, y)



class EnemySpawner:

    def __init__(self):
        self.spawn_timer = 0
        self.spawn_interval = 1.1
        self.difficulty_timer = 0
        self.pending_spawns = 0

    def update(self, dt):
        self.spawn_timer += dt
        self.difficulty_timer += dt

        if self.difficulty_timer >= 30:
            self.difficulty_timer -= 30
            self.spawn_interval = max(0.8, round(self.spawn_interval - 0.1, 2))

        if self.pending_spawns > 0:
            return True

        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer -= self.spawn_interval

            self.pending_spawns = random.choices(
                [1, 2, 3],
                weights=[48, 48, 4],
                k=1
            )[0]

            return True

        return False

    def spawn(self):
        if self.pending_spawns > 0:
            self.pending_spawns -= 1

        return create_random_enemy()

