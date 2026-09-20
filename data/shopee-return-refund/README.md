# Shopee return/refund corpus

Corpus nhóm Nguyễn Văn Duy, Dương Thị Ngân, Lục Tiến Đạt và Nguyễn Thanh Bình gồm 8 bản tóm lược từ các trang chính sách công khai chính thức của Shopee cho `buyer`, `seller` và `both`.

- URL gốc và provenance nằm trong `sources.csv`.
- Tất cả URL được kiểm tra truy cập lại ngày 2026-09-20.
- Không chứa dữ liệu cá nhân, nội dung đăng nhập hoặc API key.
- Metadata bắt buộc: `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`; mỗi file có thêm `category` và `language`.
- `license_or_permission=public-help-page-manual-summary`: bản tóm lược phục vụ học tập từ trang trợ giúp public; không tuyên bố sở hữu nội dung gốc của Shopee.

`audience` nhận một trong ba giá trị: `buyer`, `seller`, `both`.

## Phân công điều phối

- Nguyễn Văn Duy — Code/Integration.
- Dương Thị Ngân — Data.
- Lục Tiến Đạt — Strategy.
- Nguyễn Thanh Bình — Benchmark.

Phân công trên là vai trò điều phối phần nhóm; mỗi thành viên vẫn tự hoàn thiện TODO, chạy benchmark chiến lược riêng và viết `REPORT_CANHAN.md`.
