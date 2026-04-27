import os, sys, subprocess# 1. KHỞI TẠO HỆ THỐNG & CÀI ĐẶT THƯ VIỆNos.environ["TRITON_INTERPRET"] = "1"os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"def install_deps():
    try:
        from torchcrf import CRF
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyvi", "pytorch-crf", "transformers", "-q"])install_deps()import json, unicodedata, random, csv, argparseimport numpy as npimport torchimport torch.nn as nnimport torch.nn.functional as Ffrom torch.utils.data import Dataset, DataLoader, WeightedRandomSamplerfrom transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmupfrom torch.optim import AdamWfrom torchcrf import CRFfrom sklearn.metrics import f1_scorefrom tqdm.auto import tqdm# =========================# CONFIG# =========================MODEL_NAME      = "Fsoft-AIC/videberta-base"TRAIN_FILE      = "/kaggle/input/datasets/minhhuy304/data-absa/data_train_v5.jsonl"VAL_FILE        = "/kaggle/input/datasets/minhhuy304/data-absa/val_data.jsonl"MODEL_SAVE      = "/kaggle/working/best_model_v5.pt"MAX_LEN, EPOCHS, PATIENCE, PHASE1_EPOCHS, MAX_OPS = 224, 30, 7, 5, 8LR_BACKBONE, LR_HEADS, WARMUP_RATIO = 8e-6, 3e-5, 0.1MAX_CONTEXT_WINDOW, SPAN_MATCH_IOU, CONTRAST_MARGIN = 12, 0.5, 0.25LAMBDA_BIO, LAMBDA_SENT, LAMBDA_GLOBAL, LAMBDA_CONS, LAMBDA_CONTRAST = 1.5, 1.0, 0.5, 0.1, 0.1DEVICE  = torch.device("cuda" if torch.cuda.is_available() else "cpu")ASPECTS = ["Fashion", "Electronics", "General", "Service", "Ship", "Price", "App"]def build_bio():
    labels = ["O"]
    for a in ASPECTS: labels += [f"B-{a}", f"I-{a}"]
    return labels, {l: i for i, l in enumerate(labels)}, {i: l for i, l in enumerate(labels)}BIO_LABELS, BIO_L2I, BIO_I2L = build_bio()N_BIO, N_SENT = len(BIO_LABELS), 3# =========================# UTILS# =========================def nfc(x): return unicodedata.normalize("NFC", x)def set_seed(seed=42):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)def is_gold_contrast(span_sent_tensor):
    v = span_sent_tensor[span_sent_tensor != -100]
    return len(v) >= 2 and len(v.unique()) >= 2def compute_clause_aware_window(tmin, tmax, op_idx, span_token_lists, offsets, text, seq_len):
    lo, hi = max(tmin - MAX_CONTEXT_WINDOW, 1), min(tmax + MAX_CONTEXT_WINDOW, seq_len - 1)
    stops = {",", ".", "!", "?", ";", ":"}
    bounds = {"nhưng", "tuy", "dù", "mà", "song", "còn", "tuy_nhiên", "thế_mà", "thế_nhưng"}
    if op_idx > 0: lo = max(lo, max(span_token_lists[op_idx - 1]) + 1)
    if op_idx < len(span_token_lists) - 1: hi = min(hi, min(span_token_lists[op_idx + 1]) - 1)
    for ci in range(tmin - 1, lo - 1, -1):
        if 0 < ci < seq_len:
            cs, ce = int(offsets[ci][0]), int(offsets[ci][1])
            if text[cs:ce].lower().strip() in stops: lo = ci + 1; break
    for ci in range(tmax + 1, hi + 1):
        if 0 < ci < seq_len:
            cs, ce = int(offsets[ci][0]), int(offsets[ci][1])
            txt = text[cs:ce].lower().strip()
            if txt in stops or txt in bounds: hi = ci - 1; break
    return lo, hidef extract_spans(seq):
    spans, start, cur = set(), None, None
    for i, lid in enumerate(seq):
        tag = BIO_I2L.get(lid, "O")
        if tag.startswith("B-"):
            if start is not None: spans.add((start, i - 1, cur))
            start, cur = i, tag[2:]
        elif not (tag.startswith("I-") and cur == tag[2:]):
            if start is not None: spans.add((start, i - 1, cur))
            start, cur = None, None
    if start is not None: spans.add((start, len(seq) - 1, cur))
    return spans# =========================# DATASET & MODEL# =========================class ABSADataset(Dataset):
    def __init__(self, file, tokenizer, max_len):
        self.items = []
        with open(file, encoding="utf-8") as f: lines = f.readlines()
        print(f"Pre-tokenizing {len(lines)} records...")
        for line in lines:
            rec = json.loads(line); text = nfc(rec["text"])
            enc = tokenizer(text, max_length=max_len, padding="max_length", truncation=True, return_offsets_mapping=True, return_special_tokens_mask=True)
            offsets, spec_mask = enc.pop("offset_mapping"), enc.pop("special_tokens_mask")
            L = len(enc["input_ids"])
            bio, s_mask = [0]*L, torch.zeros(MAX_OPS, L)
            s_sent, v_ops = torch.full((MAX_OPS,), -100, dtype=torch.long), []
            for op in rec.get("opinions", []):
                s, e, asp, sent = op.get("start", -1), op.get("end", -1), op.get("aspect", ""), op.get("sentiment", -1)
                if not asp or sent == -1: continue
                tokens = [i for i, (a, b) in enumerate(offsets) if not spec_mask[i] and max(a, s) < min(b, e)]
                if tokens: v_ops.append((tokens, asp, sent))
            v_ops.sort(key=lambda x: x[0][0])
            st_lists = [v[0] for v in v_ops[:MAX_OPS]]
            for idx, (tokens, asp, sent) in enumerate(v_ops[:MAX_OPS]):
                for k, i in enumerate(tokens): bio[i] = BIO_L2I[f"B-{asp}" if k == 0 else f"I-{asp}"]
                lo, hi = compute_clause_aware_window(min(tokens), max(tokens), idx, st_lists, offsets, text, L)
                for i in range(lo, hi + 1): 
                    if not spec_mask[i]: s_mask[idx, i] = 1.0
                s_sent[idx] = sent
            self.items.append({"ids": torch.tensor(enc["input_ids"]), "mask": torch.tensor(enc["attention_mask"]), "offsets": torch.tensor(offsets), "spec_mask": torch.tensor(spec_mask, dtype=torch.bool), "bio": torch.tensor(bio), "span_mask": s_mask, "span_sent": s_sent, "text": text, "global": torch.tensor(rec.get("global_sentiment", -1))})
    def __len__(self): return len(self.items)
    def __getitem__(self, i): return self.items[i]class ABSAModel(nn.Module):
    def __init__(self):
        super().__init__(); self.backbone = AutoModel.from_pretrained(MODEL_NAME); h = self.backbone.config.hidden_size
        self.dropout, self.bio_head, self.crf, self.fc_pool = nn.Dropout(0.3), nn.Linear(h, N_BIO), CRF(N_BIO, batch_first=True), nn.Linear(h, 1)
        self.sent_head, self.global_head = nn.Sequential(nn.Dropout(0.2), nn.Linear(h, N_SENT)), nn.Linear(h, N_SENT)
    def forward(self, ids, mask, span_mask=None, bio=None, cached_seq=None):
        seq = self.dropout(self.backbone(ids, attention_mask=mask).last_hidden_state) if cached_seq is None else cached_seq
        emiss = self.bio_head(seq); crf_l = -self.crf(emiss, bio, mask=mask.bool(), reduction="mean") if bio is not None else None
        s_log = None
        if span_mask is not None:
            B, M, L, h_dim = ids.shape[0], MAX_OPS, seq.shape[1], seq.shape[2]
            score = self.fc_pool(seq.unsqueeze(1).expand(B, M, L, h_dim)).squeeze(-1).masked_fill(span_mask == 0, -1e4)
            s_log = self.sent_head((seq.unsqueeze(1).expand(B, M, L, h_dim) * torch.softmax(score, dim=-1).unsqueeze(-1)).sum(dim=2))
        return crf_l, emiss, s_log, self.global_head(seq[:, 0]), seqdef contrast_loss_fn(s_log, s_sent, g_glob):
    loss, n = torch.tensor(0.0, device=DEVICE), 0
    for b in range(s_log.shape[0]):
        if not is_gold_contrast(s_sent[b]): continue
        v_idx = (s_sent[b] != -100).nonzero().flatten()
        if v_idx.numel() < 2: continue
        probs, labels = torch.softmax(s_log[b][v_idx], dim=-1), s_sent[b][v_idx]
        p_loss, p_cnt = torch.tensor(0.0, device=DEVICE), 0
        for i in range(v_idx.numel()):
            for j in range(i + 1, v_idx.numel()):
                if labels[i] != labels[j]:
                    sim = F.cosine_similarity(probs[i].unsqueeze(0), probs[j].unsqueeze(0)).squeeze()
                    p_loss += F.relu(sim - CONTRAST_MARGIN); p_cnt += 1
        if p_cnt > 0: loss += (2.0 if g_glob[b] == 2 else 1.0) * (p_loss / p_cnt); n += 1
    return loss / max(n, 1)# =========================# EVALUATION# =========================def evaluate(model, dl):
    model.eval(); p_all, g_all, s_p, s_g, gb_p, gb_g = [], [], [], [], [], []
    with torch.inference_mode():
        for b in dl:
            ids, mask, spec, bio, s_sent, glob = [b[k].to(DEVICE) for k in ["ids", "mask", "spec_mask", "bio", "span_sent", "global"]]
            with torch.autocast(device_type="cuda", dtype=torch.float16): _, emiss, _, g_log, cached = model(ids, mask)
            bio_p = model.crf.decode(emiss, mask=mask.bool()); pred_sm = torch.zeros(ids.shape[0], MAX_OPS, ids.shape[1], device=DEVICE)
            for i, seq in enumerate(bio_p):
                ps = sorted(extract_spans(seq)); st_lists = [list(range(t[0], t[1]+1)) for t in ps[:MAX_OPS]]
                for idx, (tmin, tmax, _) in enumerate(ps[:MAX_OPS]):
                    lo, hi = compute_clause_aware_window(tmin, tmax, idx, st_lists, b["offsets"][i], b["text"][i], ids.shape[1])
                    for k in range(lo, hi + 1): 
                        if not spec[i, k]: pred_sm[i, idx, k] = 1.0
            with torch.autocast(device_type="cuda", dtype=torch.float16): _, _, s_log, _, _ = model(ids, mask, span_mask=pred_sm, cached_seq=cached)
            for i in range(ids.shape[0]):
                vl = int(mask[i].sum()); p_set, g_set = extract_spans(bio_p[i][:vl]), extract_spans(bio.tolist()[i][:vl])
                p_all.append(p_set); g_all.append(g_set)
                orig_sents = [s_sent[i, slot].item() for slot in range(MAX_OPS) if s_sent[i, slot] != -100]
                g_sorted = sorted(g_set); g_with_s = [(gs, ge, ga, orig_sents[k]) for k, (gs, ge, ga) in enumerate(g_sorted[:len(orig_sents)])]
                if s_log is not None:
                    p_spans = sorted([(ps, pe, pa) for ps, pe, pa in p_set])[:MAX_OPS]
                    for idx, (ps, pe, pa) in enumerate(p_spans):
                        best_iou, best_gs = 0.0, None
                        for gs, ge, ga, g_sv in g_with_s:
                            if ga != pa: continue
                            inter = max(0, min(pe, ge) - max(ps, gs) + 1); iou = inter / ((pe-ps+1) + (ge-gs+1) - inter)
                            if iou > best_iou: best_iou, best_gs = iou, g_sv
                        if best_iou >= SPAN_MATCH_IOU:
                            s_p.append(s_log[i, idx].argmax().item()); s_g.append(best_gs)
            if (glob != -1).any(): gb_p.extend(g_log.argmax(-1)[glob != -1].cpu().tolist()); gb_g.extend(glob[glob != -1].cpu().tolist())
    tp, fp, fn = sum(len(p & g) for p, g in zip(p_all, g_all)), sum(len(p - g) for p, g in zip(p_all, g_all)), sum(len(g - p) for p, g in zip(p_all, g_all))
    s_f1, sn_f1, gb_f1 = 2 * tp / (2 * tp + fp + fn + 1e-9), f1_score(s_g, s_p, average="macro", zero_division=0) if s_g else 0.0, f1_score(gb_g, gb_p, average="macro", zero_division=0) if gb_g else 0.0
    return 0.5 * s_f1 + 0.3 * sn_f1 + 0.2 * gb_f1, s_f1, sn_f1, gb_f1# =========================# TRAIN ENGINE# =========================set_seed(42); tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)train_ds, val_ds = ABSADataset(TRAIN_FILE, tokenizer, MAX_LEN), ABSADataset(VAL_FILE, tokenizer, MAX_LEN)train_dl = DataLoader(train_ds, batch_size=16, sampler=WeightedRandomSampler([1.5 if is_gold_contrast(it["span_sent"]) else 1.0 for it in train_ds.items], len(train_ds)), num_workers=2, pin_memory=True)val_dl = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=2)model = ABSAModel().to(DEVICE).float()opt = AdamW([{"params": model.backbone.parameters(), "lr": 8e-6, "weight_decay": 0.01}, {"params": [p for n, p in model.named_parameters() if "backbone" not in n], "lr": 3e-5}])sched = get_linear_schedule_with_warmup(opt, int(len(train_dl)*EPOCHS*0.1//2), len(train_dl)*EPOCHS//2); scaler = torch.amp.GradScaler('cuda')best_f1, patience = 0.0, 0for ep in range(1, EPOCHS + 1):
    model.train(); in_p1 = (ep <= PHASE1_EPOCHS); w_scale = min(1.0, (ep - PHASE1_EPOCHS) / 5.0) if not in_p1 else 0.0
    pbar = tqdm(train_dl, desc=f"Ep {ep:02d}")
    for step, b in enumerate(pbar):
        ids, mask, bio, s_mask, s_sent, g = [b[k].to(DEVICE) for k in ["ids", "mask", "bio", "span_mask", "span_sent", "global"]]
        with torch.autocast(device_type="cuda", dtype=torch.float16):
            crf_l, _, s_log, g_log, _ = model(ids, mask, span_mask=None if in_p1 else s_mask, bio=bio)
            l_s = F.cross_entropy(s_log.view(-1, 3), s_sent.view(-1), ignore_index=-100, label_smoothing=0.1) if not in_p1 else torch.tensor(0., device=DEVICE)
            l_g = F.cross_entropy(g_log[g!=-1], g[g!=-1], label_smoothing=0.1) if (g!=-1).any() else torch.tensor(0., device=DEVICE)
            l_ctr = contrast_loss_fn(s_log, s_sent, g) if not in_p1 else torch.tensor(0., device=DEVICE)
            total_l = (LAMBDA_BIO*crf_l + LAMBDA_GLOBAL*l_g + LAMBDA_SENT*l_s + LAMBDA_CONTRAST*w_scale*l_ctr).float() / 2
        
        scaler.scale(total_l).backward()
        if (step + 1) % 2 == 0:
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scale_before = scaler.get_scale()
            scaler.step(opt)
            scaler.update()
            if scaler.get_scale() >= scale_before:  # no overflow → opt.step() ran
                sched.step()
            opt.zero_grad(set_to_none=True)
        pbar.set_postfix({"loss": f"{total_l.item()*2:.3f}"})
    
    comp, span, sent, glob = evaluate(model, val_dl)
    print(f"Ep {ep} | Comp: {comp:.4f} | Span: {span:.4f} | Sent: {sent:.4f} | Glob: {glob:.4f}")
    if comp > best_f1: 
        best_f1, patience = comp, 0; torch.save(model.state_dict(), MODEL_SAVE)
        print(f"--- ⭐ New Best: {best_f1:.4f} ---")
    else: patience += 1
    if not in_p1 and patience >= PATIENCE: print("Early stopping."); break

