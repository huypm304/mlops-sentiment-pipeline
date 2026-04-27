# Data Quality Audit Report
**File**: data_train_v6_final.jsonl
**Total records**: 7565
**Records co loi**: 272 (3.60%)

---

## Tong hop theo loai loi

| Ma | Mo ta | So records | % |
|----|-------|------------|---|
| E1 | Offset sai | 0 | 0.00% |
| E2 | Target co space thua | 0 | 0.00% |
| E3 | Target la opinion word | 0 | 0.00% |
| E4 | Duplicate aspect | 0 | 0.00% |
| E5 | Sentiment sai ro rang | 200 | 2.64% |
| E6 | Global conflict aspect | 72 | 0.95% |
| E7 | Khong co opinions | 0 | 0.00% |
| E8 | Text qua ngan | 0 | 0.00% |

---

## Phan tich chi tiet

### E1 - Offset sai
- Khong phat hien vi du.

### E2 - Target co space thua
- Khong phat hien vi du.

### E3 - Target la opinion word
- Khong phat hien vi du.

### E4 - Duplicate aspect
- Khong phat hien vi du.

### E5 - Sentiment sai ro rang
- line 66: target="Vải" | context="Vải mịn nên mặc lâu vẫn" | predict=1 | nen la 0
- line 90: target="Đường_may" | context="Đường_may gọn nên tổng thể nhìn" | predict=1 | nen la 2
- line 177: target="app" | context="Cá_nhân mik thì mik thấy app này khá tiện_lợi và rất" | predict=1 | nen la 0
- line 214: target="cáp_sạc" | context="cáp_sạc free size nên ai khung" | predict=0 | nen la 1
- line 227: target="Vải" | context="Vải mịn nên mặc lâu vẫn" | predict=1 | nen la 0
- line 276: target="app" | context="quá nhiều quảng_cáo dùng app khác quảng_cáo đều nhảy qua" | predict=0 | nen la 1
- line 283: target="app" | context="app hai quá hay quá đặt_hàng" | predict=1 | nen la 0
- line 283: target="giao" | context="đặt_hàng 2 3 tiếng là giao rồi" | predict=1 | nen la 0
- line 362: target="shop" | context="cảm_ơn shop . chắc_chắn sẽ quay lại" | predict=1 | nen la 2
- line 396: target="hình" | context="đảm_bảo i hình luon" | predict=1 | nen la 2

### E6 - Global conflict
- line 972: aspects=[1] | global=0
- line 1174: aspects=[1, 1] | global=0
- line 1248: aspects=[1] | global=0
- line 1394: aspects=[1] | global=0
- line 1451: aspects=[0] | global=1

---

## Uoc tinh tac dong den training

- E1 + E5 la nghiem trong nhat -> anh huong truc tiep den Span F1 (E1) va Sentiment F1 (E5)
- E2 + E3 anh huong nhe hon, fix bang post-processing
- E4 + E6 gay confusion cho model khi hoc

---

## Khuyen nghi uu tien

1. Ra soat Sentiment sai ro rang (200 records) truoc khi train lai vi no lam lech sentiment head.
2. Can tach va kiem tra Global conflict aspect (72 records) vi global head dang hoc tu nhan mau thuan.
