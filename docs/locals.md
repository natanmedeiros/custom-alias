
## Locals Management

Store and manage local variables in the cache for use in commands.

### Key Features
- **Persistence:** Locals are stored in the cache file (`_locals` key) and persist across sessions.
- **Substitution:** Use `$${locals.key}` in any command to access the value.
- **Management:** Flags to set and clear locals.

### Usage

1. **Set a local variable:**
   ```bash
   dya --dya-set-locals my_key "my value"
   # Output: Local variable set: my_key=my value
   ```

2. **Use in a command:**
   ```yaml
   command: echo "The value is $${locals.my_key}"
   ```

3. **Clear all locals:**
   ```bash
   dya --dya-clear-locals
   # Output: Local variables cleared
   ```

> [!NOTE]
> `locals` is a reserved built-in source. You do not need to define `locals` in your `dya.yaml` file.
