# Data Quality Audit Report
**File**: data_train_v5.autofixed.jsonl
**Total records**: 7565
**Records co loi**: 593 (7.84%)

---

## Tong hop theo loai loi

| Ma | Mo ta | So records | % |
|----|-------|------------|---|
| E1 | Offset sai | 0 | 0.00% |
| E2 | Target co space thua | 0 | 0.00% |
| E3 | Target la opinion word | 0 | 0.00% |
| E4 | Duplicate aspect | 0 | 0.00% |
| E5 | Sentiment sai ro rang | 593 | 7.84% |
| E6 | Global conflict aspect | 0 | 0.00% |
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
- line 5: target="nhân viên" | context="thái độ phục vụ của nhân viên tgdđ là quá ok rồi.mới" | predict=1 | nen la 0
- line 36: target="pin" | context="vụ của google vào máy, pin thì nếu mà chơi game" | predict=1 | nen la 0
- line 66: target="Vải" | context="Vải mịn nên mặc lâu vẫn" | predict=1 | nen la 0
- line 67: target="nhân viên" | context="được game. Còn Khá ổn nhân viên nhiệt tình tư vấn" | predict=1 | nen la 2
- line 90: target="Đường_may" | context="Đường_may gọn nên tổng thể nhìn" | predict=1 | nen la 2
- line 109: target="giá" | context="mặc hơi lộ nhưg tầm giá này thì cx là ok" | predict=1 | nen la 0
- line 114: target="chuột" | context="cầu cơ bản. Chỉ có chuột máy với độ phân giải" | predict=1 | nen la 0
- line 128: target="shop" | context="shop cực dễ_thương" | predict=1 | nen la 2
- line 177: target="app" | context="Cá_nhân mik thì mik thấy app này khá tiện_lợi và rất" | predict=1 | nen la 0
- line 186: target="nhân viên" | context="hình ổn,camera ổn,loa ổn,củ_sạc quá OK,nhân viên tư vấn nhiệt tình,vui vẻ.Cám" | predict=1 | nen la 2

### E6 - Global conflict
- Khong phat hien vi du.

---

## Uoc tinh tac dong den training

- E1 + E5 la nghiem trong nhat -> anh huong truc tiep den Span F1 (E1) va Sentiment F1 (E5)
- E2 + E3 anh huong nhe hon, fix bang post-processing
- E4 + E6 gay confusion cho model khi hoc

---

## Khuyen nghi uu tien

1. Ra soat Sentiment sai ro rang (593 records) truoc khi train lai vi no lam lech sentiment head.
