# Changelog

All notable changes to Dynamic Alias will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-01-17

### ✨ New Features

#### Indexed Access for Dicts and Dynamic Dicts
Direct position selection in data sources using bracket syntax:
```yaml
# Default (position 0)
command: echo $${db_servers.host}

# Explicit index access
command: echo $${db_servers[0].host} $${db_servers[1].host} $${db_servers[2].host}
```
Access any position in your dict/dynamic_dict data directly without list mode selection.

#### New Helper System
Completely redesigned help output with two modes:

- **Auto Helper** (`helper_type: auto`): Structured format with Description, Usage, Args, and Options/Subcommands sections
- **Custom Helper** (`helper_type: custom`): Raw concatenated helper text for custom formatting

**Dynamic Usage Display**: Usage section now shows the full matched command path with optional args and subcommands in bracket notation:
```
deep-cmd [-v | --verbose | -c | --config] [level1 [-f | --force] | status [-a | --all]]
```

#### Array Aliases for Arguments
Define multiple aliases for the same argument:
```yaml
args:
  - alias: ["-o ${file}", "--output ${file}"]
    command: -o ${file}
    helper: Output file path
  - alias: ["-v", "--verbose"]
    command: --verbose
    helper: Verbose mode
```
Both `-o` and `--output` trigger the same argument. Displayed as `-o, --output ${file}` in help.

### 🔧 Improvements

#### Enhanced Validator
- **Variable Reference Validation**: Checks all dict/dynamic_dict variables are defined
- **Position Validation**: Validates indexed access syntax `$${source[N].key}`
- **Key Validation**: Ensures referenced keys exist in data sources
- **Array Alias Validation**: Verifies consistent variable structure across alias arrays

### 📚 Documentation
- New dedicated [Helper System documentation](docs/helper.md)
- Updated [Commands documentation](docs/commands.md) with array aliases
- Added Helper System to README documentation index

---

## [1.0.0] - 2026-01-15

🚀 **Dynamic Alias to the world!**

We're thrilled to announce the first public release of Dynamic Alias — a declarative CLI builder that transforms complex command-line workflows into simple, memorable aliases with smart autocompletion.

### What is Dynamic Alias?
Modern infrastructure professionals juggle dozens of CLI tools daily—AWS, GCP, Azure, Kubernetes, databases, and more. Dynamic Alias lets you define your workflows once in YAML and use them everywhere:

```bash
# Instead of remembering:
aws ssm start-session --target i-0abc123def456 --region us-east-1

# Just type:
dya ssm prod-web-server
```

### ✨ Key Features

- **Declarative Configuration** — Define commands, aliases, and data sources in YAML
- **Smart Autocompletion** — Tab-complete through your resources, databases, and servers
- **Dynamic Data Sources** — Fetch live data from AWS, GCP, Azure, or any CLI tool
- **Interactive Shell** — Run `dya` for a full shell experience with history navigation
- **Caching & TTL** — Reduce API calls with configurable cache expiration
- **Subcommands & Arguments** — Build complex CLI trees with nested commands
- **Custom Branding** — Create your own branded CLI tool for your organization

### 🎯 Who is this for?

- **DBAs, SREs, DBREs, DevOps engineers, and sysadmins** who work with multiple tools daily
- **Companies building internal CLIs** for their teams
- Anyone tired of memorizing instance IDs, hostnames, and complex flags

### 📦 Installation

```bash
pip install dynamic-alias
```

### 📚 Documentation

Full documentation with examples for AWS, GCP, Azure, and OCI is available on [GitHub](https://github.com/natanmedeiros/dynamic-alias).

---

**Thank you for using Dynamic Alias!** We'd love to hear your feedback and see how you're using it.

[1.1.0]: https://github.com/natanmedeiros/dynamic-alias/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/natanmedeiros/dynamic-alias/releases/tag/v1.0.0
