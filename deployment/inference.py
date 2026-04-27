import argparse
import json
import os
import unicodedata
from contextlib import nullcontext

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer

try:
	from torchcrf import CRF
except ImportError as exc:
	raise RuntimeError(
		"Missing dependency 'pytorch-crf'. Run: pip install -r requirements.txt"
	) from exc


MODEL_NAME = "Fsoft-AIC/videberta-base"
DEFAULT_MODEL_CANDIDATES = [
	os.path.join(os.path.dirname(__file__), "best_model_v6.pt"),
	os.path.join(os.path.dirname(__file__), "checkpoint_v6.pt"),
	os.path.join(os.path.dirname(__file__), "best_model_v5.pt"),
]
MAX_LEN = 224
MAX_OPS = 8
MAX_CONTEXT_WINDOW = 5

ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]
SENTIMENT_LABELS = ["negative", "positive", "neutral"]


def nfc(text):
	return unicodedata.normalize("NFC", text)


def build_bio():
	labels = ["O"]
	for aspect in ASPECTS:
		labels += [f"B-{aspect}", f"I-{aspect}"]
	return labels, {label: idx for idx, label in enumerate(labels)}, {idx: label for idx, label in enumerate(labels)}


BIO_LABELS, BIO_L2I, BIO_I2L = build_bio()
N_BIO = len(BIO_LABELS)
N_SENT = len(SENTIMENT_LABELS)


def resolve_default_model_path():
	for candidate in DEFAULT_MODEL_CANDIDATES:
		if os.path.exists(candidate):
			return candidate
	return DEFAULT_MODEL_CANDIDATES[0]


DEFAULT_MODEL_PATH = resolve_default_model_path()


def context_window(tmin, tmax, op_idx, v_ops, seq_len):
	lo = max(tmin - MAX_CONTEXT_WINDOW, 1)
	hi = min(tmax + MAX_CONTEXT_WINDOW, seq_len - 1)
	if op_idx > 0:
		lo = max(lo, max(v_ops[op_idx - 1][0]) + 1)
	if op_idx < len(v_ops) - 1:
		hi = min(hi, min(v_ops[op_idx + 1][0]) - 1)
	return lo, hi


def extract_spans(seq):
	spans = []
	start = None
	current_aspect = None
	for idx, label_id in enumerate(seq):
		tag = BIO_I2L.get(int(label_id), "O")
		if tag.startswith("B-"):
			if start is not None:
				spans.append((start, idx - 1, current_aspect))
			start = idx
			current_aspect = tag[2:]
		elif not (tag.startswith("I-") and current_aspect == tag[2:]):
			if start is not None:
				spans.append((start, idx - 1, current_aspect))
			start = None
			current_aspect = None
	if start is not None:
		spans.append((start, len(seq) - 1, current_aspect))
	return spans


class ABSAModel(nn.Module):
	def __init__(self):
		super().__init__()
		self.backbone = AutoModel.from_pretrained(MODEL_NAME)
		hidden_size = self.backbone.config.hidden_size
		self.dropout = nn.Dropout(0.3)
		self.bio_head = nn.Linear(hidden_size, N_BIO)
		self.crf = CRF(N_BIO, batch_first=True)
		self.fc_pool = nn.Linear(hidden_size, 1)
		self.sent_head = nn.Sequential(nn.Dropout(0.2), nn.Linear(hidden_size, N_SENT))
		self.global_head = nn.Linear(hidden_size, N_SENT)

	def forward(self, ids, mask, span_mask=None, bio=None, cached_seq=None):
		if cached_seq is None:
			seq = self.dropout(self.backbone(ids, attention_mask=mask).last_hidden_state)
		else:
			seq = cached_seq
		emissions = self.bio_head(seq)
		crf_loss = None
		if bio is not None:
			crf_loss = -self.crf(emissions, bio, mask=mask.bool(), reduction="mean")

		sent_logits = None
		if span_mask is not None:
			batch_size, max_ops, seq_len, hidden_size = ids.shape[0], MAX_OPS, seq.shape[1], seq.shape[2]
			expanded_seq = seq.unsqueeze(1).expand(batch_size, max_ops, seq_len, hidden_size)
			scores = self.fc_pool(expanded_seq).squeeze(-1).masked_fill(span_mask == 0, -1e4)
			attn = torch.softmax(scores, dim=-1).unsqueeze(-1)
			pooled = (expanded_seq * attn).sum(dim=2)
			sent_logits = self.sent_head(pooled)

		return crf_loss, emissions, sent_logits, self.global_head(seq[:, 0]), seq


