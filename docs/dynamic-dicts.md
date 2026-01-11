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

## Example: AWS EC2 Instances

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

---

| ← Previous | Next → |
|:-----------|-------:|
| [Static Dicts](dicts.md) | [Commands](commands.md) |
