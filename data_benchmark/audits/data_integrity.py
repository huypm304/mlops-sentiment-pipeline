#!/usr/bin/env python3
"""
Data Integrity Audit Beyond Leakage
====================================

Checks:
1. Style divergence: text length, vocab, opinion density distributions
2. Template overlap: opening trigrams, common phrases per split
3. Lexical diversity: unique patterns per aspect-sentiment
4. Source independence: detect systematic style bias across splits

Output: data_integrity_style_analysis.json
"""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from difflib import SequenceMatcher


def tokenize_vietnamese(text: str) -> List[str]:
    """Basic Vietnamese tokenization (split on spaces + normalize)"""
    text = text.lower().strip()
    # Split on spaces and common punctuation
    tokens = re.sub(r'[^\w\s]', ' ', text).split()
    return [t for t in tokens if t]


def get_trigrams(tokens: List[str]) -> List[Tuple[str, str, str]]:
    """Extract 3-grams from token sequence"""
    return [tuple(tokens[i:i+3]) for i in range(len(tokens) - 2)]


def get_opening_trigrams(text: str, num_words: int = 3) -> str:
    """Get first N words of text (opening pattern)"""
    tokens = tokenize_vietnamese(text)
    return ' '.join(tokens[:min(num_words, len(tokens))])


def compute_style_metrics(samples: List[Dict]) -> Dict:
    """Compute style metrics for a dataset split"""
    text_lengths = []
    vocab_set = set()
    opinion_counts = []
    all_tokens = []
    
    for sample in samples:
        text = sample.get('text', '')
        tokens = tokenize_vietnamese(text)
        
        text_lengths.append(len(tokens))
        vocab_set.update(tokens)
        all_tokens.extend(tokens)
        opinion_counts.append(len(sample.get('opinions', [])))
    
    text_lengths = np.array(text_lengths)
    opinion_counts = np.array(opinion_counts)
    
    return {
        'num_samples': len(samples),
        'text_length': {
            'mean': float(text_lengths.mean()),
            'std': float(text_lengths.std()),
            'min': int(text_lengths.min()),
            'max': int(text_lengths.max()),
            'median': float(np.median(text_lengths))
        },
        'opinion_count': {
            'mean': float(opinion_counts.mean()),
            'std': float(opinion_counts.std()),
            'min': int(opinion_counts.min()),
            'max': int(opinion_counts.max())
        },
        'vocab_size': len(vocab_set),
        'vocab_diversity': len(vocab_set) / len(all_tokens) if all_tokens else 0,
        'opinion_density': float(opinion_counts.sum() / len(text_lengths))
    }


def analyze_template_overlap(samples: List[Dict], split_name: str) -> Dict:
    """Analyze opening trigrams and common patterns"""
    opening_trigrams = Counter()
    opening_bigrams = Counter()
    common_words = Counter()
    all_tokens = []
    
    for sample in samples:
        text = sample.get('text', '')
        tokens = tokenize_vietnamese(text)
        all_tokens.extend(tokens)
        
        # Opening patterns
        if len(tokens) >= 3:
            opening_trigrams[get_opening_trigrams(text, 3)] += 1
        if len(tokens) >= 2:
            opening_bigrams[get_opening_trigrams(text, 2)] += 1
    
    # Top keywords
    common_words = Counter(all_tokens)
    top_keywords = dict(common_words.most_common(30))
    top_trigrams = dict(opening_trigrams.most_common(20))
    
    # Coverage: how many samples start with top-3 opening trigrams?
    total_samples = len(samples)
    top3_coverage = sum(count for _, count in opening_trigrams.most_common(3))
    
    return {
        'split': split_name,
        'num_samples': total_samples,
        'top_opening_trigrams': top_trigrams,
        'top_opening_trigrams_coverage': {
            'coverage_ratio': top3_coverage / total_samples if total_samples > 0 else 0,
            'num_samples_covered': top3_coverage
        },
        'top_keywords': top_keywords,
        'unique_opening_patterns': len(opening_trigrams)
    }


