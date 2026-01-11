# Azure Example

This example demonstrates Dynamic Alias configurations for common Microsoft Azure workflows:

- **Azure Login** - Authenticate with Azure CLI
- **VM SSH** - Connect to Virtual Machines
- **PostgreSQL Flexible Server** - Connect to Azure Database for PostgreSQL
- **Azure Cache for Redis** - Connect to Redis Cache

## Features Used

| Feature | Description |
|---------|-------------|
| `dynamic_dict` | Fetch Azure resources dynamically |
| `dict` | Static default values |
| `cache-ttl` | Cache az command responses |
| `timeout` | Prevent hanging on slow API calls |

## Prerequisites

- Azure CLI installed (`az`)
- Authenticated with `az login`
- Appropriate RBAC permissions

## Commands

### Azure Login

```bash
dya azlogin <subscription-name>
```

Logs in and sets the active subscription.

### VM SSH

```bash
dya azssh <vm-name>
```

SSH into an Azure Virtual Machine.

### PostgreSQL

```bash
dya azpg <server-name>
```

Connects to Azure Database for PostgreSQL.

### Redis Cache

```bash
dya azcache <cache-name>
```

Connects to Azure Cache for Redis.

## Configuration Details

### Dynamic Dict: Subscriptions

```yaml
type: dynamic_dict
name: subscriptions
command: |
  az account list --output json
mapping:
  id: id
  name: name
```

### Dynamic Dict: Virtual Machines

```yaml
type: dynamic_dict
name: vms
command: |
  az vm list --show-details --output json
mapping:
  name: name
  ip: publicIps
  resourceGroup: resourceGroup
```

### Dynamic Dict: PostgreSQL Servers

```yaml
type: dynamic_dict
name: postgres
command: |
  az postgres flexible-server list --output json
mapping:
  name: name
  host: fullyQualifiedDomainName
```

### Dynamic Dict: Redis Cache

```yaml
type: dynamic_dict
name: redis
command: |
  az redis list --output json
mapping:
  name: name
  host: hostName
  port: sslPort
```