class Predictor:
	def __init__(self, model_path=None, device=None):
		self.model_path = model_path or DEFAULT_MODEL_PATH
		self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
		self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
		self.model = ABSAModel().to(self.device).float()
		self._load_weights()
		self.model.eval()

	def _load_weights(self):
		if not os.path.exists(self.model_path):
			raise FileNotFoundError(f"Checkpoint not found: {self.model_path}")

		state = torch.load(self.model_path, map_location=self.device)
		if isinstance(state, dict):
			for key in ["state_dict", "model_state_dict", "model"]:
				if key in state and isinstance(state[key], dict):
					state = state[key]
					break

		if not isinstance(state, dict):
			raise RuntimeError("Unsupported checkpoint format. Expected a state_dict.")

		if any(key.startswith("module.") for key in state):
			state = {key.replace("module.", "", 1): value for key, value in state.items()}

		missing, unexpected = self.model.load_state_dict(state, strict=False)
		if missing or unexpected:
			raise RuntimeError(
				"Checkpoint does not match current train.py architecture. "
				f"Missing keys: {missing}. Unexpected keys: {unexpected}."
			)

	def _encode(self, text):
		encoded = self.tokenizer(
			text,
			max_length=MAX_LEN,
			padding="max_length",
			truncation=True,
			return_offsets_mapping=True,
			return_special_tokens_mask=True,
			return_tensors="pt",
		)
		offsets = encoded.pop("offset_mapping")[0]
		spec_mask = encoded.pop("special_tokens_mask")[0].bool()
		ids = encoded["input_ids"].to(self.device)
		mask = encoded["attention_mask"].to(self.device)
		return ids, mask, offsets, spec_mask

	def predict(self, text):
		text = nfc(text)
		ids, mask, offsets, spec_mask = self._encode(text)
		autocast_ctx = torch.autocast(device_type="cuda", dtype=torch.float16) if self.device.type == "cuda" else nullcontext()

		with torch.inference_mode():
			with autocast_ctx:
				_, emissions, _, global_logits, cached_seq = self.model(ids, mask)

			decoded = self.model.crf.decode(emissions, mask=mask.bool())[0]
			valid_len = int(mask[0].sum().item())
			spans = extract_spans(decoded[:valid_len])

			pred_span_mask = torch.zeros(1, MAX_OPS, ids.shape[1], device=self.device)
			sliced = [(list(range(start, end + 1)), aspect, 0) for start, end, aspect in spans[:MAX_OPS]]
			for idx, (start_tok, end_tok, _) in enumerate(spans[:MAX_OPS]):
				lo, hi = context_window(
					start_tok,
					end_tok,
					idx,
					sliced,
					ids.shape[1],
				)
				for token_idx in range(lo, hi + 1):
					if not spec_mask[token_idx]:
						pred_span_mask[0, idx, token_idx] = 1.0

			span_logits = None
			if spans:
				with autocast_ctx:
					_, _, span_logits, _, _ = self.model(ids, mask, span_mask=pred_span_mask, cached_seq=cached_seq)

		global_probs = torch.softmax(global_logits[0], dim=-1).detach().cpu()
		opinions = []
		for idx, (start_tok, end_tok, aspect) in enumerate(spans[:MAX_OPS]):
			char_start = int(offsets[start_tok][0].item())
			char_end = int(offsets[end_tok][1].item())
			target = text[char_start:char_end]
			sentiment_id = 2
			sentiment_conf = None
			if span_logits is not None:
				sentiment_probs = torch.softmax(span_logits[0, idx], dim=-1).detach().cpu()
				sentiment_id = int(sentiment_probs.argmax().item())
				sentiment_conf = float(sentiment_probs[sentiment_id].item())

			opinions.append(
				{
					"target": target,
					"aspect": aspect,
					"sentiment": SENTIMENT_LABELS[sentiment_id],
					"sentiment_id": sentiment_id,
					"start": char_start,
					"end": char_end,
					"token_start": start_tok,
					"token_end": end_tok,
					"confidence": sentiment_conf,
				}
			)

		global_id = int(global_probs.argmax().item())
		return {
			"text": text,
			"global_sentiment": {
				"label": SENTIMENT_LABELS[global_id],
				"sentiment_id": global_id,
				"confidence": float(global_probs[global_id].item()),
				"probabilities": {
					SENTIMENT_LABELS[idx]: float(global_probs[idx].item()) for idx in range(N_SENT)
				},
			},
			"opinions": opinions,
		}


_PREDICTOR = None


def get_predictor(model_path=None):
	global _PREDICTOR
	if _PREDICTOR is None or (model_path and os.path.abspath(model_path) != os.path.abspath(_PREDICTOR.model_path)):
		_PREDICTOR = Predictor(model_path=model_path)
	return _PREDICTOR


def lambda_handler(event, context):
	body = event
	if isinstance(event, dict) and "body" in event:
		body = event["body"]
		if isinstance(body, str):
			body = json.loads(body)

	if isinstance(body, str):
		body = {"text": body}

	if not isinstance(body, dict):
		raise ValueError("Expected event body to be a dict or JSON string.")

	model_path = body.get("model_path")
	predictor = get_predictor(model_path=model_path)

	if "texts" in body:
		predictions = [predictor.predict(text) for text in body["texts"]]
	elif "text" in body:
		predictions = predictor.predict(body["text"])
	else:
		raise ValueError("Provide 'text' or 'texts' in the request body.")

	return {"statusCode": 200, "body": json.dumps(predictions, ensure_ascii=False)}


def main():
	parser = argparse.ArgumentParser(description="Inference for current train.py checkpoint")
	parser.add_argument("--model-path", default=DEFAULT_MODEL_PATH, help="Path to model checkpoint")
	parser.add_argument("--text", action="append", help="Input text to predict. Can be passed multiple times.")
	parser.add_argument("--input-file", help="Text or JSONL file. TXT: one sample per line. JSONL: {'text': ...} per line.")
	parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
	args = parser.parse_args()

	predictor = get_predictor(model_path=args.model_path)
	texts = []

	if args.text:
		texts.extend(args.text)

	if args.input_file:
		with open(args.input_file, encoding="utf-8") as handle:
			for line in handle:
				line = line.strip()
				if not line:
					continue
				if args.input_file.endswith(".jsonl"):
					texts.append(json.loads(line)["text"])
				else:
					texts.append(line)

	if not texts:
		while True:
			try:
				line = input("Nhap text de test (de trong de thoat): ").strip()
			except EOFError:
				break
			if not line:
				break
			result = predictor.predict(line)
			print(json.dumps(result, ensure_ascii=False, indent=2))
		return

	results = [predictor.predict(text) for text in texts]
	payload = results[0] if len(results) == 1 else results
	print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None))


if __name__ == "__main__":
	main()
