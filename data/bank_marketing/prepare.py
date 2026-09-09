"""Convert the official downloaded source.zip into verified comma CSVs."""
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

folder = Path(__file__).resolve().parent
archive = folder / 'source.zip'
manifest = {
    'source': 'https://archive.ics.uci.edu/static/public/222/bank+marketing.zip',
    'license': 'CC BY 4.0',
    'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
    'files': {},
}
with ZipFile(archive) as outer:
    with ZipFile(io.BytesIO(outer.read('bank-additional.zip'))) as inner:
        for filename, expected in [('bank-additional-full.csv', 41188), ('bank-additional.csv', 4119)]:
            raw = inner.read('bank-additional/' + filename)
            reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), delimiter=';')
            rows = list(reader)
            assert len(rows) == expected
            assert len(reader.fieldnames) == 21
            assert all(None not in row and None not in row.values() for row in rows)
            assert set(row['y'] for row in rows) == {'yes', 'no'}
            path = folder / filename
            with path.open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=reader.fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            with path.open(encoding='utf-8', newline='') as stream:
                assert list(csv.DictReader(stream)) == rows
            manifest['files'][filename] = {
                'rows': len(rows), 'columns': reader.fieldnames,
                'target_counts': dict(Counter(row['y'] for row in rows)),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'source_member_sha256': hashlib.sha256(raw).hexdigest(),
                'bytes': path.stat().st_size,
            }
        (folder / 'bank-additional-names.txt').write_bytes(inner.read('bank-additional/bank-additional-names.txt'))
sample = manifest['files']['bank-additional.csv']
assert sample['rows'] <= 10000 and sample['bytes'] <= 5 * 1024 * 1024
(folder / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(json.dumps({name: {k: v for k, v in info.items() if k != 'columns'}
                  for name, info in manifest['files'].items()}, indent=2))
