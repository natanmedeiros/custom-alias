# Dynamic Dicts

Dynamic dicts fetch data from external commands at runtime. Perfect for cloud resources, API responses, or any data that changes.

## Basic Structure

```yaml
---
type: dynamic_dict
name: ec2_instances
command: |
  aws ec2 describe-instances \
    --query 'Reservations[].Instances[].{id:InstanceId,name:Tags[?Key==`Name`].Value|[0]}' \
    --output json
mapping:
  name: name
  id: id
```

## Required Fields

| Field | Description |
|-------|-------------|
| `type` | Must be `dynamic_dict` |
| `name` | Unique identifier |
| `command` | Shell command that outputs JSON |
| `mapping` | Maps JSON keys to internal keys |

## Optional Fields

| Field | Default | Description |
|-------|---------|-------------|
| `priority` | `1` | Execution order (lower = first) |
| `timeout` | `10` | Seconds before timeout |
| `cache-ttl` | `300` | Cache validity in seconds |

## Access Modes

Dynamic dicts support the same two access modes as static dicts:

### List Mode (Dict in Alias)

When you reference the dict in the **alias**, the user selects an item interactively:

```yaml
---
type: dynamic_dict
name: ec2
command: |
  aws ec2 describe-instances \
    --query 'Reservations[].Instances[].{name:Tags[?Key==`Name`].Value|[0],ip:PrivateIpAddress}' \
    --output json
mapping:
  name: name
  ip: ip

---
type: command
name: SSH to EC2
alias: ec2 $${ec2.name}          # ← Dict in ALIAS (list mode)
command: ssh ec2-user@$${ec2.ip}
```

**Usage:**
```
dya> ec2 <TAB>
        web-prod
        api-prod
        db-prod

dya> ec2 web-prod
Running: ssh ec2-user@10.0.1.50
```

### Direct Mode (Dict NOT in Alias)

When you reference the dict **only in the command**, it always accesses the **first item (position 0)**:

```yaml
---
type: dynamic_dict
name: current_context
command: kubectl config current-context | jq -R '{name: .}'
mapping:
  name: name

---
type: command
name: K8s Context
alias: k8s-context                 # ← No dict in alias (direct mode)
command: echo "Current context: $${current_context.name}"
```

**Usage:**
```
dya> k8s-context
Running: echo "Current context: prod-cluster"
```

> [!IMPORTANT]
> In **direct mode**, even if the dynamic dict returns multiple items, it **always accesses position 0** (the first item).

### Mode Comparison

| Mode | Dict in Alias | Behavior |
|------|---------------|----------|
| **List** | ✓ Yes | User selects item; all keys from same item |
| **Direct** | ✗ No | Always uses first item (position 0) |

## Mapping

The `mapping` field translates JSON output keys to your internal keys:

```yaml
# Command outputs: [{"InstanceId": "i-123", "PrivateIp": "10.0.0.5"}]
mapping:
  id: InstanceId      # Internal 'id' ← JSON 'InstanceId'
  ip: PrivateIp       # Internal 'ip' ← JSON 'PrivateIp'
```

## Caching

Dynamic dict results are cached to avoid repeated API calls.

### Cache TTL (Time-To-Live)

```yaml
---
type: dynamic_dict
name: instances
cache-ttl: 600  # Cache valid for 10 minutes
command: aws ec2 describe-instances --output json
mapping:
  id: InstanceId
```

### Cache Storage

Cache is stored in the cache file (default: `~/.dya.json`):

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

### Force Refresh

Delete the cache file or wait for TTL expiration:
```bash
rm ~/.dya.json
```

## Priority

When dynamic dicts depend on each other, use `priority`. Lower values execute first:

```yaml
---
type: dynamic_dict
name: current_region
priority: 1  # Executes first
command: cat ~/.aws/last_region || echo "us-east-1"
mapping:
  name: region

---
type: dynamic_dict
name: vpcs
priority: 2  # Executes after 'current_region', can use its result
command: aws ec2 describe-vpcs --region $${current_region.name} --query 'Vpcs[].{id:VpcId,name:Tags[?Key==`Name`].Value|[0]}' --output json
mapping:
  id: id
  name: name
```

