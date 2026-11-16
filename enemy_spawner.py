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
        self.spawn_interval = 2.5

    def update(self, dt):
        self.spawn_timer += dt

        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            return True

        return False

    def spawn(self):
        return create_random_enemy()
