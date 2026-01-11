# GCP Example

This example demonstrates Dynamic Alias configurations for common Google Cloud Platform workflows:

- **Auth Login** - Authenticate with gcloud
- **Compute SSH** - Connect to Compute Engine instances
- **Cloud SQL PostgreSQL** - Connect to Cloud SQL databases
- **Memorystore Redis** - Connect to Memorystore Redis instances

## Features Used

| Feature | Description |
|---------|-------------|
| `dynamic_dict` | Fetch GCP resources dynamically |
| `dict` | Static default values |
| `cache-ttl` | Cache gcloud command responses |
| `timeout` | Prevent hanging on slow API calls |

## Prerequisites

- Google Cloud SDK (gcloud) installed
- Authenticated with `gcloud auth login`
- Appropriate IAM permissions

## Commands

### Auth Login

```bash
dya gauth <project-name>
```

Authenticates and sets the active project.

### Compute SSH

```bash
dya gssh <instance-name>
```

SSH into a Compute Engine instance.

### Cloud SQL PostgreSQL

```bash
dya gpg <instance-name>
```

Connects to Cloud SQL PostgreSQL using Cloud SQL Proxy or direct connection.

### Memorystore Redis

```bash
dya gcache <instance-name>
```

Connects to Memorystore Redis instance.

## Configuration Details

### Dynamic Dict: GCP Projects

```yaml
type: dynamic_dict
name: projects
command: |
  gcloud projects list --format=json
mapping:
  id: projectId
  name: name
```

### Dynamic Dict: Compute Instances

```yaml
type: dynamic_dict
name: compute
command: |
  gcloud compute instances list --format=json
mapping:
  name: name
  zone: zone
  ip: networkInterfaces[0].networkIP
```

### Dynamic Dict: Cloud SQL Instances

```yaml
type: dynamic_dict
name: cloudsql
command: |
  gcloud sql instances list --format=json
mapping:
  name: name
  host: ipAddresses[0].ipAddress
  region: region
```

### Dynamic Dict: Memorystore Redis

```yaml
type: dynamic_dict
name: memorystore
command: |
  gcloud redis instances list --format=json --region=us-central1
mapping:
  name: name
  host: host
  port: port
```
