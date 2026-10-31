#!/usr/bin/env python3
"""Build the pinned Lucene sources and host using native paths on every OS."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / 'lmcode/build'

def execute(argv, **kwargs):
    return subprocess.run([str(a) for a in argv], cwd=ROOT, check=True, **kwargs)

def java_argv():
    java = shutil.which('java')
    if not java:
        raise SystemExit('JDK 21+ is required')
    classpath = os.pathsep.join([str(BUILD / 'lmlucene.jar'), str(BUILD / 'lib/*')])
    return [java, '--enable-native-access=ALL-UNNAMED', '-cp', classpath, 'io.lmctl.lucene.Main']

def build():
    execute([sys.executable, 'lmcode/check-pins.py'])
    wrapper = ROOT / ('gradlew.bat' if os.name == 'nt' else 'gradlew')
    execute([wrapper, ':lucene:core:jar', ':lucene:analysis:common:jar', ':lucene:queryparser:jar',
             '-Pgradle.ge=false', '-Pvalidation.errorprone=false', '--console=plain', '--no-daemon'])
    for directory in ['classes', 'lib', 'generated']:
        path = BUILD / directory
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)
    for module in ['core', 'analysis/common', 'queries', 'sandbox', 'queryparser', 'facet']:
        jars = [p for p in (ROOT / 'lucene' / module / 'build/libs').glob('lucene-*.jar')
                if not p.name.endswith(('-sources.jar', '-javadoc.jar'))]
        if len(jars) != 1:
            raise SystemExit(f'Expected one compiled Lucene JAR for {module}: {jars}')
        shutil.copy2(jars[0], BUILD / 'lib' / jars[0].name)
    version = os.environ.get('LMLUCENE_VERSION', '0.1.0')
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise SystemExit('LMLUCENE_VERSION must be X.Y.Z')
    generated = BUILD / 'generated/BuildInfo.java'
    generated.write_text('package io.lmctl.lucene;\npublic final class BuildInfo { public static final String VERSION = "' + version + '"; }\n', encoding='utf-8', newline='\n')
    sources = sorted((ROOT / 'lmcode/src').rglob('*.java')) + sorted((ROOT / 'lmcode/vendor/lmcode-java/src/main/java').rglob('*.java')) + [generated]
    (BUILD / 'sources.txt').write_text('\n'.join(p.relative_to(ROOT).as_posix() for p in sources)+'\n', encoding='utf-8', newline='\n')
    classpath = os.pathsep.join(str(p) for p in sorted((BUILD / 'lib').glob('*.jar')))
    execute(['javac', '--release', '21', '-encoding', 'UTF-8', '-cp', classpath,
             '-d', BUILD / 'classes', '@lmcode/build/sources.txt'])
    execute(['jar', '--create', '--file', BUILD / 'lmlucene.jar', '--main-class', 'io.lmctl.lucene.Main', '-C', BUILD / 'classes', '.'])
    schema = execute([*java_argv(), '--lmcode-schema', '--json'], stdout=subprocess.PIPE).stdout
    (BUILD / 'lucene.dsl.json').write_bytes(schema)
    print(f'Built lmlucene {version} with Lucene from this checkout', flush=True)

if __name__ == '__main__':
    build()
