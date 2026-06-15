"""ABSAModel — extracted verbatim from train/train.py.

Layer names, forward signature, and architecture are frozen.
Do NOT rename layers; doing so breaks checkpoint compatibility.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchcrf import CRF
from transformers import AutoModel

from .labels import ASPECTS, N_BIO, N_SENT


# ---------------------------------------------------------------------------
# Contrast feature helper — verbatim from train/train.py
# ---------------------------------------------------------------------------

CONTRAST_WORDS = {"nhưng", "tuy", "dù", "mà", "song", "còn"}


def extract_contrast_feature(sequence, offsets_batch, text_batch, mask):
    """
    Tìm hidden state của contrast words dựa trên char offsets thay vì subword tokens.
    Tránh bug khi ViBERTa split "nhưng" thành nhiều piece.
    Tránh inplace ops trên tensors có grad_fn để không phá autograd graph.
    """
    B, L, H = sequence.shape
    per_batch = []

    for b in range(B):
        text    = text_batch[b].lower()
        offsets = offsets_batch[b]
        found   = []
        for i in range(L):
            if mask[b, i]:
                continue
            cs  = int(offsets[i, 0])
            ce  = int(offsets[i, 1])
            tok = text[cs:ce].strip()
            if tok in CONTRAST_WORDS:
                found.append(sequence[b, i])
        if found:
            summed = torch.stack(found, dim=0).sum(0)   # no inplace
            per_batch.append(F.normalize(summed, dim=0))
        else:
            per_batch.append(sequence.new_zeros(H))

    return torch.stack(per_batch, dim=0)  # (B, H)


def compute_clause_position(span_start, span_end, offsets_row, text, seq_len):
    contrast_words = {"nhưng", "tuy", "dù", "mà", "song", "còn", "tuy_nhiên", "thế_nhưng"}
    contrast_pos = None
    for idx in range(seq_len):
        cs = int(offsets_row[idx][0])
        ce = int(offsets_row[idx][1])
        token = text[cs:ce].lower().strip()
        if token in contrast_words:
            contrast_pos = idx
            break
    if contrast_pos is None:
        return 0
    center = 0.5 * (span_start + span_end)
    return 1 if center < contrast_pos else 2


# ---------------------------------------------------------------------------
# Model — verbatim from train/train.py
# ---------------------------------------------------------------------------

class ABSAModel(nn.Module):
    def __init__(self, model_name: str, max_ops: int):
        super().__init__()
        self.max_ops  = max_ops
        self.backbone = AutoModel.from_pretrained(model_name)
        h             = self.backbone.config.hidden_size
        self.dropout      = nn.Dropout(0.3)
        self.bio_lstm     = nn.LSTM(h, h // 2, num_layers=1, batch_first=True, bidirectional=True)
        self.bio_head     = nn.Linear(h, N_BIO)
        self.crf          = CRF(N_BIO, batch_first=True)
        self.fc_pool      = nn.Linear(h, 1)
        self.span_proj    = nn.Linear(h * 4, h)
        self.cross_attn   = nn.MultiheadAttention(h, num_heads=8, dropout=0.1, batch_first=True)
        self.cross_attn_scale = nn.Parameter(torch.tensor(0.5))
        self.cross_attn_norm  = nn.LayerNorm(h)
        self.span_self_attn = nn.MultiheadAttention(h, num_heads=4, dropout=0.1, batch_first=True)
        self.aspect_embed = nn.Embedding(len(ASPECTS) + 1, h, padding_idx=len(ASPECTS))
        self.aspect_scale = nn.Parameter(torch.tensor(0.8))
        self.clause_pos_embed = nn.Embedding(3, h)
        self.clause_pos_scale = nn.Parameter(torch.tensor(0.5))
        self.sent_head    = nn.Sequential(
            nn.Linear(h, h),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(h, h // 2),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(h // 2, N_SENT),
        )
        # Polarity-aware global head: [cls, neg_pool, pos_pool, contra_vec] → h → N_SENT
        self.global_polarity_fusion = nn.Linear(h * 4, h)
        self.global_head  = nn.Sequential(nn.Dropout(0.2), nn.Linear(h, N_SENT))

    def forward(self, ids, mask, span_mask=None, bio=None, cached_seq=None,
                span_aspect=None, span_clause_pos=None, offsets=None, texts=None):
        seq      = self.dropout(self.backbone(ids, attention_mask=mask).last_hidden_state) \
                   if cached_seq is None else cached_seq
        B        = seq.shape[0]
        bio_feat, _ = self.bio_lstm(seq)
        emiss    = self.bio_head(bio_feat)
        crf_loss = -self.crf(emiss.float(), bio, mask=mask.bool(), reduction="mean") \
                   if bio is not None else None

        sent_logits = None
        span_features = None
        if span_mask is not None:
            B2, L, H = seq.shape
            M        = span_mask.shape[1]
            exp_seq  = seq.unsqueeze(1).expand(B2, M, L, H)
            scores   = self.fc_pool(exp_seq).squeeze(-1).masked_fill(span_mask == 0, -1e4)
            attn     = torch.softmax(scores, dim=-1).unsqueeze(-1)
            pooled   = (exp_seq * attn).sum(dim=2)          # (B, M, H)

            # Contrast feature — Fix: dùng char offsets
            if offsets is not None and texts is not None:
                c_vec  = extract_contrast_feature(seq, offsets, texts, ~mask.bool())
                pooled = pooled + 0.3 * c_vec.unsqueeze(1)

            # CLS residual
            pooled = pooled + seq[:, 0].unsqueeze(1)

            if span_aspect is not None:
                pooled = pooled + self.aspect_scale * self.aspect_embed(span_aspect)

            if span_clause_pos is not None:
                pooled = pooled + self.clause_pos_scale * self.clause_pos_embed(span_clause_pos)
            elif offsets is not None and texts is not None:
                clause_pos_ids = torch.zeros((B2, M), dtype=torch.long, device=seq.device)
                for b_idx in range(B2):
                    for m_idx in range(M):
                        active = (span_mask[b_idx, m_idx] > 0).nonzero(as_tuple=False).flatten()
                        if active.numel() == 0:
                            continue
                        span_start = int(active.min().item())
                        span_end = int(active.max().item())
                        clause_pos_ids[b_idx, m_idx] = compute_clause_position(
                            span_start,
                            span_end,
                            offsets[b_idx],
                            texts[b_idx],
                            L,
                        )
                pooled = pooled + self.clause_pos_scale * self.clause_pos_embed(clause_pos_ids)

            span_active = span_mask > 0
            valid_span_slots = span_active.any(dim=-1, keepdim=True).float()
            span_padding_mask = ~span_active.any(dim=-1)

            pos_ids = torch.arange(L, device=seq.device).view(1, 1, L).expand(B2, M, L)
            start_pos = pos_ids.masked_fill(~span_active, L).min(dim=-1).values
            end_pos = pos_ids.masked_fill(~span_active, -1).max(dim=-1).values
            empty_spans = span_padding_mask
            start_pos = start_pos.masked_fill(empty_spans, 0).long()
            end_pos = end_pos.masked_fill(empty_spans, 0).long()

            batch_ids = torch.arange(B2, device=seq.device).view(B2, 1).expand(B2, M)
            start_repr = seq[batch_ids, start_pos] * valid_span_slots
            end_repr = seq[batch_ids, end_pos] * valid_span_slots
            boundary_feat = torch.cat([pooled, start_repr, end_repr, start_repr * end_repr], dim=-1)
            pooled = self.span_proj(boundary_feat)

            cross_out, _ = self.cross_attn(
                pooled,
                seq,
                seq,
                key_padding_mask=~mask.bool(),
                need_weights=False,
            )
            pooled = self.cross_attn_norm(pooled + self.cross_attn_scale * cross_out * valid_span_slots)

            span_interact, _ = self.span_self_attn(
                pooled,
                pooled,
                pooled,
                key_padding_mask=span_padding_mask,
                need_weights=False,
            )
            pooled = pooled + span_interact * valid_span_slots
            span_features = pooled

            sent_logits = self.sent_head(pooled)            # (B, M, N_SENT)

        # Global head — polarity-aware pooling over span_features
        # For mixed reviews: neg_pool and pos_pool carry distinct signal;
        # contra_vec = neg_pool − pos_pool is the contradiction-aware direction.
        cls_repr = seq[:, 0]
        h_dim = seq.shape[-1]
        if sent_logits is not None and span_features is not None:
            valid_spans = (span_mask.sum(dim=-1) > 0).float()      # (B, M)
            # Prevent global loss from directly pulling sentiment logits.
            span_probs  = sent_logits.detach().softmax(-1)          # (B, M, 3)
            neg_w = span_probs[:, :, 0] * valid_spans              # (B, M)
            pos_w = span_probs[:, :, 1] * valid_spans
            neg_pool = (span_features * neg_w.unsqueeze(-1)).sum(1) / neg_w.sum(1, keepdim=True).clamp(min=1e-4)
            pos_pool = (span_features * pos_w.unsqueeze(-1)).sum(1) / pos_w.sum(1, keepdim=True).clamp(min=1e-4)
            contra_vec = neg_pool - pos_pool                        # explicit contradiction signal
        else:
            neg_pool = pos_pool = contra_vec = seq.new_zeros(B, h_dim)

        fused = F.gelu(self.global_polarity_fusion(
            torch.cat([cls_repr, neg_pool, pos_pool, contra_vec], dim=-1)
        ))
        global_logits = self.global_head(fused)

        return crf_loss, emiss, sent_logits, global_logits, seq, span_features
