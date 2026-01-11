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

## BOM Handling

Config files with UTF-8 BOM (Byte Order Mark) are automatically handled. This ensures compatibility with files created by Windows editors.

---

| ← Previous | Next → |
|:-----------|-------:|
| [Commands](commands.md) | [Interactive Mode](interactive-mode.md) |