def compute_sentiment_distribution(samples: List[Dict]) -> Dict:
    """Compute per-aspect sentiment distribution"""
    aspect_sentiments = {}
    
    for sample in samples:
        for opinion in sample.get('opinions', []):
            aspect = opinion.get('aspect', 'Unknown')
            sentiment = opinion.get('sentiment', -1)
            
            if aspect not in aspect_sentiments:
                aspect_sentiments[aspect] = {'NEG': 0, 'POS': 0, 'NEU': 0}
            
            sentiment_name = {0: 'NEG', 1: 'POS', 2: 'NEU'}.get(sentiment, 'Unknown')
            if sentiment_name in aspect_sentiments[aspect]:
                aspect_sentiments[aspect][sentiment_name] += 1
    
    # Normalize to percentages
    for aspect in aspect_sentiments:
        total = sum(aspect_sentiments[aspect].values())
        for sent in aspect_sentiments[aspect]:
            aspect_sentiments[aspect][sent] = aspect_sentiments[aspect][sent] / total if total > 0 else 0
    
    return aspect_sentiments


def compute_split_divergence(style_metrics: Dict) -> Dict:
    """Compute divergence metrics between splits.
    
    INTERPRETATION:
    - Identical text length across splits → suspicious (likely same source)
    - Identical vocab diversity → suspicious (likely same source)
    - DEV/TEST with HIGHER vocab diversity than TRAIN → GOOD (more variety)
    - DEV/TEST with LOWER vocab diversity → possible concern
    """
    splits = ['train', 'dev', 'test']
    divergence = {}
    
    # Compare text length distributions
    text_means = {s: style_metrics[s]['text_length']['mean'] for s in splits if s in style_metrics}
    text_range = max(text_means.values()) - min(text_means.values())
    
    # If text lengths are suspiciously identical → flag
    text_warning = 'HIGH' if text_range < 0.5 else 'LOW'
    
    divergence['text_length_mean'] = {
        'values': text_means,
        'range': text_range,
        'interpretation': f'Range={text_range:.2f} {"(suspiciously similar)" if text_warning=="HIGH" else "(good variation)"}',
        'warning': text_warning
    }
    
    # Compare vocabulary diversity
    vocab_div = {s: style_metrics[s]['vocab_diversity'] for s in splits if s in style_metrics}
    vocab_div_range = max(vocab_div.values()) - min(vocab_div.values())
    
    # Lower vocab diversity in dev/test is more concerning than higher
    train_div = vocab_div.get('train', 0)
    dev_test_div_lower = any(vocab_div.get(s, 0) < train_div * 0.9 for s in ['dev', 'test'])
    vocab_warning = 'HIGH' if dev_test_div_lower else 'LOW'
    
    divergence['vocab_diversity'] = {
        'values': vocab_div,
        'range': vocab_div_range,
        'interpretation': f"Train={train_div:.4f}, Dev/Test higher is GOOD (not leak), lower may be concerning",
        'warning': vocab_warning
    }
    
    # Compare opinion density
    opinion_dens = {s: style_metrics[s]['opinion_density'] for s in splits if s in style_metrics}
    opinion_dens_range = max(opinion_dens.values()) - min(opinion_dens.values())
    opinion_warning = 'HIGH' if opinion_dens_range < 0.02 else 'LOW'
    
    divergence['opinion_density'] = {
        'values': opinion_dens,
        'range': opinion_dens_range,
        'interpretation': f'Range={opinion_dens_range:.4f} {"(suspiciously similar)" if opinion_warning=="HIGH" else "(good variation)"}',
        'warning': opinion_warning
    }
    
    return divergence


