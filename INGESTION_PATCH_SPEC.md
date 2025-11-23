# Ingestion Patch Technical Specification

## Problem Statement
- **Baseline regression**: Goldminer ingestion lacks ftfy-style text repair, causing mojibake and mixed-encoding corruption in SMS payloads (Risk R01_MOJIBAKE).
- **Temporal ambiguity**: Parser does not infer missing years from file metadata, leading to historical timestamp drift (Risk R02_TIMESTAMP_DRIFT).
- **Negative classification gap**: Declined/OTP/Code messages are misclassified as monetary spends, creating false positives in reporting (Risk R03_FALSE_POSITIVES).
- **Operational constraint**: Do **not** decommission `sms_multi_bank_parser_v4.py` until all acceptance criteria pass end-to-end QA.

## Proposed Solution
### Phase 1: Text Repair Middleware
- Introduce a pre-processor that auto-detects mixed UTF-8/Windows-1252 and applies ftfy-equivalent normalization (e.g., `ftfy.fix_text` or ICU normalization) prior to regex parsing.
- Add unit tests with mojibake fixtures (e.g., curled quotes, mis-decoded currency symbols) and mixed Arabic/Latin strings to guarantee round-trip safety.
- Expose a toggle (`text_repair_enabled`) in config to allow gradual rollout; default **on** for SMS ingestion.

### Phase 2: Context-Aware Timestamp Inference
- Pass file creation/ingestion timestamps into the regex parsing context.
- When a date token lacks a year (e.g., `21/07`), infer the year using file creation date; fall back to ingestion time; allow override via CLI/loader parameter.
- Persist both `extracted_date_raw` and `resolved_date` to enable auditing, and add a QA check that flags when inferred year differs from creation year by > 1.

### Phase 3: Negative Classification Safeguards
- Extend regex templates with negative lookaheads and dedicated state flags for keywords: `Declined|Refused|OTP|Code` (case- and locale-aware).
- Route matches into a `transaction_state` field with enumerations: `MONETARY`, `PROMO`, `OTP`, `DECLINED`, `UNKNOWN`.
- Ensure `DECLINED`, `OTP`, and ambiguous `UNKNOWN` rows are excluded from `Total Expense` aggregation but retained for auditing.

### Shared Implementation Notes
- Keep deterministic override support (safe pattern maps/YAML) ahead of fuzzy resolution when both are present.
- Preserve idempotent SHA-256 row hashing; include `transaction_state` and `resolved_date` in the hash inputs to prevent drift when inference changes.
- Maintain backward compatibility with legacy exports (Flagged_Transactions.csv, dashboard sheets) by adding new columns rather than altering existing ones.

## Acceptance Criteria
- **AC1 – Text Repair**: Ingestion reports show zero mojibake for mixed-encoding fixtures; Arabic-Indic numerals and RTL/LTR strings parse without corruption.
- **AC2 – Timestamp Inference**: For fixtures with day/month only, `resolved_date` matches file creation year and surfaces an audit trail of the inference.
- **AC3 – Negative Classification**: Declined/OTP/Code messages are captured with `transaction_state` ≠ `MONETARY` and are excluded from expense totals.
- **AC4 – Determinism & Idempotency**: Re-ingesting the same file yields identical hashes and no duplicate records, even after inference logic is enabled.
- **AC5 – Compatibility**: Legacy dashboards and flagged transaction exports remain intact with added columns for `transaction_state`, `resolved_date`, and `text_repaired`.

## Code Logic Examples
- **Text repair pipeline**:
  ```python
  from ftfy import fix_text

  def repair_text(message: str, *, enabled: bool = True) -> str:
      if not enabled:
          return message
      return fix_text(message, normalization='NFC')
  ```
- **Timestamp resolution**:
  ```python
  def resolve_date(extracted_dt, file_created, ingested_at):
      if extracted_dt.year is None:
          inferred_year = file_created.year or ingested_at.year
          resolved = extracted_dt.replace(year=inferred_year)
      else:
          resolved = extracted_dt
      return resolved
  ```
- **Negative classification guard**:
  ```python
  NEGATIVE_KEYWORDS = re.compile(r"(declined|refused|otp|code)", re.I)

  def classify_state(message: str) -> str:
      if NEGATIVE_KEYWORDS.search(message):
          if "otp" in message.lower() or "code" in message.lower():
              return "OTP"
          return "DECLINED"
      return "MONETARY"
  ```
- **Hash stability including inference**:
  ```python
  def transaction_hash(tx):
      payload = f"{tx.resolved_date}|{tx.amount}|{tx.payee}|{tx.account_id}|{tx.transaction_state}"
      return hashlib.sha256(payload.encode("utf-8")).hexdigest()
  ```
