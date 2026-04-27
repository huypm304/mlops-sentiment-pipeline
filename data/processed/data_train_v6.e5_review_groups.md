# V6 Remaining E5 Review Queue
**Source**: data_train_v6.jsonl
**Total E5 records**: 159

## Top Target Errors
- "app": 21 lần
- "pin": 8 lần
- "phần_mềm": 7 lần
- "voucher": 6 lần
- "shop": 5 lần
- "Tầm_giá": 5 lần
- "áo": 5 lần
- "Wifi": 5 lần
- "Giày": 5 lần
- "hàng": 5 lần
- "Vải": 4 lần
- "Đường_may": 4 lần
- "giá": 4 lần
- "cập nhật": 4 lần
- "nhân viên": 4 lần
- "ứng dụng": 3 lần
- "giá_tiền": 3 lần
- "Shop": 3 lần
- "size": 3 lần
- "Cập_nhật": 3 lần

## Top Aspect Errors
- App: 40 lần
- Electronics: 37 lần
- Service: 27 lần
- Fashion: 25 lần
- Price: 24 lần
- General: 10 lần
- Ship: 7 lần

## Sentiment Transitions
- POS->NEG: 96 lần
- POS->NEU: 57 lần
- NEG->POS: 17 lần

## Sample Cases
- line 66: aspect=Fashion | target="Vải" | current=POS | suggested=NEG
  text: "Vải mịn nên mặc lâu vẫn thấy dễ chịu. Bù_lại, Voucher nghèo nên cảm_giác không hời."
  context: "Vải mịn nên mặc lâu vẫn"
- line 90: aspect=Fashion | target="Đường_may" | current=POS | suggested=NEU
  text: "Đường_may gọn nên tổng thể nhìn khá chỉn_chu. Tuy_nhiên, Phí_ship đắt làm mình chùn tay."
  context: "Đường_may gọn nên tổng thể nhìn"
- line 177: aspect=App | target="app" | current=POS | suggested=NEG
  text: "Cá_nhân mik thì mik thấy app này khá tiện_lợi và rất đa_dạng vật_dụng. Tuy nhiên, Tiki giá đắt ae ạ đặt_hàng 50 k lên tận 400 k tiki kiểu j đấy bịp à"
  context: "Cá_nhân mik thì mik thấy app này khá tiện_lợi và rất"
- line 227: aspect=Fashion | target="Vải" | current=POS | suggested=NEG
  text: "Vải mịn nên mặc lâu vẫn thấy dễ chịu mà giá_tiền như vậy là chưa đáng."
  context: "Vải mịn nên mặc lâu vẫn"
- line 276: aspect=App | target="app" | current=NEG | suggested=POS
  text: "quá nhiều quảng_cáo dùng app khác quảng_cáo đều nhảy qua lazada"
  context: "quá nhiều quảng_cáo dùng app khác quảng_cáo đều nhảy qua"
- line 283: aspect=App | target="app" | current=POS | suggested=NEG
  text: "app hai quá hay quá đặt_hàng 2 3 tiếng là giao rồi"
  context: "app hai quá hay quá đặt_hàng"
- line 283: aspect=Ship | target="giao" | current=POS | suggested=NEG
  text: "app hai quá hay quá đặt_hàng 2 3 tiếng là giao rồi"
  context: "đặt_hàng 2 3 tiếng là giao rồi"
- line 362: aspect=Service | target="shop" | current=POS | suggested=NEU
  text: "cảm_ơn shop . chắc_chắn sẽ quay lại lần nữa"
  context: "cảm_ơn shop . chắc_chắn sẽ quay lại"
- line 396: aspect=General | target="hình" | current=POS | suggested=NEU
  text: "đảm_bảo i hình luon"
  context: "đảm_bảo i hình luon"
- line 401: aspect=Electronics | target="sóng" | current=POS | suggested=NEU
  text: "sóng căng vứt"
  context: "sóng căng vứt"
- line 405: aspect=Electronics | target="Bàn_phím" | current=POS | suggested=NEG
  text: "Bàn_phím gõ êm và độ nảy khá tốt. Trái_lại, Nhân_viên nói chuyện khó chịu nên mình ngại hỏi thêm."
  context: "Bàn_phím gõ êm và độ nảy"
- line 408: aspect=Price | target="giá" | current=POS | suggested=NEG
  text: "mua tiện_lợi giá hợp_lý"
  context: "mua tiện_lợi giá hợp_lý"
- line 437: aspect=Service | target="Phục_vụ" | current=NEG | suggested=POS
  text: "Củ_sạc đi kèm dùng ổn và vào điện nhanh. Bù_lại, Phục_vụ lạnh_nhạt nên trải_nghiệm rất tụt mood."
  context: "và vào điện nhanh. Bù_lại, Phục_vụ lạnh_nhạt nên trải_nghiệm rất tụt"
- line 450: aspect=Price | target="Tầm_giá" | current=POS | suggested=NEG
  text: "Form may rộng thùng_thình nên nhìn rất dừ. Bù_lại, Tầm_giá này mua khá hời."
  context: "nên nhìn rất dừ. Bù_lại, Tầm_giá này mua khá hời."
- line 459: aspect=App | target="phần_mềm" | current=POS | suggested=NEG
  text: "phần_mềm mua_sắm tiện_lợi uy_tín mọi người nên tải về sử_dụng"
  context: "phần_mềm mua_sắm tiện_lợi uy_tín mọi người"
- line 461: aspect=App | target="app" | current=POS | suggested=NEG
  text: "app tối 99"
  context: "app tối 99"
- line 506: aspect=App | target="ứng_dụng" | current=NEG | suggested=POS
  text: "bị khóa tài_khoản lần đầu dùng ứng_dụng"
  context: "khóa tài_khoản lần đầu dùng ứng_dụng"
- line 508: aspect=App | target="app" | current=NEG | suggested=POS
  text: "chơi game khá mượt (điều mình thích nhất ở vivo y11) , hình ảnh camera thì không bằng samsung galaxy j7 prime mặc dù đều là 13 mega pixel và 8 mega pixel, với những app nước ngoài như naver thì xử lí khá chậm còn lại mọi thứ khá ổn so với giá thành, ah còn dung lượng hệ thống quá nhiều, 32G chỉ khả dụng gần 20G, xem như tạm ổn."
  context: "8 mega pixel, với những app nước ngoài như naver thì"
- line 534: aspect=Electronics | target="pin" | current=POS | suggested=NEU
  text: "Sản phẩm qua gọn trong tầm giá pin châu câu hịnh gọn . Rất hài lòng ae nào chiến gmae thiua nhẹ đất ok đã trại ghiep hơn 1t"
  context: "qua gọn trong tầm giá pin châu câu hịnh gọn ."
- line 549: aspect=Fashion | target="áo" | current=POS | suggested=NEG
  text: "áo như hình tuy thời_gian giao hành lâu nhưng không sao"
  context: "áo như hình tuy thời_gian giao"