def detect_lexical_leakage(samples_dict: Dict[str, List[Dict]]) -> Dict:
    """Detect if dev/test share unusual amounts of exact phrases with train.
    
    NOTE: High token overlap (>80%) is NORMAL for same-domain data.
    Only EXACT text matches or suspicious near-identical sequences indicate leakage.
    """
    train_texts = set(s.get('text', '').strip() for s in samples_dict.get('train', []))
    
    # Extract common phrases (3+ word sequences) from train
    train_phrases = set()
    for sample in samples_dict.get('train', []):
        text = sample.get('text', '')
        tokens = tokenize_vietnamese(text)
        for i in range(len(tokens) - 2):
            phrase = ' '.join(tokens[i:i+3])
            if len(phrase) > 10:  # Only meaningful phrases
                train_phrases.add(phrase)
    
    results = {}
    
    for split in ['dev', 'test']:
        if split not in samples_dict:
            continue
        
        exact_matches = 0
        suspicious_phrases = 0  # Text sharing 5+ exact phrases with train
        
        for sample in samples_dict[split]:
            text = sample.get('text', '').strip()
            tokens = tokenize_vietnamese(text)
            
            # Check exact text match
            if text in train_texts:
                exact_matches += 1
            
            # Check phrase overlap (only flag if very high)
            phrase_overlap = 0
            for i in range(len(tokens) - 2):
                phrase = ' '.join(tokens[i:i+3])
                if phrase in train_phrases:
                    phrase_overlap += 1
            
            # If >30% of 3-grams match train phrases → suspicious
            total_phrases = max(1, len(tokens) - 2)
            if phrase_overlap / total_phrases > 0.3:
                suspicious_phrases += 1
        
        results[split] = {
            'num_samples': len(samples_dict[split]),
            'exact_text_match': exact_matches,
            'exact_match_percent': 100 * exact_matches / len(samples_dict[split]) if samples_dict[split] else 0,
            'suspicious_phrase_overlap': suspicious_phrases,
            'suspicious_phrase_percent': 100 * suspicious_phrases / len(samples_dict[split]) if samples_dict[split] else 0,
            'note': 'High token overlap (>80%) is normal for same domain. Only exact/phrase matches are concerning.'
        }
    
    return results


