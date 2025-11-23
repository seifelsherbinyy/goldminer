"""Unit tests for SMSMultiBankParserV4."""

import os
import tempfile
from datetime import datetime

import unittest

from goldminer.etl.sms_parser_v4 import SMSMultiBankParserV4


class StubParser:
    def __init__(self, result):
        self.result = result

    def parse_sms(self, *_args, **_kwargs):  # pragma: no cover - trivial
        return self.result


class StubPromoClassifier:
    def __init__(self, response=True):
        self.response = response

    def is_promotional(self, _sms):  # pragma: no cover - trivial
        return self.response


class TestSMSParserV4(unittest.TestCase):
    def test_text_repair_applied(self):
        parser = SMSMultiBankParserV4()
        parser.parser = StubParser(
            {
                "amount": "100",
                "currency": "EGP",
                "date": "2023-01-01",
                "payee": "Cafe\u0301 Central",
                "transaction_type": None,
                "card_suffix": None,
                "confidence": "high",
                "matched_bank": "Generic",
                "matched_template": "stub",
                "sms_text": "Cafe\u0301 Central",
                "ml_category": None,
                "ml_category_score": None,
                "ml_category_confidence": None,
            }
        )

        result = parser.parse_message("Cafe\u0301 Central")
        self.assertTrue(result["text_repaired"])
        self.assertEqual(result["transaction_state"], "MONETARY")

    def test_missing_year_inferred_from_file_metadata(self):
        inferred_date = datetime(2022, 7, 21, 10, 0, 0)
        parser = SMSMultiBankParserV4()
        parser.parser = StubParser(
            {
                "amount": "250",
                "currency": "EGP",
                "date": "21/07",
                "payee": "Store",
                "transaction_type": None,
                "card_suffix": None,
                "confidence": "high",
                "matched_bank": "Generic",
                "matched_template": "stub",
                "sms_text": "",
                "ml_category": None,
                "ml_category_score": None,
                "ml_category_confidence": None,
            }
        )

        with tempfile.NamedTemporaryFile(delete=False) as handle:
            filepath = handle.name
        os.utime(filepath, (inferred_date.timestamp(), inferred_date.timestamp()))

        result = parser.parse_message(
            "Transaction 250", file_created_ts=datetime.fromtimestamp(os.path.getmtime(filepath))
        )

        os.unlink(filepath)

        self.assertEqual(result["resolved_date"], "2022-07-21")

    def test_transaction_state_classification(self):
        parser = SMSMultiBankParserV4(promo_classifier=StubPromoClassifier())
        parser.parser = StubParser(
            {
                "amount": None,
                "currency": None,
                "date": None,
                "payee": None,
                "transaction_type": None,
                "card_suffix": None,
                "confidence": "low",
                "matched_bank": "Generic",
                "matched_template": "stub",
                "sms_text": "OTP code 1234",
                "ml_category": None,
                "ml_category_score": None,
                "ml_category_confidence": None,
            }
        )

        otp_result = parser.parse_message("OTP code 1234")
        self.assertEqual(otp_result["transaction_state"], "OTP")

        parser.parser.result["sms_text"] = "Payment declined"
        declined_result = parser.parse_message("Payment declined")
        self.assertEqual(declined_result["transaction_state"], "DECLINED")

        parser.parser.result["sms_text"] = "special promo for you"
        promo_result = parser.parse_message("special promo for you")
        self.assertEqual(promo_result["transaction_state"], "PROMO")


if __name__ == "__main__":
    unittest.main()
