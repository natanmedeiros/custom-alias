"""
Helper Formatter Module

Implements two helper formatting strategies:
- AutoHelperFormatter: Recursive format with Description, Args, Options/Subcommands (80 col limit)
- CustomHelperFormatter: Concatenates raw helper text from matched chain

Only affects command-specific help (dya command -h).
Global help (dya -h) remains unchanged.
"""
from abc import ABC, abstractmethod
from typing import List, Union
from .models import CommandConfig, SubCommand, ArgConfig


MAX_LINE_WIDTH = 80
MIN_SPACING = 2
MAX_SPACING = 20


class HelperFormatter(ABC):
    """Abstract base class for helper formatting strategies."""
    
    @abstractmethod
    def format(self, command_chain: List[Union[CommandConfig, SubCommand, ArgConfig]]) -> str:
        """Format helper output for the command chain."""
        pass


class CustomHelperFormatter(HelperFormatter):
    """
    Concatenates raw helper text from matched command chain.
    Displays only what's explicitly defined in each command's helper field.
    """
    
    def format(self, command_chain: List[Union[CommandConfig, SubCommand, ArgConfig]]) -> str:
        lines = []
        
        for obj in command_chain:
            if obj.helper:
                lines.append(obj.helper.strip())
        
        if not lines:
            return "No helper information available for this command."
        
        return "\n\n".join(lines)


