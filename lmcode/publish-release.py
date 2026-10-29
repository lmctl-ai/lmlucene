#!/usr/bin/env python3
"""Publish atomically after every native matrix job succeeds; never mutate a published release."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT/'dist'
version = os.environ['LMLUCENE_VERSION']
commit = os.environ['GITHUB_SHA']
tag = 'v' + version
platforms = ['linux-x64','linux-arm64','macos-x64','macos-arm64','windows-x64']
expected = set()
for platform in platforms:
    windows = platform.startswith('windows')
    expected.add('lmlucene-'+platform+('.exe' if windows else ''))
    expected.add('lmlucene-'+platform+('.zip' if windows else '.tar.gz'))
if {p.name for p in DIST.iterdir()} != expected:
    raise SystemExit('Release requires exactly five raw executables and five archives')
for source, target in [('LICENSE.txt','LICENSE'),('NOTICE.txt','NOTICE'),('THIRD_PARTY_NOTICES.md','THIRD_PARTY_NOTICES.md'),
                       ('lmcode/vendor/lmcode-java/LICENSE','SDK-LICENSE'),('lmcode/lucene.dsl.json','lucene.dsl.json'),
                       ('lmcode/cli.schema.dev.json','cli.schema.latest.json')]:
    shutil.copy2(ROOT/source,DIST/target)
(DIST/'build-info.json').write_text(json.dumps({'version':version,'commit':commit,'platforms':platforms,
    'lucene':'10.5.2','lucene_source_commit':'145d89cd30c38d25e39a0a2232cf00eee208b9cf',
    'graalvm':'community 21.0.2','lmscript':'0.2.444'},indent=2)+'\n')
checksums = ''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(DIST.iterdir()))
(DIST/'SHA256SUMS').write_text(checksums)
def gh(*args, check=True, **kwargs):
    return subprocess.run(['gh',*map(str,args),'--repo',os.environ['GITHUB_REPOSITORY']],check=check,**kwargs)
existing = gh('release','view',tag,'--json','isDraft,targetCommitish',check=False,capture_output=True,text=True)
if existing.returncode == 0:
    state = json.loads(existing.stdout)
    if state['targetCommitish'] != commit:
        raise SystemExit('Existing release belongs to another commit')
    if not state['isDraft']:
        with tempfile.TemporaryDirectory() as path:
            gh('release','download',tag,'--pattern','SHA256SUMS','--dir',path)
            if (Path(path)/'SHA256SUMS').read_text() != checksums:
                raise SystemExit('Published release is immutable; use a new workflow run for new bytes')
        print('Release already published with these exact assets')
        raise SystemExit(0)
else:
    notes = ROOT/'release-notes.txt'
    notes.write_text('Automatically built from '+commit+'.\n\n'
        'All five platforms passed the JVM example gallery, native integration suite and all 32 native gallery examples. '
        'Executables require no Java installation. Linux builds target glibc 2.39+; Windows requires the MSVC x64 runtime. '
        'macOS artifacts are unsigned. Archives include licenses and schemas; SHA256SUMS covers all assets.\n')
    gh('release','create',tag,'--draft','--target',commit,'--title','lmlucene '+tag,'--notes-file',notes)
gh('release','upload',tag,*sorted(DIST.iterdir()),'--clobber')
gh('release','edit',tag,'--draft=false','--latest')
print('Published '+tag)
