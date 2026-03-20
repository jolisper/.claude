# Sensitive Data Patterns

## Hardcoded secrets & credentials

Look at every `+` line in the diff for:

| Category | Patterns to detect |
|---|---|
| Private keys / certs | `-----BEGIN ... PRIVATE KEY-----`, `-----BEGIN CERTIFICATE-----` |
| API keys & tokens | assignments like `api_key=`, `token=`, `auth_token=`, `access_token=` with a non-trivial value (≥8 chars, not a placeholder like `<your-key>`) |
| Passwords in config | `password=`, `passwd=`, `pwd=` with a non-empty, non-placeholder value |
| AWS credentials | `AKIA[0-9A-Z]{16}`, `aws_secret_access_key` |
| Generic secrets | `secret=`, `client_secret=`, `private_key=` with a real value |
| Connection strings | URIs with embedded credentials: `://user:password@`, `postgres://`, `mysql://`, `mongodb://` containing a password segment |
| `.env` files | any file named `.env`, `.env.local`, `.env.production`, `.env.*` |
| SSH private key files | files named `id_rsa`, `id_ed25519`, `id_ecdsa`, or inside `.ssh/` |

## Sensitive file types

Check the filenames listed in the diff header lines (`diff --git a/... b/...`). Flag any staged file whose name matches:

- `*.key`, `*.pem`, `*.crt`, `*.p12`, `*.pfx`, `*.jks`, `*.token`, `*.txt`
- `output.json`, `credentials.json`, `secrets.yaml`, `secrets.json`
- `*.sql`, `*.csv`, `*.dump` — when it is a new file (first commit of this path)
- Any file whose entire added content is a single long string (≥32 chars, no whitespace) — likely a raw key or token written by a script

## Warning block format

When sensitive data is found, show this block **before asking anything else**:

```
⚠️  SENSITIVE DATA DETECTED — do not commit

The staged diff contains what appears to be sensitive or private data:

  • <file>:<line> — <category>: "<redacted excerpt — first 6 chars + …>"

Committing secrets or real data exposes them in git history permanently,
even after a later removal commit.

Options:
  (a) Unstage the affected file / hunk and continue without it
  (b) Replace the value with an environment variable or config reference
  (c) Add the file to .gitignore and unstage it
  (d) Abort and handle manually

What would you like to do?
```
