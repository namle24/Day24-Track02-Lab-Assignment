# Lab 24 Validation Summary

## Dataset
- Generated `data/raw/patients_raw.csv` locally with 200 patient records.
- PII columns: `ho_ten`, `cccd`, `ngay_sinh`, `so_dien_thoai`, `email`, `dia_chi`, `bac_si_phu_trach`.
- Generated `data/processed/patients_anonymized.csv` with 200 rows.

## Tests
- `pytest tests/ -v --tb=short`: 6 passed.
- PII detection rate target: >= 95%; test suite passed.
- Encryption round-trip: passed.
- Data quality validation: passed.

## API/RBAC
- `bob` reading raw patient data: 403.
- `alice` reading raw patient data: 200.
- `bob` reading anonymized training data: 200.
- `carol` reading aggregate metrics: 200.
- `bob` deleting patient data: 403.

## Security
- Bandit report generated at `reports/bandit_report.json`.
- TruffleHog/OPA/git-secrets CLIs were not installed locally; rerun commands are documented in `reports/security_tools_status.txt`.
