# Báo cáo cá nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn Duy  
**MSSV:** 2A202602729  
**Nhóm:** kingpro — Nguyễn Văn Duy, Dương Thị Ngân, Lục Tiến Đạt, Nguyễn Thanh Bình  
**Ngày:** 20/09/2026  
**Trạng thái:** Hoàn thành nội dung cá nhân CP1–CP6; còn CP7 demo và nộp link.

## 1. Khởi động — 5 điểm

### Cosine similarity

Cosine similarity cao nghĩa là hai vector chỉ gần cùng hướng, nên hai đoạn văn có nội dung hoặc ý nghĩa gần nhau. Giá trị gần 1 thể hiện mức tương đồng cao; gần 0 thể hiện ít liên quan.

**Ví dụ tương đồng cao:**

- Câu A: “Người mua nhận tiền hoàn trong bao lâu?”
- Câu B: “Thời gian Shopee hoàn lại tiền cho khách hàng là bao nhiêu ngày?”
- Hai câu khác từ nhưng cùng hỏi thời hạn hoàn tiền.

**Ví dụ tương đồng thấp:**

- Câu A: “Người bán cần cung cấp bằng chứng khiếu nại nào?”
- Câu B: “Cách tạo môi trường ảo Python trên Windows?”
- Hai câu thuộc hai miền và mục đích khác nhau.

Cosine phù hợp với text embedding vì nó so sánh hướng biểu diễn ngữ nghĩa và ít bị ảnh hưởng bởi độ lớn vector. Khoảng cách Euclid còn phụ thuộc độ lớn nên hai vector cùng hướng vẫn có thể bị coi là xa.

### Tính số chunk

Với `L=10.000`, `chunk_size=500`, `overlap=50`:

```text
step = 500 - 50 = 450
count = ceil((10.000 - 50) / 450)
      = ceil(22,111...)
      = 23 chunk
```

Khi tăng overlap lên 100:

```text
step = 500 - 100 = 400
count = ceil((10.000 - 100) / 400)
      = ceil(24,75)
      = 25 chunk
```

Overlap lớn hơn tạo thêm hai chunk và tốn lưu trữ/tính toán hơn, nhưng giảm nguy cơ mất thông tin nằm đúng ở ranh giới hai chunk.

## 2. Hướng tiếp cận của tôi — 10 điểm

### `SentenceChunker.chunk`

Dùng regex `(?<=[.!?])(?:\s+|\n+)` để tách sau dấu kết thúc câu nhưng giữ lại dấu câu. Các câu được `strip`, bỏ phần rỗng rồi gom tối đa `max_sentences_per_chunk`; text rỗng trả `[]`. Hạn chế còn lại là chữ viết tắt như `TS.` hoặc `v.v.` có thể bị nhận nhầm là hết câu.

### `RecursiveChunker.chunk` và `_split`

Thuật toán thử separator từ lớn đến nhỏ: đoạn trống, xuống dòng, dấu chấm, khoảng trắng rồi chuỗi rỗng. Mảnh vượt `chunk_size` được đệ quy với separator tiếp theo; các mảnh nhỏ liền nhau được gom đến sát giới hạn. Base case gồm text rỗng, text đã đủ ngắn, và hết separator thì chuyển sang fixed-size không overlap.

### `compute_similarity`

Tính tích vô hướng chia cho tích độ lớn hai vector. Nếu một vector có độ lớn bằng 0, hàm trả `0.0` để tránh chia cho 0.

### `ChunkingStrategyComparator`

Chạy `FixedSizeChunker`, `SentenceChunker` và `RecursiveChunker` trên cùng văn bản. Mỗi chiến lược trả `count`, `avg_length` và danh sách `chunks`; text rỗng không gây chia cho 0.

### `EmbeddingStore`

