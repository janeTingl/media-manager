# Translation workflow

This project stores Qt translation sources in `translations/i18n`. The Simplified Chinese catalog is generated from the Python sources with the standard Qt tooling that ships with PySide6.

## Update the `.ts` catalog

From the repository root run:

```bash
pyside6-lupdate $(find src/media_manager -name '*.py' -print) -ts translations/i18n/media_manager_zh_CN.ts
```

Alternatively you can use the helper command below, which mirrors what we run locally:

```bash
python - <<'PY'
import subprocess
from pathlib import Path
files = sorted(Path('src/media_manager').rglob('*.py'))
cmd = ['pyside6-lupdate', *[str(f) for f in files], '-ts', 'translations/i18n/media_manager_zh_CN.ts']
subprocess.run(cmd, check=True)
PY
```

The `.ts` file intentionally keeps untranslated entries (marked as TODO) so that native speakers can provide the final wording via Qt Linguist.

## Compile the runtime `.qm`

After updating the source catalog, rebuild the binary QM file that the application loads at runtime:

```bash
pyside6-lrelease translations/i18n/media_manager_zh_CN.ts -qm src/media_manager/resources/i18n/media_manager_zh_CN.qm
```

The compiled QM files are copied into the application bundle (and PyInstaller packages) via `src/media_manager/i18n.py` and the updated `media_manager.spec` configuration.
