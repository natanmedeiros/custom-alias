# Interactive Mode

Launch the interactive shell for autocomplete and history navigation.

## Starting the Shell

```bash
dya
```

You'll see:
```
dya> (tab for menu)
```

## Autocomplete

Press **Tab** to see available completions:

```
dya> <TAB>
      hello
      ssh
      pg
      k
```

### Smart Completion

Autocomplete works at every level:

```
dya> ssh <TAB>
          prod
          staging
          dev

dya> k get <TAB>
            pods
            services
            deployments
```

### Dynamic Data

Dynamic dict values are autocompleted:

```
dya> pg <TAB>
          production
          staging
          analytics
```

## History Navigation

Use arrow keys to navigate command history:

| Key | Action |
|-----|--------|
| ↑ (Up) | Previous command |
| ↓ (Down) | Next command |

History persists across sessions in the cache file.

## Styling

Customize the appearance:

```yaml
config:
  style-completion: "bg:#008888 #ffffff"
  style-completion-current: "bg:#00aaaa #000000"
  style-scrollbar-background: "bg:#88aaaa"
  style-scrollbar-button: "bg:#222222"
  style-placeholder-color: "gray"
  style-placeholder-text: "(type command)"
```

## Help

Get help at any point:

```
dya> -h
# Shows global help with all dicts and commands

dya> ssh -h
# Shows help for 'ssh' command
```

## Exiting

Exit the shell:

```
dya> exit
# or press Ctrl+C / Ctrl+D
```

## Non-Interactive Execution

Run commands directly without entering the shell:

```bash
dya ssh prod
dya pg production
dya k get pods
```

The command executes and returns to your normal shell.

---

| ← Previous | Next → |
|:-----------|-------:|
| [Features](features.md) | [Examples](examples/) |
