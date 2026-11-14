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
