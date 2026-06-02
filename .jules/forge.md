## 2026-06-03 - [Policy Inheritance Tracking Pattern]
**Learning:** In hierarchical policy systems (Global > Org > Repo), mere resolution of the effective value is insufficient for administrative transparency. Users need to know the 'Lineage' of a rule to avoid confusion when local changes are ignored due to higher-level overrides or vice-versa.
**Action:** When implementing hierarchical stores, always return a parallel 'sources' metadata object alongside the 'values' object to enable frontend decorators (badges/labels).

## 2026-06-03 - [Bash Session EOF Safety]
**Learning:** Using `cat <<EOF` in a bash session to write Python code can lead to silent or loud syntax errors if the code contains backslashes or other shell-special characters that are interpreted before writing.
**Action:** Always use `cat <<'EOF'` (quoted heredoc) when writing source code files to a sandbox via bash to ensure the content is written literally.