`add_documents` tạo embedding một lần cho từng `Document`, copy metadata, bảo đảm có `doc_id` và lưu record trong bộ nhớ. `search` embed câu hỏi, tính dot product với toàn bộ record, sắp giảm dần và lấy top-k; embedding đã chuẩn hóa nên dot product tương đương cosine.

`search_with_filter` lọc record theo metadata **trước** khi xếp hạng để các tài liệu sai đối tượng không chiếm top-k. `delete_document` loại toàn bộ chunk có cùng `metadata['doc_id']` và trả `True` khi thực sự xóa được.

### `KnowledgeBaseAgent.answer`

Agent truy xuất top-k, đánh số context `[1]`, `[2]`, `[3]` kèm `source_url`, rồi yêu cầu LLM chỉ trả lời dựa trên context và trích dẫn số nguồn. Nếu không có kết quả, agent trả thông báo thiếu thông tin và không gọi LLM.

### Chiến lược cá nhân CP4: `MarkdownHeadingChunker`

Tôi chọn chunk theo heading Markdown vì các chính sách Shopee được tổ chức theo mục. Regex nhận heading `##` hoặc `###`; section ngắn trở thành một chunk, section dài được cắt tiếp bằng `RecursiveChunker`, sau đó heading được gắn lại vào từng chunk con.

Kết quả trên nội dung chính của `return-refund-policy.md`: 61 chunk, trung bình 316,1 ký tự, dài nhất 633 ký tự và 60/61 chunk giữ hoặc được gắn lại heading. CP5 cho thấy heading giúp giữ ngữ cảnh ở câu 2–3, nhưng chưa đủ xử lý tốt bảng ở câu 1 và câu 4.

## 3. Hoàn thiện code — 30 điểm

```text
pytest tests/ -v
============================= 42 passed in 0.78s =============================
```

**Số test vượt qua:** **42/42**  
**Bằng chứng trong repo:** `evidence/Day07-CP3-42-Tests.txt`

Các phần đã hoàn thiện:

- `SentenceChunker`
- `RecursiveChunker`
- `compute_similarity`
- `ChunkingStrategyComparator`
- `EmbeddingStore`, metadata filter và delete
- `KnowledgeBaseAgent`
- `MarkdownHeadingChunker` cho chiến lược cá nhân

## 4. Dự đoán độ tương tự — đã đo bằng embedding thật