def load_jsonl(path: Path) -> List[Dict]:
    samples = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
    return samples


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Style / template integrity audit")
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--dev", type=Path, required=True)
    parser.add_argument("--test", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    cli = parser.parse_args()

    samples_dict = {}
    for split, filepath in [("train", cli.train), ("dev", cli.dev), ("test", cli.test)]:
        if filepath is None:
            continue
        if not filepath.exists():
            print(f"✗ Not found: {filepath}")
            continue
        samples_dict[split] = load_jsonl(filepath)
        print(f"✓ Loaded {split}: {len(samples_dict[split])} samples")
    
    # ===== ANALYSIS =====
    report = {
        'timestamp': str(Path.cwd()),
        'checks': {}
    }
    
    # 1. Style metrics per split
    print("\n[1] Computing style metrics per split...")
    style_metrics = {}
    for split, samples in samples_dict.items():
        style_metrics[split] = compute_style_metrics(samples)
    report['checks']['style_metrics'] = style_metrics
    
    # 2. Template/pattern analysis
    print("[2] Analyzing template overlap...")
    template_analysis = {}
    for split, samples in samples_dict.items():
        template_analysis[split] = analyze_template_overlap(samples, split)
    report['checks']['template_analysis'] = template_analysis
    
    # 3. Split divergence
    print("[3] Computing split divergence...")
    divergence = compute_split_divergence(style_metrics)
    report['checks']['split_divergence'] = divergence
    
    # 4. Sentiment distribution per aspect
    print("[4] Analyzing sentiment distribution...")
    sentiment_dist = {}
    for split, samples in samples_dict.items():
        sentiment_dist[split] = compute_sentiment_distribution(samples)
    report['checks']['sentiment_distribution'] = sentiment_dist
    
    # 5. Lexical leakage detection
    print("[5] Detecting lexical leakage...")
    lexical_leakage = detect_lexical_leakage(samples_dict)
    report['checks']['lexical_leakage'] = lexical_leakage
    
    # ===== SUMMARY & WARNINGS =====
    print("\n[SUMMARY]")
    summary = {
        'style_divergence_risk': 'LOW' if all(
            div['warning'] == 'LOW' 
            for div in [
                divergence['text_length_mean'],
                divergence['vocab_diversity'],
                divergence['opinion_density']
            ]
        ) else 'HIGH',
        'lexical_leakage_risk': 'LOW' if all(
            lexical_leakage[s]['exact_match_percent'] < 1 and lexical_leakage[s]['suspicious_phrase_percent'] < 5
            for s in lexical_leakage
        ) else 'HIGH'
    }
    report['summary'] = summary
    
    # Print warnings
    print("\n" + "="*60)
    if summary['style_divergence_risk'] == 'HIGH':
        print("⚠️  STYLE DIVERGENCE RISK: Suspicious similarity across splits")
        for metric, data in divergence.items():
            if data['warning'] == 'HIGH':
                print(f"    - {metric}: {data['interpretation']}")
    else:
        print("✅ Style metrics are well-diverged (good variation across splits)")
    
    if summary['lexical_leakage_risk'] == 'HIGH':
        print("\n⚠️  LEXICAL LEAKAGE RISK: High exact or phrase overlap")
        for split in ['dev', 'test']:
            if split in lexical_leakage:
                exact_pct = lexical_leakage[split]['exact_match_percent']
                phrase_pct = lexical_leakage[split]['suspicious_phrase_percent']
                if exact_pct > 0 or phrase_pct > 5:
                    print(f"    - {split}: {exact_pct:.1f}% exact match, {phrase_pct:.1f}% suspicious phrase overlap")
    else:
        print("✅ Lexical leakage is minimal (no meaningful exact match or phrase overlap)")
    
    # Opening pattern coverage
    print("\n" + "="*60)
    print("Template Concentration (top-3 opening trigrams):")
    print("(Lower = more diverse openings, GOOD. Higher = template heavy.)")
    template_risk = False
    for split in ['train', 'dev', 'test']:
        if split in template_analysis:
            coverage = template_analysis[split]['top_opening_trigrams_coverage']['coverage_ratio']
            num_unique = template_analysis[split]['unique_opening_patterns']
            status = "✓" if coverage < 0.05 else "⚠" if coverage < 0.10 else "✗"
            print(f"  {status} {split:5s}: {100*coverage:5.2f}% samples ({template_analysis[split]['top_opening_trigrams_coverage']['num_samples_covered']:4d}/{template_analysis[split]['num_samples']:4d}), {num_unique:4d} unique patterns")
            if coverage > 0.05:
                template_risk = True
    
    # Aspect-sentiment balance
    print("\n" + "="*60)
    print("Sentiment Distribution Balance (per aspect):")
    for split in ['train', 'dev', 'test']:
        if split in sentiment_dist:
            print(f"\n{split.upper()}:")
            for aspect in sorted(sentiment_dist[split].keys()):
                dist = sentiment_dist[split][aspect]
                print(f"  {aspect:12s}: NEG={dist['NEG']*100:5.1f}% POS={dist['POS']*100:5.1f}% NEU={dist['NEU']*100:5.1f}%")
    
    print("\n" + "="*60)
    
    # Save report
    output_file = cli.output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Report saved: {output_file}")
    
    print(f"\n📊 FINAL VERDICT:")
    print(f"  Style Divergence Risk: {summary['style_divergence_risk']}")
    print(f"  Lexical Leakage Risk: {summary['lexical_leakage_risk']}")
    print(f"\n  Overall: {'⚠️  NEEDS REVIEW' if 'HIGH' in [summary['style_divergence_risk'], summary['lexical_leakage_risk']] else '✅ SAFE TO USE'}")


if __name__ == '__main__':
    main()
