# CP4 — Kế hoạch chiến lược chunking của nhóm

## Nguyên tắc so sánh công bằng

Cả bốn thành viên dùng chung:

- Corpus `data/shopee-return-refund/` gồm 8 tài liệu.
- Cùng 5 benchmark query và gold answer.
- Cùng embedding backend.
- Cùng `top_k=3`.
- Cùng metadata filter cho câu hỏi seller/buyer.
- Chỉ thay đổi chiến lược chunking.

## Phân công chiến lược

| Thành viên | Vai trò điều phối | Chiến lược cá nhân | Tham số | Giả thuyết cần kiểm chứng |
|---|---|---|---|---|
| Nguyễn Văn Duy | Code/Integration | `MarkdownHeadingChunker` | `chunk_size=650` | Chính sách có cấu trúc mục rõ; giữ heading giúp chunk không mất ngữ cảnh điều khoản. |
| Dương Thị Ngân | Data | `SentenceChunker` | `max_sentences_per_chunk=3` | Chunk ngắn theo câu làm các mốc thời gian và điều kiện nổi bật hơn. |
| Lục Tiến Đạt | Strategy | `FixedSizeChunker` | `chunk_size=500`, `overlap=50` | Baseline đơn giản; overlap giúp giữ thông tin ở biên chunk. |
| Nguyễn Thanh Bình | Benchmark | `RecursiveChunker` | `chunk_size=300` | Cắt theo đoạn/câu và kích thước nhỏ có thể tăng mật độ evidence. |

Mỗi thành viên vẫn tự hoàn thiện TODO, chạy 42 tests, chạy benchmark chiến lược được giao và viết `REPORT_CANHAN.md`.

## Số liệu phải ghi cho mỗi chiến lược

1. Tổng số chunk.
2. Độ dài chunk trung bình.
3. Top 3 của từng benchmark query.
4. Số câu có evidence thật trong Top 3 (`evidence@3`).
5. Điểm 0/1/2 cho từng câu.
6. Kết quả câu có filter so với không filter.
7. Ít nhất một failure case và nguyên nhân.

## Điều kiện hoàn thành CP4

- Không có hai thành viên dùng cùng chiến lược và cùng tham số.
- Có ít nhất một chiến lược theo heading/section.
- Mọi người xác nhận cùng corpus, query, embedding và `top_k`.
- `MarkdownHeadingChunker` của Duy chạy được trên tài liệu chính sách thật và giữ heading khi phải cắt section dài.
