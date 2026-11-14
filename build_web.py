import ast
import io
import json
import tempfile
import zipfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
IMAGES = ROOT / "assets/images"
RELEASE = ROOT / "itchio"
SPRITES = [
    "player/player_ship_blue",
    "enemies/enemy_black_5",
    "enemies/enemy_blue_3",
    "enemies/enemy_extension_ship_003",
    "enemies/enemy_green_4",
    "enemies/enemy_red_1",
    "enemies/boss_ship_large",
]


def image_bytes(image, image_format, **options):
    output = io.BytesIO()
    image.save(output, image_format, **options)
    return output.getvalue()


def pack_images(archive):
    ships = {}
    for filename in SPRITES:
        with Image.open(IMAGES / f"{filename}.png") as source:
            ships[Path(filename).name] = source.convert("RGBA")
    sheet = Image.new("RGBA", (sum(im.width for im in ships.values()), max(im.height for im in ships.values())))
    regions = {}
    x = 0
    for name, ship in ships.items():
        sheet.paste(ship, (x, 0))
        regions[name] = [x, 0, ship.width, ship.height]
        x += ship.width
    archive.writestr("ships.png", image_bytes(sheet, "PNG", optimize=True))

    backgrounds = sorted((IMAGES / "backgrounds/seamless_space").glob("*Nebula*.png"))
    if not backgrounds:
        raise FileNotFoundError("Missing nebula artwork")
    for index, path in enumerate(backgrounds):
        with Image.open(path) as source:
            archive.writestr(f"space/{index}.webp", image_bytes(source.convert("RGB"), "WEBP", quality=86, method=6))
    return regions, len(backgrounds)


def pack_audio(archive):
    tree = ast.parse((ROOT / "arcade_audio.py").read_text(encoding="utf-8-sig"))
    sound_files = next(ast.literal_eval(node.value) for node in ast.walk(tree)
                       if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and
                       target.id == "SOUND_FILES" for target in node.targets))
    for filename in sorted(set(sound_files.values())):
        archive.write(ROOT / "assets/audio" / filename, "sounds/" + filename)
    return {event: "sounds/" + filename for event, filename in sound_files.items()}


def build():
    RELEASE.mkdir(exist_ok=True)
    destination = RELEASE / "System-Failure-HTML5.zip"
    with tempfile.TemporaryDirectory(dir=RELEASE) as scratch:
        pending = Path(scratch) / destination.name
        with zipfile.ZipFile(pending, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            regions, count = pack_images(archive)
            sounds = pack_audio(archive)
            manifest = {"sprites": regions, "backgroundCount": count, "sounds": sounds}
            scripts = ["const media = " + json.dumps(manifest, separators=(",", ":")) + ";"]
            for filename in ("simulation.js", "render.js", "play.js"):
                scripts.append((WEB / filename).read_text(encoding="utf-8"))
            archive.writestr("flight.js", "(() => {\n'use strict';\n" + "\n".join(scripts) + "\n})();")
            archive.write(IMAGES / "player/player_ship_blue.png", "favicon.png")
            for page in sorted(WEB.iterdir()):
                if page.suffix in (".css", ".html"):
                    archive.write(page, page.name)
        pending.replace(destination)
    print(f"{destination} ({destination.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()
