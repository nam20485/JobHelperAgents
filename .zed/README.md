# Zed Agent Rules System

## Overview

This directory contains the Agno project's Zed Agent rules infrastructure, optimized for **minimal token usage** and **redundancy elimination**. Rules guide AI agent behavior while consuming the least possible context.

## Key Files

- **`custom-instructions.md`** - Authoritative rule definitions. Always read before tasks.
- **`tasks.json`** - Zed tasks for automation, including the compress-rules tool
- **`scripts/compress-rules.py`** - Script to compress rules AND detect/report redundancy
- **`examples/`** - External example files referenced by rules (not stored in rule content)

## Rule Format

All rules use standardized XML notation. See `examples/rule-format-examples.md` for examples.

### Quick Format
```xml
<rule "id"="rule-id" "use"="mandatory|optional" ["context"="when-applies"]>
  <description>One-line summary</description>
  <content>
Detailed directives and instructions
  </content>
</rule>
```

### Attributes
- **`id`**: Unique kebab-case identifier (required)
- **`use`**: `mandatory` (always apply) or `optional` (apply when context matches)
- **`context`**: Required for optional rules; describes applicability

## Using Rules

### In Zed Agent
- Mandatory rules apply automatically to all interactions
- Reference optional rules with: `@rule rule-id-name`
- Stack multiple rules: `@rule rule-1 @rule rule-2`

### Running Tasks
1. Open command palette: `Cmd+Shift+P` / `Ctrl+Shift+P`
2. Type `task: spawn`
3. Select desired task:
   - **compress-rules: Current File** - Compress active file
   - **compress-rules: All Rules** - Compress all rule files

## Compress-Rules Tool

The `compress-rules.py` script both **compresses** and **detects redundancy** to minimize token usage.

### Compression: What It Does
- Removes verbose phrases ("should be", "it is recommended that", etc.)
- Eliminates excessive whitespace
- Maintains all essential meaning and directives
- Typically achieves **70-80% size reduction**

### Redundancy Detection: What It Does
- Identifies repeated phrases across rules (>1 occurrence)
- Finds conceptual overlaps (e.g., multiple "mandatory" enforcement rules)
- Suggests consolidation strategies (e.g., create a meta-rule to reference)
- Proposes reducing duplication via links instead of repetition
- **Does NOT modify files** - only reports opportunities

### Usage

**Compress files:**
```bash
# Via task (recommended)
task: spawn → compress-rules: Current File
task: spawn → compress-rules: All Rules

# Via CLI
python .zed/scripts/compress-rules.py .zed/custom-instructions.md
python .zed/scripts/compress-rules.py .
```

**Analyze redundancy (report only, no modifications):**
```bash
python .zed/scripts/compress-rules.py .zed/custom-instructions.md --redundancy
python .zed/scripts/compress-rules.py . --redundancy
```

### Redundancy Detection Strategy

The tool analyzes rules for:

1. **Repeated Phrases** - Exact phrases appearing in multiple rules
   - Shows token savings if consolidated
   - Suggests consolidating into a single authoritative rule with references

2. **Concept Overlaps** - Multiple rules addressing similar topics
   - Groups by concept (mandatory enforcement, external references, etc.)
   - Recommends meta-rules to consolidate cross-cutting concerns
   - Suggests using `@rule` cross-references to avoid duplication

3. **Consolidation Opportunities** - Specific recommendations
   - "Consolidate Mandatory": Multiple enforcement rules → core-enforcement meta-rule
   - "Consolidate References": Multiple external file refs → shared index rule
   - "Extract Common Directives": Repeated patterns → separate reference rule

### Output Example

