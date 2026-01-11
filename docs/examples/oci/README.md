# OCI (Oracle Cloud Infrastructure) Example

This example demonstrates Dynamic Alias configurations for common OCI workflows:

- **Session Authenticate** - Authenticate with OCI CLI
- **Compute SSH** - Connect to Compute instances
- **Autonomous Database** - Connect to Autonomous Database
- **OCI Cache with Redis** - Connect to OCI Cache (Redis)

## Features Used

| Feature | Description |
|---------|-------------|
| `dynamic_dict` | Fetch OCI resources dynamically |
| `dict` | Static default values |
| `cache-ttl` | Cache OCI CLI responses |
| `timeout` | Prevent hanging on slow API calls |

## Prerequisites

- OCI CLI installed and configured
- Authenticated via `oci session authenticate`
- Appropriate IAM policies

## Commands

### Session Authenticate

```bash
dya oci-auth <profile-name>
```

Authenticates and activates the profile.

### Compute SSH

```bash
dya oci-ssh <instance-name>
```

SSH into an OCI Compute instance.

### Autonomous Database

```bash
dya oci-pg <db-name>
```

Connects to Autonomous Database using SQL*Plus or compatible client.

### OCI Cache (Redis)

```bash
dya oci-cache <cluster-name>
```

Connects to OCI Cache with Redis.

## Configuration Details

### Dynamic Dict: OCI Tenancies/Compartments

```yaml
type: dynamic_dict
name: compartments
command: |
  oci iam compartment list --output json
mapping:
  id: id
  name: name
```

### Dynamic Dict: Compute Instances

```yaml
type: dynamic_dict
name: compute
command: |
  oci compute instance list \
    --compartment-id $COMPARTMENT_ID \
    --output json
mapping:
  name: display-name
  id: id
  ip: primary-private-ip
```

### Dynamic Dict: Autonomous Databases

```yaml
type: dynamic_dict
name: autonomous_db
command: |
  oci db autonomous-database list \
    --compartment-id $COMPARTMENT_ID \
    --output json
mapping:
  name: display-name
  host: connection-strings.profiles[0].host
```

### Dynamic Dict: OCI Cache

```yaml
type: dynamic_dict
name: oci_cache
command: |
  oci redis cluster list \
    --compartment-id $COMPARTMENT_ID \
    --output json
mapping:
  name: display-name
  host: primary-endpoint
```
