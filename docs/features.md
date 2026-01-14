# Features

## Strict Mode

By default, extra arguments are appended to the command. Enable `strict: true` to reject them.

### Default Behavior (strict: false)

```yaml
---
type: command
name: Echo
alias: echo
command: echo hello
strict: false  # Default
```

```bash
dya echo world
# Executes: echo hello world
```

### Strict Mode (strict: true)

```yaml
---
type: command
name: Exact Command
alias: exact
command: echo 'This is exact'
strict: true
```

```bash
dya exact extra args
# Error: Strict mode enabled. Unknown arguments: "extra args"
```

## Timeout

Set execution time limits to prevent hanging commands.

### Command Timeout

```yaml
---
type: command
name: Long Task
alias: task
command: ./long-running-script.sh
timeout: 60  # 60 seconds
```

If the command exceeds the timeout:
```
Error: Command timed out after 60s
```

### Dynamic Dict Timeout

```yaml
---
type: dynamic_dict
name: slow_api
timeout: 30
command: curl -s https://api.example.com/slow
mapping:
  id: id
```

## History

Command history is stored in the cache file and persists across sessions.

### Configuration

```yaml
config:
  history-size: 100  # Max 1000
```

### Storage

History is stored in the cache file:
```json
{
  "_history": [
    "pg production",
    "ssh web-server",
    "k get pods"
  ]
}
```

### Behavior

- **Create**: If `_history` doesn't exist, it's created
- **Append**: New commands are appended
- **Shift**: When exceeding `history-size`, oldest entries are removed

### Navigation

In interactive mode, use arrow keys:
- **↑ (Up)**: Previous command
- **↓ (Down)**: Next command

## Cache TTL

Dynamic dict results are cached with time-to-live:

```yaml
---
type: dynamic_dict
name: instances
cache-ttl: 600  # 10 minutes
command: aws ec2 describe-instances --output json
mapping:
  id: InstanceId
```

### Cache Behavior

1. **First call**: Executes command, caches result with timestamp
2. **Within TTL**: Returns cached data (no execution)
3. **After TTL**: Re-executes command, updates cache

### Cache File Structure

```json
{
  "instances": {
    "timestamp": 1704067200,
    "data": [
      {"id": "i-abc123", "name": "prod-web"}
    ]
  }
}
```

## Environment Variables

Access OS environment variables:

```yaml
---
type: command
name: Home Dir
alias: home
command: cd $${env.HOME} && ls
```

## Config Validator

Validate your configuration file for errors before use.

### Manual Validation

Run the validator with full output:

```bash
dya --dya-validate
# Or with custom config:
dya --dya-validate --dya-config ./path/to/config.yaml
```

**Example output:**
```
============================================================
  Configuration Validator (dya)
============================================================

  Config: ./dya.yaml

  VALIDATION CHECKLIST
  ----------------------------------------
  [✓] Config file exists: ./dya.yaml
  [✓] Valid YAML syntax
  [✓] Config block has valid keys
  [✓] All dict/dynamic_dict references are valid
  [✓] Priority order is correct

  ----------------------------------------
  SUMMARY
  ----------------------------------------

  ✓ All 5 checks passed!

  Configuration is valid.
============================================================
```

### Automatic Silent Validation

At startup (interactive and non-interactive modes), the config is automatically validated. If errors are found, they are displayed and execution stops:

```
[DYA] Configuration errors found in: ./config.yaml
--------------------------------------------------
  ✗ command 'my_command' references undefined source: 'undefined_dict'
    Location: Block 3
    Hint: Define a dict or dynamic_dict named 'undefined_dict'
--------------------------------------------------
Fix the 1 error(s) above or run 'dya --dya-validate' for full report.
```

### What is Validated

| Check | Description |
|-------|-------------|
| **File exists** | Config file must exist |
| **Valid YAML** | Syntax must be correct |
| **Required fields** | Each block type must have required fields |
| **Config keys** | Only valid keys in config block |
| **References** | All `$${source.key}` must reference defined sources |
| **Priority order** | Dynamic dicts must respect priority when referencing others |

## BOM Handling

Config files with UTF-8 BOM (Byte Order Mark) are automatically handled. This ensures compatibility with files created by Windows editors.

---

| ← Previous | Next → |
|:-----------|-------:|
| [Commands](commands.md) | [Interactive Mode](interactive-mode.md) |

