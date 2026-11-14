const width = 960;
const height = 540;
const shipHalfSize = 20;
const storageKey = "system-failure.best";

const enemySprites = [
    "enemy_black_5", "enemy_blue_3", "enemy_extension_ship_003", "enemy_green_4", "enemy_red_1"
];

const explanations = {
    NONE: "All systems operational",
    REVERSED: "Movement controls are reversed",
    RECOIL: "Firing pushes your ship backwards",
    DAMAGED_THRUSTERS: "Movement speed is reduced",
    SHIELD_MALFUNCTION: "Collisions deal double damage",
    WEAPON_OVERHEATING: "Firing builds heat until the weapon jams",
    ENGINE_STALLING: "Your engines periodically stop",
    TARGETING_GLITCH: "Bullets may veer off target",
    ENGINE_DRIFT: "Your ship drifts to the right",
    REACTOR_INSTABILITY: "Random bursts push your ship off course"
};
const failures = Object.keys(explanations).filter(name => name !== "NONE");

function randomItem(items) {
    return items[Math.floor(Math.random() * items.length)];
}

function readBest() {
    try {
        const saved = JSON.parse(localStorage.getItem(storageKey));
        const best = saved?.high_score ?? saved;
        return Number.isSafeInteger(best) && best >= 0 ? best : 0;
    } catch {
        return 0;
    }
}

function storeBest(best) {
    try {
        localStorage.setItem(storageKey, JSON.stringify({high_score: best}));
    } catch {
        return;
    }
}

function keepInBounds(ship) {
    ship.x = Math.max(shipHalfSize, Math.min(width - shipHalfSize, ship.x));
    ship.y = Math.max(shipHalfSize, Math.min(height - shipHalfSize, ship.y));
}

function enemyAt(x, y, boss = false) {
    const maxHealth = boss ? 5 : 3;
    return {
        x, y, boss, maxHealth, health: maxHealth, hitFlash: 0,
        sprite: boss ? "boss_ship_large" : randomItem(enemySprites)
    };
}

function touches(a, b, reach) {
    return Math.abs(Math.round(a.x) - Math.round(b.x)) < reach &&
        Math.abs(Math.round(a.y) - Math.round(b.y)) < reach;
}

function separateEnemies(enemies) {
    for (let i = 0; i < enemies.length; i++) {
        const a = enemies[i];
        for (let j = i + 1; j < enemies.length; j++) {
            const b = enemies[j];
            let x = b.x - a.x;
            let y = b.y - a.y;
            let distance = Math.hypot(x, y);
            if (distance >= 44) continue;
            if (distance < 0.001) {
                x = i % 2 === 0 ? 1 : -1;
                y = 0;
                distance = 1;
            }
            const push = (44 - distance) / (2 * distance);
            a.x -= x * push;
            a.y -= y * push;
            b.x += x * push;
            b.y += y * push;
            keepInBounds(a);
            keepInBounds(b);
        }
    }
}

export class Game {
    constructor() {
        this.highScore = readBest();
        this.restart();
    }

    restart() {
        this.player = {x: width / 2, y: height / 2, health: 5};
        this.enemies = [enemyAt(150, 150), enemyAt(800, 150), enemyAt(150, 400)];
        this.bullets = [];
        this.events = [];
        this.score = 0;
        this.previousHighScore = this.highScore;
        this.newRecord = false;
        this.ammo = 16;
        this.time = 0;
        this.round = 1;
        this.nextFailure = 15;
        this.malfunction = "NONE";
        this.bannerTime = 0;
        this.shotDelay = 0;
        this.hurtDelay = 0;
        this.spawnTime = 0;
        this.lastBossTime = 0;
        this.emptyTime = 0;
        this.recoilX = 0;
        this.recoilY = 0;
        this.aimX = this.player.x;
        this.aimY = this.player.y - 1;
        this.resetFailureEffects();
    }

