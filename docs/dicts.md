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

## Usage in Commands

Reference dict values using `$${dict_name.key}`:

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
alias: ssh $${servers.name}
command: ssh $${servers.user}@$${servers.host}
```

When you type `ssh prod`, it expands to:
```bash
ssh admin@192.168.1.10
```

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

In interactive mode, typing the alias prefix shows all available options:

```
dya> ssh <TAB>
          prod
          staging
```

---

| ← Previous | Next → |
|:-----------|-------:|
| [Configuration](configuration.md) | [Dynamic Dicts](dynamic-dicts.md) |
