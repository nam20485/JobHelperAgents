# Rule Format Examples

## Mandatory Rule Example

```xml
<rule "id"="code-quality" "use"="mandatory">
  <description>Enforce consistent code quality standards</description>
  <content>
When generating or reviewing code:
- Follow language idioms and conventions
- Include error handling
- Add comments for complex logic
- Minimize code duplication
- Ensure type safety where applicable
  </content>
</rule>
```

## Optional Rule with Context

```xml
<rule "id"="rust-best-practices" "use"="optional" "context"="Rust development">
  <description>Apply Rust-specific safety and performance best practices</description>
  <content>
When working with Rust code:
- Prefer borrowing over unnecessary cloning
- Use Result/Option for error handling
- Leverage type system for compile-time guarantees
- Consider performance implications of abstractions
- Use cargo clippy recommendations
  </content>
</rule>
```

## Minimal Rule (Compressed Format)

```xml
<rule "id"="docs-first" "use"="optional" "context"="documentation tasks">
  <description>Documentation-first approach for API design</description>
  <content>
1. Write docs before implementation
2. Include usage examples
3. Document edge cases and limitations
4. Keep examples in separate .md files
  </content>
</rule>
```

## Rule with External Examples Reference

```xml
<rule "id"="testing-standards" "use"="mandatory">
  <description>Standardized testing practices</description>
  <content>
Write tests for all public APIs. Follow patterns in [testing examples](../examples/test-patterns.md).
- Aim for 80%+ coverage
- Test happy path and error cases
- Use descriptive test names
  </content>
</rule>
```
