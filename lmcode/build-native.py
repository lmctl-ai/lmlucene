#!/usr/bin/env python3
"""Trace the JVM gallery, compile with GraalVM, then test the actual executable."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from build import ROOT, BUILD, java_argv, execute

def native_build():
    binary = shutil.which('native-image')
    if not binary:
        raise SystemExit('GraalVM 21 native-image is required on PATH')
    native_dir = BUILD / 'native'
    metadata = BUILD / 'native-metadata'
    if metadata.exists():
        shutil.rmtree(metadata)
    metadata.mkdir(parents=True)
    native_dir.mkdir(parents=True, exist_ok=True)
    # Actual API usage captures SPI codecs, analyzers and reflective method handles.
    java = java_argv()
    traced = [java[0], f'-agentlib:native-image-agent=config-merge-dir={metadata}', *java[1:]]
    trace_env = dict(os.environ, LMLUCENE_ARGV=json.dumps(traced))
    execute([sys.executable, 'lmcode/tests/gallery.py'], env=trace_env)
    classpath = os.pathsep.join([str(BUILD / 'lmlucene.jar'), *(str(p) for p in sorted((BUILD / 'lib').glob('*.jar')))])
    flags = ['-H:+UnlockExperimentalVMOptions', '--no-fallback', '-march=compatibility',
             '-J-Xmx' + os.environ.get('NATIVE_IMAGE_HEAP', '4g'), '-H:NumberOfThreads=2',
             '-H:+ReportExceptionStackTraces', '--initialize-at-run-time=org.apache.lucene',
             f'-H:ConfigurationFileDirectories={metadata}']
    if sys.platform.startswith('linux'):
        flags += ['-H:+StaticExecutableWithDynamicLibC', '-H:NativeLinkerOption=-static-libstdc++', '-H:NativeLinkerOption=-static-libgcc']
    output = native_dir / 'lmlucene'
    execute([binary, *flags, '-cp', classpath, 'io.lmctl.lucene.Main', output])
    executable = output.with_suffix('.exe') if os.name == 'nt' else output
    if not executable.is_file():
        raise SystemExit('native-image did not produce the expected executable')
    native_env = dict(os.environ, LMLUCENE_ARGV=json.dumps([str(executable)]),
                      PATH=str(native_dir)+os.pathsep+os.environ['PATH'])
    execute([executable, '--version'])
    execute([sys.executable, 'lmcode/tests/integration.py'], env=native_env)
    execute([sys.executable, 'lmcode/tests/gallery.py'], env=native_env)
    print('PASS native executable, integration suite and all gallery examples', flush=True)

if __name__ == '__main__':
    native_build()
