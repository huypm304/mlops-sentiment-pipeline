Role: Bạn là một Chuyên gia Senior AI Research Engineer chuyên về NLP và MLOps.

Context:
Tôi đang thực hiện bài toán Aspect-Based Sentiment Analysis (ABSA) cho review thương mại điện tử tiếng Việt.

Model: ViDeBERTa-base + CRF (Joint learning: BIO, Sentiment, Global).

Dataset (v6_final): 7,565 records đã được audit sạch (chỉ còn ~3% nhiễu nhãn).

Trạng thái hiện tại (Full Fine-tuning): - Kết quả: Composite 0.5431 | Span 0.6637 | Sent 0.4532 | Glob 0.3768.

Vấn đề 1: Sentiment POS chỉ đúng 35.1% (nghi ngờ bị Catastrophic Forgetting do Full Fine-tuning).

Vấn đề 2: Confusion giữa nhãn Ship và General (Recall Ship thấp ~49%).

Vấn đề 3: Model chưa hội tụ ở Epoch 30 (Best ở Ep 27).

Task:
Hãy giúp tôi nâng cấp script huấn luyện từ Full Fine-tuning sang Hybrid LoRA Approach để giải quyết các vấn đề trên.

Yêu cầu chi tiết:

Architecture: Sử dụng thư viện peft để cấu hình LoRA cho ViDeBERTa Backbone. Giữ nguyên Full Fine-tuning cho các Task Heads (CRF, Sentiment, Global).

LoRA Config: Hãy đề xuất giá trị r, lora_alpha, và target_modules tối ưu cho ViDeBERTa-base để bảo tồn tri thức ngôn ngữ (giúp cứu điểm POS sentiment).

Hyperparameters: Thiết lập lại Learning Rate riêng biệt cho LoRA (~5e-5) và Task Heads (~1e-4). Cấu hình 50 Epoch và Patience 10.

Optimization: Tắt hoàn toàn lambda_consistency (KL Divergence) vì Global label vẫn còn nhiễu nhẹ.

Output Code: Viết lại class ABSAModel và hàm main() để tích hợp LoRA, đồng thời đảm bảo việc lưu model chỉ lưu các trainable parameters (PEFT weights) để tiết kiệm dung lượng.

Reasoning Requirement: Trước khi viết code, hãy giải thích tại sao phương pháp Hybrid LoRA này có thể giúp cải thiện độ chính xác của nhãn POS Sentiment so với Full Fine-tuning trong trường hợp này