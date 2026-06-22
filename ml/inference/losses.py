"""Loss functions — extracted verbatim from train/train.py.

Do NOT modify formulas. Any change breaks training reproducibility.
"""

from __future__ import annotations

import math

import torch
import torch.nn.functional as F

from .utils import is_gold_contrast


# ---------------------------------------------------------------------------
# Contrast loss — verbatim
# ---------------------------------------------------------------------------

def contrast_loss_fn(span_features, span_sent, global_sent, margin, device):
    loss, n = torch.tensor(0.0, device=device), 0
    for b in range(span_features.shape[0]):
        if not is_gold_contrast(span_sent[b]):
            continue
        v_idx = (span_sent[b] != -100).nonzero().flatten()
        if v_idx.numel() < 2:
            continue
        feats = F.normalize(span_features[b][v_idx], dim=-1)
        labels = span_sent[b][v_idx]
        neg_sims = []
        pos_sims = []
        for i in range(v_idx.numel()):
            for j in range(i + 1, v_idx.numel()):
                sim = F.cosine_similarity(feats[i].unsqueeze(0), feats[j].unsqueeze(0)).squeeze()
                if labels[i] != labels[j]:
                    neg_sims.append(sim)
                else:
                    pos_sims.append(sim)
        if neg_sims:
            hard_neg = torch.stack(neg_sims)
            top_k = min(3, hard_neg.numel())
            neg_loss = F.relu(hard_neg.topk(top_k).values - margin).mean()
        else:
            neg_loss = torch.tensor(0.0, device=device)
        if pos_sims:
            pos_loss = F.relu(0.55 - torch.stack(pos_sims)).mean()
        else:
            pos_loss = torch.tensor(0.0, device=device)
        pair_loss = neg_loss + 0.5 * pos_loss
        if pair_loss.detach().item() > 0:
            weight = 2.0 if global_sent[b].item() == 2 else 1.0
            loss  += weight * pair_loss
            n     += 1
    return loss / max(n, 1)


# ---------------------------------------------------------------------------
# Smoothed cross-entropy helpers — verbatim
# ---------------------------------------------------------------------------

def smooth_values_for_targets(targets, label_smoothing, n_classes):
    if isinstance(label_smoothing, (list, tuple)):
        smooth = torch.tensor(label_smoothing, dtype=torch.float32, device=targets.device)
        if smooth.numel() != n_classes:
            raise ValueError(f"label_smoothing must have {n_classes} values, got {smooth.numel()}")
        return smooth[targets]
    return torch.full(
        (targets.shape[0],),
        float(label_smoothing),
        dtype=torch.float32,
        device=targets.device,
    )


def smoothed_ce_per_sample(logits, targets, weight=None, ignore_index=-100, label_smoothing=0.0):
    valid = (targets != ignore_index)
    if not valid.any():
        return logits.new_zeros((0,)), valid

    logits_valid = logits[valid]
    targets_valid = targets[valid]
    n_classes = logits_valid.shape[-1]
    smoothing = smooth_values_for_targets(targets_valid, label_smoothing, n_classes).to(logits_valid.dtype)
    log_probs = F.log_softmax(logits_valid, dim=-1)
    true_dist = torch.zeros_like(log_probs)
    true_dist.scatter_(1, targets_valid.unsqueeze(1), 1.0)
    if n_classes > 1:
        true_dist = true_dist * (1.0 - smoothing.unsqueeze(1)) + \
                    (1.0 - true_dist) * (smoothing.unsqueeze(1) / (n_classes - 1))
    losses = -(true_dist * log_probs).sum(dim=-1)
    if weight is not None:
        losses = losses * weight[targets_valid]
    return losses, valid


def smoothed_cross_entropy(logits, targets, weight=None, ignore_index=-100, label_smoothing=0.0):
    losses, valid = smoothed_ce_per_sample(
        logits,
        targets,
        weight=weight,
        ignore_index=ignore_index,
        label_smoothing=label_smoothing,
    )
    if valid.any():
        return losses.mean()
    return logits.sum() * 0.0


def focal_loss(logits, targets, weight=None, gamma=2.0, ignore_index=-100, label_smoothing=0.0):
    ce, valid = smoothed_ce_per_sample(
        logits,
        targets,
        weight=weight,
        ignore_index=ignore_index,
        label_smoothing=label_smoothing,
    )
    if not valid.any():
        return logits.sum() * 0.0
    logits_valid = logits[valid]
    targets_valid = targets[valid]
    pt = F.softmax(logits_valid, dim=-1).gather(1, targets_valid.unsqueeze(1)).squeeze(1).clamp_min(1e-6)
    focal = ((1.0 - pt) ** gamma) * ce
    return focal.mean()


def symmetric_kl_loss(logits_a, logits_b):
    if logits_a.numel() == 0 or logits_b.numel() == 0:
        return logits_a.sum() * 0.0
    log_pa = F.log_softmax(logits_a, dim=-1)
    log_pb = F.log_softmax(logits_b, dim=-1)
    pa = log_pa.exp()
    pb = log_pb.exp()
    return 0.5 * (
        F.kl_div(log_pa, pb, reduction="batchmean") +
        F.kl_div(log_pb, pa, reduction="batchmean")
    )


# ---------------------------------------------------------------------------
# Loss-balanced task weighter — verbatim
# ---------------------------------------------------------------------------

class LBTWWeighter:
    def __init__(self, base_weights, ema_decay=0.99, clamp_min=0.3, clamp_max=3.0, eps=1e-6):
        self.base_weights = {name: float(value) for name, value in base_weights.items()}
        self.ema_decay = ema_decay
        self.clamp_min = clamp_min
        self.clamp_max = clamp_max
        self.eps = eps
        self.ema = {name: None for name in self.base_weights}

    def base_snapshot(self, active_names=None):
        active_set = set(self.base_weights.keys()) if active_names is None else set(active_names)
        return {
            name: (weight if name in active_set else 0.0)
            for name, weight in self.base_weights.items()
        }

    def compute_weights(self, losses):
        ratios = {}
        active_names = []

        for name, loss in losses.items():
            value = float(loss.detach().item())
            if not math.isfinite(value):
                value = self.ema[name] if self.ema[name] is not None else 0.0
            ema_prev = self.ema.get(name)
            ema_value = value if ema_prev is None else self.ema_decay * ema_prev + (1.0 - self.ema_decay) * value
            self.ema[name] = ema_value
            ratios[name] = value / max(ema_value, self.eps)
            active_names.append(name)

        if not active_names:
            return self.base_snapshot(active_names=[])

        ratio_sum = sum(ratios.values())
        n_active = len(active_names)
        weights = self.base_snapshot(active_names=[])

        for name in active_names:
            factor = n_active * ratios[name] / max(ratio_sum, self.eps)
            factor = min(max(factor, self.clamp_min), self.clamp_max)
            weights[name] = self.base_weights[name] * factor

        return weights

    def combine(self, losses, weights):
        total = None
        for name, loss in losses.items():
            weighted = weights[name] * loss
            total = weighted if total is None else total + weighted
        if total is None:
            raise ValueError("No losses were provided to LBTWWeighter.combine")
        return total
