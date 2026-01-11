# Custom CLI Example

This example demonstrates how to create your own branded CLI tool using Dynamic Alias.

## Overview

Instead of using the default `dya` command, you can build a CLI with your company's name and branding.

**Example:** Create a CLI called `infra` for "ACME Infrastructure Tool"

## Configuration

### 1. Update `pyproject.toml`

```toml
[project]
name = "acme-infra"
version = "1.0.0"
description = "ACME Infrastructure CLI"

[project.scripts]
infra = "dynamic_alias.main:main"

[tool.custom-build]
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
