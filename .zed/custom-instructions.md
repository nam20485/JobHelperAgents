# Zed Agent Rules

<rule "id"="rule-format" "use"="mandatory">
  <description>XML rule format standard</description>
  <content>
All rules MUST use this format:

```
<rule "id"="kebab-case-id" "use"="mandatory|optional" ["context"="when-to-use"]>
  <description>One-line summary</description>
  <content>Rule details here</content>
</rule>
```

**Attributes:**
- `id` (required): Kebab-case unique identifier
- `use` (required): `mandatory` or `optional`
- `context` (required for optional rules): When/why this rule applies

**Elements:**
- `<description>`: Brief one-liner
- `<content>`: Detailed rule body

**Rules:**
1. Mandatory rules always apply; optional rules apply only when their context matches
2. Use kebab-case for all rule IDs
3. Both elements required for every rule
4. Minimize verbosity to reduce token overhead
  </content>
</rule>

<rule "id"="read-custom-instructions" "use"="mandatory">
  <description>Read custom-instructions.md for project rules before acting</description>
  <content>
Before acting, read entire .zed/custom-instructions.md file for project-specific rules. Include relevant rule content in completions.
  </content>
</rule>

<rule "id"="examples-external" "use"="mandatory">
  <description>Store examples in external files, not in rule content</description>
  <content>
Never embed static examples in rule content. Instead:
1. Create .zed/examples/<example-kind>.md file
2. Add examples there with full context
3. Reference file with markdown link in rule content
This reduces rule token overhead and keeps examples maintainable.
  </content>
</rule>

<rule "id"="compress-rules-strategy" "use"="mandatory">
  <description>Compress rules and detect redundancy to minimize tokens</description>
  <content>
When editing or reviewing rule files:
1. Run compress-rules.py to identify redundancy before adding rules
2. Remove verbose explanations; keep only actionable directives
3. Use bullet points instead of paragraphs
4. Move examples to .zed/examples/<kind>.md files with links
5. Consolidate repeated phrases into meta-rules with @rule references
6. Target: 80% size reduction + zero redundant content
7. Run via: task: spawn → compress-rules tasks, or python .zed/scripts/compress-rules.py . --redundancy
  </content>
</rule>

<rule "id"="use-sequential-thinking" "use"="mandatory">
  <description>Use sequential thinking for complex tasks</description>
  <content>
For non-trivial requests (>2-3 replies), use sequential-thinking MCP tools to plan approach. Err on side of using when in doubt.
  </content>
</rule>

<rule "id"="emoji-prefix" "use"="mandatory">
  <description>Prefix responses with animal and fire hydrant emoji</description>
  <content>
Start every response with one animal emoji and fire hydrant emoji (🔴).
  </content>
</rule>

<rule "id"="zed-official-rules" "use"="optional" "context"="adding rules to Zed IDE">
  <description>Add rules only to Zed's official library</description>
  <content>
When adding rules to Zed IDE, reference official Zed docs and only use Zed's official rules library, not custom files.
  </content>
</rule>

<rule "id"="check-zed-docs" "use"="optional" "context"="IDE features, configuration, functionality">
  <description>Check Zed docs for IDE-related questions</description>
  <content>
1. Check https://zed.dev/docs first for IDE features/config
2. Search docs site before answering
3. Reference settings.json docs for config
4. Check Agent Settings/Rules sections
5. Web search if needed (include "zed ide" in query)
6. Prefer official Zed docs; don't invent functionality
  </content>
</rule>