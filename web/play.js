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