In this example:
1. `current_region` (priority 1) reads the last configured region from `~/.aws/last_region`
2. `vpcs` (priority 2) uses `$${current_region.name}` to filter VPCs by that region

## Chaining

Dynamic dicts can reference values from **static dicts** and **other dynamic dicts** with lower priority. This enables powerful chaining patterns.

### Chaining Order

1. **Static dicts** are always available (no priority needed)
2. **Dynamic dicts** with lower `priority` values are resolved first
3. Higher priority dynamic dicts can reference lower priority ones

### Example: Dict → Dynamic Dict → Dynamic Dict

```yaml
# Step 1: Static dict with base configuration
---
type: dict
name: config
data:
  - prefix: PROD
    region: us-east-1

# Step 2: First dynamic dict - references static dict
---
type: dynamic_dict
name: cluster_info
priority: 1
command: |
  aws eks describe-cluster \
    --name $${config.prefix}-cluster \
    --region $${config.region} \
    --query 'cluster.{name:name,endpoint:endpoint}' \
    --output json
mapping:
  name: name
  endpoint: endpoint

# Step 3: Second dynamic dict - references first dynamic dict
---
type: dynamic_dict
name: cluster_nodes
priority: 2
command: |
  kubectl --server=$${cluster_info.endpoint} get nodes -o json | \
    jq '[.items[] | {name: .metadata.name, ip: .status.addresses[0].address}]'
mapping:
  name: name
  ip: ip

# Step 4: Command uses the final result
---
type: command
name: SSH to Node
alias: node $${cluster_nodes.name}
command: ssh admin@$${cluster_nodes.ip}
```

**Resolution Flow:**
```
config.prefix = "PROD"
      ↓
cluster_info (priority 1) → executes with "PROD-cluster"
      ↓
cluster_info.endpoint = "https://eks.example.com"
      ↓
cluster_nodes (priority 2) → executes with resolved endpoint
      ↓
command → user selects node, resolves IP
```

**Usage:**
```
dya> node <TAB>
        node-1
        node-2
        node-3

dya> node node-1
Running: ssh admin@10.0.1.50
```

### Simple Chaining Example

```yaml
# Base configuration
---
type: dict
name: api_base
data:
  - url: https://api.example.com
    version: v2

# Dynamic dict that uses the base config
---
type: dynamic_dict
name: api_status
priority: 1
command: |
  curl -s $${api_base.url}/$${api_base.version}/status
mapping:
  status: status
  uptime: uptime

# Command that shows the status
---
type: command
name: API Status
alias: api-status
command: echo "Status: $${api_status.status}, Uptime: $${api_status.uptime}"
```

**Usage:**
```
dya> api-status
Running: echo "Status: healthy, Uptime: 99.9%"
Status: healthy, Uptime: 99.9%
```

> [!NOTE]
> When a dynamic dict references another source that hasn't been resolved yet, the system automatically resolves the dependency first (lazy resolution).

## Timeout

Prevent hanging on slow commands:

```yaml
---
type: dynamic_dict
name: slow_api
timeout: 30  # 30 second timeout
command: curl -s https://slow-api.example.com/data
mapping:
  id: id
```

## Complete Example: AWS EC2

```yaml
---
type: dynamic_dict
name: ec2
priority: 1
timeout: 15
cache-ttl: 300
command: |
  aws ec2 describe-instances \
    --query 'Reservations[].Instances[].{id:InstanceId,name:Tags[?Key==`Name`].Value|[0],ip:PrivateIpAddress}' \
    --output json
mapping:
  name: name
  id: id
  ip: ip

---
type: command
name: SSH to EC2
alias: ec2 $${ec2.name}
command: ssh ec2-user@$${ec2.ip}
```

**Usage:**
```
dya> ec2 <TAB>
        web-prod
        api-server
        db-master

dya> ec2 web-prod
Running: ssh ec2-user@10.0.1.100
```

---

| ← Previous | Next → |
|:-----------|-------:|
| [Static Dicts](dicts.md) | [Commands](commands.md) |
