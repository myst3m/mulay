# mulay

A lightweight runtime for MuleSoft Mule 4 applications, written in [Clay](https://gitlab.com/myst3m/clay).
It runs a Mule project directory, a deployable application JAR, or a single Mule XML file as a single
native binary — no JVM.

```
Mule XML ─► loader (properties, DataWeave compiled at load) ─► flow engine ─► HTTP listener / scheduler
```

## Build

Needs Clay (`clay --version`; tested with 0.86.5) and clang.

```bash
clay build src/mulay/cli/main.clay -o mulay
```

## Usage

```bash
mulay help                               # list of commands; mulay help run (or mulay run --help) for one command
mulay run ./my-mule-project              # src/main/mule/*.xml + src/main/resources
mulay run                                # no <app>: the current directory (also validate, inspect, build)
mulay run app-1.0.0-mule-application.jar
mulay run flows.xml http.port=8081       # key=value overrides properties
mulay run app.jar -P /run/app.props      # key=value entries separated by NUL bytes (secrets stay out of ps)
mulay run ./project -l DEBUG             # log level
mulay validate ./project                 # load and compile only; exit code 1 on problems
mulay inspect ./project                  # dump flows, processors, configs and properties (value + origin)
mulay inspect app.jar env=prod --props   # only the properties, with overrides applied
mulay dw script.dwl payload=application/json:in.json   # evaluate DataWeave once
mulay dw --path src/main/resources test/t.dwl        # with your modules (import * from a::b::C)
mulay dw test src/test/dw                           # run dw::test suites (exit 1 on FAIL/ERROR)
mulay build ./my-mule-project -o my-app                 # one executable for this app (needs clay + clang)
./my-app                                                # runs the embedded app; key=value and -l LEVEL allowed
```

`mulay build` embeds the application (configuration files and resources) and compiles every DataWeave script
to native code ([docs/aot.md](docs/aot.md)). The result runs without the project, the JAR or a JVM.

Templates: [templates/agent-harness](templates/agent-harness) is an agent (LLM + tool loop + MCP tools + A2A + history
+ document search + a SOAP backend) built as a plain Mule app with the Inference, MCP, A2A, Vectors, Validation, Web Service Consumer
and Object Store connectors.
[templates/org-sync](templates/org-sync) is two-way record sync between two Salesforce orgs (Platform Events over the
Pub/Sub API, versioned upserts, initial copy with Bulk API 2.0, periodic reconcile).

## What is supported (v1)

| Area | Status |
|---|---|
| DataWeave 2.x | Full language (selectors, pattern matching, `update`, `do`, types, generics), all standard modules (`dw::Core`, `dw::core::*`, `dw::util::*`, `dw::Runtime`, `dw::Crypto`, `dw::System`, `dw::module::*`, `dw::Mule::p`), formats JSON / XML / CSV / YAML / dw / text / urlencoded / multipart / ndjson / properties / binary |
| Core processors | set-payload, set-variable, remove-variable, logger, ee:transform, flow-ref, raise-error, parse-template, choice, foreach, parallel-foreach, scatter-gather, try, until-successful, async, first-successful, round-robin, idempotent-message-validator, ee:cache (invalidate-key, invalidate-cache), batch:job (steps, aggregator, on-complete) |
| Errors | Mule error types with the real hierarchy, on-error-continue / on-error-propagate (type lists, `when`), global and default error handlers, error-mapping |
| Sources | http:listener (multiple ports, path/uri params, http:response / error-response), scheduler (fixed-frequency, cron with time zone), file:listener, vm:listener, Salesforce object listeners (new / modified / deleted) and replay topic / channel listeners, Anypoint MQ subscriber, A2A task-listener, MCP tool / resource / prompt listeners |
| Connectors | http:request, ObjectStore, File, SFTP, VM, APIkit router (OpenAPI 3, RAML 1.0 / 0.8), Salesforce (SOAP partner API, Bulk API v1 / v2, metadata, Apex, streaming), Salesforce Composite, Anypoint MQ (publish / consume / ack / nack, subscriber), Database (SQLite, PostgreSQL, Oracle 23ai+, MySQL), Web Service Consumer (SOAP), A2A, MCP, Inference, Vectors, Validation, jmx (a custom log/metrics module), secure properties — see [docs/connectors.md](docs/connectors.md) |
| Configuration | configuration-properties (YAML / .properties), global-property, `${}` nesting, `${file::..}` |

Not yet: FTP, JMS, Kafka, Email, SQL Server, Java interop (`java!`).
See [docs/compat/deviations.md](docs/compat/deviations.md) for known differences from Mule.

## How correctness is measured

Real Mule (4.11.3 and 4.12.0) is the reference. Nothing is hand-asserted:

- **DataWeave**: 3,300+ golden fixtures (`test/fixtures/dw/**/*.dwt`) whose expected output was produced by the
  DataWeave engine shipped with Mule (`tools/dw-oracle`). Run: `tools/dwt-all.sh` (add `-e` to also compare
  error messages).
- **Applications**: 92 app scenarios / 2,692 HTTP requests (`test/fixtures/apps/*/scenario.scn`) recorded against a real
  Mule. Run: `tools/mule-oracle/mule-oracle mulay`. The Salesforce apps run against a real org and need
  credentials that are not in the repository (`src/main/resources/sf-secret.yaml`); without them they are skipped.
- **Libraries**: unit tests under ASan/LSan (`tools/test.sh`); decimal, regex, time, Unicode and number
  formatting are checked against values generated by Java 17.

## Layout

```
src/mulay/lib    generic libraries (BigDecimal, regex, java.time, XML, YAML, CSV, ZIP, Unicode, file system, glob,
                 JSON Schema, java.util.HashMap order, crypto, X.509 / keystores, SSH / SFTP, SQLite engine, OTLP)
src/mulay/dw     DataWeave: parser, resolver, evaluator, standard library, data formats, native code generator (AOT)
src/mulay/mule   Mule XML loader, properties, model, lint
src/mulay/rt     flow engine, events, errors, logging, cron, connector interface, streams, persistence, metrics
src/mulay/conn   connectors (http, os, file, sftp, vm, apikit, salesforce, salesforce-composite, db, anypoint-mq,
                 a2a, mcp, inference, vectors, validation, wsc, jmx) and their registry
src/mulay/db     database drivers (SQLite, PostgreSQL, MySQL, Oracle)
src/mulay/app    application startup and sources (HTTP / A2A / MCP listeners, scheduler, polled sources),
                 OpenTelemetry metrics, Anypoint Monitoring metrics
src/mulay/cli    the mulay command, the dwt golden runner
docs/            design and reference documents
tools/           oracles, fixture generators, test runners
```

Design documents: [design](docs/design.md), [DataWeave evaluator](docs/dw-eval.md),
[Mule runtime](docs/mule-runtime.md), [test fixtures](docs/fixtures.md), [connectors](docs/connectors.md),
[differences from Mule](docs/compat/deviations.md), [ahead-of-time compilation](docs/aot.md), [SQLite](docs/sqlite.md),
[DataWeave formats](docs/dw-formats.md).

## License

mulay is licensed under the [Apache License, Version 2.0](LICENSE). Some generated data tables and test
fixtures come from third-party works under their own licenses (Unicode, CLDR/OpenJDK, Apache Tika,
Apache Commons Validator, and others); see [NOTICE](NOTICE).