    get gameOver() {
        return this.player.health <= 0;
    }

    get explanation() {
        return explanations[this.malfunction];
    }

    resetFailureEffects() {
        this.heat = 0;
        this.overheated = false;
        this.stalled = false;
        this.stallTime = 0;
        this.reactorTime = 0;
        this.burstRemaining = 0;
        this.burstX = 0;
        this.burstY = 0;
    }

    updateRound(dt) {
        this.bannerTime = Math.max(0, this.bannerTime - dt);
        if (this.time < this.nextFailure) return;
        if (this.malfunction !== "NONE") this.round++;
        this.malfunction = randomItem(failures.filter(name => name !== this.malfunction));
        this.nextFailure += 30;
        this.bannerTime = 2;
        this.resetFailureEffects();
        this.events.push({type: "warning"});
    }

    movePlayer(dt, input) {
        let dx = Number(Boolean(input.right)) - Number(Boolean(input.left));
        let dy = Number(Boolean(input.down)) - Number(Boolean(input.up));
        const length = Math.hypot(dx, dy) || 1;
        const sign = this.malfunction === "REVERSED" ? -1 : 1;
        let speed = this.malfunction === "DAMAGED_THRUSTERS" ? 125 : 250;
        if (this.malfunction === "ENGINE_STALLING") {
            this.stallTime += dt;
            if (this.stallTime >= (this.stalled ? 1.5 : 5)) {
                this.stalled = !this.stalled;
                this.stallTime = 0;
            }
            if (this.stalled) speed = 0;
        }
        const player = this.player;
        dx *= sign * speed / length;
        dy *= sign * speed / length;
        player.x += (dx + this.recoilX) * dt;
        player.y += (dy + this.recoilY) * dt;
        this.recoilX *= Math.max(0, 1 - 6 * dt);
        this.recoilY *= Math.max(0, 1 - 6 * dt);
        keepInBounds(player);
        if (this.malfunction === "ENGINE_DRIFT") player.x += 80 * dt;
        if (this.malfunction === "REACTOR_INSTABILITY") {
            this.reactorTime += dt;
            if (this.burstRemaining <= 0 && this.reactorTime >= 4) {
                const x = Math.random() * 2 - 1;
                const y = Math.random() * 2 - 1;
                const magnitude = Math.hypot(x, y) || 1;
                this.burstX = 350 * x / magnitude;
                this.burstY = 350 * y / magnitude;
                this.burstRemaining = 0.5;
                this.reactorTime = 0;
            }
            this.burstRemaining -= dt;
            if (this.burstRemaining > 0) {
                player.x += this.burstX * dt;
                player.y += this.burstY * dt;
            }
        }
        keepInBounds(player);
    }

    moveEnemies(dt) {
        if (this.enemies.length < 9) {
            this.spawnTime += dt;
            if (this.spawnTime >= 1 / Math.min(0.65, 0.30 + this.time * 0.002)) {
                this.spawnTime = 0;
                const edge = Math.floor(Math.random() * 4);
                const x = edge < 2 ? 20 + Math.floor(Math.random() * 921) : edge === 2 ? 20 : 940;
                const y = edge < 2 ? (edge === 0 ? 20 : 520) : 20 + Math.floor(Math.random() * 501);
                const boss = this.time - this.lastBossTime >= 40 &&
                    !this.enemies.some(enemy => enemy.boss) && Math.random() < 0.5;
                if (boss) this.lastBossTime = this.time;
                this.enemies.push(enemyAt(x, y, boss));
            }
        }
        for (const enemy of this.enemies) {
            enemy.hitFlash = Math.max(0, enemy.hitFlash - dt);
            const dx = this.player.x - enemy.x;
            const dy = this.player.y - enemy.y;
            const distance = Math.hypot(dx, dy) || 1;
            enemy.x += dx / distance * 100 * dt;
            enemy.y += dy / distance * 100 * dt;
        }
        separateEnemies(this.enemies);
    }

