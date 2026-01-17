---
trigger: always_on
---

If dya --help must list available commands with its description only.
To separate command, just break line, without separator like '---------------'

Helper Custom Template Rules
# Custom Template root command helper
# Displays a lista of concatenated helpers if dya command --help so only selected command helper, or subcommand helper if command sub --help, or args helper if command [sub] --arg --help
# Displays only whats matched
# "..." means sequence rolling out

Helper Auto Template Rules

# Auto Template root command helper
# Line limited to 80 columns and must break line if reach it and start again from position 0
# This template is recursive and must show selected command helper and its children, if subcommand, so must display subcommand helper and its children, or if args helper, must display only selected args helper.
# "..." means sequence rolling out
<root command alias>

    Description:
        <root command helper>

    Usage:
        <root command alias>

    Args:
        # When alias is a single string: display as-is
        # When alias is an array: combine with comma, e.g. "-o, --output ${filename}"
        <root args alias 1>                <root command args 1 helper>
        <root args alias ...>              <root command args ... helper> # helper must be align with above helper init. must be dynamic spaces count with max of 20 spaces and min of 2.

    Options/Subcommands:
        <root subcommand1 alias 1>

            Description:
                <root subcommand1 helper 1>

            Args:
                <subcommand1 args alias 1>            <subcommand1 args 1 helper>
                <subcommand1 args alias ...>          <subcommand1 args ... helper>

            <root subcommand... alias ...>
            <root subcommand... helper ...>

            Args:
                <subcommand... args alias 1>          <subcommand... args 1 helper>
                <subcommand... args alias ...>        <subcommand... args ... helper>
            
            Options/Subcommands: # Subcommands can be recursive repeating same structure
                <subcommand... subcommand1 alias 1>

                    Description:
                        <subcommand... subcommand1 helper 1>

                    Args:
                        <subcommand... subcommand1 args alias 1>          <subcommand... subcommand1 args 1 helper>
                        <subcommand... subcommand1 args alias ...>        <subcommand... subcommand1 args ... helper>

                    <subcommand... subcommand... alias 1>
                    <subcommand... subcommand... helper ...>

                    Args:
                        <subcommand... subcommand... args alias 1>          <subcommand... subcommand... args 1 helper>
                        <subcommand... subcommand... args alias ...>        <subcommand... subcommand... args ... helper>

                    Options/Subcommands: # Subcommands can be recursive repeating same structure
                        ...