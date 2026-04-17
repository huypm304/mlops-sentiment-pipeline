Bạn là một NLP data augmentation specialist.

Tôi có file `data/processed/data_train_v4_norm.jsonl` là bộ ABSA training data tiếng Việt, domain thương mại điện tử. Cấu trúc mỗi record:
{"text": "...", "opinions": [{"target": "...", "aspect": "...", "sentiment": "..."}], "global_sentiment": "..."}

Aspect taxonomy gồm 7 nhãn: Service, General, Price, Fashion, Electronics, App, Ship.
Sentiment gồm 3 nhãn: Pos, Neg, Neu.

Vấn đề hiện tại: 3 ô trong ma trận aspect×sentiment đang bị thiếu đáng kể:
- App × Neu (hiện có ~165 samples)
- Ship × Pos (hiện có ~323 samples)
- Ship × Neu (hiện có ~230 samples)

Nhiệm vụ:
1. Đọc file và lấy mẫu các record hiện có thuộc 3 ô trên để hiểu pattern ngôn ngữ thực tế.
2. Sinh thêm data mới theo phương pháp paraphrase + template filling, bám sát ngữ điệu tiếng Việt tự nhiên, tránh sinh câu quá template cứng.
3. Mục tiêu số lượng cần bổ sung: App-Neu +200, Ship-Pos +150, Ship-Neu +120.
4. Mỗi record mới phải có:
   - `text` tiếng Việt tự nhiên, không có lỗi chính tả rõ ràng
   - Đúng 1 opinion khớp với aspect và sentiment mục tiêu
   - `global_sentiment` nhất quán với sentiment của opinion
   - Không trùng với text đã có trong file gốc
5. Ghi các record mới vào `data/processed/augmented_weak_cells.jsonl`.
6. In báo cáo: số record đã sinh theo từng ô, 5 ví dụ đại diện mỗi ô.

Ưu tiên sự đa dạng target: không dùng lặp quá 3 lần cùng 1 target trong cùng 1 ô.