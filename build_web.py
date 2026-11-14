from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import textwrap
import shutil
import zipfile

root = Path(__file__).resolve().parent
release = root / "itchio"
release.mkdir(exist_ok=True)
ship = root / "assets/images/player/player_ship_blue.png"
backgrounds = root / "assets/images/backgrounds/seamless_space"

with TemporaryDirectory() as temporary:
    stage = Path(temporary) / "system-failure"
    stage.mkdir()
    modules = [p for p in root.glob("*.py") if p.stem not in {"build_web", "prepare_resources"}]
    from arcade_audio import ArcadeAudio
    sounds = {root / "assets/audio" / name for name in ArcadeAudio.SOUND_FILES.values()}
    enemy_names = ["boss_ship_large", "enemy_black_5", "enemy_blue_3", "enemy_extension_ship_003", "enemy_green_4", "enemy_red_1"]
    sprites = [root / "assets/images/enemies" / (name + ".png") for name in enemy_names]
    for source in [*modules, *sounds, *sprites, ship, *backgrounds.glob("*Nebula*.png")]:
        target = stage / source.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    subprocess.run([sys.executable, "-m", "pygbag", "--build", "--no_opt", "--title",
                    "System Failure: Bounce Back", "--icon", str(ship), str(stage)], check=True)
    built = stage / "build/web"
    loader = (built / "index.html").read_text(encoding="utf-8")
    start = loader.index("    if platform.window.location.host")
    zip_start = loader.index("        import zipfile", start)
    zip_end = loader.index("    else:", zip_start)
    end = loader.index("    # preloader", zip_end)
    loader = loader[:start] + textwrap.indent(textwrap.dedent(loader[zip_start:zip_end]), "    ") + "\n" + loader[end:]
    loader = loader.replace('fb_width : "1280"', 'fb_width : "960"').replace('fb_height : "720"', 'fb_height : "540"')
    loader = loader.replace("#7f7f7f", "#080a19").replace("background: green;", "background: #0c1428;").replace("color: blue;", "color: #dcecff;")
    loader = loader.replace("Ready to start ! Please click/touch page", "Click to enter the cockpit")
    destination = release / "System-Failure-HTML5.zip"
    pending = release / "System-Failure-HTML5.tmp"
    with zipfile.ZipFile(pending, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("game.html", loader)
        archive.write(built / "system-failure.apk", "system-failure.apk")
        archive.write(ship, "favicon.png")
        archive.write(backgrounds / "512x512 Blue Nebula 1.png", "nebula.png")
        for page in sorted((root / "web").iterdir()):
            archive.write(page, page.name)
    pending.replace(destination)
    print(destination)
