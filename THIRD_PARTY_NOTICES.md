# Third-party notices

The application includes Apache Lucene 10.5.2, licensed under Apache License 2.0.
The complete license and upstream attribution are in `LICENSE.txt` and `NOTICE.txt` in source (LICENSE/NOTICE in archives).
The preserved source snapshot is based on Apache Lucene commit
`145d89cd30c38d25e39a0a2232cf00eee208b9cf` (tag `releases/lucene/10.5.2`).

The embedded lmcode Java SDK is MIT licensed. Its exact source pin and hashes
are in `lmcode/sdk.lock`; its license is distributed as `SDK-LICENSE` in each
release archive and in `lmcode/vendor/lmcode-java/LICENSE` in source.

Native executables are produced by GraalVM Community 21.0.2. GraalVM Community
and OpenJDK runtime components are distributed under GPLv2 with the Classpath
Exception and additional third-party licenses. Release packaging collects the
actual build toolchain's `legal/` files as `GRAALVM-NOTICES.txt` in each archive.

Linux executables link the C++ runtime and zlib statically and glibc dynamically.
Windows executables may require Microsoft's redistributable x64 C++ runtime.
macOS executables rely on system libraries and are unsigned.
