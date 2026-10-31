# lmlucene

[![Build, test and publish](https://github.com/lmctl-ai/lmlucene/actions/workflows/release.yml/badge.svg)](https://github.com/lmctl-ai/lmlucene/actions/workflows/release.yml)

Apache Lucene indexing and search from typed `_lmcode_` blocks inside LMScript.
Expose Java Lucene objects, customize analysis and scoring with SAM rule entries,
and run as a standalone GraalVM executable on Linux, macOS or Windows.

## Install a native executable

[GitHub Releases](https://github.com/lmctl-ai/lmlucene/releases) contains native
executables for Linux x64/arm64, macOS x64/arm64 and Windows x64, plus archives
with licenses and schemas. No Java installation is required to run them.
Check downloads against the release's `SHA256SUMS`, then place `lmlucene`
(or `lmlucene.exe`) on PATH. Unix binaries need executable permission.

With LMScript installed, its native-tool installer can select the platform asset:

```sh
lmscript install github:lmctl-ai/lmlucene@latest
lmlucene --version
lmlucene --lmcode-schema --json
```

Linux binaries target glibc 2.39+; Windows may need the MSVC x64 redistributable.
macOS binaries are unsigned. Building from source remains available on other
supported environments. `.lms` source execution requires LMScript; the native
host itself reads compiled `.dslb` programs.

## Index and query

Save this as `hello.lms` with `lmlucene` on PATH:

```lmscript
program = _lmcode_ cli="lmlucene";
let directory = memory_directory();
let analyzer = standard_analyzer();
let writer = index_writer(directory, writer_config(analyzer));
writer.add(document().keyword("id", "1", true).text("body", "Hello Lucene", true));
let reader = writer.reader();
index_searcher(reader).search(term_query("body", "lucene"), 10).emit("matches");
end _lmcode_
savedsl(program, "hello.dslb");
r = system lmlucene --lmcode hello.dslb;
assert(r.code == 0);
print(r.stdout);
```

Run `lmscript hello.lms`. The outer language compiles the embedded typed program;
the host checks its schema hash and runs it against real Lucene objects.

The [32-example gallery](lmcode/examples/gallery/README.md) covers file indexing,
query syntax, stemming, term vectors, sorting, pagination, facets, KNN and SAM
customization. Each example has assertions and upstream source links. The
[host guide](lmcode/README.md) describes the full API and persistent index examples.

## Build and test

The repository retains the Apache Lucene 10.5.2 source snapshot and pins the
lmcode-java SDK. Requires JDK 21+, Python 3.12 and LMScript 0.2.444:

```sh
npm install -g @lmctl-ai/lmctl@0.2.444
python3 lmcode/build.py
python3 lmcode/tests/integration.py
python3 lmcode/tests/gallery.py
```

On Windows, use `python` and the native build/test workflow below. With GraalVM
Community 21.0.2, its native compiler prerequisites, and its bin directory on PATH:

```sh
python3 lmcode/build.py
python3 lmcode/build-native.py
```

This traces all examples on the JVM, compiles a real executable under
`lmcode/build/native`, and tests the executable with the complete integration
suite and gallery. Set `LMLUCENE_VERSION=X.Y.Z` to stamp a version; default is 0.1.0.
The JVM launcher remains available as `lmcode/lmlucene` on Unix.

To run repository examples against an installed native binary instead of the
JVM launcher, set `LMLUCENE_ARGV` to a JSON argv array, for example
`["/absolute/path/lmlucene"]` or `["C:/tools/lmlucene.exe"]`. Then run:

```sh
lmscript --no-preflight lmcode/examples/run-gallery.lms
```

## Automatic releases

Every push to `main` automatically builds and tests all five platforms. Only
a successful complete matrix publishes `v0.1.<run number>` with raw executables,
archives, schemas, provenance and checksums. Pull requests build and test without
publishing. Manual workflow dispatch is also supported. See the
[workflow](.github/workflows/release.yml) and [release guide](durable-memory/releases.md).

Like [lmaws](https://github.com/lmctl-ai/lmaws), the tool publishes a CLI schema:
`lmlucene --schema` describes `run --program FILE`, JSON input, dry-run and
read-only policy. [cli.schema.latest.json](cli.schema.latest.json) and
[cli.schema.dev.json](cli.schema.dev.json) expose that contract. Its API contract
version is independent of the executable build number.

## Project references and licenses

Start agent work at [durable-memory/index.md](durable-memory/index.md).
Lucene source: Apache-2.0 ([LICENSE](LICENSE.txt), [NOTICE](NOTICE.txt)); lmcode-java: MIT.
See [third-party notices](THIRD_PARTY_NOTICES.md) and the preserved
[upstream Lucene README](README.lucene.md). The initial source is Lucene commit
`145d89cd30c38d25e39a0a2232cf00eee208b9cf`, with host work from
[lmctl-ai/lucene](https://github.com/lmctl-ai/lucene/tree/lmcode-host).
