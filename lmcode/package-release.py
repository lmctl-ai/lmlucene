#!/usr/bin/env python3
"""Package only a native binary that passed the platform's full test suite."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
PLATFORMS = ['linux-x64', 'linux-arm64', 'macos-x64', 'macos-arm64', 'windows-x64']
platform = sys.argv[1]
if platform not in PLATFORMS:
    raise SystemExit('Unsupported release platform')
version = os.environ['LMLUCENE_VERSION']
extension = '.exe' if platform.startswith('windows') else ''
binary = ROOT / ('lmcode/build/native/lmlucene' + extension)
magic = binary.read_bytes()[:4]
expected = [b'\x7fELF'] if platform.startswith('linux') else ([b'MZ'] if platform.startswith('windows') else [b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xcf'])
if not any(magic.startswith(prefix) for prefix in expected):
    raise SystemExit('Release asset is not a native executable for this OS')
identity = subprocess.check_output([str(binary), '--version'], text=True).strip()
if not identity.startswith(f'lmlucene {version} '):
    raise SystemExit(f'Wrong executable version: {identity}')
dist = ROOT / 'dist'
dist.mkdir(exist_ok=True)
name = 'lmlucene-' + platform
shutil.copy2(binary, dist / (name + extension))
legal = Path(os.environ['JAVA_HOME'])/'legal'
notices = ROOT/'lmcode/build/GRAALVM-NOTICES.txt'
if not legal.is_dir():
    raise SystemExit('GraalVM legal directory is required for distribution')
with notices.open('w',encoding='utf-8',newline='\n') as output:
    for path in sorted(legal.rglob('*')):
        if path.is_file():
            output.write('\n===== '+path.relative_to(legal).as_posix()+' =====\n')
            output.write(path.read_text(encoding='utf-8',errors='replace')+'\n')
files = [(binary, 'lmlucene' + extension), (ROOT/'LICENSE.txt','LICENSE'), (ROOT/'NOTICE.txt','NOTICE'),
         (ROOT/'THIRD_PARTY_NOTICES.md','THIRD_PARTY_NOTICES.md'),
         (notices,'GRAALVM-NOTICES.txt'),
         (ROOT/'lmcode/vendor/lmcode-java/LICENSE','SDK-LICENSE'),
         (ROOT/'lmcode/lucene.dsl.json','lucene.dsl.json'),
         (ROOT/'lmcode/cli.schema.dev.json','cli.schema.json')]
if platform.startswith('windows'):
    with zipfile.ZipFile(dist/(name+'.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
        for source, target in files:
            archive.write(source, target)
else:
    with tarfile.open(dist/(name+'.tar.gz'),'w:gz') as archive:
        for source, target in files:
            archive.add(source, arcname=target)
print('Packaged ' + name)
