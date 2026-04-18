import json
import random

# Aspect pools for positive sentiment
aspect_pools = {
    "App": {
        "targets": ["ứng dụng", "app", "phần mềm", "giao diện", "tính năng"],
        "positive": ["rất mượt", "dễ dùng", "đẹp mắt", "tốc độ nhanh", "vượt trội"]
    },
    "Ship": {
        "targets": ["giao hàng", "ship", "vận chuyển", "shipper", "thời gian giao"],
        "positive": ["nhanh chóng", "đúng hạn", "siêu tốc", "nhiệt tình", "cẩn thận"]
    },
    "Service": {
        "targets": ["nhân viên", "dịch vụ", "chăm sóc", "tư vấn", "hỗ trợ"],
        "positive": ["nhiệt tình", "chu đáo", "tận tâm", "rất tốt", "chuyên nghiệp"]
    }
}

sentence_templates = [
    "{target} {context}.",
    "Mình thấy {target} {context}, nên mua.",
    "Đánh giá 5 sao vì {target} {context}.",
    "Cá nhân mình cảm thấy {target} {context}.",
    "Dù mọi thứ ổn nhưng {target} {context}."
]

def make_opinion(text, aspect, target, sentiment):
    start = text.find(target)
    end = start + len(target)
    return [{
        "target": target,
        "aspect": aspect,
        "sentiment": sentiment,
        "start": start,
        "end": end
    }]

def generate_positive_samples(aspect, n=300):
    pool = aspect_pools[aspect]
    samples = []
    for _ in range(n):
        target = random.choice(pool["targets"])
        context = random.choice(pool["positive"])
        template = random.choice(sentence_templates)
        text = template.format(target=target, context=context)
        opinions = make_opinion(text, aspect, target, 1)
        samples.append({
            "text": text,
            "opinions": opinions,
            "global_sentiment": 1
        })
    return samples

# Generate and append to train_data.jsonl
data_path = "data/processed/train_data.jsonl"
with open(data_path, "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f]

new_samples = []
for aspect in aspect_pools:
    new_samples.extend(generate_positive_samples(aspect, n=300))

with open(data_path, "a", encoding="utf-8") as f:
    for item in new_samples:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"Đã bổ sung {len(new_samples)} câu positive cho các aspect App, Ship, Service vào train_data.jsonl!")
