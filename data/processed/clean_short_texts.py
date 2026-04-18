import json

input_path = 'data/processed/train_data.jsonl'
output_path = 'data/processed/train_data_cleaned.jsonl'

with open(input_path, 'r', encoding='utf-8') as f:
    lines = [json.loads(line) for line in f]

# Loại bỏ các mẫu có text ngắn hơn 10 ký tự (sau khi loại bỏ khoảng trắng)
filtered = [item for item in lines if len(item['text'].strip()) >= 10]

with open(output_path, 'w', encoding='utf-8') as f:
    for item in filtered:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"Đã loại bỏ {len(lines) - len(filtered)} mẫu text ngắn. File mới: {output_path}")
