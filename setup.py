import re
from setuptools import setup

def get_config_value(section, key, default):
    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Find section
        section_match = re.search(f'^\\[{section}\\]', content, re.MULTILINE)
        if not section_match:
            return default
            
        # Find key in content after section
        start = section_match.end()
        # Find next section or end of file
        next_section = re.search(r'^\[', content[start:], re.MULTILINE)
        end = start + next_section.start() if next_section else len(content)
        
        section_content = content[start:end]
        
        # Find key
        key_match = re.search(f'^{key}\\s*=\\s*["\']([^"\']+)["\']', section_content, re.MULTILINE)
        if key_match:
            return key_match.group(1)
            
    except Exception:
        pass
    return default

CUSTOM_SHORTCUT = get_config_value("custom-build", "shortcut", "dya")
CUSTOM_NAME = get_config_value("custom-build", "name", "DYNAMIC ALIAS")

# Setup entry points based on parsed config

setup(
    entry_points={
        "console_scripts": [
            f"{CUSTOM_SHORTCUT} = dynamic_alias.main:main",
        ],
    },
)