#!/usr/bin/env python3

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path


OUTPUT_FILE = Path("data/processed/annotation_prompt_contrastive_500.jsonl")
REPORT_FILE = Path("data/processed/annotation_prompt_contrastive_500.report.json")

SEED = 42

PAIR_QUOTAS = {
    ("Fashion", "Price"): 180,
    ("Electronics", "Service"): 110,
    ("App", "Ship"): 110,
    ("General", "Ship"): 100,
}

CONNECTORS = [
    " nhưng ",
    ". Tuy_nhiên, ",
    " mà ",
    ". Bù_lại, ",
    ". Trái_lại, ",
    "; còn ",
    ". Xét_về_mặt_khác, ",
]

CLAUSES = {
    ("Fashion", 1): [
        ("Vải", "Vải mặc mát và sờ rất êm"),
        ("áo", "áo lên form gọn và mặc khá tôn dáng"),
        ("quần", "quần mặc đứng dáng và co_giãn ổn"),
        ("váy", "váy lên dáng xinh và đường cắt gọn"),
        ("size", "size khá chuẩn nên mặc vào vừa người"),
        ("form", "form ôm vừa phải nhìn rất nịnh dáng"),
        ("phom", "phom giữ dáng tốt nên nhìn rất gọn"),
        ("giày", "giày đi êm chân và phối đồ dễ"),
        ("dép", "dép đi nhẹ chân và nhìn sạch sẽ"),
        ("túi", "túi cầm chắc tay và nhìn khá sang"),
        ("đầm", "đầm mặc lên rất xinh và tôn dáng"),
        ("đường_may", "đường_may gọn nên tổng thể nhìn khá chỉn_chu"),
        ("kiểu_dáng", "kiểu_dáng nhìn trẻ và khá dễ mặc"),
        ("vải", "vải mịn nên mặc lâu vẫn thấy dễ chịu"),
        ("áo", "áo mặc mát và màu lên nhìn rất sáng"),
    ],
    ("Fashion", 0): [
        ("Vải", "Vải hơi thô và mặc bí người"),
        ("áo", "áo mặc vào bị rộng vai và lệch dáng"),
        ("quần", "quần bị chật phần hông nên đi lại khó"),
        ("váy", "váy lên dáng xấu và phần tà bị cứng"),
        ("size", "size bị lệch nên mặc vào chật hẳn"),
        ("form", "form may rộng thùng_thình nên nhìn rất dừ"),
        ("phom", "phom bị lệch nên mặc không đứng dáng"),
        ("giày", "giày đi cấn chân và form bị bè ngang"),
        ("dép", "dép đi trơn và quai khá cấn"),
        ("túi", "túi may xộc_xệch và nhìn thiếu chắc_chắn"),
        ("đầm", "đầm mặc lên bị rộng eo và không tôn người"),
        ("đường_may", "đường_may hơi ẩu nên nhìn rất thiếu chỉn_chu"),
        ("kiểu_dáng", "kiểu_dáng hơi quê nên mặc lên bị dừ"),
        ("vải", "vải khá mỏng nên mặc dễ lộ"),
        ("áo", "áo bị nhăn form và mặc vào nhìn kém đẹp"),
    ],
    ("Price", 1): [
        ("giá", "giá khá mềm so với chất_lượng"),
        ("giá_tiền", "giá_tiền nhìn chung rất dễ chịu"),
        ("tầm_giá", "tầm_giá này mua khá hời"),
        ("voucher", "voucher áp vào giảm được kha_khá"),
        ("mã_giảm_giá", "mã_giảm_giá dùng được nên tiết_kiệm rõ"),
        ("phí_ship", "phí_ship rẻ nên chốt đơn cũng nhẹ đầu"),
        ("giá", "giá ổn nên mua thử cũng đáng"),
        ("tầm_giá", "tầm_giá khá hợp_lý cho nhu_cầu cơ_bản"),
        ("giá_tiền", "giá_tiền như vậy là quá ổn"),
        ("voucher", "voucher nhiều nên tổng tiền xuống khá đẹp"),
        ("giá", "giá dễ thở nên mua lại vẫn thấy hợp"),
        ("mã_giảm_giá", "mã_giảm_giá giúp đơn này rẻ hơn hẳn"),
    ],
    ("Price", 0): [
        ("giá", "giá hơi chát so với kỳ_vọng"),
        ("giá_tiền", "giá_tiền bị đội lên khá cao"),
        ("tầm_giá", "tầm_giá này mình thấy chưa hợp_lý"),
        ("voucher", "voucher quá yếu nên gần như không ăn_thua"),
        ("mã_giảm_giá", "mã_giảm_giá ít nên vẫn thấy đắt"),
        ("phí_ship", "phí_ship cao nên tổng đơn bị chát"),
        ("giá", "giá cao hơn mặt_bằng chung khá nhiều"),
        ("giá_tiền", "giá_tiền như vậy là chưa đáng"),
        ("tầm_giá", "tầm_giá này bỏ ra hơi tiếc"),
        ("voucher", "voucher nghèo nên cảm_giác không hời"),
        ("giá", "giá hơi mắc nên phải đắn_đo mới mua"),
        ("phí_ship", "phí_ship đắt làm mình chùn tay"),
    ],
    ("Electronics", 1): [
        ("Máy", "Máy chạy mượt và phản_hồi khá nhanh"),
        ("pin", "pin trụ ổn nên dùng cả ngày vẫn thoải_mái"),
        ("màn_hình", "màn_hình sáng rõ và nhìn khá đã mắt"),
        ("camera", "camera lên màu đẹp và bắt nét ổn"),
        ("củ_sạc", "củ_sạc đi kèm dùng ổn và vào điện nhanh"),
        ("cáp_sạc", "cáp_sạc chắc tay và sạc khá ổn định"),
        ("điện_thoại", "điện_thoại dùng mượt nên thao_tác rất dễ chịu"),
        ("bàn_phím", "bàn_phím gõ êm và độ nảy khá tốt"),
        ("chuột", "chuột rê nhạy và cầm vừa tay"),
        ("loa", "loa mở to mà tiếng vẫn khá trong"),
        ("wifi", "wifi bắt ổn nên xem video không bị đứt"),
        ("vân_tay", "vân_tay nhận nhanh nên mở máy tiện"),
        ("chip", "chip xử_lý mượt nên chuyển app rất nhanh"),
        ("ram", "ram giữ tác_vụ ổn nên ít phải tải lại"),
    ],
    ("Electronics", 0): [
        ("Máy", "Máy nhanh nóng và dùng lâu hơi ì"),
        ("pin", "pin tụt nhanh nên phải sạc liên_tục"),
        ("màn_hình", "màn_hình ám nhẹ và nhìn ngoài trời khá khó"),
        ("camera", "camera lấy nét chậm nên ảnh dễ bệt"),
        ("củ_sạc", "củ_sạc vào điện chập_chờn nên rất khó chịu"),
        ("cáp_sạc", "cáp_sạc lỏng đầu nên sạc lúc được lúc không"),
        ("điện_thoại", "điện_thoại hay giật nên dùng hơi bực"),
        ("bàn_phím", "bàn_phím gõ cứng nên rất nhanh mỏi tay"),
        ("chuột", "chuột rê không đều nên dùng khá cáu"),
        ("loa", "loa rè nhẹ nên nghe lâu khá khó chịu"),
        ("wifi", "wifi bắt yếu nên gọi video hay chập_chờn"),
        ("vân_tay", "vân_tay nhận chậm nên mở máy hay hụt nhịp"),
        ("chip", "chip xử_lý chậm nên mở tác_vụ khá ì"),
        ("ram", "ram giữ app kém nên thoát nền liên_tục"),
    ],
    ("Service", 1): [
        ("nhân_viên", "nhân_viên tư_vấn có tâm và nói chuyện dễ chịu"),
        ("shop", "shop phản_hồi nhanh và xử_lý khá gọn"),
        ("cửa_hàng", "cửa_hàng hỗ_trợ nhiệt_tình nên mình khá yên_tâm"),
        ("tư_vấn", "tư_vấn rõ_ràng nên mình chọn hàng dễ hơn"),
        ("phục_vụ", "phục_vụ lịch_sự nên trải_nghiệm mua dễ chịu"),
        ("bảo_hành", "bảo_hành hướng_dẫn kỹ nên không bị rối"),
        ("chăm_sóc khách_hàng", "chăm_sóc khách_hàng trả_lời khá chuẩn"),
        ("nhân_viên", "nhân_viên hỗ_trợ nhanh nên đỡ mất thời_gian"),
        ("shop", "shop giữ lời nên mình thấy khá tin_tưởng"),
        ("cửa_hàng", "cửa_hàng xử_lý ổn nên mình không phải chờ lâu"),
    ],
    ("Service", 0): [
        ("nhân_viên", "nhân_viên tư_vấn hời_hợt nên hỏi gì cũng cụt_lủn"),
        ("shop", "shop phản_hồi chậm nên mình đợi khá mệt"),
        ("cửa_hàng", "cửa_hàng xử_lý thiếu trách_nhiệm nên rất bực"),
        ("tư_vấn", "tư_vấn qua loa nên càng hỏi càng rối"),
        ("phục_vụ", "phục_vụ lạnh_nhạt nên trải_nghiệm rất tụt mood"),
        ("bảo_hành", "bảo_hành hướng_dẫn vòng_vo nên mất thời_gian"),
        ("chăm_sóc khách_hàng", "chăm_sóc khách_hàng trả_lời máy_móc và chậm"),
        ("nhân_viên", "nhân_viên nói chuyện khó chịu nên mình ngại hỏi thêm"),
        ("shop", "shop xử_lý lửng_lơ nên mình không tin_tưởng"),
        ("cửa_hàng", "cửa_hàng hỗ_trợ quá chậm nên mình phải nhắc liên_tục"),
    ],
    ("App", 1): [
        ("App", "App đặt hàng khá mượt và thao_tác rất nhanh"),
        ("ứng_dụng", "ứng_dụng chạy ổn nên tìm món rất tiện"),
        ("phần_mềm", "phần_mềm phản_hồi nhanh nên bấm gì cũng trôi"),
        ("cập_nhật", "cập_nhật mới giúp app chạy đỡ giật hẳn"),
        ("giao_diện", "giao_diện rõ ràng nên tìm mục nào cũng dễ"),
        ("giỏ_hàng", "giỏ_hàng hoạt_động ổn nên thêm món rất nhanh"),
        ("thông_báo", "thông_báo hiện đúng lúc nên theo dõi đơn khá dễ"),
        ("App", "App dùng mượt nên đặt đồ không bị khựng"),
        ("ứng_dụng", "ứng_dụng thao_tác tiện nên mình khá ưng"),
        ("giao_diện", "giao_diện nhìn gọn nên dùng lâu không rối"),
    ],
    ("App", 0): [
        ("App", "App hay lag nên mỗi lần đặt đồ đều hơi bực"),
        ("ứng_dụng", "ứng_dụng chạy chậm nên lướt món rất khựng"),
        ("phần_mềm", "phần_mềm hay lỗi nên thanh_toán rất thiếu ổn_định"),
        ("cập_nhật", "cập_nhật mới làm app kém mượt hơn trước"),
        ("giao_diện", "giao_diện rối nên tìm mã giảm khá mệt"),
        ("giỏ_hàng", "giỏ_hàng hay nhảy lỗi nên thêm món rất bực"),
        ("thông_báo", "thông_báo lên chậm nên theo dõi đơn khá rối"),
        ("App", "App giật nhẹ liên_tục nên thao_tác mất hứng"),
        ("ứng_dụng", "ứng_dụng hay văng nên mình phải mở lại liên_tục"),
        ("giao_diện", "giao_diện bố_trí kém nên dùng khá rối mắt"),
    ],
    ("Ship", 1): [
        ("shipper", "shipper giao đúng hẹn nên mình khá hài_lòng"),
        ("giao_hàng", "giao_hàng nhanh nên không phải chờ lâu"),
        ("vận_chuyển", "vận_chuyển cập_nhật rõ nên theo dõi đơn dễ"),
        ("thời_gian giao_hàng", "thời_gian giao_hàng khá chuẩn như cam_kết"),
        ("đơn_hàng", "đơn_hàng đến đúng lịch nên rất tiện sắp_xếp"),
        ("shipper", "shipper gọi trước nên nhận hàng rất chủ_động"),
        ("giao_hàng", "giao_hàng cẩn_thận nên món tới nơi còn đẹp"),
        ("vận_chuyển", "vận_chuyển xử_lý nhanh nên đơn đi khá mượt"),
        ("đơn_hàng", "đơn_hàng giao gọn nên mình không phải nhắc"),
        ("shipper", "shipper thân_thiện và giao khá đúng giờ"),
    ],
    ("Ship", 0): [
        ("shipper", "shipper giao trễ nên mình phải đợi rất lâu"),
        ("giao_hàng", "giao_hàng quá ẩu nên nhận món hơi nản"),
        ("vận_chuyển", "vận_chuyển cập_nhật chậm nên theo dõi đơn rất mệt"),
        ("thời_gian giao_hàng", "thời_gian giao_hàng kéo dài hơn hẳn cam_kết"),
        ("đơn_hàng", "đơn_hàng đi lòng_vòng nên chờ rất sốt_ruột"),
        ("shipper", "shipper gọi muộn rồi giao còn khá cẩu_thả"),
        ("giao_hàng", "giao_hàng chậm nên mình lỡ cả việc"),
        ("vận_chuyển", "vận_chuyển xử_lý ì nên đơn cứ đứng im"),
        ("đơn_hàng", "đơn_hàng về trễ nên trải_nghiệm tụt hẳn"),
        ("shipper", "shipper giao thiếu cẩn_thận nên mình khá bực"),
    ],
    ("General", 1): [
        ("đóng_gói", "đóng_gói cẩn_thận nên mở ra thấy khá yên_tâm"),
        ("hàng", "hàng nhìn chắc_chắn và khá chỉn_chu"),
        ("sản_phẩm", "sản_phẩm cầm lên thấy khá hoàn_thiện"),
        ("màu", "màu lên đẹp nên nhìn ngoài còn ưng hơn ảnh"),
        ("chất", "chất tổng_thể khá ổn nên dùng thấy yên_tâm"),
        ("chất_liệu", "chất_liệu nhìn ổn nên cảm_giác khá xịn"),
        ("chất_lượng", "chất_lượng tổng_quan khá tốt so với mong_đợi"),
        ("hộp", "hộp còn nguyên nên nhận đồ thấy khá thích"),
        ("độ_bền", "độ_bền ban_đầu cho cảm_giác khá ổn"),
        ("bề_mặt", "bề_mặt hoàn_thiện khá đẹp và sạch"),
    ],
    ("General", 0): [
        ("đóng_gói", "đóng_gói sơ_sài nên mở ra thấy khá ngán"),
        ("hàng", "hàng bên trong bị móp nên nhìn hơi chán"),
        ("sản_phẩm", "sản_phẩm hoàn_thiện chưa kỹ nên thấy hơi hụt_hẫng"),
        ("màu", "màu lệch ảnh nên nhìn ngoài không đẹp như mong_đợi"),
        ("chất", "chất tổng_thể hơi bèo nên cầm lên thấy thất_vọng"),
        ("chất_liệu", "chất_liệu nhìn khá rẻ nên cảm_giác không đã"),
        ("chất_lượng", "chất_lượng tổng_quan chưa tới nên thấy hơi tiếc tiền"),
        ("hộp", "hộp móp méo nên nhận hàng mất cảm_tình ngay"),
        ("độ_bền", "độ_bền có vẻ thấp nên dùng cũng hơi lo"),
        ("bề_mặt", "bề_mặt hoàn_thiện xước nhẹ nên nhìn thiếu đẹp"),
    ],
}


