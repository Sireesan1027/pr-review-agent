from langchain_core.tools import tool

SECURITY_PROMPT = """You are a security engineer conducting a focused security review.
Analyze the code changes in the diff below for security vulnerabilities.

Check for:
- Injection risks: SQL injection, command injection, LDAP injection, XPath injection
- XSS: unescaped user input rendered to HTML, missing Content-Security-Policy
- Hardcoded secrets: API keys, passwords, tokens, private keys in code
- Authentication/Authorization: missing auth checks, insecure direct object references (IDOR)
- Insecure deserialization: pickle.loads, YAML.load without Loader, ObjectInputStream
- Cryptography: weak algorithms (MD5, SHA1, DES), hardcoded IVs/salts, ECB mode
- Path traversal: user-controlled file paths without sanitization
- SSRF: user-controlled URLs fetched server-side without allowlist
- Dependency risks: known-vulnerable packages, unpinned dependencies
- Logging sensitive data: passwords, tokens, PII in log statements

Rate each finding: CRITICAL / HIGH / MEDIUM / LOW.
Reference exact file names and line numbers.
If no issues found, write "No security issues found."

---DIFF---
{diff}
---END DIFF---"""


@tool
def security_scanner(diff: str) -> str:
    """Run a security-focused review on a code diff.

    Checks for OWASP Top 10 vulnerabilities, hardcoded secrets, injection risks,
    weak cryptography, and other security issues.

    Args:
        diff: Unified diff string containing the code changes.

    Returns:
        Security review with severity ratings and specific findings.
    """
    return SECURITY_PROMPT.format(diff=diff)