    fireWeapon(dt, input) {
        this.shotDelay = Math.max(0, this.shotDelay - dt);
        if (this.malfunction === "WEAPON_OVERHEATING") {
            this.heat = Math.max(0, this.heat - 9 * dt);
            if (this.heat <= 40) this.overheated = false;
        }
        if (this.ammo === 0 && this.bullets.length === 0) {
            this.emptyTime += dt;
            if (this.emptyTime >= 5) {
                this.ammo = 3;
                this.emptyTime = 0;
                this.events.push({type: "ammo"});
            }
        } else {
            this.emptyTime = 0;
        }
        if (!input.fire || this.shotDelay > 0 || this.ammo === 0 || this.overheated) return;
        const {x, y} = this.player;
        if (x === this.aimX && y === this.aimY) return;
        let angle = Math.atan2(this.aimY - y, this.aimX - x);
        if (this.malfunction === "TARGETING_GLITCH") angle += (Math.random() * 34 - 17) * Math.PI / 180;
        const dx = Math.cos(angle);
        const dy = Math.sin(angle);
        this.bullets.push({x, y, dx, dy});
        this.events.push({type: "shoot", x, y, dx, dy});
        this.shotDelay = 0.2;
        this.ammo--;
        if (this.malfunction === "RECOIL") {
            this.recoilX -= dx * 220;
            this.recoilY -= dy * 220;
        }
        if (this.malfunction === "WEAPON_OVERHEATING") {
            this.heat = Math.min(100, this.heat + 5);
            if (this.heat >= 100) {
                this.overheated = true;
                this.events.push({type: "overheat"});
            }
        }
    }

    hitEnemy(enemy) {
        const {x, y, boss} = enemy;
        this.events.push({type: "hit", x, y, boss});
        enemy.health--;
        enemy.hitFlash = 0.17;
        if (enemy.health > 0) return;
        this.events.push({type: "enemy_down", x, y, boss});
        this.enemies.splice(this.enemies.indexOf(enemy), 1);
        this.score += 100;
        this.ammo = Math.min(24, this.ammo + 4);
        if (this.score > this.highScore) {
            this.highScore = Math.max(this.score, readBest());
            this.newRecord = this.score === this.highScore;
            if (this.newRecord) storeBest(this.highScore);
        }
    }

    advanceBullets(dt) {
        this.bullets = this.bullets.filter(bullet => {
            bullet.x += bullet.dx * 500 * dt;
            bullet.y += bullet.dy * 500 * dt;
            if (bullet.x <= -4 || bullet.x >= width + 4 || bullet.y <= -4 || bullet.y >= height + 4) return false;
            const target = this.enemies.find(enemy => touches(bullet, enemy, 24));
            if (!target) return true;
            this.hitEnemy(target);
            return false;
        });
    }

    update(dt, input) {
        this.events = [];
        if (this.gameOver) return;
        dt = Math.max(0, Math.min(0.05, dt));
        if (Number.isFinite(input.aimX)) this.aimX = input.aimX;
        if (Number.isFinite(input.aimY)) this.aimY = input.aimY;
        this.time += dt;
        this.updateRound(dt);
        this.movePlayer(dt, input);
        this.moveEnemies(dt);
        this.fireWeapon(dt, input);
        this.advanceBullets(dt);
        this.hurtDelay = Math.max(0, this.hurtDelay - dt);
        if (this.hurtDelay === 0 && this.enemies.some(enemy => touches(this.player, enemy, 40))) {
            const damage = this.malfunction === "SHIELD_MALFUNCTION" ? 2 : 1;
            this.player.health = Math.max(0, this.player.health - damage);
            this.hurtDelay = 1;
            this.events.push({type: "player_hit", x: this.player.x, y: this.player.y, damage});
            if (this.gameOver) this.events.push({type: "game_over"});
        }
    }
}