Notes:
- UNEXPECTED	:can be ignored when loading from different task/architecture; not ok if you expect identical arch.
Ep 1 | Comp: 0.0421 | Span: 0.0030 | Sent: 0.0000 | Glob: 0.2031
--- ⭐ New Best: 0.0421 ---
Ep 2 | Comp: 0.0366 | Span: 0.0000 | Sent: 0.0000 | Glob: 0.1832
Ep 3 | Comp: 0.0980 | Span: 0.0045 | Sent: 0.2000 | Glob: 0.1784
--- ⭐ New Best: 0.0980 ---
Ep 4 | Comp: 0.0910 | Span: 0.0407 | Sent: 0.0837 | Glob: 0.2275
Ep 5 | Comp: 0.1934 | Span: 0.2052 | Sent: 0.1536 | Glob: 0.2239
--- ⭐ New Best: 0.1934 ---
Ep 6 | Comp: 0.3134 | Span: 0.3005 | Sent: 0.3911 | Glob: 0.2292
--- ⭐ New Best: 0.3134 ---
Ep 7 | Comp: 0.3762 | Span: 0.3801 | Sent: 0.4270 | Glob: 0.2900
--- ⭐ New Best: 0.3762 ---
Ep 8 | Comp: 0.4109 | Span: 0.4459 | Sent: 0.4421 | Glob: 0.2766
--- ⭐ New Best: 0.4109 ---
Ep 9 | Comp: 0.4495 | Span: 0.4943 | Sent: 0.4593 | Glob: 0.3228
--- ⭐ New Best: 0.4495 ---
Ep 10 | Comp: 0.4550 | Span: 0.5069 | Sent: 0.4692 | Glob: 0.3039
--- ⭐ New Best: 0.4550 ---
Ep 11 | Comp: 0.4726 | Span: 0.5332 | Sent: 0.4525 | Glob: 0.3515
--- ⭐ New Best: 0.4726 ---
Ep 12 | Comp: 0.4887 | Span: 0.5589 | Sent: 0.4624 | Glob: 0.3527
--- ⭐ New Best: 0.4887 ---
Ep 13 | Comp: 0.5033 | Span: 0.5809 | Sent: 0.4647 | Glob: 0.3672
--- ⭐ New Best: 0.5033 ---
Ep 14 | Comp: 0.5125 | Span: 0.5997 | Sent: 0.4660 | Glob: 0.3642
--- ⭐ New Best: 0.5125 ---
Ep 15 | Comp: 0.5251 | Span: 0.6209 | Sent: 0.4644 | Glob: 0.3767
--- ⭐ New Best: 0.5251 ---
Ep 16 | Comp: 0.5245 | Span: 0.6216 | Sent: 0.4588 | Glob: 0.3801
Ep 17 | Comp: 0.5320 | Span: 0.6352 | Sent: 0.4546 | Glob: 0.3903
--- ⭐ New Best: 0.5320 ---
Ep 18 | Comp: 0.5391 | Span: 0.6466 | Sent: 0.4592 | Glob: 0.3903
--- ⭐ New Best: 0.5391 ---
Ep 19 | Comp: 0.5368 | Span: 0.6458 | Sent: 0.4554 | Glob: 0.3864
Ep 20 | Comp: 0.5456 | Span: 0.6535 | Sent: 0.4718 | Glob: 0.3862
--- ⭐ New Best: 0.5456 ---
Ep 21 | Comp: 0.5379 | Span: 0.6517 | Sent: 0.4550 | Glob: 0.3779
Ep 22 | Comp: 0.5452 | Span: 0.6601 | Sent: 0.4617 | Glob: 0.3832
Ep 23 | Comp: 0.5469 | Span: 0.6618 | Sent: 0.4600 | Glob: 0.3900
--- ⭐ New Best: 0.5469 ---
Ep 24 | Comp: 0.5491 | Span: 0.6604 | Sent: 0.4659 | Glob: 0.3957
--- ⭐ New Best: 0.5491 ---
Ep 25 | Comp: 0.5517 | Span: 0.6691 | Sent: 0.4655 | Glob: 0.3874
--- ⭐ New Best: 0.5517 ---
Ep 26 | Comp: 0.5559 | Span: 0.6683 | Sent: 0.4654 | Glob: 0.4108
--- ⭐ New Best: 0.5559 ---
Ep 27 | Comp: 0.5532 | Span: 0.6659 | Sent: 0.4689 | Glob: 0.3981
Ep 28 | Comp: 0.5539 | Span: 0.6658 | Sent: 0.4670 | Glob: 0.4046
Ep 29 | Comp: 0.5526 | Span: 0.6639 | Sent: 0.4684 | Glob: 0.4008
Ep 30 | Comp: 0.5552 | Span: 0.6650 | Sent: 0.4710 | Glob: 0.4070
đây là script train trước thấy cũng y chang