Các dự đoán được ghi trước khi chạy `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Không dùng `MockEmbedder` vì mock chỉ băm chuỗi và không biểu diễn ngữ nghĩa.

| # | Câu A | Câu B | Dự đoán | Cosine thực tế | Đánh giá |
|---:|---|---|---|---|
| 1 | Người mua nhận tiền hoàn trong bao lâu? | Thời gian hoàn tiền cho khách hàng là mấy ngày? | Cao nhất | 0,738255 | Cao nhưng không cao nhất |
| 2 | Điều kiện để yêu cầu trả hàng là gì? | Trường hợp nào người mua được hoàn trả sản phẩm? | Cao | 0,461986 | Trung bình |
| 3 | Người bán khiếu nại quyết định hoàn tiền thế nào? | Nhà bán hàng phản hồi tranh chấp bằng cách nào? | Cao | 0,795722 | Cao nhất thực tế |
| 4 | Phí gửi hàng hoàn trả do ai chịu? | Người bán cần nộp bằng chứng hình ảnh nào? | Trung bình/thấp | 0,285926 | Thấp, đúng xu hướng |
| 5 | Chính sách hoàn tiền Shopee | Cách tạo môi trường ảo Python | Thấp nhất | 0,023886 | Thấp nhất, đúng dự đoán |

Kết quả bất ngờ nhất là cặp 3 cao hơn cặp 1 dù dùng từ khác nhau nhiều hơn. Điều này cho thấy embedding chú trọng quan hệ ngữ nghĩa “người bán phản hồi/khiếu nại tranh chấp” thay vì chỉ đếm từ trùng. Cặp 5 gần 0 xác nhận hai chủ đề không liên quan được tách rõ.

## 5. Kết quả truy xuất cá nhân — CP5

Tôi chạy 5 query chung do Lục Tiến Đạt đề xuất trên `MarkdownHeadingChunker(chunk_size=650)`, cùng embedding backend và `top_k=3` với ba thành viên còn lại.

Kết quả benchmark chính do nhóm tổng hợp, có xét top-3 và câu trả lời agent, chấm chiến lược của tôi **9/10**. Bảng dưới là lượt audit độc lập nghiêm ngặt hơn: chỉ tính đạt khi marker đáp án xuất hiện trực tiếp trong chunk truy xuất; kết quả audit là **5/10**. Việc ghi cả hai giúp phân biệt đánh giá end-to-end và kiểm tra retrieval thuần.

| # | Query | Filter | Top-1 (score) | Evidence chuẩn | Điểm retrieval |
|---:|---|---|---|---:|---|---|
| 1 | Thẻ tín dụng/ghi nợ nhận tiền hoàn trong bao lâu? | Không | `seller-return-process#2` (0,652738) | Không có marker 7–14 ngày trong top-3 | 0/2 |
| 2 | Thực phẩm tươi sống/đông lạnh được gửi yêu cầu tối đa bao lâu? | Không | `return-refund-policy#12` (0,794739), chứa đúng đáp án | Rank 1 theo nội dung | 2/2 |
| 3 | Người bán có bao nhiêu ngày để khiếu nại Hoàn tiền ngay? | `audience=seller` | `seller-refund-appeal#5` (0,896788) | Rank 1 | 2/2 |
| 4 | Khiếu nại Hoàn tiền ngay bắt buộc cần bằng chứng nào? | `audience=seller` | `seller-refund-appeal#7` (0,823247) | Không có đủ marker đáp án trong top-3 | 0/2 |
| 5 | Hình thức hoàn trả nào yêu cầu người mua trả trước phí? | `audience=buyer` | `buyer-return-process#0` (0,783714), chỉ là heading | Rank 3 — `buyer-return-shipping` | 1/2 |

**Kết quả audit:** `evidence@3 = 3/5`; điểm retrieval theo marker nội dung là **5/10**. Toàn bộ top-3 nằm trong `ket_qua_benchmark.txt`. Điểm benchmark nhóm dùng để tự đánh giá là **9/10**; điểm audit được giữ như failure analysis có thể tái lập từ repo.

Metadata filter đưa evidence câu 5 từ ngoài top-3 lên rank 3; câu 3 giữ nguyên rank 1; câu 4 vẫn trượt. Failure case cho thấy đúng `doc_id` chưa đủ: top-3 câu 1 và 4 cùng đúng chủ đề nhưng không chứa chuỗi đáp án. Cải tiến tiếp theo là chunk từng hàng bảng và ghép heading-only chunk với nội dung kế tiếp.

Điều tôi học được từ kết quả baseline của Lục Tiến Đạt là recursive split giữ cấu trúc tốt hơn fixed-size. Tuy nhiên, heading-aware chunking vẫn cần xử lý heading đứng riêng; chỉ giữ tiêu đề chưa bảo đảm chunk có đủ bằng chứng.

## Tự đánh giá cá nhân

| Tiêu chí | Điểm tự đánh giá | Bằng chứng |
|---|---:|---|
| Khởi động | 5/5 | Giải thích cosine và tính đúng 23/25 chunk |
| Hướng tiếp cận | 10/10 | Mô tả thuật toán, edge case và thiết kế RAG |
| Core implementation | 30/30 | 42/42 tests |
| Dự đoán similarity | 4/5 | Đo 5 cặp bằng embedding thật; cặp 3 cao hơn dự đoán |
| Competition results | 9/10 | Điểm benchmark nhóm; audit marker độc lập 5/10 |
| **Tổng** | **58/60** | CP1–CP6 hoàn thành |
