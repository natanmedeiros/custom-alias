# Static Dicts

Static dicts define fixed data that doesn't change at runtime. Use them for configuration values, server lists, or any static reference data.

## Basic Structure

```yaml
---
type: dict
name: servers
data:
  - name: web-prod
    host: 10.0.1.10
    port: 22
  - name: web-staging
    host: 10.0.2.10
    port: 22
  - name: db-prod
    host: 10.0.1.20
    port: 5432
```

## Required Fields

| Field | Description |
|-------|-------------|
| `type` | Must be `dict` |
| `name` | Unique identifier for the dict |
| `data` | List of key-value objects |

## Access Modes

There are **two ways** to use dicts in commands:

### List Mode (Dict in Alias)

When you reference the dict in the **alias**, the user selects an item interactively, and all keys in the command resolve from that **same item**:

```yaml
---
type: dict
name: servers
data:
  - name: prod
    host: 192.168.1.10
    user: admin
  - name: staging
    host: 192.168.1.20
    user: deploy

---
type: command
name: SSH Connect
alias: ssh $${servers.name}        # ← Dict in ALIAS (list mode)
command: ssh $${servers.user}@$${servers.host}
```

**Usage:**
```
dya> ssh <TAB>
         prod
         staging

dya> ssh prod
Running: ssh admin@192.168.1.10
```

The user selects `prod`, so `$${servers.user}` resolves to `admin` and `$${servers.host}` resolves to `192.168.1.10` from the **same item**.

### Direct Mode (Dict NOT in Alias)

When you reference the dict **only in the command** (not in alias), it always accesses the **first item (position 0)** of the data list:

```yaml
---
type: dict
name: api_config
data:
  - key: MY_API_KEY
    endpoint: https://api.example.com
    timeout: 30

---
type: command
name: API Call
alias: api-call                    # ← No dict in alias (direct mode)
command: curl -H "Authorization: $${api_config.key}" $${api_config.endpoint}
```

**Usage:**
```
dya> api-call
Running: curl -H "Authorization: MY_API_KEY" https://api.example.com
```

> [!IMPORTANT]
> In **direct mode**, even if the dict has multiple items, it **always accesses position 0** (the first item).

**Example with multiple items (only first is used):**

```yaml
---
type: dict
name: regions
data:
  - name: us-east-1    # ← Position 0 (used in direct mode)
    endpoint: https://us-east-1.api.com
  - name: eu-west-1    # ← Position 1 (ignored in direct mode)
    endpoint: https://eu-west-1.api.com

---
type: command
name: Default Region
alias: default-region              # ← No dict in alias
command: echo "Using region: $${regions.name}"
```

**Usage:**
```
dya> default-region
Running: echo "Using region: us-east-1"   # Always uses position 0
```

## Mode Comparison

| Mode | Dict in Alias | Behavior |
|------|---------------|----------|
| **List** | ✓ Yes | User selects item; all keys from same item |
| **Direct** | ✗ No | Always uses first item (position 0) |

## Multiple Keys

Each data item can have any number of keys:

```yaml
---
type: dict
name: databases
data:
  - name: analytics
    host: db-analytics.internal
    port: 5432
    user: analyst
    dbname: analytics_prod
  - name: orders
    host: db-orders.internal
    port: 5432
    user: app
    dbname: orders_prod
```

## Autocomplete

In interactive mode (list mode), typing the alias prefix shows all available options:

```
dya> ssh <TAB>
         prod
         staging
```

---

| ← Previous | Next → |
|:-----------|-------:|
| [Configuration](configuration.md) | [Dynamic Dicts](dynamic-dicts.md) |
