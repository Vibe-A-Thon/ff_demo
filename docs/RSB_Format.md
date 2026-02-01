# RSB Format and Merge Rules

## Package Structure
RSB archives are ZIP files containing the following structure:

- manifest.json
- rule/specification.json
- rule/rule.json
- rule/description.md
- rule/rule_Patch.py
- code/ruleC_<RULE_ID>.py
- code/ruleCP_<RULE_ID>.py (optional)
- tests/ruleUT_*.py
- tests/ruleIT_*.py
- compliance/* (optional)

## Validation Rules
- Manifest must include rule_id, name, rule_version, and attack_type.
- RuleSpec and RuleDefinition must match the manifest rule_id.
- A core implementation file is required under code/ruleC_*.py.

## Merge Rules
- Merges require conflict resolution when rule_id collisions are detected.
- A package must pass validation before merge.
- Merge creates a patched archive with updated rule_version.

## Patch Application
- Accepted patches update the rule_spec with patch_notes.
- Rejected patches keep existing code and rule_spec.
- Patched archives are stored with _patched suffix.
