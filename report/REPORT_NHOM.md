# Báo cáo nhóm — Lab 7: Embedding & Vector Store

**Thành viên:** Nguyễn Văn Duy, Dương Thị Ngân, Lục Tiến Đạt, Nguyễn Thanh Bình  
**Chủ đề:** Trợ lý tra cứu chính sách Trả hàng/Hoàn tiền Shopee  
**Ngày:** 20/09/2026  
**Trạng thái:** Đã hoàn thành CP1–CP6; CP7 còn hoàn thiện demo và nộp bài.

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
| Dương Thị Ngân | Data | `FixedSizeChunker` | `chunk_size=500`, `overlap=50` | Overlap giảm mất thông tin tại biên fixed-size |
| Lục Tiến Đạt | Strategy | `RecursiveChunker` | `chunk_size=500` | Ưu tiên ranh giới đoạn/câu để bảo toàn cấu trúc |
| Nguyễn Thanh Bình | Benchmark | `SentenceChunker` | `max_sentences_per_chunk=3` | Giữ câu hoàn chỉnh và gom ba câu mỗi chunk |

### Kiểm tra chiến lược của Nguyễn Văn Duy

- `MarkdownHeadingChunker` tạo 61 chunk từ nội dung chính của `return-refund-policy.md`.
- Độ dài trung bình 316,1 ký tự; dài nhất 633 ký tự.
- 60/61 chunk giữ hoặc được gắn lại heading.
- Test hồi quy đạt **42/42**.

| Thành viên | Điểm retrieval (/10) | Điểm mạnh dự kiến | Rủi ro cần kiểm tra ở CP5 |
|---|---:|---|---|
| Nguyễn Văn Duy | 5/10; evidence@3 3/5 | Giữ heading và ngữ cảnh điều khoản | Heading đứng riêng/lặp lại có thể tăng nhiễu |
| Dương Thị Ngân | 3/10; evidence@3 2/5 | Kích thước đều và có overlap | Có thể cắt giữa câu hoặc dòng bảng |
| Lục Tiến Đạt | 4/10; evidence@3 2/5 | Tôn trọng ranh giới đoạn/câu | Chunk lớn có thể làm loãng evidence |
| Nguyễn Thanh Bình | 5/10; evidence@3 3/5 | Giữ câu hoàn chỉnh | Có thể tách tiêu đề khỏi nội dung |

**Kết luận CP4:** quan sát baseline cho thấy Recursive giữ cấu trúc tốt nhất. Chưa kết luận chiến lược thắng chung cuộc cho đến khi bốn người chạy cùng 5 query ở CP5.

## 3. Câu hỏi đánh giá và chất lượng truy xuất — đã chốt query, chờ chạy CP5

Lục Tiến Đạt đề xuất 5 query và gold answer; nhóm đã đối chiếu cả năm với corpus. Câu 3–4 bắt buộc lọc `audience=seller`, câu 5 bắt buộc lọc `audience=buyer`.

| # | Query | Gold answer | Tài liệu/chunk chứa bằng chứng | Filter |
|---:|---|---|---|---|
| 1 | Người mua thanh toán đơn hàng bằng Thẻ tín dụng/ghi nợ thì nhận được tiền hoàn trong bao lâu? | 7–14 ngày làm việc tùy ngân hàng, tính sau khi Shopee chấp nhận hoàn tiền; tiền hoàn về đúng thẻ đã dùng. | `buyer-refund-timeline.md`, bảng thời gian và Lưu ý chung | Không |
| 2 | Đối với sản phẩm thực phẩm tươi sống và đông lạnh, thời gian tối đa để người mua gửi yêu cầu Trả hàng/Hoàn tiền là bao lâu? | Trong vòng 24 giờ kể từ khi đơn hàng được cập nhật “Giao hàng thành công”, trừ lý do Chưa nhận được hàng. | `buyer-return-eligibility.md`, mục 1.2 | Không |
| 3 | Người bán có thời hạn bao nhiêu ngày để gửi khiếu nại nếu không đồng ý với quyết định Hoàn tiền ngay của Shopee? | Trong vòng 2 ngày kể từ khi Shopee thông báo Hoàn tiền ngay cho Người mua mà không yêu cầu trả hàng; Shopee xem xét trong 3–5 ngày làm việc. | `seller-refund-appeal.md`, bảng tổng quan và mục 1 | `{"audience":"seller"}` |
| 4 | Khi người bán khiếu nại quyết định hoàn tiền ngay không yêu cầu trả hàng của Shopee, loại bằng chứng nào là bắt buộc phải cung cấp? | Bằng chứng đóng gói: video ghi lại toàn bộ quá trình đóng gói sản phẩm trước khi bàn giao cho đơn vị vận chuyển. Không bắt buộc bằng chứng mở hàng hoàn. | `seller-return-evidence.md`, mục B và C.1 | `{"audience":"seller"}` |
| 5 | Trong các phương thức gửi hàng hoàn trả của Shopee, hình thức nào yêu cầu người mua phải thanh toán trước phí trả hàng? | “Tự sắp xếp”: người mua trả trước phí gửi tại bưu cục; Shopee hỗ trợ hoàn lại theo chính sách. | `buyer-return-shipping.md`, mục 1.1 và 2.2 | `{"audience":"buyer"}` |

