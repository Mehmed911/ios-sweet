#!/usr/bin/env python3
"""Copy and audit the original Setup fallback fonts from the mounted 20F66 image."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

from fontTools.ttLib import TTCollection, TTFont

source, dest = map(Path, sys.argv[1:])
dest.mkdir()
core = (
    'AppleSDGothicNeo.ttc', 'AppleSymbols.ttf', 'ArialHB.ttc', 'Fallback.ttf',
    'GeezaPro.ttc', 'HiraginoKakuGothic.ttc', 'Kailasa.ttc', 'Kefa.ttf', 'KhmerSangamMN.ttf',
    'Kohinoor.ttc', 'KohinoorBangla.ttc', 'KohinoorGujarati.ttc', 'KohinoorTelugu.ttc',
    'LaoSangamMN.ttf', 'LastResort.otf', 'MalayalamSangamMN.ttc', 'MuktaMahee.ttc',
    'MyanmarSangamMN.ttc', 'NotoNastaliq.ttc', 'NotoSansArmenian.ttc', 'NotoSansKannada.ttc',
    'NotoSansMyanmar.ttc', 'NotoSansOriya.ttc', 'SFArabic.ttf', 'SFArabicRounded.ttf',
    'SinhalaSangamMN.ttc', 'TamilSangamMN.ttc', 'Thonburi.ttc', 'ThonburiUI.ttc',
)
names = [Path('Core') / name for name in core] + [Path('LanguageSupport/PingFang.ttc')]
entries = {}
coverage = set()


def sha(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


for relative in names:
    path, out = source / relative, dest / relative
    out.parent.mkdir(exist_ok=True)
    shutil.copyfile(path, out)
    assert out.stat().st_size == path.stat().st_size and out.stat().st_size > 0
    digest = sha(path)
    assert sha(out) == digest
    entries[str(relative)] = dict(bytes=out.stat().st_size, sha256=digest)
    if out.name in ('Fallback.ttf', 'LastResort.otf'):
        continue
    if out.suffix == '.ttc':
        collection = TTCollection(out, lazy=True)
        fonts = collection.fonts
    else:
        collection = None
        fonts = [TTFont(out, lazy=True)]
    for font in fonts:
        for cmap in font['cmap'].tables:
            if cmap.isUnicode():
                coverage.update(cp for cp, glyph in cmap.cmap.items() if glyph != '.notdef')
    (collection or fonts[0]).close()

autonyms = (
    '简体中文', '繁體中文', '日本語', '한국어', 'العربية', 'ภาษาไทย', 'हिन्दी', 'עברית',
    'বাংলা', 'தமிழ்', 'తెలుగు', 'ਪੰਜਾਬੀ', 'ગુજરાતી', 'മലയാളം', 'ಕನ್ನಡ', 'ଓଡ଼ିଆ',
    'မြန်မာ', 'ខ្មែរ', 'ລາວ', 'සිංහල', 'اردو', 'Հայերեն', 'አማርኛ', 'བོད་ཡིག',
)
for name in autonyms:
    missing = ''.join(sorted(set(c for c in name if ord(c) not in coverage)))
    print(name, 'missing ' + missing if missing else 'covered')
manifest = dest / 'manifest.json'
manifest.write_text(json.dumps(entries, sort_keys=True, indent=2) + '\n')
print('manifest sha256', sha(manifest), 'bytes', sum(e['bytes'] for e in entries.values()))
