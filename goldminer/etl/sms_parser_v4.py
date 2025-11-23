"""SMS Multi-bank parser v4 with text repair and timestamp inference."""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:  # pragma: no cover - optional dependency
    from ftfy import fix_text
except Exception:  # pragma: no cover - optional dependency
    fix_text = None

from goldminer.analysis.regex_parser_engine import RegexParserEngine
from goldminer.etl.field_validator import FieldValidator
from goldminer.etl.schema_normalizer import SchemaNormalizer
from goldminer.etl.promo_classifier import PromoClassifier
from goldminer.utils import setup_logger


class SMSMultiBankParserV4:
    """Parse SMS messages with ftfy-style repair and context aware metadata."""

    NEGATIVE_KEYWORDS = re.compile(r"\b(declined|refused)\b", re.IGNORECASE)
    OTP_KEYWORDS = re.compile(r"\b(otp|one\s*time\s*password|code)\b", re.IGNORECASE)

    def __init__(
        self,
        templates_file: Optional[str] = None,
        *,
        text_repair_enabled: bool = True,
        promo_classifier: Optional[PromoClassifier] = None,
    ) -> None:
        self.logger = setup_logger(__name__)
        self.text_repair_enabled = text_repair_enabled
        self.parser = RegexParserEngine(templates_file=templates_file)
        self.validator = FieldValidator()
        self.normalizer = SchemaNormalizer()
        self.promo_classifier = promo_classifier or PromoClassifier()

    def parse_file(
        self,
        filepath: str,
        *,
        messages: Optional[List[str]] = None,
        bank_id: Optional[str] = None,
        ingested_at: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Parse a local SMS file with inference using filesystem metadata."""

        from goldminer.etl import load_sms_messages

        ingested_at = ingested_at or datetime.utcnow()
        file_messages = messages or load_sms_messages(filepath)
        parsed: List[Dict[str, Any]] = []

        for sms in file_messages:
            parsed.append(
                self.parse_message(
                    sms,
                    bank_id=bank_id,
                    file_created_ts=self._get_file_created_ts(filepath),
                    ingested_at=ingested_at,
                )
            )

        return parsed

    def parse_message(
        self,
        sms: str,
        *,
        bank_id: Optional[str] = None,
        file_created_ts: Optional[datetime] = None,
        ingested_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Parse a single SMS with text repair and timestamp resolution."""

        ingested_at = ingested_at or datetime.utcnow()
        repaired_sms, repaired_flag = self._repair_text(sms)

        parsed = self.parser.parse_sms(repaired_sms, bank_id=bank_id)

        extracted_date_raw = parsed.get("date")
        resolved_date = self._resolve_timestamp(
            extracted_date_raw,
            file_created_ts=file_created_ts,
            ingested_at=ingested_at,
        )

        parsed_fields = {
            **parsed,
            "extracted_date_raw": extracted_date_raw,
            "resolved_date": resolved_date,
            "text_repaired": repaired_flag,
            "transaction_state": self._classify_state(parsed, repaired_sms),
        }

        validated = self.validator.validate(parsed_fields)
        normalized = self.normalizer.normalize(validated)

        result = {
            **parsed_fields,
            "date": normalized.date,
            "amount": normalized.amount,
            "currency": normalized.currency,
            "payee": normalized.payee,
            "normalized_merchant": normalized.normalized_merchant,
            "category": normalized.category,
            "subcategory": normalized.subcategory,
            "account_id": normalized.account_id,
            "account_type": normalized.account_type,
            "interest_rate": normalized.interest_rate,
            "tags": normalized.tags,
            "urgency": normalized.urgency,
            "confidence": normalized.confidence,
            "resolved_date": normalized.resolved_date,
            "transaction_state": parsed_fields["transaction_state"],
            "text_repaired": repaired_flag,
        }

        return result

    def _repair_text(self, sms: str) -> Tuple[str, bool]:
        if not sms or not isinstance(sms, str):
            return sms, False

        original = sms
        cleaned = sms

        if self.text_repair_enabled:
            if fix_text is not None:
                cleaned = fix_text(cleaned, normalization="NFC")
            else:
                cleaned = cleaned.encode("latin-1", errors="ignore").decode(
                    "utf-8", errors="ignore"
                )
                cleaned = cleaned
        cleaned = cleaned.strip()

        if cleaned != original:
            return cleaned, True
        return cleaned, False

    def _resolve_timestamp(
        self,
        extracted_date: Optional[str],
        *,
        file_created_ts: Optional[datetime],
        ingested_at: datetime,
    ) -> Optional[str]:
        if not extracted_date:
            return None

        date_formats = ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"]
        for fmt in date_formats:
            try:
                dt = datetime.strptime(extracted_date, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        day_month_match = re.match(r"^(?P<day>\d{1,2})[/-](?P<month>\d{1,2})$", extracted_date)
        if day_month_match:
            year_source = file_created_ts or ingested_at
            inferred_year = year_source.year
            try:
                dt = datetime(
                    year=inferred_year,
                    month=int(day_month_match.group("month")),
                    day=int(day_month_match.group("day")),
                )
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                return None

        return None

    def _classify_state(
        self, parsed_fields: Dict[str, Any], sms_text: str
    ) -> str:
        sms_lower = sms_text.lower() if isinstance(sms_text, str) else ""

        if self.OTP_KEYWORDS.search(sms_lower):
            return "OTP"

        if self.NEGATIVE_KEYWORDS.search(sms_lower):
            return "DECLINED"

        if self.promo_classifier.is_promotional(sms_text):
            return "PROMO"

        if not parsed_fields.get("amount"):
            return "UNKNOWN"

        return "MONETARY"

    def _get_file_created_ts(self, filepath: str) -> Optional[datetime]:
        try:
            timestamp = os.path.getmtime(filepath)
            return datetime.fromtimestamp(timestamp)
        except (OSError, TypeError):
            return None

