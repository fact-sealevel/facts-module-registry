# facts-module-registry

`facts-module-registry` holds the module YAML configuration files for every module in the FACTS v2 ecosystem. It acts as the interface between FACTS v2's containerized modules and [facts-experiment-builder](https://github.com/fact-sealevel/facts-experiment-builder) (FEB). For a module to be usable by FEB, it must have a YAML file registered here that accurately describes the module's current container image, arguments, inputs, and outputs.

---

## Contents

Each module has its own subdirectory under `src/facts_module_registry/`:

```
src/facts_module_registry/
├── fair-temperature/
│   └── fair_temperature_module.yaml
├── bamber19-icesheets/
│   └── bamber19_icesheets_module.yaml
├── ipccar5-glaciers/
│   └── ipccar5_glaciers_module.yaml
└── ...
```

Each `*_module.yaml` defines everything FEB needs to build a Docker Compose service for that module:

- **`container_image`** — the Docker image to run
- **`command`** — the entrypoint command
- **`arguments`** — top-level args, options, inputs, outputs, and fingerprint params
- **`uses_climate_file`** — whether the module consumes temperature projection output
- **`volumes`** — additional volume mounts
- **`depends_on`** — other services this module depends on

See the [module contributor docs](#) (TODO ADD!)) for a full schema reference and guide to writing or updating a module YAML.

---

## How users interact with this registry

It is not required to clone or interact with this repo directly for basic use. When you install `facts-experiment-builder`, `facts-module-registry` is bundled as a dependency and available automatically.

However, it may be helpful to **browse or modify module definitions** — for example, to inspect what parameters a module expects, or to adapt a module YAML for a custom experiment. To do this, clone the [facts-module-registry](https://github.com/fact-sealevel/facts-module-registry/tree/main) repo into your project workspace:

```bash
# From your FACTS project workspace root
git clone https://github.com/fact-sealevel/facts-module-registry.git
```

Your workspace should look like this:

```
my-facts-workspace/
├── experiments/           # your experiment configs and outputs
└── facts-module-registry/ # module YAML definitions (this repo)
```

When `facts-module-registry/` is present in your workspace, FEB will automatically use it instead of the bundled copy. This means any local edits to module YAMLs take effect immediately — no reinstall needed.

> **Note:** If you modify module YAMLs locally, FEB will warn you that your registry has uncommitted changes when you run any command. This is a reminder that your local definitions may differ from the published registry, not an error.

---

## How it connects to facts-experiment-builder

FEB declares `facts-module-registry` as a Python package dependency. At runtime, FEB's `ModuleRegistry.default()` function discovers the registry using the following priority order:

| Priority | Source | When it applies |
|----------|--------|-----------------|
| 1 | `FACTS_REGISTRY_PATH` env var | Explicit override — points to any directory |
| 2 | `./facts-module-registry/` in cwd | Workspace clone — takes precedence for visibility and editing |
| 3 | Installed Python package | Bundled fallback — used when no local clone is present |

FEB uses the registry in two places:

1. **`setup-experiment`** — reads each selected module's YAML to populate `experiment-config.yaml` with the correct parameter names, input/output paths, and placeholder values for the user to fill in.

2. **`generate-compose`** — reads each module's YAML to build the Docker Compose service definition: container image, command, volume mounts, and service dependencies.

The registry version used to create an experiment is recorded in `experiment-config.yaml` under `module_registry_version` for traceability.

---

## Adding or updating a module

To register a new module or update an existing one:

1. Create (or update) a subdirectory under `src/facts_module_registry/` named after the module in kebab-case
2. Add (or update) the `*_module.yaml` inside it
3. Open a pull request against this repo

See the [module contributor docs](#) (TODO ADD!)) for the full YAML schema and validation guidance.
