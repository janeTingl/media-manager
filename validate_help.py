#!/usr/bin/env python3
"""Quick validation script for help center implementation."""

import json
import sys
from pathlib import Path

HELP_LOCALE = "zh-CN"


def validate_help_system():
    """Validate help system files and structure."""
    print("Validating Help Center Implementation...")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Check docs directory exists
    docs_path = Path(__file__).parent / "docs"
    if not docs_path.exists():
        errors.append("docs/ directory not found")
        return errors, warnings
    
    # Check Simplified Chinese locale
    locale_path = docs_path / HELP_LOCALE
    if not locale_path.exists():
        errors.append(f"docs/{HELP_LOCALE}/ directory not found")
        return errors, warnings
    
    print(f"✓ Documentation directory structure exists ({HELP_LOCALE})")
    
    # Check index file
    index_file = locale_path / "index.json"
    if not index_file.exists():
        errors.append(f"docs/{HELP_LOCALE}/index.json not found")
        return errors, warnings
    
    print("✓ Help index file exists")
    
    # Parse and validate index
    try:
        with open(index_file, encoding="utf-8") as f:
            index_data = json.load(f)
        
        # Check required fields
        if "topics" not in index_data:
            errors.append("index.json missing 'topics' field")
        if "title" not in index_data:
            warnings.append("index.json missing 'title' field")
        if "locale" not in index_data:
            warnings.append("index.json missing 'locale' field")
        
        print(f"✓ Help index is valid JSON with {len(index_data.get('topics', []))} topics")
        
        # Validate topics
        topics = index_data.get("topics", [])
        topic_files = set()
        
        for i, topic in enumerate(topics):
            # Check required fields
            if "id" not in topic:
                errors.append(f"Topic {i} missing 'id'")
            if "title" not in topic:
                errors.append(f"Topic {i} ({topic.get('id', 'unknown')}) missing 'title'")
            if "file" not in topic:
                errors.append(f"Topic {i} ({topic.get('id', 'unknown')}) missing 'file'")
            else:
                topic_file = locale_path / topic["file"]
                if not topic_file.exists():
                    errors.append(f"Help file not found: {topic['file']}")
                else:
                    topic_files.add(topic["file"])
            
            if "keywords" not in topic:
                warnings.append(f"Topic {topic.get('id', 'unknown')} missing 'keywords'")
        
        print(f"✓ All {len(topic_files)} topic files exist")
        
        # Check for broken internal links
        import re
        broken_links = []
        
        for topic in topics:
            if "file" not in topic:
                continue
            
            topic_file = locale_path / topic["file"]
            if not topic_file.exists():
                continue
            
            with open(topic_file, encoding="utf-8") as f:
                content = f.read()
            
            # Find href links
            links = re.findall(r'href="([^"]+)"', content)
            for link in links:
                # Skip external links
                if link.startswith("http"):
                    continue
                
                # Check if it's a topic link
                if link.endswith(".html"):
                    if link not in topic_files:
                        broken_links.append(f"{topic['file']} -> {link}")
        
        if broken_links:
            errors.append(f"Broken internal links found: {', '.join(broken_links)}")
        else:
            print("✓ No broken internal links detected")
        
    except json.JSONDecodeError as e:
        errors.append(f"index.json is not valid JSON: {e}")
    except Exception as e:
        errors.append(f"Error validating index: {e}")
    
    # Check Python files exist
    src_path = Path(__file__).parent / "src" / "media_manager"
    
    help_center_file = src_path / "help_center_dialog.py"
    if not help_center_file.exists():
        errors.append("help_center_dialog.py not found")
    else:
        print("✓ HelpCenterDialog implementation exists")
    
    onboarding_file = src_path / "onboarding_wizard.py"
    if not onboarding_file.exists():
        errors.append("onboarding_wizard.py not found")
    else:
        print("✓ OnboardingWizard implementation exists")
    
    test_file = Path(__file__).parent / "tests" / "test_help_center.py"
    if not test_file.exists():
        errors.append("test_help_center.py not found")
    else:
        print("✓ Help center tests exist")
    
    print("=" * 60)
    
    if errors:
        print(f"\n❌ {len(errors)} ERROR(S) FOUND:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} WARNING(S):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors:
        print("\n✅ All validation checks passed!")
        print("\nHelp system is ready to use:")
        print("  - Press F1 in the application for context help")
        print("  - Access Help → Help Center from the menu")
        print("  - First-run onboarding will show automatically")
    
    return errors, warnings


if __name__ == "__main__":
    errors, warnings = validate_help_system()
    sys.exit(1 if errors else 0)