class AutoHelperFormatter(HelperFormatter):
    """
    Recursive format with Description, Args, Options/Subcommands sections.
    80 column limit with line wrapping.
    """
    
    def format(self, command_chain: List[Union[CommandConfig, SubCommand, ArgConfig]]) -> str:
        lines = []
        
        # Get the root command and the matched target
        root = command_chain[0] if command_chain else None
        target = command_chain[-1] if command_chain else None
        
        if not root:
            return "No helper information available for this command."
        
        # Build matched path from command chain (excludes ArgConfig entries)
        matched_path = self._build_matched_path(command_chain)
        
        # Alias first (no indent) - just the matched path for the header
        lines.append(matched_path)
        lines.append("")
        
        # Description section (4 spaces indent, content 8 spaces)
        lines.append("    Description:")
        if target.helper:
            for line in target.helper.strip().split('\n'):
                lines.append(f"        {line}")
        else:
            lines.append("        No description available.")
        lines.append("")
        
        # Usage section with full dynamic string
        lines.append("    Usage:")
        usage_string = self._build_usage_string(command_chain)
        lines.append(f"        {usage_string}")
        
        # Args section for the target (4 spaces indent, content 8 spaces)
        if hasattr(target, 'args') and target.args:
            lines.append("")
            lines.append("    Args:")
            for arg in target.args:
                lines.extend(self._format_arg(arg, indent=8))
        
        # Options/Subcommands section for the target (4 spaces indent)
        if hasattr(target, 'sub') and target.sub:
            lines.append("")
            lines.append("    Options/Subcommands:")
            for sub in target.sub:
                lines.extend(self._format_subcommand(sub, indent=8, matched_path_prefix=matched_path))
        
        return '\n'.join(lines)
    
    def _build_matched_path(self, command_chain: List[Union[CommandConfig, SubCommand, ArgConfig]]) -> str:
        """Build the matched path from command chain (commands and subs only)."""
        parts = []
        for obj in command_chain:
            if isinstance(obj, (CommandConfig, SubCommand)):
                parts.append(obj.alias)
        return ' '.join(parts)
    
    def _build_usage_string(self, command_chain: List[Union[CommandConfig, SubCommand, ArgConfig]]) -> str:
        """Build dynamic usage string: matched path + optional args/subs in brackets."""
        # Build matched path
        matched_parts = []
        for obj in command_chain:
            if isinstance(obj, (CommandConfig, SubCommand)):
                matched_parts.append(obj.alias)
        
        # Get the target (last non-ArgConfig in chain)
        target = None
        for obj in reversed(command_chain):
            if isinstance(obj, (CommandConfig, SubCommand)):
                target = obj
                break
        
        if not target:
            return ' '.join(matched_parts)
        
        # Build optional section for target's args and subs
        optional_section = self._build_optional_section(target)
        
        if optional_section:
            return f"{' '.join(matched_parts)} {optional_section}"
        return ' '.join(matched_parts)
    
    def _build_optional_section(self, obj: Union[CommandConfig, SubCommand]) -> str:
        """Build optional args and subs in bracket format recursively."""
        parts = []
        
        # Add args first: [arg1 | arg2 | ...]
        if hasattr(obj, 'args') and obj.args:
            arg_flags = []
            for arg in obj.args:
                arg_flags.extend(self._get_arg_flags(arg))
            if arg_flags:
                parts.append(f"[{' | '.join(arg_flags)}]")
        
        # Add subs: [sub1 [...] | sub2 [...] | ...]
        if hasattr(obj, 'sub') and obj.sub:
            sub_parts = []
            for sub in obj.sub:
                sub_optional = self._build_optional_section(sub)
                if sub_optional:
                    sub_parts.append(f"{sub.alias} {sub_optional}")
                else:
                    sub_parts.append(sub.alias)
            if sub_parts:
                parts.append(f"[{' | '.join(sub_parts)}]")
        
        return ' '.join(parts)
    
    def _get_arg_flags(self, arg: ArgConfig) -> List[str]:
        """Get flag-only parts from arg alias (without variables)."""
        if isinstance(arg.alias, list):
            # For array aliases, get short flags only
            flags = []
            for alias in arg.alias:
                flag = alias.split()[0] if alias else alias
                flags.append(flag)
            return flags
        else:
            # Single alias
            flag = arg.alias.split()[0] if arg.alias else arg.alias
            return [flag]
    
    def _get_alias_display(self, obj: Union[CommandConfig, SubCommand, ArgConfig]) -> str:
        """Get display string for alias (handles array format)."""
        if isinstance(obj, ArgConfig) and isinstance(obj.alias, list):
            # Combine array aliases: e.g., "-o, --output ${filename}"
            return ", ".join(self._strip_vars_prefix(a) for a in obj.alias)
        return obj.alias
    
    def _strip_vars_prefix(self, alias: str) -> str:
        """Extract just the flag prefix without variables for display."""
        parts = alias.split()
        if parts:
            return parts[0]
        return alias
    
    def _format_arg(self, arg: ArgConfig, indent: int) -> List[str]:
        """Format a single argument with proper spacing."""
        lines = []
        prefix = " " * indent
        
        alias_display = self._get_alias_display(arg)
        helper_text = arg.helper.strip() if arg.helper else ""
        
        # Calculate spacing (min 2, max 20)
        spacing = max(MIN_SPACING, MAX_SPACING - len(alias_display))
        spacing = min(spacing, MAX_SPACING)
        
        # Format with alignment
        if helper_text:
            line = f"{prefix}{alias_display}{' ' * spacing}{helper_text}"
            # Wrap if exceeds max width
            if len(line) > MAX_LINE_WIDTH:
                lines.append(f"{prefix}{alias_display}")
                lines.append(f"{prefix}    {helper_text}")
            else:
                lines.append(line)
        else:
            lines.append(f"{prefix}{alias_display}")
        
        return lines
    
    def _format_subcommand(self, sub: SubCommand, indent: int, matched_path_prefix: str = "") -> List[str]:
        """Format a subcommand with its args and nested subs."""
        lines = []
        prefix = " " * indent
        prefix_inner = " " * (indent + 4)
        
        # Build full path for this subcommand
        full_path = f"{matched_path_prefix} {sub.alias}" if matched_path_prefix else sub.alias
        
        # Alias first at base indent
        lines.append(f"{prefix}{sub.alias}")
        lines.append("")
        
        # Description section (indent +4, content +8)
        lines.append(f"{prefix_inner}Description:")
        if sub.helper:
            for line in sub.helper.strip().split('\n'):
                lines.append(f"{prefix_inner}    {line}")
        else:
            lines.append(f"{prefix_inner}    No description available.")
        lines.append("")
        
        # Usage section with full matched path + optional args/subs
        lines.append(f"{prefix_inner}Usage:")
        optional_section = self._build_optional_section(sub)
        if optional_section:
            lines.append(f"{prefix_inner}    {full_path} {optional_section}")
        else:
            lines.append(f"{prefix_inner}    {full_path}")
        
        # Subcommand args (indent +4, content +8)
        if sub.args:
            lines.append("")
            lines.append(f"{prefix_inner}Args:")
            for arg in sub.args:
                lines.extend(self._format_arg(arg, indent + 8))
        
        # Nested subcommands (indent +4)
        if sub.sub:
            lines.append("")
            lines.append(f"{prefix_inner}Options/Subcommands:")
            for nested in sub.sub:
                lines.extend(self._format_subcommand(nested, indent + 8, matched_path_prefix=full_path))
        
        lines.append("")  # Blank line between subs
        return lines


def get_helper_formatter(helper_type: str = "auto") -> HelperFormatter:
    """Factory function to get the appropriate formatter based on helper_type."""
    if helper_type == "custom":
        return CustomHelperFormatter()
    return AutoHelperFormatter()

