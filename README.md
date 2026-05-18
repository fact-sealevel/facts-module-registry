# facts-module-registry

`facts-module-registry` holds the module YAML configuration files for every module in the FACTS v2 ecosystem. It acts as the interface between FACTS v2's containerized modules and [facts-experiment-builder](https://github.com/fact-sealevel/facts-experiment-builder) (FEB). For a module to be usable by FEB, it must have a YAML file registered here that accurately describes the module's current container image, arguments, inputs, and outputs.

---

## Contents

Each module has its own subdirectory at the root of this repo:

```
facts-module-registry/
├── fair-temperature/
│   └── fair_temperature_module.yaml
├── bamber19-icesheets/
│   └── bamber19_icesheets_module.yaml
├── facts-total/
│   └── facts_total_module.yaml
└── ...
```

Each `*_module.yaml` defines everything FEB needs to configure and run that module as a Docker Compose service:

| Field | Description |
|-------|-------------|
| `container_image` | The Docker image to run |
| `command` | The entrypoint command |
| `arguments` | Structured args: `top_level`, `options`, `inputs`, `outputs`, `fingerprint_params` |
| `uses_climate_file` | Whether this module consumes temperature projection output from the climate step |
| `volumes` | Additional volume mounts beyond the standard input/output paths |
| `depends_on` | Other services this module must wait for before starting |

The `arguments` section is the most important part for users: it defines every parameter name, input filename, and output filename the module expects. When you run `setup-experiment`, FEB reads this section to populate your `experiment-config.yaml` with the correct fields.

See the [module contributor docs](#) (TODO ADD!) for a full schema reference and guide to writing or updating a module YAML.

---

## How to set up your workspace

`facts-module-registry` is designed to live in your FACTS project workspace alongside your experiments. Clone it into the root of your workspace:

```bash
# From your FACTS project workspace root
git clone https://github.com/fact-sealevel/facts-module-registry.git
```

Your workspace should look like this:

```
my-facts-workspace/
├── experiments/                  # your experiment configs and outputs
│   └── my-experiment/
│       ├── experiment-config.yaml
│       └── experiment-compose.yaml
└── facts-module-registry/        # this repo — module YAML definitions
    ├── fair-temperature/
    ├── bamber19-icesheets/
    └── ...
```

FEB expects to find `facts-module-registry/` in whatever directory you run commands from. Always run `feb` commands from your workspace root.

---

## Browsing and editing module YAMLs

You do not need to modify module YAMLs for standard experiments — FEB reads them automatically when you run `setup-experiment` or `generate-compose`.

However, the YAMLs are designed to be readable. If you want to understand what parameters a module accepts, what input files it expects, or what outputs it produces, browse the relevant YAML directly. For example, `fair-temperature/fair_temperature_module.yaml` shows every argument the FaIR temperature module accepts and the exact parameter names FEB will use in your `experiment-config.yaml`.

If you need to adapt a module for a custom experiment — for example, changing an image tag or adding a non-standard argument — you can edit the YAML directly in your local clone. FEB will pick up the change immediately on the next command, no reinstall needed.

> **Note:** If you have uncommitted changes in your local registry, FEB will warn you when you run any command:
> ```
> UserWarning: facts-module-registry at .../facts-module-registry has uncommitted changes.
> Module definitions may differ from the published registry.
> ```
> This is informational, not an error. It's a reminder that your local definitions may differ from the shared registry.

---

## How FEB uses this registry

FEB looks for `facts-module-registry/` in your current working directory when any command is run. If it's not found, FEB fails with a clear error and the clone command above.

FEB uses the registry in two places:

**1. `setup-experiment`**

Reads each selected module's YAML to build `experiment-config.yaml`. The `arguments` section of the YAML determines which fields appear in your config — parameter names, input/output paths, and which values you need to fill in.

**2. `generate-compose`**

Reads each module's YAML to build the Docker Compose service definition: container image, command with all resolved arguments, volume mounts, and service dependencies.

The git commit hash of your local registry is recorded in `experiment-config.yaml` under `module_registry_version` (e.g. `local@a3f92c1`) each time you run `setup-experiment`. This gives a record of exactly which module definitions were used to create each experiment.

---

## Keeping your registry up to date

To pull the latest module definitions:

```bash
git -C facts-module-registry pull
```

If you have local modifications you want to preserve, commit or stash them first.

---

## Adding or updating a module

To register a new module or update an existing one:

1. Create (or update) a subdirectory at the root of this repo named after the module in kebab-case
2. Add (or update) the `*_module.yaml` inside it
3. Open a pull request against this repo

See the [module contributor docs](#) (TODO ADD!) for the full YAML schema and validation guidance.
