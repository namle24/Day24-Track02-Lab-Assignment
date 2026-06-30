"""Anonymization pipeline for MedViet patient data."""

from __future__ import annotations

import hashlib
import re
import secrets

import pandas as pd
from faker import Faker

from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")


def _fake_cccd() -> str:
    return str(secrets.randbelow(9) + 1) + "".join(str(secrets.randbelow(10)) for _ in range(11))


def _fake_phone() -> str:
    return f"0{secrets.choice([3, 5, 7, 8, 9])}{''.join(str(secrets.randbelow(10)) for _ in range(8))}"


class MedVietAnonymizer:
    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """Anonymize detected PII with replace, mask, or hash strategy."""

        text = "" if text is None else str(text)
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        replacements = {
            "PERSON": fake.name(),
            "EMAIL_ADDRESS": fake.email(),
            "VN_CCCD": _fake_cccd(),
            "VN_PHONE": _fake_phone(),
        }

        anonymized = text
        for result in sorted(results, key=lambda item: item.start, reverse=True):
            original = anonymized[result.start : result.end]
            if strategy == "replace":
                replacement = replacements.get(result.entity_type, "<REDACTED>")
            elif strategy == "mask":
                replacement = self._mask_value(original)
            elif strategy == "hash":
                replacement = hashlib.sha256(original.encode("utf-8")).hexdigest()
            else:
                raise ValueError(f"Unsupported anonymization strategy: {strategy}")
            anonymized = anonymized[: result.start] + replacement + anonymized[result.end :]

        return anonymized

    @staticmethod
    def _mask_value(value: str) -> str:
        return re.sub(r"(?<=.).(?=.)", "*", value)

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Anonymize PII while keeping modeling columns intact."""

        df_anon = df.copy()

        if "ho_ten" in df_anon:
            df_anon["ho_ten"] = [fake.name() for _ in range(len(df_anon))]
        if "email" in df_anon:
            df_anon["email"] = [fake.email() for _ in range(len(df_anon))]
        if "dia_chi" in df_anon:
            df_anon["dia_chi"] = [fake.address().replace("\n", ", ") for _ in range(len(df_anon))]
        if "bac_si_phu_trach" in df_anon:
            df_anon["bac_si_phu_trach"] = [fake.name() for _ in range(len(df_anon))]
        if "cccd" in df_anon:
            df_anon["cccd"] = [_fake_cccd() for _ in range(len(df_anon))]
        if "so_dien_thoai" in df_anon:
            df_anon["so_dien_thoai"] = [_fake_phone() for _ in range(len(df_anon))]
        if "ngay_sinh" in df_anon:
            df_anon["nam_sinh"] = df_anon["ngay_sinh"].astype(str).str[-4:]
            df_anon = df_anon.drop(columns=["ngay_sinh"])

        return df_anon

    def calculate_detection_rate(
        self,
        original_df: pd.DataFrame,
        pii_columns: list[str],
    ) -> float:
        """Return the share of PII cells where at least one entity is detected."""

        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if results:
                    detected += 1

        return detected / total if total > 0 else 0.0
