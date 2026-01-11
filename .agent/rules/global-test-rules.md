---
trigger: always_on
---

Global Test Rules
These rules must be applied to every test file.
1. Create a test for every pattern present in @config-file-rules.md
2. Create tests for subs and args
3. Create multiple tests for every pattern
4. Create and use ./tests/dya.yaml as configuration file with --dya-config
5. Use .tests/dya.json as cache file and use with --dya-cache