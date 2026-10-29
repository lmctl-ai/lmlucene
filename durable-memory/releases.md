# lmlucene native release pipeline

Public repository: https://github.com/lmctl-ai/lmlucene, default branch `main`.
The standalone source snapshot retains Apache Lucene 10.5.2 and the tested host
from https://github.com/lmctl-ai/lucene/tree/lmcode-host. The prior fork remains
available; this repository owns the distributable CLI and release automation.

## Trigger and gate

`.github/workflows/release.yml` runs on pushes to main, pull requests, and manual
dispatch. Each matrix job builds the checked-in Lucene source and Java host,
executes all 32 examples on the JVM under the GraalVM tracing agent, compiles a
real native executable with `--no-fallback`, then runs all integration groups
and all 32 examples against that executable. A failed platform blocks publishing.

Platforms: Linux x64/arm64 (Ubuntu 24.04), macOS x64/arm64 (macOS 15), Windows x64
(Windows Server 2022 with MSVC). GraalVM Community 21.0.2, Python 3.12 and LMScript
0.2.444 are pinned. `-march=compatibility` avoids build-machine CPU assumptions.
Native compilation uses a 4 GiB Java heap and two compilation threads by default.

The publish job has contents:write; build jobs have read-only repository access.
Actions are SHA-pinned. PRs and non-main manual runs cannot publish. Successful
main runs publish `v0.1.<workflow run number>`, targeting the exact tested commit.
The publisher checks the complete five-platform asset set, creates a draft,
uploads all files and SHA256SUMS, then makes the release public and latest.
Published releases are immutable; a rerun refuses different bytes for the same
version. Fixes go through a new main push and a new version.

## Build and artifacts

- `python lmcode/build.py`: cross-platform source/JAR build. Generates BuildInfo
  from `LMLUCENE_VERSION` (default 0.1.0). The CLI schema version is the API contract
  version; executable release versions are independent, exposed by `--version`.
- `python lmcode/build-native.py`: JVM tracing, native build, native integration
  and gallery tests. Requires GraalVM's java/native-image on PATH.
- `python lmcode/package-release.py PLATFORM`: verifies native file magic and
  executable version, then packages the tested binary with licenses and schemas.
- `python lmcode/publish-release.py`: CI-only atomic release publication.

Assets: `lmlucene-linux-{x64,arm64}`, `lmlucene-macos-{x64,arm64}`,
`lmlucene-windows-x64.exe`, matching tar.gz/zip archives, schemas, provenance,
licenses, and SHA256SUMS. Archives include the actual GraalVM build toolchain's
legal notices. Executables require no JVM; running `.lms` still requires LMScript.
Linux uses dynamic glibc 2.39+ and statically linked C++/zlib components. Windows
may need the MSVC x64 runtime. macOS executables are unsigned/not notarized.

## Native compatibility

Filesystem indexing uses NIOFSDirectory consistently on JVM and native builds,
avoiding JVM foreign-memory/MMapDirectory loading. Index formats remain standard
Lucene. Scalar vector implementations are used; no incubator vector module is
required. Lucene classes initialize at runtime. The tracing agent records the
actual SPI codecs, analysis classes, resources and reflective handles exercised
by the whole gallery on each build OS. New bindings must be represented in the
gallery or tracing fixtures so their metadata is discovered before release.

Test harnesses and `.lms` wrappers accept `LMLUCENE_ARGV` (JSON argv array). The
native build sets it to the executable path; the tracing pass sets it to java
plus the agent and classpath. The native executable's directory is first on PATH
for schema-import tests. Python resolves the LMScript launcher on Windows.
All pinned sources and schema bytes use stable line endings across operating systems.

The complete upstream source is retained. Apache's unrelated scheduled workflows
were removed from this repository; only the lmlucene release workflow is enabled.
