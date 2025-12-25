# Short Command (`shoco`)

Short Command is a powerful CLI application that allows users to create "aliases with superpowers". It transforms complex command-line interactions into simple, autocompletable shortcuts, leveraging dynamic data sources and structured configurations.

## Features

-   **Superpowered Aliases**: Define aliases that map to complex commands.
-   **Dynamic Data**: Use output from external commands (e.g., AWS, Redis) as data sources for your aliases.
-   **Smart Autocomplete**: Context-aware autocompletion for commands, subcommands, arguments, and dynamic data values.
-   **Variable Support**:
    -   **User Input Variables** (`${var}`): Placeholders that you fill in during execution.
    -   **Application Variables** (`$${source.key}`): Values automatically populated from your dynamic data sources.
    -   **Environment Variables** (`$${env.VAR}`): Integration with system environment variables.
-   **Interactive Shell**: A robust shell environment (`shoco >`) with menu-based completion.

## System Requirements

-   Python 3.x
-   Dependencies: `prompt_toolkit`, `pyyaml`
-   Configuration file: `shoco.yaml` (default at `~/.shoco.yaml` or current directory)

## Configuration (`shoco.yaml`)

The application is driven by a YAML configuration file that defines three main structures: **Dict**, **Dynamic Dict**, and **Command**.

### 1. Variables Syntax
-   `$${variable}`: Application variable (from Dynamic Dicts or Environment).
-   `${variable}`: User input variable (you type the value).

### 2. Dict (Static Data)
Defines static key-value lists.
```yaml
---
type: dict
name: application_servers
data:
  - name: app1
    host: 192.168.1.10
    port: 8080
```

### 3. Dynamic Dict (Dynamic Data)
Fetches data by executing a shell command. The output must be JSON.
```yaml
---
type: dynamic_dict
name: redis_servers
priority: 1
command: |
  aws elasticache describe-cache-clusters --output json ...
mapping:
  name: CacheClusterId
  host: Endpoint.Address
```

### 4. Command (The Alias)
Defines the executable command, its structure, and arguments.

```yaml
---
type: command
name: PostgreSQL Client
alias: pg $${database_servers.name} # Uses dynamic variable
command: psql -h $${database_servers.host} ...
helper: |
    Connects to a database.
args:
  - alias: -o ${filename} # Argument with user variable
    command: -o ${filename}
    helper: Output to file
sub:
  - alias: file ${filename} # Subcommand
    command: -f ${filename}
```

## Application Behavior

### Autocomplete & Navigation
*   **Smart Suggestions**: As you type, `shoco` dynamically suggests commands, subcommands, and arguments.
*   **Menu Navigation**:
    *   **Tab**: Opens the completion menu or cycles through options.
    *   **Enter**: Selects the highlighted option from the menu. If no menu is open, it executes the command.
*   **Clean Interface**: To keep the interface uncluttered, placeholders for user variables (like `${filename}`) are not suggested in the menu. Simply type your value, and autocomplete will resume for the next argument.

### Dynamic Data Caching
To ensure speed, data fetched from external commands (Dynamic Dicts) is cached locally (default: `~/.shoco.json`). This cache is updated automatically, so your autocomplete remains fast even with complex data sources.

### Context-Aware Resolution
When you select an item from a dynamic list (e.g., a database name), `shoco` intelligently resolves all associated properties (like host IP, port, or user) for that specific item, ensuring your command executes with the correct context every time.

## Usage Example

1.  **Start the shell**:
    ```bash
    python short_command.py
    ```
2.  **Type a command**:
    ```text
    shoco > pg db1 -o my_output.txt
    ```
    -   `pg` triggers the alias.
    -   `db1` is autocompleted from your `database_servers` list.
    -   `-o` is an optional argument.
    -   `my_output.txt` is the value for `${filename}`.

## Installation

```bash
pip install prompt_toolkit pyyaml
```
