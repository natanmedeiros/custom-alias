# AWS Example

This example demonstrates Dynamic Alias configurations for common AWS workflows:

- **SSO Login** - Authenticate with AWS SSO profiles
- **SSM Sessions** - Connect to EC2 instances via Session Manager
- **RDS PostgreSQL** - Connect to RDS PostgreSQL databases
- **ElastiCache Redis** - Connect to ElastiCache Redis clusters

## Features Used

| Feature | Description |
|---------|-------------|
| `dynamic_dict` | Fetch AWS resources dynamically |
| `dict` | Static default values |
| `cache-ttl` | Cache AWS API responses |
| `timeout` | Prevent hanging on slow API calls |
| Multiline commands | Complex AWS CLI queries |
| Variable substitution | Reference dict values in commands |

## Prerequisites

- AWS CLI v2 installed and configured
- AWS SSO configured (`aws configure sso`)
- Appropriate IAM permissions for EC2, RDS, ElastiCache

## Commands

### SSO Login

```bash
dya sso <account-name>
```

Logs into the specified AWS SSO profile and saves it as the last used profile.

### SSM Session

```bash
dya ssm <instance-name>
```

Starts an SSM session to the specified EC2 instance.

### PostgreSQL RDS

```bash
dya pg <rds-name>
```

Connects to the specified RDS PostgreSQL instance using `psql`.

### ElastiCache Redis

```bash
dya cache <cluster-name>
```

Connects to the specified ElastiCache Redis cluster using `redis-cli`.

## Configuration Details

### Dynamic Dict: AWS SSO Profiles

Extracts SSO profiles from `~/.aws/config`:

```yaml
type: dynamic_dict
name: accounts
command: |
  grep -E '^\[profile ' ~/.aws/config | 
  sed 's/\[profile //' | sed 's/\]//' | 
  jq -R -s 'split("\n") | map(select(length > 0)) | map({id: ., name: .})'
mapping:
  id: id
  name: name
```

### Dynamic Dict: EC2 Instances

Fetches running EC2 instances with Name tags:

```yaml
type: dynamic_dict
name: ec2
command: |
  aws ec2 describe-instances \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[].Instances[].{id:InstanceId,name:Tags[?Key==`Name`].Value|[0]}' \
    --output json
mapping:
  name: name
  id: id
```

### Dynamic Dict: RDS PostgreSQL

Fetches PostgreSQL RDS instances:

```yaml
type: dynamic_dict
name: rds
command: |
  aws rds describe-db-instances \
    --query 'DBInstances[?Engine==`postgres`].{name:DBInstanceIdentifier,host:Endpoint.Address,dbname:DBName}' \
    --output json
mapping:
  name: name
  host: host
  dbname: dbname
```

### Dynamic Dict: ElastiCache Redis

Fetches ElastiCache Redis clusters:

```yaml
type: dynamic_dict
name: elasticache
command: |
  aws elasticache describe-cache-clusters \
    --show-cache-node-info \
    --query 'CacheClusters[?Engine==`redis`].{name:CacheClusterId,host:CacheNodes[0].Endpoint.Address}' \
    --output json
mapping:
  name: name
  host: host
```

## Default Users

Static dict for default database users:

```yaml
type: dict
name: default_user
data:
  - name: postgres
    user: postgres
  - name: redis
    user: default
```
