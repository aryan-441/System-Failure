(() => {
'use strict';
const media = {"sprites":{"player_ship_blue":[0,0,99,75],"enemy_black_5":[99,0,97,84],"enemy_blue_3":[196,0,103,84],"enemy_extension_ship_003":[299,0,100,94],"enemy_green_4":[399,0,82,84],"enemy_red_1":[481,0,93,84],"boss_ship_large":[574,0,172,151]},"backgroundCount":15,"sounds":{"shoot":"sounds/weapons/laser_small.ogg","hit":"sounds/warnings/player_damage_metal_impact.ogg","enemy_down":"sounds/explosions/explosion_crunch.ogg","player_hit":"sounds/warnings/player_damage_metal_impact.ogg","game_over":"sounds/interface/defeat.ogg","overheat":"sounds/warnings/system_force_field.ogg","ammo":"sounds/interface/recovery_shield_up.ogg","warning":"sounds/warnings/system_computer_noise.ogg"}};
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

class Game {
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
            this.heat = Math.max(0, this.heat - 5 * dt);
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
            this.heat = Math.min(100, this.heat + 10);
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
        this.ammo = Math.min(16, this.ammo + 4);
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


const WIDTH = 960;
const HEIGHT = 540;
const TAU = Math.PI * 2;
const WHITE = "#ffffff";
const GOLD = "#ffdc5a";
const CORAL = "#ff7882";
const MINT = "#78ffaa";

function between(min, max) {
    return min + Math.random() * (max - min);
}

function label(ctx, value, x, y, size = 20, color = WHITE, align = "left") {
    ctx.font = `bold ${size}px Arial, sans-serif`;
    ctx.textAlign = align;
    ctx.textBaseline = "middle";
    ctx.fillStyle = color;
    ctx.fillText(value, x, y);
}

function circle(ctx, x, y, radius) {
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, TAU);
    ctx.fill();
}

function drawShip(ctx, image, x, y, width, height, fallback) {
    if (image) {
        ctx.drawImage(image, x - width / 2, y - height / 2, width, height);
    } else {
        ctx.fillStyle = fallback;
        ctx.fillRect(x - width / 2, y - height / 2, width, height);
    }
}

function drawLaser(ctx, bullet) {
    ctx.beginPath();
    ctx.moveTo(bullet.x - bullet.dx * 26, bullet.y - bullet.dy * 26);
    ctx.lineTo(bullet.x, bullet.y);
    ctx.strokeStyle = "#0f416e";
    ctx.lineWidth = 12;
    ctx.stroke();
    ctx.strokeStyle = "#1eb4ff";
    ctx.lineWidth = 7;
    ctx.stroke();
    ctx.strokeStyle = "#f0faff";
    ctx.lineWidth = 3;
    ctx.stroke();
}

function drawHud(ctx, game) {
    label(ctx, `Score: ${game.score}`, 20, 30);
    label(ctx, `Health: ${game.player.health}`, 20, 70);
    label(ctx, `Ammo: ${game.ammo}`, 20, 110, 20, GOLD);
    label(ctx, `High Score: ${game.highScore}`, 940, 30, 20, GOLD, "right");
    const failure = game.malfunction.replaceAll("_", " ");
    if (game.time < 15) {
        label(ctx, "SYSTEM STABLE", 940, 70, 20, WHITE, "right");
        label(ctx, `FIRST FAILURE IN ${Math.floor(16 - game.time)}s`, 940, 108, 16, CORAL, "right");
    } else {
        label(ctx, `ROUND: ${game.round}`, 940, 70, 20, WHITE, "right");
        label(ctx, `SYSTEM ERROR: ${failure}`, 940, 108, 16, CORAL, "right");
        label(ctx, game.explanation, 940, 138, 16, "#c8d2e6", "right");
    }
    if (game.malfunction === "WEAPON_OVERHEATING") {
        label(ctx, `Weapon Heat: ${Math.floor(game.heat)}%`, 940, 190, 20, "#ff6450", "right");
        if (game.overheated) label(ctx, "WEAPON OVERHEATED!", 940, 230, 20, "#ff3232", "right");
    }
    if (game.ammo === 0) label(ctx, "OUT OF AMMO - EMERGENCY SUPPLY INCOMING", 20, 150, 20, "#ff5050");
    if (game.newRecord) label(ctx, `NEW HIGH SCORE! PREVIOUS: ${game.previousHighScore}`, 940, 510, 20, MINT, "right");
    if (game.bannerTime > 0) {
        ctx.save();
        ctx.globalAlpha = Math.max(0, Math.min(1, (2 - game.bannerTime) / 0.18, game.bannerTime / 0.45));
        ctx.beginPath();
        ctx.roundRect(1.5, 152.5, WIDTH - 3, 87, 12);
        ctx.fillStyle = "rgba(45,8,25,.63)";
        ctx.fill();
        ctx.lineWidth = 3;
        ctx.strokeStyle = "#ff5569";
        ctx.stroke();
        label(ctx, "SYSTEM ERROR", 480, 179, 38, CORAL, "center");
        label(ctx, failure, 480, 218, 24, WHITE, "center");
        ctx.restore();
    }
}

function drawGameOver(ctx, game) {
    label(ctx, "SYSTEM FAILURE", 480, 200, 60, "#ff4155", "center");
    label(ctx, `FINAL SCORE: ${game.score}`, 480, 280, 20, WHITE, "center");
    label(ctx, "PRESS R TO RESTART", 480, 340, 22, "#78c8ff", "center");
    label(ctx, `HIGH SCORE: ${game.highScore}`, 480, 385, 20, GOLD, "center");
    if (game.newRecord) label(ctx, `NEW HIGH SCORE! PREVIOUS: ${game.previousHighScore}`, 480, 425, 20, MINT, "center");
}

class Renderer {
    constructor(canvas, assets) {
        this.canvas = canvas;
        this.ctx = canvas.getContext("2d", {alpha: false});
        this.assets = assets;
        this.age = 0;
        this.previousTime = 0;
        this.masks = new WeakMap();
        this.stars = Array.from({length: 80}, () => ({
            x: Math.random() * WIDTH,
            y: Math.random() * HEIGHT,
            radius: Math.random() < 0.5 ? 1 : 2,
            speed: between(10, 45)
        }));
        this.clearEffects();
    }

    clearEffects() {
        this.particles = [];
        this.labels = [];
        this.shake = 0;
        this.damageFlash = 0;
        this.smokeTimer = 0;
    }

    background(dt) {
        const {ctx, assets} = this;
        this.age += dt;
        const images = assets.backgrounds;
        const first = images[0];
        ctx.fillStyle = "#080a19";
        ctx.fillRect(0, 0, WIDTH, HEIGHT);
        if (first) {
            const index = Math.floor(this.age / 12) % images.length;
            const phase = this.age % 12;
            const current = images[index] || first;
            const next = images[(index + 1) % images.length];
            const offset = Math.floor(this.age * 15) % 512;
            this.tiles(current, offset);
            if (phase > 10 && next) {
                ctx.globalAlpha = (phase - 10) / 2;
                this.tiles(next, offset);
                ctx.globalAlpha = 1;
            }
        }
        ctx.fillStyle = "#b4d2ff";
        for (const star of this.stars) {
            star.y += star.speed * dt;
            if (star.y > HEIGHT) {
                star.y = 0;
                star.x = Math.random() * WIDTH;
            }
            circle(ctx, Math.round(star.x), Math.round(star.y), star.radius);
        }
    }

    tiles(image, offset) {
        for (let y = offset - 512; y < HEIGHT; y += 512) {
            for (let x = 0; x < WIDTH; x += 512) {
                this.ctx.drawImage(image, x, y, 512, 512);
            }
        }
    }

    enemy(enemy) {
        const {ctx} = this;
        const image = this.assets.sprites[enemy.sprite];
        const scale = enemy.boss ? 1.5 : 1;
        const size = 40 * scale;
        drawShip(ctx, image, enemy.x, enemy.y, size, size, "#ff0000");
        const start = enemy.x - (enemy.maxHealth * 15 - 3) / 2;
        for (let i = 0; i < enemy.maxHealth; i++) {
            ctx.fillStyle = i < enemy.health ? "#ff4650" : "#414150";
            ctx.fillRect(Math.round(start + 15 * i), Math.round(enemy.y - size / 2 - 10), 12, 5);
        }
        if (enemy.hitFlash > 0 && image) {
            let mask = this.masks.get(image);
            if (!mask) {
                mask = document.createElement("canvas");
                mask.width = image.naturalWidth || image.width;
                mask.height = image.naturalHeight || image.height;
                const target = mask.getContext("2d");
                target.drawImage(image, 0, 0);
                target.globalCompositeOperation = "source-in";
                target.fillStyle = WHITE;
                target.fillRect(0, 0, mask.width, mask.height);
                this.masks.set(image, mask);
            }
            drawShip(ctx, mask, enemy.x, enemy.y, mask.width * scale, mask.height * scale);
        }
    }

    particle(x, y, vx, vy, color, life, radius) {
        this.particles.push({x, y, vx, vy, color, life, duration: life, radius});
    }

    sparks(x, y, count, color) {
        for (let i = 0; i < count; i++) {
            const angle = Math.random() * TAU;
            const speed = between(60, 220);
            this.particle(x, y, Math.cos(angle) * speed, Math.sin(angle) * speed, color, between(0.15, 0.5), between(2, 5));
        }
    }

    updateEffects(game, dt) {
        this.shake = Math.max(0, this.shake - dt * 28);
        this.damageFlash = Math.max(0, this.damageFlash - dt);
        for (const event of game.events) {
            const {type, x, y} = event;
            if (type === "shoot") {
                for (let i = 0; i < 5; i++) {
                    const angle = Math.atan2(event.dy, event.dx) + between(-Math.PI / 6, Math.PI / 6);
                    const speed = between(40, 130);
                    this.particle(x + event.dx * 28, y + event.dy * 28, Math.cos(angle) * speed, Math.sin(angle) * speed, "#5fdcff", 0.12, 3);
                }
            } else if (type === "hit") {
                this.sparks(x, y, 10, "#afebff");
            } else if (type === "enemy_down") {
                this.sparks(x, y, 24, event.boss ? "#ff645f" : "#ffb946");
                this.shake = Math.max(this.shake, event.boss ? 7 : 3);
            } else if (type === "player_hit") {
                this.sparks(x, y, 22, "#ff415a");
                this.labels.push({x: x + between(-8, 8), y: y - 22, value: `-${event.damage}`, life: 0.95});
                this.shake = 9;
                this.damageFlash = 0.28;
            } else if (type === "warning") {
                this.shake = Math.max(this.shake, 4);
            }
        }
        if (game.overheated) {
            this.smokeTimer += dt;
            while (this.smokeTimer >= 0.035) {
                this.smokeTimer -= 0.035;
                const grey = Math.floor(between(100, 161));
                this.particle(game.player.x + between(-20, 20), game.player.y + between(-10, 10), between(-25, 25), between(-75, -30), `rgb(${grey},${grey},${grey})`, between(0.5, 1.1), between(5, 10));
            }
        }
    }

    drawEffects(dt) {
        const {ctx} = this;
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            p.life -= dt;
            if (p.life <= 0) {
                this.particles.splice(i, 1);
                continue;
            }
            p.x += p.vx * dt;
            p.y += p.vy * dt;
            const fraction = p.life / p.duration;
            ctx.globalAlpha = 0.86 * fraction;
            ctx.fillStyle = p.color;
            circle(ctx, p.x, p.y, Math.max(1, Math.floor(p.radius * (1.5 - fraction * 0.5))));
        }
        for (let i = this.labels.length - 1; i >= 0; i--) {
            const item = this.labels[i];
            item.life -= dt;
            if (item.life <= 0) {
                this.labels.splice(i, 1);
                continue;
            }
            item.y -= 60 * dt;
            ctx.globalAlpha = item.life / 0.95;
            label(ctx, item.value, item.x, item.y, 24, "#ff5069", "center");
        }
        ctx.globalAlpha = 1;
    }

    render(game, dt, pointer) {
        const {ctx, canvas} = this;
        ctx.setTransform(canvas.width / WIDTH, 0, 0, canvas.height / HEIGHT, 0, 0);
        if (game.time < this.previousTime) this.clearEffects();
        this.previousTime = game.time;
        if (!game.gameOver) this.updateEffects(game, dt);
        ctx.save();
        if (this.shake >= 1 && !game.gameOver) {
            ctx.fillStyle = "#0a0c1c";
            ctx.fillRect(0, 0, WIDTH, HEIGHT);
            ctx.translate(Math.round(between(-this.shake, this.shake)), Math.round(between(-this.shake, this.shake)));
        }
        this.background(dt);
        if (game.gameOver) {
            ctx.restore();
            drawGameOver(ctx, game);
            return;
        }
        const player = game.player;
        const aim = pointer || {x: game.aimX, y: game.aimY};
        ctx.save();
        ctx.translate(player.x, player.y);
        if (aim.x !== player.x || aim.y !== player.y) ctx.rotate(Math.atan2(aim.y - player.y, aim.x - player.x) + Math.PI / 2);
        drawShip(ctx, this.assets.sprites.player_ship_blue, 0, 0, 40, 40, "#46a0ff");
        ctx.restore();
        for (const enemy of game.enemies) this.enemy(enemy);
        for (const bullet of game.bullets) drawLaser(ctx, bullet);
        this.drawEffects(dt);
        ctx.restore();
        drawHud(ctx, game);
        if (this.damageFlash > 0) {
            ctx.lineWidth = 17;
            ctx.strokeStyle = `rgba(255,20,55,${0.29 * Math.min(1, this.damageFlash / 0.15)})`;
            ctx.strokeRect(8.5, 8.5, WIDTH - 17, HEIGHT - 17);
        }
    }
}

const canvas = document.querySelector("#canvas");
const loading = document.querySelector("#loading");

function loadImage(url) {
    return new Promise((resolve, reject) => {
        const image = new Image();
        image.onload = () => resolve(image);
        image.onerror = () => reject(new Error("Could not load " + url));
        image.src = url;
    });
}

function cutSprites(sheet) {
    const sprites = {};
    for (const [name, [x, y, width, height]] of Object.entries(media.sprites)) {
        const part = document.createElement("canvas");
        part.width = width;
        part.height = height;
        part.getContext("2d").drawImage(sheet, x, y, width, height, 0, 0, width, height);
        sprites[name] = part;
    }
    return sprites;
}

function makeSoundPlayer() {
    if (location.protocol === "file:") {
        const clips = new Map();
        return {
            enable() {},
            play(type) {
                const path = media.sounds[type];
                if (!path) return;
                if (!clips.has(path)) clips.set(path, new Audio(path));
                const clip = clips.get(path);
                clip.currentTime = 0;
                clip.volume = 0.45;
                clip.play().catch(() => {});
            }
        };
    }
    let context;
    const sounds = new Map();
    const paths = Object.values(media.sounds);
    function enable() {
        try {
            if (!context) {
                context = new AudioContext();
                for (const path of new Set(paths)) {
                    const buffer = fetch(path).then(response => {
                        if (!response.ok) throw new Error(path);
                        return response.arrayBuffer();
                    }).then(data => context.decodeAudioData(data)).catch(() => null);
                    sounds.set(path, buffer);
                }
            }
            if (context.state === "suspended") context.resume().catch(() => {});
        } catch {}
    }
    async function play(type) {
        const pending = sounds.get(media.sounds[type]);
        if (!pending || !context) return;
        const buffer = await pending;
        if (!buffer || context.state !== "running") return;
        const source = context.createBufferSource();
        const gain = context.createGain();
        gain.gain.value = 0.45;
        source.buffer = buffer;
        source.connect(gain).connect(context.destination);
        source.start();
    }
    return {enable, play};
}

function bindControls(game, audio) {
    const keys = new Set();
    const controls = {aimX: 480, aimY: 0, fire: false};
    const bindings = {
        left: ["KeyA", "ArrowLeft"], right: ["KeyD", "ArrowRight"],
        up: ["KeyW", "ArrowUp"], down: ["KeyS", "ArrowDown"]
    };
    function updateKeys() {
        for (const [name, codes] of Object.entries(bindings)) {
            controls[name] = codes.some(code => keys.has(code));
        }
    }
    function reset() {
        keys.clear();
        updateKeys();
        controls.fire = false;
    }
    function aim(event) {
        const rect = canvas.getBoundingClientRect();
        controls.aimX = (event.clientX - rect.left) * canvas.width / rect.width;
        controls.aimY = (event.clientY - rect.top) * canvas.height / rect.height;
    }
    window.addEventListener("keydown", event => {
        if (event.ctrlKey || event.altKey || event.metaKey || event.isComposing) return;
        if (event.code.startsWith("Arrow")) event.preventDefault();
        if (event.code === "KeyR" && !event.repeat && game.gameOver) game.restart();
        if (!event.repeat) audio.enable();
        keys.add(event.code);
        updateKeys();
    });
    window.addEventListener("keyup", event => {
        keys.delete(event.code);
        updateKeys();
    });
    canvas.addEventListener("pointermove", aim);
    canvas.addEventListener("pointerdown", event => {
        if (event.button !== 0) return;
        canvas.focus();
        audio.enable();
        canvas.setPointerCapture(event.pointerId);
        aim(event);
        controls.fire = true;
    });
    window.addEventListener("pointerup", event => {
        if (event.button === 0) controls.fire = false;
    });
    canvas.addEventListener("lostpointercapture", () => { controls.fire = false; });
    window.addEventListener("blur", reset);
    document.addEventListener("visibilitychange", () => { if (document.hidden) reset(); });
    return controls;
}

async function startGame() {
    const [sheet, nebula] = await Promise.all([loadImage("ships.png"), loadImage("space/0.webp")]);
    const backgrounds = Array(media.backgroundCount).fill(null);
    backgrounds[0] = nebula;
    const game = new Game();
    const audio = makeSoundPlayer();
    const controls = bindControls(game, audio);
    const renderer = new Renderer(canvas, {sprites: cutSprites(sheet), backgrounds});
    const requested = new Set([0]);
    let previousTime = performance.now();
    let elapsed = 0;

    function frame(now) {
        const dt = Math.max(0, Math.min((now - previousTime) / 1000, 0.05));
        previousTime = now;
        elapsed += dt;
        game.update(dt, controls);
        renderer.render(game, dt);
        for (const event of game.events) audio.play(event.type);
        if (elapsed >= 2) {
            const next = (Math.floor(elapsed / 12) + 1) % backgrounds.length;
            if (!requested.has(next)) {
                requested.add(next);
                loadImage("space/" + next + ".webp").then(image => { backgrounds[next] = image; }).catch(() => {});
            }
        }
        requestAnimationFrame(frame);
    }
    canvas.focus({preventScroll: true});
    frame(previousTime);
    loading.remove();
    performance.mark("game-playable");
}

startGame().catch(() => {
    loading.replaceChildren("Flight deck could not load. ");
    const retry = document.createElement("a");
    retry.href = location.href;
    retry.textContent = "Try again";
    loading.append(retry);
});

})();