### Kết quả CP5 của Nguyễn Văn Duy

Backend: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`; chunker: `MarkdownHeadingChunker(650)`; 185 chunk; `top_k=3`.

| # | Evidence rank | Điểm retrieval | Nhận xét |
|---:|---:|---:|---|
| 1 | Không có | 0/2 | Top-3 cùng chủ đề nhưng không chứa mốc 7–14 ngày |
| 2 | 1 | 2/2 | Top-1 ở policy chung chứa đúng mốc 24 giờ |
| 3 | 1 | 2/2 | Filter seller; kết quả đúng ngay top-1 |
| 4 | Không có | 0/2 | Top-3 nói về khiếu nại nhưng thiếu dòng “Bắt buộc — Bằng chứng đóng gói” |
| 5 | 3 | 1/2 | Filter buyer đưa evidence từ ngoài top-3 lên rank 3 |

Kết quả của Duy: **evidence@3 = 3/5**, điểm retrieval **5/10**. Cách chấm kiểm marker đáp án trong nội dung chunk, không chỉ kiểm `doc_id`. Metadata filter giúp câu 5 từ ngoài top-3 lên rank 3. Đây mới là điểm retrieval; điểm agent answer chỉ ghi sau khi chạy LLM thật.

## 4. So sánh CP6 và bài học nhóm

Nhóm chạy lại bốn cấu hình bằng cùng model, corpus, query, filter và `top_k=3`. Kết quả được lưu tại `ket_qua_so_sanh_nhom.txt`.

| Thành viên | Chiến lược | Số chunk | Evidence rank Q1–Q5 | evidence@3 | Điểm |
|---|---|---:|---|---:|---:|
| Nguyễn Thanh Bình | Sentence, 3 câu | 205 | miss, 1, 1, miss, 2 | 3/5 | 5/10 |
| Nguyễn Văn Duy | Heading, 650 | 185 | miss, 1, 1, miss, 3 | 3/5 | 5/10 |
| Lục Tiến Đạt | Recursive, 500 | 183 | miss, 1, 1, miss, miss | 2/5 | 4/10 |
| Dương Thị Ngân | Fixed 500, overlap 50 | 145 | miss, 3, 1, miss, miss | 2/5 | 3/10 |

**Kết luận:** Sentence và Heading đồng hạng theo điểm tổng nhưng mạnh ở các câu khác nhau. Heading đáp ứng yêu cầu bắt buộc về heading/section và đưa câu 5 vào rank 3 khi có filter. Sentence đưa câu 5 lên rank 2. Không chiến lược nào lấy đúng evidence cho câu 1 và câu 4, cho thấy bảng Markdown cần chunker giữ nguyên từng hàng hoặc bổ sung metadata `sub_topic`.

**Failure case:** kiểm `doc_id` từng làm kết quả có vẻ đạt 5/5, nhưng top-3 câu 1 không chứa mốc 7–14 ngày và top-3 câu 4 không chứa dòng bằng chứng bắt buộc. Đây đúng là lỗi “đúng tài liệu, sai chunk”.

**Nếu làm lại:** nhóm sẽ thêm table-row chunking, ghép heading đứng riêng với nội dung kế tiếp, và dùng metadata `payment_method`, `appeal_type`, `sub_topic` để lọc trước retrieval.

## Trạng thái checkpoint

| CP | Trạng thái | Bằng chứng |
|---|---|---|
| CP1 Setup | Ready | Baseline 11 passed, 31 failed |
| CP2 Data | Ready | 8 tài liệu, `sources.csv`, `audit.json` |
| CP3 Code | Duy Ready | 42/42 tests; các thành viên khác tự nộp bằng chứng |
| CP4 Strategy | Ready | Baseline của Đạt, 4 chiến lược riêng, custom chunker của Duy |
| CP5 Benchmark | Ready | Duy: embedding thật, 185 chunk, evidence@3 3/5, retrieval 5/10 |
| CP6 Compare | Ready | Bốn cấu hình chạy cùng điều kiện; có bảng so sánh và failure analysis |