def maybe_capitalize_first(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def maybe_lower_first(text: str) -> str:
    if not text:
        return text
    if len(text) > 1 and text[1].isupper():
        return text
    return text[:1].lower() + text[1:]


def build_text(left_clause: str, right_clause: str, connector: str) -> str:
    if connector.startswith("."):
        return maybe_capitalize_first(left_clause) + connector + maybe_capitalize_first(right_clause) + "."
    return maybe_capitalize_first(left_clause) + connector + maybe_lower_first(right_clause) + "."


def find_target_span(text: str, target: str) -> tuple[str, int] | None:
    variants = [target, maybe_capitalize_first(target), maybe_lower_first(target)]
    seen = set()
    for variant in variants:
        if variant in seen:
            continue
        seen.add(variant)
        start = text.find(variant)
        if start >= 0 and text.find(variant, start + 1) == -1:
            return variant, start
    return None


def build_record(left: tuple[str, str, int], right: tuple[str, str, int], connector: str) -> dict | None:
    left_target, left_clause, left_sentiment, left_aspect = left
    right_target, right_clause, right_sentiment, right_aspect = right
    text = build_text(left_clause, right_clause, connector)
    left_loc = find_target_span(text, left_target)
    right_loc = find_target_span(text, right_target)
    if left_loc is None or right_loc is None:
        return None
    left_target_text, left_start = left_loc
    right_target_text, right_start = right_loc
    return {
        "text": text,
        "opinions": [
            {
                "target": left_target_text,
                "aspect": left_aspect,
                "sentiment": left_sentiment,
                "start": left_start,
                "end": left_start + len(left_target_text),
            },
            {
                "target": right_target_text,
                "aspect": right_aspect,
                "sentiment": right_sentiment,
                "start": right_start,
                "end": right_start + len(right_target_text),
            },
        ],
        "global_sentiment": 2,
    }


def enriched_clause_pool(aspect: str, sentiment: int) -> list[tuple[str, str, int, str]]:
    return [(target, clause, sentiment, aspect) for target, clause in CLAUSES[(aspect, sentiment)]]


def motif_key(text: str) -> str:
    return " ".join(text.split()[:3]).lower()


def validate_record(record: dict) -> None:
    text = record["text"]
    for opinion in record["opinions"]:
        start = opinion["start"]
        end = opinion["end"]
        target = opinion["target"]
        if text[start:end] != target:
            raise ValueError(f"Offset mismatch: {text!r} | {opinion!r}")


def generate_pair_records(aspect_a: str, aspect_b: str, quota: int, rng: random.Random) -> list[dict]:
    half_a = quota // 2
    half_b = quota - half_a
    directions = [
        ((aspect_a, 1), (aspect_b, 0), half_a),
        ((aspect_a, 0), (aspect_b, 1), half_b),
    ]
    records = []
    seen_texts = set()
    motif_counts = Counter()

    for left_key, right_key, direction_quota in directions:
        left_pool = enriched_clause_pool(*left_key)
        right_pool = enriched_clause_pool(*right_key)
        candidates = []
        for left in left_pool:
            for right in right_pool:
                for connector in CONNECTORS:
                    candidates.append((left, right, connector))
        rng.shuffle(candidates)

        generated = 0
        for left, right, connector in candidates:
            if generated >= direction_quota:
                break
            record = build_record(left, right, connector)
            if record is None:
                continue
            if record["text"] in seen_texts:
                continue
            key = motif_key(record["text"])
            if motif_counts[key] >= 8:
                continue
            validate_record(record)
            records.append(record)
            seen_texts.add(record["text"])
            motif_counts[key] += 1
            generated += 1

        if generated < direction_quota:
            raise RuntimeError(f"Not enough diverse candidates for {left_key} vs {right_key}: {generated}/{direction_quota}")

    return records


def main() -> int:
    rng = random.Random(SEED)
    all_records = []
    pair_counts = Counter()
    aspect_counts = Counter()
    motif_counts = Counter()
    connector_counts = Counter()

    for (aspect_a, aspect_b), quota in PAIR_QUOTAS.items():
        records = generate_pair_records(aspect_a, aspect_b, quota, rng)
        all_records.extend(records)
        pair_counts[f"{aspect_a} vs {aspect_b}"] += len(records)

    rng.shuffle(all_records)

    for record in all_records:
        motif_counts[motif_key(record["text"])] += 1
        for connector in CONNECTORS:
            if connector.strip() in record["text"]:
                connector_counts[connector.strip()] += 1
                break
        for opinion in record["opinions"]:
            aspect_counts[f"{opinion['aspect']}_{opinion['sentiment']}"] += 1

    OUTPUT_FILE.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in all_records), encoding="utf-8")
    report = {
        "output_file": str(OUTPUT_FILE),
        "total_records": len(all_records),
        "pair_counts": dict(sorted(pair_counts.items())),
        "aspect_sentiment_counts": dict(sorted(aspect_counts.items())),
        "connector_counts": dict(sorted(connector_counts.items())),
        "max_motif_repetition": max(motif_counts.values()) if motif_counts else 0,
        "top_motifs": motif_counts.most_common(20),
    }
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())