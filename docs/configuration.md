# Configuration Reference

## File Structure

Dynamic Alias uses YAML with document separators (`---`) to define blocks:

```yaml
config:
  # Global settings

---
type: dict
# Static data

---
type: dynamic_dict
# Dynamic data from commands

---
type: command
# Aliases and commands
```

## Config Block

The config block defines global settings. It can be defined two ways:

### Implicit (Recommended)
```yaml
config:
  style-completion: "bg:#008888 #ffffff"
  history-size: 100
```

### Explicit
```yaml
---
type: config
style-completion: "bg:#008888 #ffffff"
history-size: 100
```

## Config Options

| Option | Default | Description |
|--------|---------|-------------|
| `style-completion` | `bg:#008888 #ffffff` | Completion menu colors |
| `style-completion-current` | `bg:#00aaaa #000000` | Selected item colors |
| `style-scrollbar-background` | `bg:#88aaaa` | Scrollbar background |
| `style-scrollbar-button` | `bg:#222222` | Scrollbar button |
| `style-placeholder-color` | `gray` | Placeholder text color |
| `style-placeholder-text` | `(tab for menu)` | Placeholder hint |
| `history-size` | `20` | Max commands in history (max: 1000) |

> [!NOTE]
> Style parameters follow the [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/en/master/pages/advanced_topics/styling.html) styling format. Use CSS-like syntax with `bg:` for background colors and color names or hex values for foreground.

## Variable Syntax

### User Input Variables
Variables the user provides via CLI:
```yaml
alias: connect ${hostname}
command: ssh ${hostname}
```

### Application Variables  
References to dicts/dynamic_dicts:
```yaml
alias: pg $${databases.name}
command: psql -h $${databases.host} -U $${databases.user}
```

### Environment Variables
Access OS environment:
```yaml
command: echo $${env.HOME}
```

## Priority System

Dynamic dicts can reference each other. Lower priority executes first:

```yaml
---
type: dynamic_dict
name: regions
priority: 1
command: aws ec2 describe-regions --query 'Regions[].RegionName'

---
type: dynamic_dict
name: instances
priority: 2  # Executes after 'regions'
command: aws ec2 describe-instances --region $${regions.current}
```

---

| ← Previous | Next → |
|:-----------|-------:|
| [Getting Started](getting-started.md) | [Static Dicts](dicts.md) |
