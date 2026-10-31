#!/usr/bin/env python3
"""Refresh the owned SDK snapshot from an explicit local upstream checkout/ref."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

root = Path(__file__).resolve().parent
upstream = Path(sys.argv[1]).resolve()
ref = sys.argv[2] if len(sys.argv) > 2 else 'origin/main'
commit = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', ref], text=True).strip()
archive = subprocess.check_output(['git', '-C', str(upstream), 'archive', commit,
                                   'LICENSE', 'src/main/java', 'src/main/resources'])
vendor = root / 'vendor/lmcode-java'
with tempfile.TemporaryDirectory(prefix='lucene-sdk-') as tmp:
    staged = Path(tmp)
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for member in source:
            target = staged / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.extractfile(member).read())
            else:
                raise SystemExit('Unsupported SDK archive member: ' + member.name)
    if vendor.exists():
        shutil.rmtree(vendor)
    shutil.copytree(staged, vendor)
files = {p.relative_to(vendor).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(vendor.rglob('*')) if p.is_file()}
(root / 'sdk.lock').write_text(json.dumps({'repository': 'https://github.com/lmctl-ai/lmcode-java',
                                         'commit': commit, 'files': files}, indent=2) + '\n')
print('Synced SDK ' + commit)
