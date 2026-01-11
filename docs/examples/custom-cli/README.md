# Custom CLI Example

This example demonstrates how to create your own branded CLI tool using Dynamic Alias.

## Overview

Instead of using the default `dya` command, you can build a CLI with your company's name and branding.

**Example:** Create a CLI called `infra` for "ACME Infrastructure Tool"

## Configuration

### 1. Update `pyproject.toml`

```toml
[project]
version = "1.2.0"

[custom-build]
name = "ACME Infrastructure Tool"
shortcut = "infra"
```

### 2. Create Config File

The config file will be `~/.infra.yaml` (matching your shortcut):

```yaml
config:
  history-size: 100
  style-completion: "bg:#6b21a8 #ffffff"

---
type: command
name: Server Status
alias: status
command: ./scripts/check_status.sh
helper: Check status of all ACME servers
```

### 3. Build and Install

```bash
python -m build
pip install dist/acme_infra-*.whl
```

### 4. Usage

```bash
# Now use your custom command
infra status
infra -h

# Interactive mode
infra
infra> status <TAB>
```

## Features Used

| Feature | Description |
|---------|-------------|
| Custom shortcut | `infra` instead of `dya` |
| Custom name | "ACME Infrastructure Tool" in help |
| Branded styling | Purple color scheme |
| Company-specific commands | Internal scripts and tools |

## File Locations

| File | Purpose |
|------|---------|
| `~/.infra.yaml` | Configuration (shortcut-based) |
| `~/.infra.json` | Cache file (shortcut-based) |

## Command Line Flags

```bash
# Override paths
infra --infra-config /path/to/config.yaml
infra --infra-cache /path/to/cache.json
```

## Benefits

1. **Branding** - Your team uses a familiar command name
2. **Discoverability** - `-h` shows your company name
3. **Distribution** - Package as deb/rpm/wheel for easy installation
4. **Customization** - Style matches company theme

## Bundled Configuration (Rules 1.1.12 & 1.1.13)

When building a CLI with Dynamic Alias, you can include a default configuration file (`dya.yaml` or `{shortcut}.yaml`).

- **Automatic Inclusion**: If `{shortcut}.yaml` exists in the project root during build, it is automatically bundled into the package.
- **Strict Synchronization**:
    - The CLI synchronizes the user's default configuration (`~/.{shortcut}.yaml`) with the bundled version.
    - On every execution, the system compares the SHA checksum of the installed user config with the bundled config.
    - **Overwrite Policy**: If they differ (e.g., manual edit or package update), the bundled version **overwrites** the user file.
    - This ensures the CLI always behaves as defined by the package version.
- **Customization**:
    - To use a custom configuration without being overwritten, you must use the flag `--{shortcut}-config <path>`.
    - Example: `infra --infra-config my_custom_config.yaml`
- **Updates**: Updating the package (`pip install --upgrade`) will bring a new bundled config, which will automatically update the user's default config on the next run.
