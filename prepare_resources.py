from pathlib import Path
from zipfile import ZipFile

root = Path(r"G:\\My Drive\\Programming\\haven")
packs = root / "original_asset_packs"
selection = {}

for archive_name, files in selection.items():
    with ZipFile(packs / archive_name) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Damaged archive member: {archive_name}: {bad}")
        for source, destination in files.items():
            target = root / destination
            if target.exists():
                continue
            target.write_bytes(archive.read(source))
    print(archive_name, len(files), "selected")
