# Báo cáo nhóm — Lab 7: Embedding & Vector Store

**Thành viên:** Nguyễn Văn Duy, Dương Thị Ngân, Lục Tiến Đạt, Nguyễn Thanh Bình  
**Chủ đề:** Trợ lý tra cứu chính sách Trả hàng/Hoàn tiền Shopee  
**Ngày:** 20/09/2026  
**Trạng thái:** Đã hoàn thành nội dung đến CP4; CP5–CP6 chờ benchmark chung.

> Báo cáo chỉ ghi số liệu đã có bằng chứng. Mỗi thành viên vẫn nộp `REPORT_CANHAN.md` và kết quả benchmark riêng.

## 1. Lựa chọn tài liệu — 10 điểm

Nhóm chọn chính sách Trả hàng/Hoàn tiền Shopee vì miền này có nhiều điều kiện, thời hạn, quy trình và khác biệt giữa người mua với người bán. Bộ tài liệu phù hợp để kiểm tra chunking, semantic retrieval và metadata filter; câu trả lời có thể đối chiếu nguồn chính thức.

| # | Tài liệu | Audience | Ký tự | Nguồn chính thức |
|---:|---|---|---:|---|
| 1 | `buyer-refund-timeline.md` | buyer | 4.141 | [Shopee Help 189473](https://help.shopee.vn/portal/4/article/189473) |
| 2 | `buyer-return-eligibility.md` | buyer | 6.668 | [Shopee Help 188931](https://help.shopee.vn/portal/4/article/188931) |
| 3 | `buyer-return-process.md` | buyer | 9.038 | [Shopee Help 190242](https://help.shopee.vn/portal/4/article/190242) |
| 4 | `buyer-return-shipping.md` | buyer | 5.947 | [Shopee Help 189477](https://help.shopee.vn/portal/4/article/189477) |
| 5 | `return-refund-policy.md` | both | 19.295 | [Shopee Help 77251](https://help.shopee.vn/portal/4/article/77251) |
| 6 | `seller-refund-appeal.md` | seller | 4.927 | [Shopee Uni 3647](https://banhang.shopee.vn/edu/article/3647) |
| 7 | `seller-return-evidence.md` | seller | 8.492 | [Shopee Uni 25057](https://banhang.shopee.vn/edu/article/25057) |
| 8 | `seller-return-process.md` | seller | 7.749 | [Shopee Uni 563](https://banhang.shopee.vn/edu/article/563) |

URL đầy đủ, ngày lấy, phiên bản và quyền sử dụng nằm trong `data/shopee-return-refund/sources.csv`.

### Data governance

- [x] 8/8 tài liệu có nguồn công khai chính thức; URL trả HTTP 200 ngày 20/09/2026.
- [x] Không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc API key.
- [x] 8/8 tài liệu có `source_url`, `retrieved_at`, `document_version`, `audience`.
- [x] `sources.csv` có 8 dòng; `audit.json` lưu số ký tự, SHA-256 và kết quả URL.
- [x] Phân bố: 4 `buyer`, 3 `seller`, 1 `both`.

| Metadata | Ví dụ | Tác dụng |
|---|---|---|
| `doc_id` | `buyer-refund-timeline` | Nhận diện và xóa tài liệu chính xác |
| `title` | `Thời gian nhận tiền hoàn...` | Hiển thị nguồn dễ hiểu |
| `audience` | `buyer`, `seller`, `both` | Lọc trước khi xếp hạng, tránh lẫn đối tượng |
| `category` | `return_refund` | Thu hẹp miền truy xuất |
| `language` | `vi` | Chọn ngôn ngữ xử lý |
| `source_url` | URL Shopee | Đối chiếu nguồn gốc |
| `retrieved_at` | `2026-08-03` | Theo dõi thời điểm lấy dữ liệu |
| `document_version` | `2026-03-11` | Theo dõi phiên bản/hiệu lực |

## 2. Thiết kế chiến lược — 15 điểm

### Nguyên tắc so sánh

Cả bốn thành viên dùng chung corpus 8 tài liệu, 5 benchmark query và gold answer, embedding backend, `top_k=3` và metadata filter. Biến thay đổi duy nhất là chiến lược chunking.

### Baseline do Lục Tiến Đạt chạy

Đạt chạy `ChunkingStrategyComparator().compare()` trên `return-refund-policy.md` và gửi kết quả nhóm lúc 10:26 ngày 20/09/2026.

| Tài liệu | Chiến lược | Chunk | Độ dài TB | Giữ ngữ cảnh |
|---|---|---:|---:|---|
| `return-refund-policy.md` | `FixedSizeChunker` (`fixed_size`) | 43 | 497,5 | Kém; nguy cơ cắt đứt câu/từ ở mốc 500 ký tự |
| `return-refund-policy.md` | `SentenceChunker` (`by_sentences`) | 41 | 436,1 | Khá; giữ câu hoàn chỉnh nhưng có thể mất liên kết tiêu đề |
| `return-refund-policy.md` | `RecursiveChunker` (`recursive`) | 65 | 294,9 | Rất tốt; ưu tiên giữ trọn tiêu đề, mục và đoạn văn |

### Chiến lược riêng của từng thành viên

| Thành viên | Vai trò | Chiến lược | Tham số | Giả thuyết |
|---|---|---|---|---|
| Nguyễn Văn Duy | Code/Integration | `MarkdownHeadingChunker` | `chunk_size=650` | Lặp heading trên chunk con để giữ tên mục khi section dài bị cắt |
| Dương Thị Ngân | Data | `SentenceChunker` | `max_sentences_per_chunk=3` | Chunk theo câu làm mốc thời gian và điều kiện nổi bật hơn |
| Lục Tiến Đạt | Strategy | `FixedSizeChunker` | `chunk_size=500`, `overlap=50` | Overlap giảm mất thông tin tại biên fixed-size |
| Nguyễn Thanh Bình | Benchmark | `RecursiveChunker` | `chunk_size=300` | Chunk nhỏ theo cấu trúc đoạn/câu tăng mật độ evidence |

### Kiểm tra chiến lược của Nguyễn Văn Duy

- `MarkdownHeadingChunker` tạo 61 chunk từ nội dung chính của `return-refund-policy.md`.
- Độ dài trung bình 316,1 ký tự; dài nhất 633 ký tự.
- 60/61 chunk giữ hoặc được gắn lại heading.
- Test hồi quy đạt **42/42**.

| Thành viên | Điểm retrieval (/10) | Điểm mạnh dự kiến | Rủi ro cần kiểm tra ở CP5 |
|---|---:|---|---|
| Nguyễn Văn Duy | Chờ CP5 | Giữ heading và ngữ cảnh điều khoản | Heading lặp có thể tăng nhiễu |
| Dương Thị Ngân | Chờ CP5 | Giữ câu hoàn chỉnh | Có thể tách tiêu đề khỏi nội dung |
| Lục Tiến Đạt | Chờ CP5 | Đơn giản, overlap bảo vệ biên | Vẫn có thể cắt giữa câu |
| Nguyễn Thanh Bình | Chờ CP5 | Tôn trọng ranh giới đoạn/câu | Nhiều chunk, ngữ cảnh có thể ngắn |

**Kết luận CP4:** quan sát baseline cho thấy Recursive giữ cấu trúc tốt nhất. Chưa kết luận chiến lược thắng chung cuộc cho đến khi bốn người chạy cùng 5 query ở CP5.

## 3. Câu hỏi đánh giá và chất lượng truy xuất — chờ CP5

Nguyễn Thanh Bình chủ trì chốt đúng 5 query và gold answer trích từ corpus. Ít nhất một câu phải so sánh có/không có `metadata_filter={"audience": "buyer"}` hoặc `seller`.

| # | Query | Gold answer | Chunk chứa bằng chứng |
|---:|---|---|---|
| 1 | Chờ CP5 | Chờ CP5 | Chờ CP5 |
| 2 | Chờ CP5 | Chờ CP5 | Chờ CP5 |
| 3 | Chờ CP5 | Chờ CP5 | Chờ CP5 |
| 4 | Chờ CP5 | Chờ CP5 | Chờ CP5 |
| 5 | Chờ CP5 | Chờ CP5 | Chờ CP5 |

## 4. Demo và bài học nhóm — chờ CP6

CP6 sẽ tổng hợp chiến lược tốt nhất theo từng query, failure case, ảnh hưởng của metadata filter và bài học sau so sánh.

## Trạng thái checkpoint

| CP | Trạng thái | Bằng chứng |
|---|---|---|
| CP1 Setup | Ready | Baseline 11 passed, 31 failed |
| CP2 Data | Ready | 8 tài liệu, `sources.csv`, `audit.json` |
| CP3 Code | Duy Ready | 42/42 tests; các thành viên khác tự nộp bằng chứng |
| CP4 Strategy | Ready | Baseline của Đạt, 4 chiến lược riêng, custom chunker của Duy |
| CP5 Benchmark | Chưa chạy | Chờ 5 query và kết quả của bốn thành viên |
| CP6 Demo | Chưa chạy | Chờ tổng hợp benchmark |
