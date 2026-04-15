# Data Quality Audit Report
**File**: train_final.jsonl
**Total records**: 7682
**Records có lỗi**: 820 (10.67%)

---

## Tổng hợp theo loại lỗi

| Mã | Mô tả | Số records | % |
|----|-------|------------|---|
| E1 | Offset sai | 0 | 0.00% |
| E2 | Target có space thừa | 0 | 0.00% |
| E3 | Target là opinion word | 27 | 0.35% |
| E4 | Duplicate aspect | 0 | 0.00% |
| E5 | Sentiment sai rõ ràng | 576 | 7.50% |
| E6 | Global conflict aspect | 0 | 0.00% |
| E7 | Không có opinions | 0 | 0.00% |
| E8 | Text quá ngắn | 228 | 2.97% |

---

## Phân tích chi tiết

### E1 — Offset sai
- Không phát hiện ví dụ.

### E2 — Target có space thừa
- Không phát hiện ví dụ.

### E3 — Target là opinion word
- "xinh": 12 lần
- "chắc": 4 lần
- "hôi": 4 lần
- "cứng": 2 lần
- "thiếu": 2 lần
- "nặng": 1 lần
- "bình thường": 1 lần
- "sai": 1 lần

### E4 — Duplicate aspect
- Không phát hiện ví dụ.

### E5 — Sentiment sai rõ ràng
- line 16: target="tầm giá" | context="thì máy quá ổn trong tầm giá. Xài hằng ngày mượt mà," | predict=1 | nên là 2
- line 16: target="Màn hình" | context="khoảng 2 tiếng là đầy. Màn hình đẹp, xài ngoài trời ổn." | predict=1 | nên là 2
- line 29: target="ứng dụng" | context="được cái hiệu năng load ứng dụng nhanh, đa nhiệm ổn. Pin" | predict=1 | nên là 2
- line 29: target="Pin" | context="dụng nhanh, đa nhiệm ổn. Pin ngon ở bản ios 10," | predict=1 | nên là 2
- line 36: target="vân tay" | context="đến chơi game K có vân tay 5.000 k có sạc nhanh" | predict=0 | nên là 1
- line 40: target="ứng_dụng" | context="ứng_dụng ổn nhưng giao hàng hơi" | predict=1 | nên là 2
- line 78: target="ứng dụng" | context="k nhại bén bằng ios, ứng dụng tải về thì ít, nhưng" | predict=0 | nên là 1
- line 78: target="ổ_cứng" | context="ít, nhưng ứng dụng trên ổ_cứng thì qúa nhiều thật vọng" | predict=0 | nên là 1
- line 115: target="củ_sạc" | context="giao chậm_ý nhma kh sao củ_sạc vẫn ok lắm" | predict=1 | nên là 0
- line 124: target="màu" | context="trước minh lấy 1 cái màu đỏ thấy ưng , lần" | predict=0 | nên là 1

### E6 — Global conflict
- Không phát hiện ví dụ.

---

## Ước tính tác động đến training

- E1 + E5 là nghiêm trọng nhất -> ảnh hưởng trực tiếp đến
  Span F1 (E1) và Sentiment F1 (E5)
- E2 + E3 ảnh hưởng nhẹ hơn, fix bằng post-processing
- E4 + E6 gây confusion cho model khi học

---

## Khuyến nghị ưu tiên

1. Uu tien 1: ra soat E5 (Sentiment sai rõ ràng) vi day la nhom loi xuat hien nhieu nhat, anh huong rong den chat luong nhan.
2. Uu tien 2: xu ly 576 record thuoc E1/E5 truoc khi train lai, vi day la hai loi tac dong truc tiep den span va sentiment.
3. Uu tien 4: chuan hoa target va loc opinion-word targets bang post-processing truoc khi dua vao pipeline huan luyen.
4. Uu tien 5: loai rieng cac record qua ngan hoac khong co opinion vi gia tri hoc rat thap.
