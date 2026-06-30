# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data production lưu trên servers/managed database đặt tại Việt Nam
- [x] Backup định kỳ cấu hình trong region VN hoặc nhà cung cấp có cam kết lưu trú dữ liệu tại VN
- [x] API/data export log `destination_country`; OPA deny export restricted data nếu `destination_country != "VN"`

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training
- [x] Có endpoint/quy trình xóa hoặc loại khỏi training set khi user rút consent (Right to Erasure)
- [x] Lưu consent record với `patient_id`, purpose, timestamp, actor, source form version

## C. Breach Notification (72h)
- [x] Có incident response plan: triage, containment, eradication, recovery, postmortem
- [x] Alert tự động qua Prometheus/Grafana khi có access bất thường hoặc secret leak
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h, DPO chịu trách nhiệm điều phối

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: dpo@medviet.example

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | Envelope encryption AES-256-GCM with local dev KEK; production KEK in KMS/HSM, TLS 1.3 in transit | ✅ Done | Infra Team |
| Audit logging | Structured API access logs with user role, resource, action, decision, request id; immutable retention in SIEM/Object Lock | ✅ Done | Platform Team |
| Breach detection | Prometheus anomaly alerts for 401/403 spikes, raw PII access bursts, export attempts, and secret scan failures | ✅ Done | Security Team |

## F. Technical Solution Details

- Audit logging: every API request records authenticated user, role, route, resource/action, allow/deny decision, status code, source IP, user agent, and request id. Logs are forwarded to SIEM with write-once retention.
- Breach detection: Prometheus scrapes API/security counters and Grafana alerts trigger when denied requests spike, restricted exports are attempted, or Bandit/git-secrets/pip-audit fail in CI.
- Erasure workflow: patient consent withdrawal marks the pseudonymous `patient_id` as revoked, removes raw PII from serving stores, and excludes the row from subsequent training snapshots.
- Localization control: OPA blocks restricted data movement outside VN and export jobs must include destination country, purpose, and approving DPO ticket.
