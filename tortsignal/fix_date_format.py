"""Fix FDA date format in all connectors."""

import re

files_to_fix = [
    'src/connectors/faers.py',
    'src/connectors/maude.py',
]

def fix_file(filepath):
    """Fix date format in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # Pattern 1: %Y%m%d format with +TO+
    content = re.sub(
        r"strftime\('%Y%m%d'\)\}\+TO\+\{([^.]+)\.strftime\('%Y%m%d'\)",
        r"strftime('%Y-%m-%d')} TO {\1.strftime('%Y-%m-%d')",
        content
    )

    # Pattern 2: %Y-%m-%d format but with +TO+
    content = re.sub(
        r"strftime\('%Y-%m-%d'\)\}\+TO\+\{([^.]+)\.strftime\('%Y-%m-%d'\)",
        r"strftime('%Y-%m-%d')} TO {\1.strftime('%Y-%m-%d')",
        content
    )

    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✓ Fixed {filepath}")

        # Count changes
        old_lines = original.count("+TO+")
        new_lines = content.count(" TO ")
        print(f"  Changed {old_lines} date ranges")
    else:
        print(f"  No changes needed in {filepath}")

print("Fixing FDA date format in connectors...")
print("="*60)

for filepath in files_to_fix:
    fix_file(filepath)

print("="*60)
print("Done!")
