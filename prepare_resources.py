from pathlib import Path
from zipfile import ZipFile

root = Path(__file__).resolve().parent
packs = root.parent / "original_asset_packs"
selection = {
    "kenney_space-shooter-redux.zip": {
        "Backgrounds/black.png": "assets/images/backgrounds/space_black.png",
        "Backgrounds/blue.png": "assets/images/backgrounds/space_blue.png",
        "Backgrounds/darkPurple.png": "assets/images/backgrounds/space_dark_purple.png",
        "PNG/playerShip1_blue.png": "assets/images/player/player_ship_blue.png",
        "PNG/playerShip2_orange.png": "assets/images/player/player_ship_orange.png",
        "PNG/Enemies/enemyRed1.png": "assets/images/enemies/enemy_red_1.png",
        "PNG/Enemies/enemyBlack5.png": "assets/images/enemies/enemy_black_5.png",
        "PNG/Enemies/enemyGreen4.png": "assets/images/enemies/enemy_green_4.png",
        "PNG/Enemies/enemyBlue3.png": "assets/images/enemies/enemy_blue_3.png",
        "PNG/Meteors/meteorGrey_big1.png": "assets/images/enemies/meteor_grey_big.png",
        "PNG/Lasers/laserBlue01.png": "assets/images/projectiles/laser_blue_01.png",
        "PNG/Lasers/laserRed01.png": "assets/images/projectiles/laser_red_01.png",
        "PNG/Effects/fire00.png": "assets/images/effects/explosion_fire_00.png",
        "PNG/Effects/fire01.png": "assets/images/effects/explosion_fire_01.png",
        "PNG/Effects/fire02.png": "assets/images/effects/explosion_fire_02.png",
        "PNG/Effects/fire03.png": "assets/images/effects/explosion_fire_03.png",
        "PNG/Effects/shield1.png": "assets/images/effects/shield_1.png",
        "PNG/UI/buttonBlue.png": "assets/images/ui/button_blue.png",
        "PNG/UI/playerLife1_blue.png": "assets/images/ui/player_life_blue.png",
        "PNG/UI/numeral0.png": "assets/images/ui/numeral_0.png",
        "Bonus/sfx_lose.ogg": "assets/audio/interface/defeat.ogg",
        "Bonus/sfx_twoTone.ogg": "assets/audio/interface/victory_or_confirm.ogg",
        "Bonus/sfx_shieldUp.ogg": "assets/audio/interface/recovery_shield_up.ogg",
    },
    "kenney_space-shooter-extension.zip": {
        "PNG/Sprites/Ships/spaceShips_007.png": "assets/images/enemies/boss_ship_large.png",
        "PNG/Sprites/Ships/spaceShips_003.png": "assets/images/enemies/enemy_extension_ship_003.png",
        "PNG/Sprites/Missiles/spaceMissiles_001.png": "assets/images/projectiles/missile_001.png",
        "PNG/Sprites/Effects/spaceEffects_001.png": "assets/images/effects/extension_effect_001.png",
    },
    "kenney_sci-fi-sounds.zip": {
        "Audio/laserSmall_000.ogg": "assets/audio/weapons/laser_small.ogg",
        "Audio/laserLarge_000.ogg": "assets/audio/weapons/laser_large.ogg",
        "Audio/explosionCrunch_000.ogg": "assets/audio/explosions/explosion_crunch.ogg",
        "Audio/lowFrequency_explosion_000.ogg": "assets/audio/explosions/explosion_low_frequency.ogg",
        "Audio/impactMetal_000.ogg": "assets/audio/warnings/player_damage_metal_impact.ogg",
        "Audio/computerNoise_000.ogg": "assets/audio/warnings/system_computer_noise.ogg",
        "Audio/forceField_000.ogg": "assets/audio/warnings/system_force_field.ogg",
    },
}

for archive_name, files in selection.items():
    with ZipFile(packs / archive_name) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Damaged archive member: {archive_name}: {bad}")
        for source, destination in files.items():
            target = root / destination
            if target.exists():
                continue
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(archive.read(source))
        for name in archive.namelist():
            if Path(name).name.lower() == "license.txt":
                target = packs / f"{Path(archive_name).stem}_LICENSE.txt"
                if not target.exists():
                    target.write_bytes(archive.read(name))
                break
    print(archive_name, len(files), "selected")
