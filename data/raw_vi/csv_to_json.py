import json

input_file = 'dataset.jsonl'
output_file = 'dataset_v2.jsonl'

with open(input_file, 'r', encoding='utf-8') as f_in:
    # Giả sử file hiện tại là một mảng JSON [{}, {}]
    data = json.load(f_in)

with open(output_file, 'w', encoding='utf-8') as f_out:
    for item in data:
        # ensure_ascii=False để giữ nguyên tiếng Việt có dấu
        line = json.dumps(item, ensure_ascii=False)
        f_out.write(line + '\n')