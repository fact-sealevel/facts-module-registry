# Module Contributor Documentation

This guide explains how to write a module YAML file and submit it to the `facts-module-registry`. A registry entry is what makes a containerized CLI application usable within the FACTS v2 framework via [facts-experiment-builder](https://github.com/fact-sealevel/facts-experiment-builder) (FEB).

Please feel free to reach out to the FACTS2 maintainers if you have any questions or would like to chat about this process. We are happy to work with you to bring your module into the FACTS2 ecosystem.

---

## Overview

Each entry in the registry is a `*_module.yaml` file that describes everything FEB needs to configure and run your module as a Docker Compose service: the container image, the CLI arguments it accepts, the input and output files it expects, and the volume mounts that make those files accessible inside the container.

When a user runs `setup-experiment`, FEB reads your YAML to populate their `experiment-config.yaml` with the correct parameter names and input/output paths. When they run `generate-compose`, FEB reads your YAML again to build the Docker Compose service definition.

---

## File naming and directory layout

Create a subdirectory at the root of the registry named after your module in **kebab-case** (words separated by dashes, -). Inside it, place a single YAML file named with **snake_case** (words separated by underscores, _) and a `_module` suffix:

```
facts-module-registry/
└── my-module/
    └── my_module_module.yaml
```

If your module uses a custom scenario name mapping, place the mapping file alongside the YAML. For an example of this, see [ssp-landwaterstorage](ssp-landwaterstorage/scenario_name_mapping_ssp_landwaterstorage.yaml).

```
└── my-module/
    ├── my_module_module.yaml
    └── scenario_name_mapping_my_module.yaml
```

---

## Top-level fields

```yaml
module_name: "my-module"
container_image: "ghcr.io/fact-sealevel/my-module:1.0.0"
command: "main"
uses_climate_file: false
climate_file_required: false
```

| Field | Type | Required | Description |
|---|---|---|---|
| `module_name` | string | yes | Kebab-case name matching the directory name |
| `container_image` | string | yes | Full Docker image URI including tag or digest |
| `command` | string | yes | Entrypoint command passed to the container (typically `"main"`) |
| `uses_climate_file` | bool | yes | Whether this module consumes climate output from the climate step |
| `climate_file_required` | bool | yes | Whether the climate file is mandatory (only relevant if `uses_climate_file: true`) |
| `depends_on` | list | no | Other services this module must wait for before starting |
| `input_dir_name` | string | no | Override for the input directory name within the shared input tree |
| `skip_fingerprint_params` | bool | no | If `true`, FEB skips fingerprint parameter handling for this module |
| `per_workflow` | bool | no | If `true`, FEB instantiates one service per workflow rather than per module |
| `output_types` | list | no | Explicitly declare which output types (`global`, `local`, `total`) this module produces |

**Container image pinning:** You may use a semantic version tag (e.g. `my-module:1.0.0`) or a SHA256 digest (e.g. `my-module@sha256:abc123...`). Digest pinning guarantees exact reproducibility.

---

## The `arguments` section

The `arguments` section is the core of the YAML. It is divided into four subsections, each corresponding to a different category of CLI argument your module accepts.

```yaml
arguments:
  top_level: [...]
  options: [...]
  fingerprint_params: [...]
  inputs: [...]
  outputs:
    files: [...]
```

### Common argument fields

Every argument entry, regardless of subsection, can use the following fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | The CLI flag name in kebab-case (e.g. `"pipeline-id"` maps to `--pipeline-id`) |
| `type` | string | yes | Data type: `str`, `int`, `float`, `bool`, or `file` |
| `source` | string | yes | Dot-path to the value in the FEB config object (see subsection docs below) |
| `optional` | bool | no | If `true`, FEB will not error when this argument is absent. Defaults to `false` |
| `help` | string | no | Human-readable description of the argument |
| `default_value` | any | no | Value to use when the argument is not provided |
| `transform` | string | no | Named transform function to apply to the value before passing it (see [Transforms](#transforms)) |
| `filename` | string or list | no | Expected filename(s) for file-type arguments |
| `multiple` | bool | no | If `true`, the flag may be specified more than once (for list inputs) |
| `envvar` | string | no | Environment variable name to use as an alternative source for this argument |
| `external_volume` | bool | no | Marks that this input file comes from another module's output volume |
| `filename_map` | object | no | Dynamically resolve the expected filename from config values (see [Dynamic filename mapping](#dynamic-filename-mapping)) |
| `mount` | object | no | Volume mount configuration for this argument (see [Mount](#mount)) |

#### Mount

The `mount` field tells FEB how to make a file accessible inside the container:

```yaml
mount:
  volume: "volume_name"          # key in the top-level `volumes` section
  container_path: "/mnt/path"    # path inside the container where the volume is mounted
  transform: "filename"          # optional: extract just the filename from a full path
```

---

### `top_level`

Arguments sourced directly from experiment-level metadata (the `metadata.*` namespace in the FEB config). These are values that apply across all modules in the experiment — things like the pipeline identifier, the emissions scenario, and the projection time window.

```yaml
top_level:
  - name: "pipeline-id"
    type: "str"
    source: "metadata.pipeline-id"
    help: "Unique identifier for this module run in the experiment."

  - name: "scenario"
    type: "str"
    source: "metadata.scenario"
    transform: "scenario_name"
    help: "Emissions scenario name."

  - name: "nsamps"
    type: "int"
    source: "metadata.nsamps"
    help: "Number of samples."
```

Common `top_level` arguments seen across modules:

| Name | Source | Description |
|---|---|---|
| `pipeline-id` | `metadata.pipeline-id` | Unique run identifier |
| `scenario` | `metadata.scenario` | Emissions scenario |
| `nsamps` | `metadata.nsamps` | Sample count |
| `baseyear` | `metadata.baseyear` | Reference base year |
| `pyear-start` | `metadata.pyear_start` | Projection start year |
| `pyear-end` | `metadata.pyear_end` | Projection end year |
| `pyear-step` | `metadata.pyear_step` | Projection year step |
| `location-file` | `metadata.location-file` | Location file for localization |

---

### `options`

Module-specific configuration parameters. Sourced from `module_inputs.options.*`. These are the knobs and settings that control your module's behavior and that users may want to tune in their `experiment-config.yaml`.

```yaml
options:
  - name: "seed"
    type: "int"
    source: "module_inputs.options.seed"
    default_value: 1234
    help: "Random seed for reproducibility."

  - name: "chunksize"
    type: "int"
    source: "module_inputs.options.chunksize"
    optional: true
    help: "Number of samples to process per chunk."
```

---

### `fingerprint_params`

Parameters related to sea-level fingerprinting — files and directories that define how global sea level is translated to local sea level at specific locations. Sourced from `module_inputs.fingerprint_params.*`.

```yaml
fingerprint_params:
  - name: "fingerprint-dir"
    type: "str"
    source: "module_inputs.fingerprint_params.fingerprint_dir"
    help: "Directory containing fingerprint files."
    mount:
      volume: "shared_input"
      container_path: "/mnt/shared_in"
```

If your module does not require fingerprint parameters, set `skip_fingerprint_params: true` at the top level.

---

### `inputs`

Input files the module reads at runtime. Sourced from `module_inputs.inputs.*`. Each input should specify the `filename` it expects to find at its mount path, so FEB can validate that the required data is present.

```yaml
inputs:
  - name: "param-file"
    type: "file"
    source: "module_inputs.inputs.param_fname"
    filename: "parameters/my_params.nc"
    help: "Parameter file for the model."
    mount:
      volume: "module_specific_in"
      container_path: "/mnt/module_specific_in"
```

**Cross-module inputs:** If your module reads output produced by another module, set `external_volume: true`. This tells FEB the file lives in the output volume of another service rather than in a dedicated input directory.

```yaml
  - name: "climate-data-file"
    type: "file"
    source: "module_inputs.inputs.climate_data_file"
    filename: "fair-temperature/climate.nc"
    external_volume: true
    help: "Climate output from the temperature module."
    mount:
      volume: "output"
      container_path: "/mnt/out"
```

**Multiple files:** If a flag can be passed more than once (e.g. a list of input files), set `multiple: true`:

```yaml
  - name: "gwd-file"
    type: "file"
    source: "module_inputs.inputs.gwd_file"
    filename: [FileA.csv, FileB.csv]
    multiple: true
    mount:
      volume: "module_specific_in"
      container_path: "/mnt/module_specific_in"
```

---

### `outputs`

Output files the module writes. Typically placed under `outputs.files`; aggregation modules may use `outputs.other`. Sourced from `module_inputs.outputs.*`.

```yaml
outputs:
  files:
    - name: "output-gslr-file"
      type: "file"
      source: "module_inputs.outputs.output_gslr_file"
      filename: "gslr.nc"
      output_type: "global"
      help: "Global mean sea level rise output."
      mount:
        volume: "output"
        container_path: "/mnt/out"
        transform: "filename"

    - name: "output-lslr-file"
      type: "file"
      source: "module_inputs.outputs.output_lslr_file"
      filename: "lslr.nc"
      output_type: "local"
      help: "Local sea level rise output."
      mount:
        volume: "output"
        container_path: "/mnt/out"
        transform: "filename"
```

The `output_type` field classifies the output. Valid values:

| Value | Description |
|---|---|
| `global` | Global mean sea level contribution |
| `local` | Localized sea level at specific points |
| `total` | Aggregated total across components |

Output mounts typically use `transform: "filename"` so that FEB passes only the filename (not the full path) to the CLI flag.

---

## The `volumes` section

The `volumes` section declares the named volumes that your argument mounts reference. Every volume key used in an argument `mount.volume` must appear here.

```yaml
volumes:
  module_specific_in:
    host_path: "module_inputs.input_paths.module_specific_input_dir"
    container_path: "/mnt/module_specific_in"
    help: "Module-specific input data directory."

  shared_in:
    host_path: "module_inputs.input_paths.shared_input_dir"
    container_path: "/mnt/shared_in"
    help: "Shared input directory (fingerprints, location file)."

  output:
    host_path: "module_inputs.output_paths.output_dir"
    container_path: "/mnt/out"
    help: "Output directory for sea level rise files."
```

| Field | Description |
|---|---|
| `host_path` | Dot-path to the directory path in the FEB config object |
| `container_path` | Absolute path where the volume is mounted inside the container |
| `help` | Human-readable description |

Most modules use the three standard volumes above (`module_specific_in`, `shared_in`, `output`). Add additional volumes only if your module requires extra mount points.

---

## Advanced features

### Transforms

The `transform` field applies a named function to a value before it is passed to the CLI. Two transforms are used across the registry:

| Transform | What it does |
|---|---|
| `scenario_name` | Extracts the scenario name string from the FEB scenario config object |
| `filename` | Extracts just the filename component from a full path |
| `scenario_name_<module>` | Module-specific scenario name mapping (see below) |

### Scenario name mapping

If your module uses different scenario name conventions than the FACTS standard (e.g. `"SSP5-8.5"` instead of `"ssp585"`), you can supply a mapping file alongside your module YAML:

```
my-module/
├── my_module_module.yaml
└── scenario_name_mapping_my_module.yaml
```

The mapping file is a simple key-value YAML:

```yaml
ssp585: "SSP5-8.5"
ssp370: "SSP3-7.0"
ssp245: "SSP2-4.5"
ssp126: "SSP1-2.6"
```

Reference the mapping in your YAML with a custom transform name:

```yaml
- name: "scenario"
  type: "str"
  source: "metadata.scenario"
  transform: "scenario_name_my_module"
  help: "Emissions scenario (mapped to module-specific name)."
```

### Dynamic filename mapping

If the expected input filename depends on configuration values (e.g. the projection end year or a region selection), use `filename_map` instead of a static `filename`:

```yaml
- name: "emu-file"
  type: "str"
  source: "module_inputs.inputs.emu_file"
  multiple: true
  filename_map:
    keys: [pyear_end, region]
    map:
      2100:
        ALL: "emu_file/model_ALL_2100.RData"
        EAIS: "emu_file/model_EAIS_2100.RData"
      2300:
        ALL: "emu_file/model_ALL_2300.RData"
        EAIS: "emu_file/model_EAIS_2300.RData"
```

`keys` lists the config parameters used to navigate the `map`. FEB resolves the actual filename at experiment setup time by looking up the values of those parameters.

---

## Minimal example

A module that does not use climate output, takes one module-specific input file, and produces one global output:

```yaml
module_name: "my-module"
container_image: "ghcr.io/fact-sealevel/my-module:1.0.0"
command: "main"
uses_climate_file: false
climate_file_required: false

arguments:
  top_level:
    - name: "pipeline-id"
      type: "str"
      source: "metadata.pipeline-id"
      help: "Unique identifier for this module run."
    - name: "scenario"
      type: "str"
      source: "metadata.scenario"
      transform: "scenario_name"
      help: "Emissions scenario."
    - name: "nsamps"
      type: "int"
      source: "metadata.nsamps"
      help: "Number of samples."
    - name: "baseyear"
      type: "int"
      source: "metadata.baseyear"
      help: "Reference base year."
    - name: "pyear-start"
      type: "int"
      source: "metadata.pyear_start"
      help: "Projection start year."
    - name: "pyear-end"
      type: "int"
      source: "metadata.pyear_end"
      help: "Projection end year."
    - name: "pyear-step"
      type: "int"
      source: "metadata.pyear_step"
      help: "Projection year step."

  options:
    - name: "seed"
      type: "int"
      source: "module_inputs.options.seed"
      default_value: 1234
      help: "Random seed for reproducibility."

  fingerprint_params:
    - name: "fingerprint-dir"
      type: "str"
      source: "module_inputs.fingerprint_params.fingerprint_dir"
      help: "Directory containing fingerprint files."
      mount:
        volume: "shared_in"
        container_path: "/mnt/shared_in"

  inputs:
    - name: "param-file"
      type: "file"
      source: "module_inputs.inputs.param_fname"
      filename: "parameters/my_params.nc"
      help: "Parameter file for the model."
      mount:
        volume: "module_specific_in"
        container_path: "/mnt/module_specific_in"

  outputs:
    files:
      - name: "output-gslr-file"
        type: "file"
        source: "module_inputs.outputs.output_gslr_file"
        filename: "gslr.nc"
        output_type: "global"
        help: "Global mean sea level rise output."
        mount:
          volume: "output"
          container_path: "/mnt/out"
          transform: "filename"

volumes:
  module_specific_in:
    host_path: "module_inputs.input_paths.module_specific_input_dir"
    container_path: "/mnt/module_specific_in"
    help: "Module-specific input data directory."
  shared_in:
    host_path: "module_inputs.input_paths.shared_input_dir"
    container_path: "/mnt/shared_in"
    help: "Shared input directory."
  output:
    host_path: "module_inputs.output_paths.output_dir"
    container_path: "/mnt/out"
    help: "Output directory."
```

---

## Input data archives

If your module's input data is archived on Zenodo (recommended), include the archive URL(s) as a comment at the top of your YAML:

```yaml
# Input data archive:
# https://zenodo.org/record/<record-id>/files/<archive-name>.tgz
```

---

## Submitting your entry

1. Fork this repository and create a branch.
2. Add your module directory and YAML following the naming conventions above.
3. Verify the YAML is valid: check that every `mount.volume` key referenced in `arguments` appears in `volumes`, and that every `source` path follows the `metadata.*` or `module_inputs.*` conventions.
4. Open a pull request against `main`.

When FEB users pull the updated registry and run `setup-experiment`, your module will become available for selection.


Please reach out with questions or if you'd like assistance! We are happy to work with you to help bring your module into the module registry! 