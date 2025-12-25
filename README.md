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

## Rules and Behaviors

The application strictly follows a set of defined rules for consistency and reliability.

### General Rules
1.  **Configuration**: Must strictly follow `shoco.yaml` criteria.
2.  **Architecture**: Based on `minha_cli_example_do_not_alter.py` reference, applying SOLID principles.
3.  **Caching**:
    -   If enabled, dynamic dicts are cached to `~/.shoco.json`.
    -   Cache is imported at startup and exported after execution.
4.  **Interactive Mode**: `shoco` provides an interactive shell with autocomplete.

### Autocomplete Rules
1.  **Dynamic Evaluation**: Autocomplete is re-evaluated dynamically after every character typed or deleted.
2.  **Navigation behavior** (Rule 13):
    -   **Menu Visible**: `Tab` and `Enter` complete the selected word.
    -   **Menu Hidden**: `Enter` executes the command.
3.  **Argument Handling**:
    -   **Resumption**: Autocomplete continues working for commands/arguments *after* an argument is used (Rule 4.19).
    -   **Suppression** (Rule 4.18, 4.20): User variables (e.g., `${filename}`) are **NOT** suggested in the autocomplete menu. Only flags and static/dynamic values are suggested. Hint text for variables is suppressed to keep the UI clean.

### Execution Logic
1.  **Variable Resolution**:
    -   When you select a value for a dynamic variable (e.g., `db1` for `$${database_servers.name}`), the application resolves all related keys (like host, port) from that distinct item in the list.
    -   If you use the 2nd item's name, it ensures the 2nd item's host is used.

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
