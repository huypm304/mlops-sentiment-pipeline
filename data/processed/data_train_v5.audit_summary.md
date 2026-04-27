# Data Quality Audit Report
**File**: data_train_v5.jsonl
**Total records**: 7565
**Records co loi**: 2589 (34.22%)

---

## Tong hop theo loai loi

| Ma | Mo ta | So records | % |
|----|-------|------------|---|
| E1 | Offset sai | 2289 | 30.26% |
| E2 | Target co space thua | 0 | 0.00% |
| E3 | Target la opinion word | 15 | 0.20% |
| E4 | Duplicate aspect | 0 | 0.00% |
| E5 | Sentiment sai ro rang | 593 | 7.84% |
| E6 | Global conflict aspect | 0 | 0.00% |
| E7 | Khong co opinions | 0 | 0.00% |
| E8 | Text qua ngan | 0 | 0.00% |

---

## Phan tich chi tiet

### E1 - Offset sai
- line 5: text="Trước tiên nói về thái độ phục vụ của nhân viên tgdđ là quá ok rồi.mới dùng máy được 1 tuần thấy khá ok chì mỗi tội hay tự động nhảy lọc ánh sáng xanh trong khi không dùng tới" | target="nhân_viên" | extracted="nhân viên"
- line 6: text="đã đặt sách trên tiki rất nhiều lần dịch_vụ của tiki tốt đóng_gói và giao hàng cũng rất okk_sách cũng đa_dạng và chất_lượng" | target="giao_hàng" | extracted="giao hàng"
- line 8: text="tiki gian_dối trong việc giao hàng hàng giao thiếu không đúng mẫu" | target="giao_hàng" | extracted="giao hàng"
- line 9: text="quá tuyệt vời so với tầm giá, loa to thiệt sự. không gg cũng không vấn đề gì vì có cửa hàng app của hw. và vẫn lên gg bằng nền tảng web. 👍👍" | target="tầm_giá" | extracted="tầm giá"
- line 9: text="quá tuyệt vời so với tầm giá, loa to thiệt sự. không gg cũng không vấn đề gì vì có cửa hàng app của hw. và vẫn lên gg bằng nền tảng web. 👍👍" | target="cửa_hàng" | extracted="cửa hàng"

### E2 - Target co space thua
- Khong phat hien vi du.

### E3 - Target la opinion word
- "dép": 15 lan

### E4 - Duplicate aspect
- Khong phat hien vi du.

### E5 - Sentiment sai ro rang
- line 5: target="nhân_viên" | context="thái độ phục vụ của nhân viên tgdđ là quá ok rồi.mới" | predict=1 | nen la 0
- line 36: target="pin" | context="vụ của google vào máy, pin thì nếu mà chơi game" | predict=1 | nen la 0
- line 66: target="vải" | context="Vải mịn nên mặc lâu vẫn" | predict=1 | nen la 0
- line 67: target="nhân_viên" | context="được game. Còn Khá ổn nhân viên nhiệt tình tư vấn" | predict=1 | nen la 2
- line 90: target="đường_may" | context="Đường_may gọn nên tổng thể nhìn" | predict=1 | nen la 2
- line 109: target="giá" | context="mặc hơi lộ nhưg tầm giá này thì cx là ok" | predict=1 | nen la 0
- line 114: target="chuột" | context="cầu cơ bản. Chỉ có chuột máy với độ phân giải" | predict=1 | nen la 0
- line 128: target="shop" | context="shop cực dễ_thương" | predict=1 | nen la 2
- line 177: target="app" | context="Cá_nhân mik thì mik thấy app này khá tiện_lợi và rất" | predict=1 | nen la 0
- line 186: target="nhân_viên" | context="hình ổn,camera ổn,loa ổn,củ_sạc quá OK,nhân viên tư vấn nhiệt tình,vui vẻ.Cám" | predict=1 | nen la 2

### E6 - Global conflict
- Khong phat hien vi du.

---

## Uoc tinh tac dong den training

- E1 + E5 la nghiem trong nhat -> anh huong truc tiep den Span F1 (E1) va Sentiment F1 (E5)
- E2 + E3 anh huong nhe hon, fix bang post-processing
- E4 + E6 gay confusion cho model khi hoc

---

## Khuyen nghi uu tien

1. Uu tien xu ly Offset sai (2289 records) vi day la loi supervision span truc tiep.
2. Ra soat Sentiment sai ro rang (593 records) truoc khi train lai vi no lam lech sentiment head.
3. Lam sach Target la opinion word (15 records) de giam noise annotation.