```
✓ .zed/custom-instructions.md
  Rules: 10
  Size: 3,427 → 2,891 bytes (15.6% reduction)

📊 Redundancy Analysis: .zed/custom-instructions.md

  Repeated Phrases (3 found):
    • [4 tokens] 'reference official Zed docs' in: check-zed-docs, zed-official-rules
    • [2 tokens] 'external files' in: examples-external, compress-rules-strategy

  Concept Overlaps (2 found):
    • mandatory: rule-format, read-custom-instructions, examples-external, use-sequential-thinking, emoji-prefix
    • external_ref: examples-external, compress-rules, check-zed-docs

  Consolidation Opportunities:
    • consolidate_mandatory: Multiple mandatory enforcement rules
      Affected: rule-format, read-custom-instructions, use-sequential-thinking
      Suggestion: Create "core-enforcement" rule referencing common patterns
```

## Best Practices: Compression & Redundancy Prevention

### Compression
1. **Minimize Examples**: Store in `examples/` directory with markdown links
2. **Use Bullet Points**: Over paragraphs or full sentences
3. **Abbreviate Clearly**: "config" for configuration, "ref" for reference
4. **Link Instead of Repeat**: Use `[see X](../examples/x.md)` instead of duplicating
5. **Remove Redundant Words**: "required", "mandatory", "should" often unnecessary

### Redundancy Prevention
1. **Check Before Adding**: Run `--redundancy` flag before adding new rules
2. **Consolidate Early**: If >2 rules share concepts, create a meta-rule
3. **Use Cross-References**: `@rule other-rule-id` instead of repeating content
4. **Extract Common Patterns**: Move shared directives to dedicated rule
5. **Regular Audits**: Run compress-rules monthly to identify new redundancy

### ID Naming
- Use kebab-case (lowercase-with-hyphens)
- Be descriptive: `python-type-hints`, `compression-strategy`
- Avoid generic: Don't use `rule-1`, `my-rule`

## Context Efficiency Philosophy

Rules accumulate over time. Every rule consumes tokens. To stay efficient:

**❌ Avoid:**
- Lengthy explanations and verbose phrasing
- Repeated examples (use links instead)
- Duplicate concepts across multiple rules
- Prose-style content when directives work

**✅ Do:**
- Bullet points and concise directives
- Links to external examples
- Consolidate similar topics into meta-rules
- Use `@rule` references for cross-cutting concerns

**Example Compression:**
```
Before (89 chars):
"It is recommended that you should use type hints in all Python function definitions"

After (45 chars):
"Use type hints in all Python function definitions"

Redundancy Prevention:
Before: 3 separate rules about "checking external resources"
After: 1 meta-rule "verify-external-docs" with @rule references in 3 specific rules
```

## Adding New Rules

1. Edit `.zed/custom-instructions.md`
2. Follow XML format (see `examples/rule-format-examples.md`)
3. Use `"use"="mandatory"` for always-apply rules
4. Use `"use"="optional" "context"="..."` for conditional rules
5. Keep `<content>` concise; link to examples via markdown
6. Run `compress-rules.py --redundancy .zed/custom-instructions.md` to check for duplication
7. If redundancy found, consolidate or add `@rule` cross-references
8. Run `compress-rules.py .zed/custom-instructions.md` to compress before committing

## Directory Structure

```
.zed/
├── README.md                          # This file
├── tasks.json                         # Zed automation tasks
├── custom-instructions.md             # Authoritative rules file
├── scripts/
│   └── compress-rules.py              # Compression + redundancy detection
└── examples/
    ├── rule-format-examples.md        # Format reference examples
    ├── [other-examples].md            # Domain-specific examples
```

## Workflow Summary

1. **Adding Rules**: Edit `custom-instructions.md`
2. **Check Redundancy**: `python scripts/compress-rules.py . --redundancy`
3. **Review Report**: Check for repeated phrases and concept overlaps
4. **Consolidate**: Create meta-rules or add `@rule` cross-references
5. **Compress**: `python scripts/compress-rules.py .`
6. **Verify**: Check file size reduction and rule integrity
7. **Commit**: Push changes with compression stats

## See Also

- `custom-instructions.md` - Authoritative rules file
- `examples/rule-format-examples.md` - Format reference with examples
- Zed Docs: https://zed.dev/docs
- Zed Rules Guide: https://zed.dev/docs/ai/rules