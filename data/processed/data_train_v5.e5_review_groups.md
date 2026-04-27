# E5 Review Queue
**Source**: data_train_v5.autofixed.jsonl
**Total E5 records**: 593

## Top Target Errors
- "app": 54 lần
- "nhân viên": 44 lần
- "shop": 30 lần
- "Nhân viên": 26 lần
- "áo": 24 lần
- "ứng_dụng": 22 lần
- "ứng dụng": 20 lần
- "hàng": 20 lần
- "giá": 19 lần
- "pin": 16 lần
- "voucher": 16 lần
- "tiền": 13 lần
- "phần_mềm": 12 lần
- "máy": 12 lần
- "Pin": 10 lần
- "chất": 10 lần
- "khách_hàng": 10 lần
- "size": 9 lần
- "màn hình": 9 lần
- "Vải": 8 lần

## Top Aspect Errors
- Service: 164 lần
- App: 128 lần
- Electronics: 114 lần
- Price: 76 lần
- Fashion: 75 lần
- General: 65 lần
- Ship: 25 lần

## Sentiment Transitions
- NEG->POS: 267 lần
- POS->NEG: 229 lần
- POS->NEU: 151 lần

## Review Groups

### App | app | NEG->POS (27)
- line 276: target="app" | aspect=App | current=NEG | suggested=POS
  text: "quá nhiều quảng_cáo dùng app khác quảng_cáo đều nhảy qua lazada"
  context: "quá nhiều quảng_cáo dùng app khác quảng_cáo đều nhảy qua"
- line 508: target="app" | aspect=App | current=NEG | suggested=POS
  text: "chơi game khá mượt (điều mình thích nhất ở vivo y11) , hình ảnh camera thì không bằng samsung galaxy j7 prime mặc dù đều là 13 mega pixel và 8 mega pixel, với những app nước ngoài như naver thì xử lí khá chậm còn lại mọi thứ khá ổn so với giá thành, ah còn dung lượng hệ thống quá nhiều, 32G chỉ khả dụng gần 20G, xem như tạm ổn."
  context: "8 mega pixel, với những app nước ngoài như naver thì"
- line 1181: target="app" | aspect=App | current=NEG | suggested=POS
  text: "quảng_cáo quá nhiều không bấm nhưng lúc_nào cũng hiện vào app"
  context: "nhưng lúc_nào cũng hiện vào app"
- line 1555: target="app" | aspect=App | current=NEG | suggested=POS
  text: "ngâm đơn hàng từ 31 7 đến 19 8 vẫn chưa thấy giao liên_hệ tổng_đài thì không au bắt máy đơn thanh_toán rồi mà ngâm kiểu đó trong khi đang cần không một ai hỗ_trợ khách_hàng thì dẹp app dùm 1 cái đến tận 11 10 mới nhận được hàng đã vậy nhận thùng hàng còn bị ẩm_ướt tèm lem"
  context: "ai hỗ_trợ khách_hàng thì dẹp app dùm 1 cái đến tận"
- line 1859: target="app" | aspect=App | current=NEG | suggested=POS
  text: "đừng lượng pin 5000 nhưng không dùng pin vẫn tụt dù app ngầm đã tắt. sạc pin 100% không dùng mà tụt đến 3%"
  context: "dùng pin vẫn tụt dù app ngầm đã tắt. sạc pin"

### App | app | POS->NEG (24)
- line 177: target="app" | aspect=App | current=POS | suggested=NEG
  text: "Cá_nhân mik thì mik thấy app này khá tiện_lợi và rất đa_dạng vật_dụng. Tuy nhiên, Tiki giá đắt ae ạ đặt_hàng 50 k lên tận 400 k tiki kiểu j đấy bịp à"
  context: "Cá_nhân mik thì mik thấy app này khá tiện_lợi và rất"
- line 283: target="app" | aspect=App | current=POS | suggested=NEG
  text: "app hai quá hay quá đặt_hàng 2 3 tiếng là giao rồi"
  context: "app hai quá hay quá đặt_hàng"
- line 461: target="app" | aspect=App | current=POS | suggested=NEG
  text: "app tối 99"
  context: "app tối 99"
- line 657: target="app" | aspect=App | current=POS | suggested=NEG
  text: "Cá_nhân mik thì mik thấy app này khá tiện_lợi và rất đa_dạng vật_dụng nhưng nói chung là bèo trong tầm giá máy cao cấp"
  context: "Cá_nhân mik thì mik thấy app này khá tiện_lợi và rất"
- line 892: target="app" | aspect=App | current=POS | suggested=NEG
  text: "Cá_nhân mik thì mik thấy app này khá tiện_lợi và rất đa_dạng vật_dụng, nhưng giá thì đắt sản_phẩm thì ít"
  context: "Cá_nhân mik thì mik thấy app này khá tiện_lợi và rất"

### Service | nhân viên | POS->NEG (23)
- line 5: target="nhân viên" | aspect=Service | current=POS | suggested=NEG
  text: "Trước tiên nói về thái độ phục vụ của nhân viên tgdđ là quá ok rồi.mới dùng máy được 1 tuần thấy khá ok chì mỗi tội hay tự động nhảy lọc ánh sáng xanh trong khi không dùng tới"
  context: "thái độ phục vụ của nhân viên tgdđ là quá ok rồi.mới"
- line 822: target="nhân viên" | aspect=Service | current=POS | suggested=NEG
  text: "Đã dùng được một tuần: mình có đánh giá như sau: Máy đẹp, pin khỏe, camera cơ bản ok, nhân viên phục vụ nhiệt tình tận nơi, các bạn còn trần trừ gì mà không nhấc,"
  context: "khỏe, camera cơ bản ok, nhân viên phục vụ nhiệt tình tận"
- line 880: target="nhân viên" | aspect=Service | current=POS | suggested=NEG
  text: "Mới lấy thêm 1 cây.Bền,rẽ,đẹp và nhất là cách phục vụ của em gái nhân viên tên Thuý .Tận tình và chu đáo."
  context: "phục vụ của em gái nhân viên tên Thuý .Tận tình và"
- line 1595: target="nhân viên" | aspect=Service | current=POS | suggested=NEG
  text: "Chơi game khá lag. Đáp ứng tốt nhu cầu cơ bản nghe gọi mạng xã hội lướt web ... nhân viên giao hàng phục vụ tận tình"
  context: "xã hội lướt web ... nhân viên giao hàng phục vụ tận"
- line 1977: target="nhân viên" | aspect=Service | current=POS | suggested=NEG
  text: "Mình cũng vừa tậu em nó hôm qua. Rất ok, 5* cho sản phẩm và nhân viên bán hàng nhé"
  context: "5* cho sản phẩm và nhân viên bán hàng nhé"

### App | ứng_dụng | NEG->POS (22)
- line 506: target="ứng_dụng" | aspect=App | current=NEG | suggested=POS
  text: "bị khóa tài_khoản lần đầu dùng ứng_dụng"
  context: "khóa tài_khoản lần đầu dùng ứng_dụng"
- line 1257: target="ứng_dụng" | aspect=App | current=NEG | suggested=POS
  text: "sử_dụng ứng_dụng mà gặp phải quảng_cáo của lazada là rất bực_mình các nút bấm điều_chỉnh trên quảng_cáo thì nhỏ thao_tác vuốt màn_hình cũng sẽ điều hướng chuyển qua lazada vì cái quảng_cáo khó_chịu này nên tôi không mua máy_hút_bụi từ lazada rất lâu rồi"
  context: "sử_dụng ứng_dụng mà gặp phải quảng_cáo của"
- line 1394: target="ứng_dụng" | aspect=App | current=NEG | suggested=POS
  text: "dm quả_cáo gì mà đi ứng_dụng nào cũng có_mặt lazada hết bực rồi đó"
  context: "dm quả_cáo gì mà đi ứng_dụng nào cũng có_mặt lazada hết"
- line 1760: target="ứng_dụng" | aspect=App | current=NEG | suggested=POS
  text: "giờ lừa_đảo nhiều ứng_dụng gì bắt bấm vào link qua tin nhắn_vớ vẫn"
  context: "giờ lừa_đảo nhiều ứng_dụng gì bắt bấm vào link"
- line 2613: target="ứng_dụng" | aspect=App | current=NEG | suggested=POS
  text: "quảng_cáo nhiều xóa ứng_dụng"
  context: "quảng_cáo nhiều xóa ứng_dụng"

### App | ứng dụng | NEG->POS (20)
- line 629: target="ứng dụng" | aspect=App | current=NEG | suggested=POS
  text: "Nhiều lúc đang vào vẫn bị văng ra..hơi đơ đơ tí, mặc dù tải ít ứng dụng grap goviet zing mp3 shoppe thôi..pin cũng không trâu lắm đâu"
  context: "tí, mặc dù tải ít ứng dụng grap goviet zing mp3 shoppe"
- line 688: target="ứng dụng" | aspect=App | current=NEG | suggested=POS
  text: "sài messenger bị giật giật.mong phan hoi từ nhan vien.mang rat manh và ko co ứng dụng ngầm mà vẫn giật"
  context: "rat manh và ko co ứng dụng ngầm mà vẫn giật"
- line 800: target="ứng dụng" | aspect=App | current=NEG | suggested=POS
  text: "Sóng sánh kém lắm,giữa đất thị trấn mà chỉ đc 2-3 vạch. Wifi vào phòng trong cách khoảng 5m mà bắt đc 3 vạch. Đã gửi đi hãng thẩm định. Pin qua đêm tắt hết ứng dụng,mạng mà sáng dậy tụt 12%.
Chơi liên quân đôi khi vẫn bị khựng lại chút.đc cái màn nét."
  context: "Pin qua đêm tắt hết ứng dụng,mạng mà sáng dậy tụt 12%."
- line 1330: target="ứng dụng" | aspect=App | current=NEG | suggested=POS
  text: "Sóng sánh kém lắm,giữa đất thị trấn mà chỉ đc 2-3 vạch. Wifi vào phòng trong cách khoảng 5m mà bắt đc 3 vạch. Đã gửi đi hãng thẩm định. Ổ_cứng qua đêm tắt hết ứng dụng,mạng mà sáng dậy tụt 12%.
Chơi liên quân đôi khi vẫn bị khựng lại chút.đc cái màn nét."
  context: "Ổ_cứng qua đêm tắt hết ứng dụng,mạng mà sáng dậy tụt 12%."
- line 1409: target="ứng dụng" | aspect=App | current=NEG | suggested=POS
  text: "Không nên mua. Thỉnh thoảng bị thoát ứng dụng . Cảm ứng k chuẩn. Vào các ứng dụng thì chậm"
  context: "mua. Thỉnh thoảng bị thoát ứng dụng . Cảm ứng k chuẩn."

### Service | nhân viên | POS->NEU (18)
- line 67: target="nhân viên" | aspect=Service | current=POS | suggested=NEU
  text: "Từ khi cập nhật phần mềm thì chậm như rùa bò không thể chơi được game. Còn Khá ổn nhân viên nhiệt tình tư vấn"
  context: "được game. Còn Khá ổn nhân viên nhiệt tình tư vấn"
- line 186: target="nhân viên" | aspect=Service | current=POS | suggested=NEU
  text: "Với tầm giá này redmi note 9S quá OK,cấu hình ổn,camera ổn,loa ổn,củ_sạc quá OK,nhân viên tư vấn nhiệt tình,vui vẻ.Cám Ơn TGDD."
  context: "hình ổn,camera ổn,loa ổn,củ_sạc quá OK,nhân viên tư vấn nhiệt tình,vui vẻ.Cám"
- line 425: target="nhân viên" | aspect=Service | current=POS | suggested=NEU
  text: "Mới mua máy đc 3 ngày à máy camera thì hơi tệ đặc biệt cm trước chụp xấu à pin xài trâu sạc tầm hơn 1 tiếng chơi game lq thì vào game hơi chậm nếu chơi 4g thì vào xong phải đợi một tý cho mạng nó ổn định thì mới chơi đc còn ko thì nó cứ đỏ lòm à chơi game ko nóng may lắm tạm đc nhưng ra vào app hơi lâu có lúc lag bắt sóng wifi kiếm cực luôn đứng trong phòng thì gần cục sóng wifi bthuong ra trước cửa phòng thì thôi đc 1 cục à trong khi phòng xa wifi chưa đc 10m 4g chơi game còn tốc độ cao thì ko sao hết thì lag lúc vào trận combat thì fps ổn định ko lag,nhân viên phục vụ nhiệt tình thân thiện"
  context: "thì fps ổn định ko lag,nhân viên phục vụ nhiệt tình thân"
- line 988: target="nhân viên" | aspect=Service | current=POS | suggested=NEU
  text: "Khá ổn nhân viên nhiệt tình tư vấn ! Mức giá tầm trung quá hợp lí !
Mong sử dụng lâu vẫn OK :))"
  context: "Khá ổn nhân viên nhiệt tình tư vấn !"
- line 1234: target="nhân viên" | aspect=Service | current=POS | suggested=NEU
  text: "Ổn trong tầm giá, nhân viên nhiệt tình, vui vẻ. Muốn Rom 64 thì chọn Realme 5 nhé, do hết hàng nên chọn con này. Rom 32 hơi đuối tí. Sau 1 ngày mua chưa thấy gì lạ."
  context: "Ổn trong tầm giá, nhân viên nhiệt tình, vui vẻ. Muốn"

### Fashion | áo | NEG->POS (16)
- line 711: target="áo" | aspect=Fashion | current=NEG | suggested=POS
  text: "áo chất cứng"
  context: "áo chất cứng"
- line 726: target="áo" | aspect=Fashion | current=NEG | suggested=POS
  text: "nhưng áo bị bung chỉ nhiều"
  context: "nhưng áo bị bung chỉ nhiều"
- line 930: target="áo" | aspect=Fashion | current=NEG | suggested=POS
  text: "mua 5 áo mà 4 chất khác nhau"
  context: "mua 5 áo mà 4 chất khác nhau"
- line 1298: target="áo" | aspect=Fashion | current=NEG | suggested=POS
  text: "hợp với giá tiền , nhưng áo thun trắng vải khác và from nhỏ hơn so với mình mua lần đầu nên hơi buồn"
  context: "với giá tiền , nhưng áo thun trắng vải khác và"
- line 2930: target="áo" | aspect=Fashion | current=NEG | suggested=POS
  text: "áo thì chật , được vải mềm không gọng như hình , có mùi hắc"
  context: "áo thì chật , được vải"

### Service | shop | POS->NEU (14)
- line 128: target="shop" | aspect=Service | current=POS | suggested=NEU
  text: "shop cực dễ_thương"
  context: "shop cực dễ_thương"
- line 362: target="shop" | aspect=Service | current=POS | suggested=NEU
  text: "cảm_ơn shop . chắc_chắn sẽ quay lại lần nữa"
  context: "cảm_ơn shop . chắc_chắn sẽ quay lại"
- line 659: target="shop" | aspect=Service | current=POS | suggested=NEU
  text: "mình mua sản_phẩm còn được shop tặng thêm món quà nhỏ rất dễ_thương"
  context: "mình mua sản_phẩm còn được shop tặng thêm món quà nhỏ"
- line 2218: target="shop" | aspect=Service | current=POS | suggested=NEU
  text: "shop nhiệt_tình còn tặng quà cho nữa"
  context: "shop nhiệt_tình còn tặng quà cho"
- line 3929: target="shop" | aspect=Service | current=POS | suggested=NEU
  text: "shop rất dễ_thương đã sẵn_lòng cho đổi size giầy"
  context: "shop rất dễ_thương đã sẵn_lòng cho"

### Service | Nhân viên | POS->NEU (14)
- line 1032: target="Nhân viên" | aspect=Service | current=POS | suggested=NEU
  text: "Nhân viên phụ vụ dễ thương .máy chiến pupg cực mượt .pin trâu game liên tục 8 tiếng . chụp ảnh rất đẹp trong tầm giá"
  context: "Nhân viên phụ vụ dễ thương .máy"
- line 1801: target="Nhân viên" | aspect=Service | current=POS | suggested=NEU
  text: "Đi thoại mượt chơi game ngon 
Âm báo thức bật maxloa luôn nghe vẫn nhỏ
Nhân viên phục vụ nhiệt tình"
  context: "maxloa luôn nghe vẫn nhỏ Nhân viên phục vụ nhiệt tình"
- line 2825: target="Nhân viên" | aspect=Service | current=POS | suggested=NEU
  text: "Nhân viên online tư vấn nhiệt tình. Mình mua online giao tận nơi rất uy tín . Máy sử dụng rất tốt. S20 untra đúng là ấn tượng pin ổn (mấy má bật full màn hình, full tốt độ 120 rồi la hao pin vãi thật). Màn hình xuất sắc . Hì hơi bực cái củ sạc chỉ có 25W chứ ko phải 45W. Nhu vay thì ok rồi cảm ơn ad."
  context: "Nhân viên online tư vấn nhiệt tình."
- line 4105: target="Nhân viên" | aspect=Service | current=POS | suggested=NEU
  text: "Mua hồi tháng 2 lúc giảm còn 5 triệu mấy .Ai cũng chê nhưng xài 1 tháng rồi mọi thứ đều ổn.Nhân viên tư vẫn nhiệt tình, tầm trung nên không thể đòi hỏi vân tay nhạy.Chs game ít khi bị giật lag.Thiết kế đẹp mắt.Màu lưng máy siêu đẹp.Nói chung những bạn có túi tiền tầm tầm thì vẫn nên mua rất tốt,dành cho làm việc giải trí đều ok.Tin dùng Samsung bao năm"
  context: "tháng rồi mọi thứ đều ổn.Nhân viên tư vẫn nhiệt tình, tầm"
- line 4977: target="Nhân viên" | aspect=Service | current=POS | suggested=NEU
  text: "Tạm thời thì thấy máy khá ổn 
Nhân viên tư vấn rất nhiệt tình
Kết nhất em máy cái cáp_sạc"
  context: "thì thấy máy khá ổn Nhân viên tư vấn rất nhiệt tình"

### Service | Nhân viên | POS->NEG (11)
- line 526: target="Nhân viên" | aspect=Service | current=POS | suggested=NEG
  text: "Nhân viên nhiệt tình nhưg bên bán trả góp FE với Home Credit làm ăn k hiểu nổi... ng ta góp mỗi thág đàg hoàng k thiếu 1ngàn nhưg lúc mua góp lại k duyệt hồ sơ... dở tệ... nhan vien tgdd thi ok"
  context: "Nhân viên nhiệt tình nhưg bên bán"
- line 774: target="Nhân viên" | aspect=Service | current=POS | suggested=NEG
  text: "Vừa mua hôm qua ở tgdd. Nhân viên rất nhiệt tình. Chơi game khá tốt nhưng có đều cáp_sạc tuột hơi nhanh"
  context: "mua hôm qua ở tgdd. Nhân viên rất nhiệt tình. Chơi game"
- line 1611: target="Nhân viên" | aspect=Service | current=POS | suggested=NEG
  text: "1 câu thui! Good
Nhân viên chăm sóc khách hàng rất nhiệt tình.
Luôn luôn ủng hộ TGDD"
  context: "1 câu thui! Good Nhân viên chăm sóc khách hàng rất"
- line 1627: target="Nhân viên" | aspect=Service | current=POS | suggested=NEG
  text: "Máy ngón trong tầm giá. Phù hợp cho học sinh. 
Nhân viên bán hàng tư vấn ok. Cáp_sạc trâu"
  context: "Phù hợp cho học sinh. Nhân viên bán hàng tư vấn ok."
- line 2611: target="Nhân viên" | aspect=Service | current=POS | suggested=NEG
  text: "Nhân viên tư vấn bán hàng nhiệt tình. Phải nói là ip xài rất ngon luôn. Chụp hình nghe nhạc tất cả đều ok. Pin tạm ổn. Khuyên mọi người nên mua sử dụng"
  context: "Nhân viên tư vấn bán hàng nhiệt"

### Price | tiền | NEG->POS (11)
- line 1164: target="tiền" | aspect=Price | current=NEG | suggested=POS
  text: "tiki giao thiếu hàng , nhắn_tin bảo sẽ bù lại tiền nhưng chẳng thấy đâu , thái_độ phục_vụ không tốt"
  context: "nhắn_tin bảo sẽ bù lại tiền nhưng chẳng thấy đâu ,"
- line 1464: target="tiền" | aspect=Price | current=NEG | suggested=POS
  text: "đặt_hàng giao cho ai đâu không , tui chưa hề nhận được mà báo đã thu tiền ngày 17 8 vậy cuối_cùng là giao cho ai"
  context: "được mà báo đã thu tiền ngày 17 8 vậy cuối_cùng"
- line 1623: target="tiền" | aspect=Price | current=NEG | suggested=POS
  text: "app lừa_đảo làm mất tiền ng dùng"
  context: "app lừa_đảo làm mất tiền ng dùng"
- line 1629: target="tiền" | aspect=Price | current=NEG | suggested=POS
  text: "Khăn đẹp , áo đẹp nhưng so với tiền bỏ ra thì mua bị mắc"
  context: "áo đẹp nhưng so với tiền bỏ ra thì mua bị"
- line 3425: target="tiền" | aspect=Price | current=NEG | suggested=POS
  text: "shop giao thiếu hàng , nhắn_tin bảo sẽ bù lại tiền nhưng chẳng thấy đâu , thái_độ phục_vụ không tốt"
  context: "nhắn_tin bảo sẽ bù lại tiền nhưng chẳng thấy đâu ,"

### Electronics | pin | POS->NEU (10)
- line 497: target="pin" | aspect=Electronics | current=POS | suggested=NEU
  text: "Đã mua tại thế giới di động thị xã An Khê gia Lai...qua 48h sử dụng cảm nhận máy rất đẹp mượt mà hợp cho mình làm vlog camera chụp hình quay video rất đẹp.. nhân viên rất nhiệt tình và dễ thương...pin rất trâu nha mọi người...sau này sẽ bình luận tiếp nha.. quá đẹp và sang trọng.."
  context: "rất nhiệt tình và dễ thương...pin rất trâu nha mọi người...sau"
- line 534: target="pin" | aspect=Electronics | current=POS | suggested=NEU
  text: "Sản phẩm qua gọn trong tầm giá pin châu câu hịnh gọn . Rất hài lòng ae nào chiến gmae thiua nhẹ đất ok đã trại ghiep hơn 1t"
  context: "qua gọn trong tầm giá pin châu câu hịnh gọn ."
- line 2439: target="pin" | aspect=Electronics | current=POS | suggested=NEU
  text: "Rất mượt, Rất ok ạ, nói chug tiền nào của nấy.  Nhưg sau 3 thág, pin tuột 2%, còn có 98%. Xài củ sạc nhah đi kèm máy."
  context: "nấy. Nhưg sau 3 thág, pin tuột 2%, còn có 98%."
- line 2599: target="pin" | aspect=Electronics | current=POS | suggested=NEU
  text: "Theo e đánh giá máy tốt .mở 4g từ 6h30 tối .em lên Youtube xem đến 5h30 sáng pin còn khoãn 33% .game liên quân .pubg Mobi .rất mượn .chụp hình e ko xài .chỉ yêu game thôi .máy như thế quá ngon rồi .còn mấy bạn thấy sao mình ko bít .máy mình ko cập nhật hệ thông .còn nguyên zin zin y xì"
  context: "Youtube xem đến 5h30 sáng pin còn khoãn 33% .game liên"
- line 4801: target="pin" | aspect=Electronics | current=POS | suggested=NEU
  text: "Sp dùng quá oki so với tầm giá, pin trâu , sóng khoẻ , game chạy mượt  , cấu hình ổn định"
  context: "oki so với tầm giá, pin trâu , sóng khoẻ ,"

### General | chất | NEG->POS (10)
- line 972: target="chất" | aspect=General | current=NEG | suggested=POS
  text: "chất rất dày"
  context: "chất rất dày"
- line 1618: target="chất" | aspect=General | current=NEG | suggested=POS
  text: "đúng chất vải thô đũi"
  context: "đúng chất vải thô đũi"
- line 3184: target="chất" | aspect=General | current=NEG | suggested=POS
  text: "chất thì được như có một cái bị rách"
  context: "chất thì được như có một"
- line 3474: target="chất" | aspect=General | current=NEG | suggested=POS
  text: "chất giày thì đk nhưng mà lỗi như thế_thì không đk"
  context: "chất giày thì đk nhưng mà"
- line 4333: target="chất" | aspect=General | current=NEG | suggested=POS
  text: "chất vải mặc vào khá ngứa"
  context: "chất vải mặc vào khá ngứa"

### General | hàng | POS->NEG (9)
- line 1470: target="hàng" | aspect=General | current=POS | suggested=NEG
  text: "chị bán hàng nhiệt_tình nữa nè"
  context: "chị bán hàng nhiệt_tình nữa nè"
- line 1717: target="hàng" | aspect=General | current=POS | suggested=NEG
  text: "bạn chủ bán hàng nhiệt_tình"
  context: "bạn chủ bán hàng nhiệt_tình"
- line 1890: target="hàng" | aspect=General | current=POS | suggested=NEG
  text: "chị bán hàng đáng yêu"
  context: "chị bán hàng đáng yêu"
- line 2847: target="hàng" | aspect=General | current=POS | suggested=NEG
  text: "app mua_bán hàng uy_tín"
  context: "app mua_bán hàng uy_tín"
- line 3218: target="hàng" | aspect=General | current=POS | suggested=NEG
  text: "hàng y hình , mỗi tội cái mùi túi rất khó_chịu"
  context: "hàng y hình , mỗi tội"

### Fashion | Vải | POS->NEG (8)
- line 66: target="Vải" | aspect=Fashion | current=POS | suggested=NEG
  text: "Vải mịn nên mặc lâu vẫn thấy dễ chịu. Bù_lại, Voucher nghèo nên cảm_giác không hời."
  context: "Vải mịn nên mặc lâu vẫn"
- line 227: target="Vải" | aspect=Fashion | current=POS | suggested=NEG
  text: "Vải mịn nên mặc lâu vẫn thấy dễ chịu mà giá_tiền như vậy là chưa đáng."
  context: "Vải mịn nên mặc lâu vẫn"
- line 627: target="Vải" | aspect=Fashion | current=POS | suggested=NEG
  text: "Vải mịn nên mặc lâu vẫn thấy dễ chịu; còn giá hơi chát so với kỳ_vọng."
  context: "Vải mịn nên mặc lâu vẫn"
- line 641: target="Vải" | aspect=Fashion | current=POS | suggested=NEG
  text: "Vải mịn nên mặc lâu vẫn thấy dễ chịu nhưng phí_ship cao nên tổng đơn bị chát."
  context: "Vải mịn nên mặc lâu vẫn"
- line 3676: target="Vải" | aspect=Fashion | current=POS | suggested=NEG
  text: "Vải mịn nên mặc lâu vẫn thấy dễ chịu. Tuy_nhiên, Voucher nghèo nên cảm_giác không hời."
  context: "Vải mịn nên mặc lâu vẫn"

### Price | giá | POS->NEG (8)
- line 109: target="giá" | aspect=Price | current=POS | suggested=NEG
  text: "bộ này vải hơi mỏg lại thêm màu trắg xanh nên mặc hơi lộ nhưg tầm giá này thì cx là ok rồi"
  context: "mặc hơi lộ nhưg tầm giá này thì cx là ok"
- line 408: target="giá" | aspect=Price | current=POS | suggested=NEG
  text: "mua tiện_lợi giá hợp_lý"
  context: "mua tiện_lợi giá hợp_lý"
- line 2134: target="giá" | aspect=Price | current=POS | suggested=NEG
  text: "tốt đáng để trải_nghiệm dễ thao_tác giá hời"
  context: "đáng để trải_nghiệm dễ thao_tác giá hời"
- line 2966: target="giá" | aspect=Price | current=POS | suggested=NEG
  text: "Mỏng hơn so với ảnh , màu nhạt hơn, nhưng bộ này vải hơi mỏg lại thêm màu trắg xanh nên mặc hơi lộ nhưg tầm giá này thì cx là ok rồi"
  context: "mặc hơi lộ nhưg tầm giá này thì cx là ok"
- line 3117: target="giá" | aspect=Price | current=POS | suggested=NEG
  text: "máy mặt sao bóng bẩy soi gương đc máy khá dầy nhưng k đòi hỏi gì với giá 3tr610 chip khá pin sục khá nhanh pin 5k như 4k sạc 18w cho viên pin 5k chờ sml luôn cam sao khá cam trc phế lqmb pupg tạm chấp nhận đc. Mua về nếu tác vụ thông thường fb zalo v..v thì mượt Sài đc chắc hơn ngày còn game thì tầm 8-10 tiếng là tèo ..Nhân viên tgdđ nhiệt tình các kiểu con Đà điểu"
  context: "k đòi hỏi gì với giá 3tr610 chip khá pin sục"

### Service | shop | POS->NEG (8)
- line 650: target="shop" | aspect=Service | current=POS | suggested=NEG
  text: "shop chắc_chắn có nên mới đặt"
  context: "shop chắc_chắn có nên mới đặt"
- line 2424: target="shop" | aspect=Service | current=POS | suggested=NEG
  text: "shop nhiệt_tình , đặt trưa nay , sáng_mai có hàng rồi"
  context: "shop nhiệt_tình , đặt trưa nay"
- line 3280: target="shop" | aspect=Service | current=POS | suggested=NEG
  text: "shop bán hàng có tâm ! !"
  context: "shop bán hàng có tâm !"
- line 5342: target="shop" | aspect=Service | current=POS | suggested=NEG
  text: "mọi sai_sót đều được shop hỗ_trợ nhiệt_tình rất ok"
  context: "mọi sai_sót đều được shop hỗ_trợ nhiệt_tình rất ok"
- line 6143: target="shop" | aspect=Service | current=POS | suggested=NEG
  text: "shop uy_tín từ a tới vậy"
  context: "shop uy_tín từ a tới vậy"

### Service | shop | NEG->POS (8)
- line 1174: target="shop" | aspect=Service | current=NEG | suggested=POS
  text: "shop giao nhầm dép"
  context: "shop giao nhầm dép"
- line 1587: target="shop" | aspect=Service | current=NEG | suggested=POS
  text: "voucher chưa dùng nhưng đúng như shop mô_tả"
  context: "chưa dùng nhưng đúng như shop mô_tả"
- line 2558: target="shop" | aspect=Service | current=NEG | suggested=POS
  text: "nhưng shop giao cho e cái bị lỗi , 1 bên ren may qua ngực . 1 bên ren chỉ may tới nữa ngực lộ nhũ . mặc lên rất kì"
  context: "nhưng shop giao cho e cái bị"
- line 3053: target="shop" | aspect=Service | current=NEG | suggested=POS
  text: "năm_ngoái cũng mua 1c quần warm bên shop rồi , quần chất khác so với năm_ngoái cứng hơn shop ạ"
  context: "mua 1c quần warm bên shop rồi , quần chất khác"
- line 4875: target="shop" | aspect=Service | current=NEG | suggested=POS
  text: "chỉ có điều khâu đặt_hàng làm trải nghiệm của mình không vui lắm dù mình hiểu là shop cũng đã cố_gắng rồi"
  context: "lắm dù mình hiểu là shop cũng đã cố_gắng rồi"

### General | Chất_liệu | NEG->POS (8)
- line 1221: target="Chất_liệu" | aspect=General | current=NEG | suggested=POS
  text: "Chất_liệu nhìn khá rẻ nên cảm_giác không đã. Bù_lại, Shipper thân_thiện và giao khá đúng giờ."
  context: "Chất_liệu nhìn khá rẻ nên cảm_giác"
- line 1603: target="Chất_liệu" | aspect=General | current=NEG | suggested=POS
  text: "Chất_liệu nhìn khá rẻ nên cảm_giác không đã mà giao_hàng cẩn_thận nên món tới nơi còn đẹp."
  context: "Chất_liệu nhìn khá rẻ nên cảm_giác"
- line 1687: target="Chất_liệu" | aspect=General | current=NEG | suggested=POS
  text: "Chất_liệu nhìn khá rẻ nên cảm_giác không đã. Bù_lại, Thời_gian giao_hàng khá chuẩn như cam_kết."
  context: "Chất_liệu nhìn khá rẻ nên cảm_giác"
- line 2909: target="Chất_liệu" | aspect=General | current=NEG | suggested=POS
  text: "Chất_liệu nhìn khá rẻ nên cảm_giác không đã. Tuy_nhiên, Shipper giao đúng hẹn nên mình khá hài_lòng."
  context: "Chất_liệu nhìn khá rẻ nên cảm_giác"
- line 3234: target="Chất_liệu" | aspect=General | current=NEG | suggested=POS
  text: "Chất_liệu nhìn khá rẻ nên cảm_giác không đã; còn vận_chuyển xử_lý nhanh nên đơn đi khá mượt."
  context: "Chất_liệu nhìn khá rẻ nên cảm_giác"

### Price | voucher | NEG->POS (8)
- line 1587: target="voucher" | aspect=Price | current=NEG | suggested=POS
  text: "voucher chưa dùng nhưng đúng như shop mô_tả"
  context: "voucher chưa dùng nhưng đúng như"
- line 1588: target="voucher" | aspect=Price | current=NEG | suggested=POS
  text: "Áo mặc mát và màu lên nhìn rất sáng nhưng voucher quá yếu nên gần như không ăn_thua."
  context: "lên nhìn rất sáng nhưng voucher quá yếu nên gần như"
- line 2708: target="voucher" | aspect=Price | current=NEG | suggested=POS
  text: "thôi chịu tự_nhiên cr 01 mặc_dù chẳng lạm_dụng voucher gì cả"
  context: "cr 01 mặc_dù chẳng lạm_dụng voucher gì cả"
- line 4689: target="voucher" | aspect=Price | current=NEG | suggested=POS
  text: "manager quán mà_lại không hề biết về dkien sử_dụng e voucher từ shopee"
  context: "biết về dkien sử_dụng e voucher từ shopee"
- line 4991: target="voucher" | aspect=Price | current=NEG | suggested=POS
  text: "cho voucher mà sử_dụng toàn bị hủy"
  context: "cho voucher mà sử_dụng toàn bị hủy"

### Price | Tầm_giá | POS->NEG (7)
- line 450: target="Tầm_giá" | aspect=Price | current=POS | suggested=NEG
  text: "Form may rộng thùng_thình nên nhìn rất dừ. Bù_lại, Tầm_giá này mua khá hời."
  context: "nên nhìn rất dừ. Bù_lại, Tầm_giá này mua khá hời."
- line 819: target="Tầm_giá" | aspect=Price | current=POS | suggested=NEG
  text: "Quần bị chật phần hông nên đi lại khó. Tuy_nhiên, Tầm_giá khá hợp_lý cho nhu_cầu cơ_bản."
  context: "nên đi lại khó. Tuy_nhiên, Tầm_giá khá hợp_lý cho nhu_cầu cơ_bản."
- line 1075: target="Tầm_giá" | aspect=Price | current=POS | suggested=NEG
  text: "Vải khá mỏng nên mặc dễ lộ. Bù_lại, Tầm_giá khá hợp_lý cho nhu_cầu cơ_bản."
  context: "nên mặc dễ lộ. Bù_lại, Tầm_giá khá hợp_lý cho nhu_cầu cơ_bản."
- line 5105: target="Tầm_giá" | aspect=Price | current=POS | suggested=NEG
  text: "Vải hơi thô và mặc bí người. Xét_về_mặt_khác, Tầm_giá khá hợp_lý cho nhu_cầu cơ_bản."
  context: "và mặc bí người. Xét_về_mặt_khác, Tầm_giá khá hợp_lý cho nhu_cầu cơ_bản."
- line 5686: target="Tầm_giá" | aspect=Price | current=POS | suggested=NEG
  text: "Áo mặc vào bị rộng vai và lệch dáng. Tuy_nhiên, Tầm_giá này mua khá hời."
  context: "vai và lệch dáng. Tuy_nhiên, Tầm_giá này mua khá hời."

### App | phần_mềm | POS->NEG (7)
- line 459: target="phần_mềm" | aspect=App | current=POS | suggested=NEG
  text: "phần_mềm mua_sắm tiện_lợi uy_tín mọi người nên tải về sử_dụng"
  context: "phần_mềm mua_sắm tiện_lợi uy_tín mọi người"
- line 1451: target="phần_mềm" | aspect=App | current=POS | suggested=NEG
  text: "phần_mềm hay lắm tôi làm được rồi nhưng mọi người đừng tải khó sài lắm"
  context: "phần_mềm hay lắm tôi làm được"
- line 2802: target="phần_mềm" | aspect=App | current=POS | suggested=NEG
  text: "phần_mềm shopee mua_sắm rất tiện_lợi và rất tốt"
  context: "phần_mềm shopee mua_sắm rất tiện_lợi và"
- line 2850: target="phần_mềm" | aspect=App | current=POS | suggested=NEG
  text: "tiki là 1 phần_mềm rất hay có nhiều đồ để mua"
  context: "tiki là 1 phần_mềm rất hay có nhiều đồ"
- line 3943: target="phần_mềm" | aspect=App | current=POS | suggested=NEG
  text: "phần_mềm rất tiện_lợi"
  context: "phần_mềm rất tiện_lợi"

### Fashion | áo | POS->NEG (7)
- line 549: target="áo" | aspect=Fashion | current=POS | suggested=NEG
  text: "áo như hình tuy thời_gian giao hành lâu nhưng không sao"
  context: "áo như hình tuy thời_gian giao"
- line 720: target="áo" | aspect=Fashion | current=POS | suggested=NEG
  text: "áo đôi có size tại_sao shop không phân_loại để khách chọn"
  context: "áo đôi có size tại_sao shop"
- line 2440: target="áo" | aspect=Fashion | current=POS | suggested=NEG
  text: "nhìn áo siêu yêu có cái hơi bự mặc_dù chọn size nhỏ nhất nên không mặc vừa phải đem cho bé chen mặc"
  context: "nhìn áo siêu yêu có cái hơi"
- line 2840: target="áo" | aspect=Fashion | current=POS | suggested=NEG
  text: "nói_chung là e nhìn là mê áo rồi đó do"
  context: "là e nhìn là mê áo rồi đó do"
- line 2907: target="áo" | aspect=Fashion | current=POS | suggested=NEG
  text: "áo y_như hình , vải hơi mỏng xíu và dây áo dơ"
  context: "áo y_như hình , vải hơi"

### Electronics | Wifi | POS->NEU (7)
- line 776: target="Wifi" | aspect=Electronics | current=POS | suggested=NEU
  text: "Wifi bắt ổn nên xem video không bị đứt; còn shop phản_hồi chậm nên mình đợi khá mệt."
  context: "Wifi bắt ổn nên xem video"
- line 1311: target="Wifi" | aspect=Electronics | current=POS | suggested=NEU
  text: "Wifi bắt ổn nên xem video không bị đứt; còn cửa_hàng xử_lý thiếu trách_nhiệm nên rất bực."
  context: "Wifi bắt ổn nên xem video"
- line 1477: target="Wifi" | aspect=Electronics | current=POS | suggested=NEU
  text: "Wifi bắt ổn nên xem video không bị đứt. Tuy_nhiên, Shop phản_hồi chậm nên mình đợi khá mệt."
  context: "Wifi bắt ổn nên xem video"
- line 5016: target="Wifi" | aspect=Electronics | current=POS | suggested=NEU
  text: "Wifi bắt ổn nên xem video không bị đứt. Tuy_nhiên, Nhân_viên tư_vấn hời_hợt nên hỏi gì cũng cụt_lủn."
  context: "Wifi bắt ổn nên xem video"
- line 6285: target="Wifi" | aspect=Electronics | current=POS | suggested=NEU
  text: "Wifi bắt ổn nên xem video không bị đứt nhưng phục_vụ lạnh_nhạt nên trải_nghiệm rất tụt mood."
  context: "Wifi bắt ổn nên xem video"

### Electronics | máy | POS->NEG (7)
- line 788: target="máy" | aspect=Electronics | current=POS | suggested=NEG
  text: "Sản phẩm tốt phục vụ chu đáo 
Mà a cho em hỏi máy này có hỗ trợ xạc không dây không anh"
  context: "Mà a cho em hỏi máy này có hỗ trợ xạc"
- line 2633: target="máy" | aspect=Electronics | current=POS | suggested=NEG
  text: "Nói chung rất OK  .và nhân viên phục vụ rất tận tình. chỉ là máy mình cầm nó hơi nặng tai"
  context: "rất tận tình. chỉ là máy mình cầm nó hơi nặng"
- line 5180: target="máy" | aspect=Electronics | current=POS | suggested=NEG
  text: "Rất tốt, nhân viên nhiệt tình lắm, lấy máy chiều hôm qua,toi về nhìn thấy vết sướt, sáng qua đoi máy khác ngay, nhân viên 333 hoàng liên sơn ,lao Cai."
  context: "viên nhiệt tình lắm, lấy máy chiều hôm qua,toi về nhìn"
- line 5406: target="máy" | aspect=Electronics | current=POS | suggested=NEG
  text: "Quá đã tiền nào của đó nhé mấy bạn máy quá em nhân viên phục vụ quá nhiệt tình luôn cảm ơn thế giới di động"
  context: "của đó nhé mấy bạn máy quá em nhân viên phục"
- line 5670: target="máy" | aspect=Electronics | current=POS | suggested=NEG
  text: "Mới mua em nó về để dùng nghe gọi, zalo fb, zing chạy cũng ổn. Còn bền k phải qua thời gian mới biết. 5sao vì các bạn nhân viên đmx rất nhiệt tình, mua máy 590k các bạn tư vấn dặn dò chu đáo. Mình mua ở đmx bùng binh mũ Tp bến tre, bạn Bình kỹ thuật và bạn Mi quản lý rất dễ thương nhiệt tình"
  context: "đmx rất nhiệt tình, mua máy 590k các bạn tư vấn"

### Electronics | Pin | NEG->POS (7)
- line 800: target="Pin" | aspect=Electronics | current=NEG | suggested=POS
  text: "Sóng sánh kém lắm,giữa đất thị trấn mà chỉ đc 2-3 vạch. Wifi vào phòng trong cách khoảng 5m mà bắt đc 3 vạch. Đã gửi đi hãng thẩm định. Pin qua đêm tắt hết ứng dụng,mạng mà sáng dậy tụt 12%.
Chơi liên quân đôi khi vẫn bị khựng lại chút.đc cái màn nét."
  context: "gửi đi hãng thẩm định. Pin qua đêm tắt hết ứng"
- line 944: target="Pin" | aspect=Electronics | current=NEG | suggested=POS
  text: "Pin tụt nhanh nên phải sạc liên_tục. Trái_lại, Shop giữ lời nên mình thấy khá tin_tưởng."
  context: "Pin tụt nhanh nên phải sạc"
- line 1395: target="Pin" | aspect=Electronics | current=NEG | suggested=POS
  text: "Pin tụt nhanh nên phải sạc liên_tục. Tuy_nhiên, Cửa_hàng xử_lý ổn nên mình không phải chờ lâu."
  context: "Pin tụt nhanh nên phải sạc"
- line 4683: target="Pin" | aspect=Electronics | current=NEG | suggested=POS
  text: "Pin tụt nhanh nên phải sạc liên_tục. Tuy_nhiên, Nhân_viên tư_vấn có tâm và nói chuyện dễ chịu."
  context: "Pin tụt nhanh nên phải sạc"
- line 6817: target="Pin" | aspect=Electronics | current=NEG | suggested=POS
  text: "Pin tụt nhanh nên phải sạc liên_tục mà phục_vụ lịch_sự nên trải_nghiệm mua dễ chịu."
  context: "Pin tụt nhanh nên phải sạc"

### Fashion | Giày | POS->NEG (7)
- line 838: target="Giày" | aspect=Fashion | current=POS | suggested=NEG
  text: "Giày đi êm chân và phối đồ dễ. Xét_về_mặt_khác, Voucher nghèo nên cảm_giác không hời."
  context: "Giày đi êm chân và phối"
- line 2444: target="Giày" | aspect=Fashion | current=POS | suggested=NEG
  text: "Giày đi êm chân và phối đồ dễ mà mã_giảm_giá ít nên vẫn thấy đắt."
  context: "Giày đi êm chân và phối"
- line 4369: target="Giày" | aspect=Fashion | current=POS | suggested=NEG
  text: "Giày đi êm chân và phối đồ dễ. Tuy_nhiên, Phí_ship cao nên tổng đơn bị chát."
  context: "Giày đi êm chân và phối"
- line 5027: target="Giày" | aspect=Fashion | current=POS | suggested=NEG
  text: "Giày đi êm chân và phối đồ dễ. Tuy_nhiên, Giá cao hơn mặt_bằng chung khá nhiều."
  context: "Giày đi êm chân và phối"
- line 5104: target="Giày" | aspect=Fashion | current=POS | suggested=NEG
  text: "Giày đi êm chân và phối đồ dễ. Trái_lại, Giá_tiền bị đội lên khá cao."
  context: "Giày đi êm chân và phối"

### General | hàng | NEG->POS (7)
- line 843: target="hàng" | aspect=General | current=NEG | suggested=POS
  text: "mọi nguii đừng dại gì mua hàng shop này"
  context: "nguii đừng dại gì mua hàng shop này"
- line 1073: target="hàng" | aspect=General | current=NEG | suggested=POS
  text: "lần đầu_tiên mình mua hàng mà đánh_giá shop nhưng thật_sự thất_vọng , form không đẹp , chất vải không xứng_đáng"
  context: "lần đầu_tiên mình mua hàng mà đánh_giá shop nhưng thật_sự"
- line 2117: target="hàng" | aspect=General | current=NEG | suggested=POS
  text: "hàng chính hãng nhưng nghe cũng bình_thường giống như loại pistom 2"
  context: "hàng chính hãng nhưng nghe cũng"
- line 3337: target="hàng" | aspect=General | current=NEG | suggested=POS
  text: "app bán cho bọn tây hay j mà chọn tiếng việt r cũng tiếng anh hàng thì toàn ở đâu_đâu quá tệ"
  context: "việt r cũng tiếng anh hàng thì toàn ở đâu_đâu quá"
- line 3769: target="hàng" | aspect=General | current=NEG | suggested=POS
  text: "shipper lấy hàng của khách chụp ảnh lung_tung quản_lý cũng chấp_nhận ad quản_lý như cc"
  context: "shipper lấy hàng của khách chụp ảnh lung_tung"

### Price | tầm giá | POS->NEU (7)
- line 4040: target="tầm giá" | aspect=Price | current=POS | suggested=NEU
  text: "Mỏng hơn so với ảnh , màu nhạt hơn. Còn OK trong tầm giá"
  context: "nhạt hơn. Còn OK trong tầm giá"
- line 4551: target="tầm giá" | aspect=Price | current=POS | suggested=NEU
  text: "Đien thoại OK trong tầm giá....a nhân viên rất nhiệt tình ...e  cảm ơn  rất nhiều"
  context: "Đien thoại OK trong tầm giá....a nhân viên rất nhiệt tình"
- line 6141: target="tầm giá" | aspect=Price | current=POS | suggested=NEU
  text: "Sản phẩm xài ok trong tầm giá, còn đc tặng tai nghe, pin rất trâu đc 2 ngày, cài aurora store là đầy đủ ứng dụng như chplay nha, còn youtube thì cài bằng youtube vance"
  context: "Sản phẩm xài ok trong tầm giá, còn đc tặng tai nghe,"
- line 6389: target="tầm giá" | aspect=Price | current=POS | suggested=NEU
  text: "Mỏng hơn so với ảnh , màu nhạt hơn. Còn Máy ok trong tầm giá"
  context: "hơn. Còn Máy ok trong tầm giá"
- line 6876: target="tầm giá" | aspect=Price | current=POS | suggested=NEU
  text: "Đã sử dụng máy máy mượt cam hơi ảo tí nhưng mình thấy đáng mua trong tầm giá pin trâu cuc kì"
  context: "mình thấy đáng mua trong tầm giá pin trâu cuc kì"

### Fashion | Đường_may | POS->NEU (6)
- line 90: target="Đường_may" | aspect=Fashion | current=POS | suggested=NEU
  text: "Đường_may gọn nên tổng thể nhìn khá chỉn_chu. Tuy_nhiên, Phí_ship đắt làm mình chùn tay."
  context: "Đường_may gọn nên tổng thể nhìn"
- line 1271: target="Đường_may" | aspect=Fashion | current=POS | suggested=NEU
  text: "Đường_may gọn nên tổng thể nhìn khá chỉn_chu. Bù_lại, Giá_tiền như vậy là chưa đáng."
  context: "Đường_may gọn nên tổng thể nhìn"
- line 2322: target="Đường_may" | aspect=Fashion | current=POS | suggested=NEU
  text: "Đường_may gọn nên tổng thể nhìn khá chỉn_chu. Tuy_nhiên, Tầm_giá này bỏ ra hơi tiếc."
  context: "Đường_may gọn nên tổng thể nhìn"
- line 5166: target="Đường_may" | aspect=Fashion | current=POS | suggested=NEU
  text: "Đường_may gọn nên tổng thể nhìn khá chỉn_chu. Xét_về_mặt_khác, Voucher quá yếu nên gần như không ăn_thua."
  context: "Đường_may gọn nên tổng thể nhìn"
- line 5802: target="Đường_may" | aspect=Fashion | current=POS | suggested=NEU
  text: "Đường_may gọn nên tổng thể nhìn khá chỉn_chu. Bù_lại, Phí_ship đắt làm mình chùn tay."
  context: "Đường_may gọn nên tổng thể nhìn"

### App | cập nhật | POS->NEG (6)
- line 681: target="cập nhật" | aspect=App | current=POS | suggested=NEG
  text: "Đã có bản cập nhật mới fix các lổi camera trước zoom bị tím màn hình, pin và camera cải thiện rõ rệt, hiệu năng tăng. Rất đáng đồng tiền. Trừ khi bạn mua sách tay hay hàng củ. Còn mua chính hãng mà thích spen thì mua con này là nhất"
  context: "Đã có bản cập nhật mới fix các lổi camera"
- line 1012: target="cập nhật" | aspect=App | current=POS | suggested=NEG
  text: "Ko biết mấy bạn chê ở điểm nào, bản cập nhật mới nhất giải quyết rất tốt khâu vân tay dưới chuột. Sạc nhanh hơn 1h là full thì đòi hỏi gì nữa mấy chế"
  context: "chê ở điểm nào, bản cập nhật mới nhất giải quyết rất"
- line 1678: target="cập nhật" | aspect=App | current=POS | suggested=NEG
  text: "Vsmart joy 3 nhà sản xuất đã gửi bản cập nhật sửa chữa các tính năng r nha các bạn bắt wifi bao mạnh"
  context: "sản xuất đã gửi bản cập nhật sửa chữa các tính năng"
- line 1985: target="cập nhật" | aspect=App | current=POS | suggested=NEG
  text: "vừa có bản cập nhật mới cải thiện vân tay nhanh quá thích ghê.cảm ứng rất mượt đặt biệt la vân tay cải thiện rất đáng để"
  context: "vừa có bản cập nhật mới cải thiện vân tay"
- line 3860: target="cập nhật" | aspect=App | current=POS | suggested=NEG
  text: "Ko biết mấy bạn chê ở điểm nào, bản cập nhật mới nhất giải quyết rất tốt khâu vân tay dưới màn hình. Sạc nhanh hơn 1h là full thì đòi hỏi gì nữa mấy chế"
  context: "chê ở điểm nào, bản cập nhật mới nhất giải quyết rất"

### Price | giá | POS->NEU (6)
- line 1501: target="giá" | aspect=Price | current=POS | suggested=NEU
  text: "Sao pin 5000 mà nó tuộc nhanh quá chơi liên quân từ 9h sáng đến 4h chiều còn 20% pin thua đt pin 4000 chơi từ 7h sáng đến 4h chiều còn 25% khó hiểu , tắc đt để trong túi tầm 1 tiếng rớt đến 3% loa ngoài nhỏ bác full mới nghe đc tiếng mới mua đc có 3 ngày vô đánh giá luôn 😩"
  context: "có 3 ngày vô đánh giá luôn 😩"
- line 2851: target="giá" | aspect=Price | current=POS | suggested=NEU
  text: "Vải khá mỏng nên mặc dễ lộ; còn giá dễ thở nên mua lại vẫn thấy hợp."
  context: "nên mặc dễ lộ; còn giá dễ thở nên mua lại"
- line 4898: target="giá" | aspect=Price | current=POS | suggested=NEU
  text: "Không đúng size đặt size l gửi size s bé tẹo mặc kiểu gì; còn quan trọng là giá phù hợp"
  context: "gì; còn quan trọng là giá phù hợp"
- line 7137: target="giá" | aspect=Price | current=POS | suggested=NEU
  text: "Mới mua xong giờ giảm giá xuống còn  23 tr tiếc ghê máy tốt nhưng pin mau hết quá"
  context: "Mới mua xong giờ giảm giá xuống còn 23 tr tiếc"
- line 7228: target="giá" | aspect=Price | current=POS | suggested=NEU
  text: "giá các linh_kiện_điện_tử cao hơn các trang mua_sắm khác"
  context: "giá các linh_kiện_điện_tử cao hơn các"

### Price | giá | NEG->POS (5)
- line 579: target="giá" | aspect=Price | current=NEG | suggested=POS
  text: "nhưng với giá chỉ 55k như_vậy thì là khá ok ạ mình áp thêm code giảm_giá"
  context: "nhưng với giá chỉ 55k như_vậy thì là"
- line 1668: target="giá" | aspect=Price | current=NEG | suggested=POS
  text: "1 trong những con máy lm ra với mục đích là để xuất chip p22 của mediatek tồn kho
Máy giật lag ko hề xứng với giá 3 triệu"
  context: "lag ko hề xứng với giá 3 triệu"
- line 2996: target="giá" | aspect=Price | current=NEG | suggested=POS
  text: "Hôm mất Đt đaq chả biết mua gì thì thấy quảng cáo ra bốc luôn :)) Nhưng phải công nhận 1 theo mình đánh giá thì đaq dùng IP quen chuyển qua SS dùng thấy nó không thích lắm :))) với lại tại hôm ra mua không để ý kỹ Camera trước nó bị mờ như kiểu Camera 2.0Mp ấy 😂😂 Tại về quê ăn tết lâu quá nên cũng chả ra TGDD hỏi nữa 😂 Nhưng sắp tới cũng pas lại mua IP dùng thôi 😂😂"
  context: "nhận 1 theo mình đánh giá thì đaq dùng IP quen"
- line 4529: target="giá" | aspect=Price | current=NEG | suggested=POS
  text: "Màn hình cực tệ vừa rơi nhẹ đã bể v mà bảo kính cường lực
Lâu lâu lại bị đứng máy, pin còn 15% tuột nhanh như nước
Mua giá cao mà chán quá"
  context: "tuột nhanh như nước Mua giá cao mà chán quá"
- line 5454: target="giá" | aspect=Price | current=NEG | suggested=POS
  text: "Khăn đẹp , áo đẹp nhưng máy giật lag ko hề xứng với giá 3 triệu"
  context: "lag ko hề xứng với giá 3 triệu"

### Price | voucher | POS->NEG (5)
- line 600: target="voucher" | aspect=Price | current=POS | suggested=NEG
  text: "rất nhiều voucher nếu cho tôi đánh_giá thì tôi sẽ đánh_giá 10"
  context: "rất nhiều voucher nếu cho tôi đánh_giá thì"
- line 694: target="voucher" | aspect=Price | current=POS | suggested=NEG
  text: "tặng toii thêm vài cái voucher nx đi"
  context: "tặng toii thêm vài cái voucher nx đi"
- line 1719: target="voucher" | aspect=Price | current=POS | suggested=NEG
  text: "ứng_dụng mua hàng tiện_lợi rất nhiều voucher giảm_giá xâu"
  context: "mua hàng tiện_lợi rất nhiều voucher giảm_giá xâu"
- line 4882: target="voucher" | aspect=Price | current=POS | suggested=NEG
  text: "ứng_dụng mua bàn_phím tiện_lợi rất nhiều voucher giảm_giá xâu"
  context: "mua bàn_phím tiện_lợi rất nhiều voucher giảm_giá xâu"
- line 7288: target="voucher" | aspect=Price | current=POS | suggested=NEG
  text: "chú_ý đến khách_hàng voucher nhiều tiện_lợi good"
  context: "chú_ý đến khách_hàng voucher nhiều tiện_lợi good"

### Fashion | size | POS->NEG (5)
- line 834: target="size" | aspect=Fashion | current=POS | suggested=NEG
  text: "mặc xinh lắm , chủ shop nhiệt_tình hỗ_trợ đổi size"
  context: "chủ shop nhiệt_tình hỗ_trợ đổi size"
- line 1752: target="size" | aspect=Fashion | current=POS | suggested=NEG
  text: "nên tăng thêm size vì size quần hơi bé"
  context: "nên tăng thêm size vì size quần hơi bé"
- line 2352: target="size" | aspect=Fashion | current=POS | suggested=NEG
  text: "kể_ra ngực mà to lên 1 size nữa thì mặc hơi bị đẹp luôn"
  context: "ngực mà to lên 1 size nữa thì mặc hơi bị"
- line 4537: target="size" | aspect=Fashion | current=POS | suggested=NEG
  text: "cực_kỳ đẹp tuy_nhiên khi mua nên inb shopee hỏi size trc vì có_thể chênh_lệch giữa các mẫu"
  context: "mua nên inb shopee hỏi size trc vì có_thể chênh_lệch giữa"
- line 4690: target="size" | aspect=Fashion | current=POS | suggested=NEG
  text: "cực_kỳ đẹp tuy_nhiên khi mua nên inb shop hỏi size trc vì có_thể chênh_lệch giữa các mẫu"
  context: "mua nên inb shop hỏi size trc vì có_thể chênh_lệch giữa"

### Fashion | quần | NEG->POS (5)
- line 986: target="quần" | aspect=Fashion | current=NEG | suggested=POS
  text: "quần bị thủng túi"
  context: "quần bị thủng túi"
- line 1374: target="quần" | aspect=Fashion | current=NEG | suggested=POS
  text: "quần mặc bị chật , nt shop không tl !"
  context: "quần mặc bị chật , nt"
- line 2864: target="quần" | aspect=Fashion | current=NEG | suggested=POS
  text: "quần vải thung dãn rất nhiều"
  context: "quần vải thung dãn rất nhiều"
- line 3053: target="quần" | aspect=Fashion | current=NEG | suggested=POS
  text: "năm_ngoái cũng mua 1c quần warm bên shop rồi , quần chất khác so với năm_ngoái cứng hơn shop ạ"
  context: "năm_ngoái cũng mua 1c quần warm bên shop rồi ,"
- line 7497: target="quần" | aspect=Fashion | current=NEG | suggested=POS
  text: "nhưng quần chật quá"
  context: "nhưng quần chật quá"

### Electronics | ổ_cứng | NEG->POS (5)
- line 1248: target="ổ_cứng" | aspect=Electronics | current=NEG | suggested=POS
  text: "Nghe gọi lúc nghe lúc không. Đã đổi con thứ 2 vẫn y vậy. Mua ổ_cứng 4 tuần mà trung bình 1 tuần 1 lần lên sửa. Nhân viên dễ thương"
  context: "2 vẫn y vậy. Mua ổ_cứng 4 tuần mà trung bình"
- line 1659: target="ổ_cứng" | aspect=Electronics | current=NEG | suggested=POS
  text: "Rõ ràng là mua ổ_cứng đang khuyến mãi mà mình phải hỏi thì nhân viên tgdd mới kiểm tra và báo lại. Xong rồi mua ốp lưng. Giảm 49% từ ngày 13.5 đến 31.5 nhưng hôm mình mua là 22.5 vẫn không được giảm giá. Và lấy của mình giá gốc.."
  context: "Rõ ràng là mua ổ_cứng đang khuyến mãi mà mình"
- line 3247: target="ổ_cứng" | aspect=Electronics | current=NEG | suggested=POS
  text: "đây là lần thứ 2 mua ổ_cứng của shop nhưng kq lại là thất_vọng với thái_độ phục_vụ của shop"
  context: "là lần thứ 2 mua ổ_cứng của shop nhưng kq lại"
- line 3533: target="ổ_cứng" | aspect=Electronics | current=NEG | suggested=POS
  text: "ổ_cứng nên gói có xốp thì an_toàn hơn"
  context: "ổ_cứng nên gói có xốp thì"
- line 3966: target="ổ_cứng" | aspect=Electronics | current=NEG | suggested=POS
  text: "Chất lượng kém so vs giá sp , ổ_cứng 5000 mà tụt nhanh quá, camera cũng k đẹp , dt thì thường xuyên bị đơ , lag, vaof ứng dụng bị văng, chán,  tầm này mua redmi xài ok hơn nhìu ,"
  context: "so vs giá sp , ổ_cứng 5000 mà tụt nhanh quá,"

### Electronics | camera | NEG->POS (5)
- line 2537: target="camera" | aspect=Electronics | current=NEG | suggested=POS
  text: "Xem đánh giá chê quá nhiều mà mình vì thích cái kiểu máy và cái camera nên cứng đầu mua và kết quả quá chán... nhất là cảm ứng nhảy lung tung và có khi nhấn không ăn,đánh chữ rất bực mình...Camera thì tạm đc, k phải quá đẹp gì, đc mỗi cái chụp góc rộng thôi.Với số tiền bỏ ra không đáng tí nào. Khuyên mn k nên mua.Thất vọng 😶"
  context: "cái kiểu máy và cái camera nên cứng đầu mua và"
- line 3543: target="camera" | aspect=Electronics | current=NEG | suggested=POS
  text: "camera hình ảnh màu nhạt, chất lượng loa hơi kém. tốc độ xử lý cũng bình thường. Nhân viên tư vấn nhiệt tình"
  context: "camera hình ảnh màu nhạt, chất"
- line 3848: target="camera" | aspect=Electronics | current=NEG | suggested=POS
  text: "Mình mua con này gần 1 tháng. Dạo này có tình trạng hay thoát các app đặc biệt là Zalo, và camera có tình trạng bị đứng khi quay video và sau đó thoát ra vô lại thì bị lỗi camera đành phải khởi động lại. Thực sự không như mong đợi"
  context: "đặc biệt là Zalo, và camera có tình trạng bị đứng"
- line 4147: target="camera" | aspect=Electronics | current=NEG | suggested=POS
  text: "Cụm 3 camera. Nhưng camera đầu và cuối để làm cảnh, chỉ có camera giữa chụp đc. Nhờ đó thiết kế trở nên sáng trọng =))). Vân tay nhạy. Còn lại chất lượng xứng đáng với tầm giá"
  context: "Cụm 3 camera. Nhưng camera đầu và cuối"
- line 5874: target="camera" | aspect=Electronics | current=NEG | suggested=POS
  text: "Mình mua con này gần 1 tháng. Dạo này có tình trạng hay thoát các phần_mềm đặc biệt là Zalo, và camera có tình trạng bị đứng khi quay video và sau đó thoát ra vô lại thì bị lỗi camera đành phải khởi động lại. Thực sự không như mong đợi"
  context: "đặc biệt là Zalo, và camera có tình trạng bị đứng"

### App | Ứng_dụng | NEG->POS (5)
- line 3467: target="Ứng_dụng" | aspect=App | current=NEG | suggested=POS
  text: "Ứng_dụng hay văng nên mình phải mở lại liên_tục nhưng vận_chuyển xử_lý nhanh nên đơn đi khá mượt."
  context: "Ứng_dụng hay văng nên mình phải"
- line 3630: target="Ứng_dụng" | aspect=App | current=NEG | suggested=POS
  text: "Ứng_dụng hay văng nên mình phải mở lại liên_tục nhưng giao_hàng nhanh nên không phải chờ lâu."
  context: "Ứng_dụng hay văng nên mình phải"
- line 4144: target="Ứng_dụng" | aspect=App | current=NEG | suggested=POS
  text: "Ứng_dụng hay văng nên mình phải mở lại liên_tục; còn shipper giao đúng hẹn nên mình khá hài_lòng."
  context: "Ứng_dụng hay văng nên mình phải"
- line 4157: target="Ứng_dụng" | aspect=App | current=NEG | suggested=POS
  text: "Ứng_dụng hay văng nên mình phải mở lại liên_tục. Tuy_nhiên, Shipper giao đúng hẹn nên mình khá hài_lòng."
  context: "Ứng_dụng hay văng nên mình phải"
- line 6245: target="Ứng_dụng" | aspect=App | current=NEG | suggested=POS
  text: "Ứng_dụng hay văng nên mình phải mở lại liên_tục. Bù_lại, Shipper thân_thiện và giao khá đúng giờ."
  context: "Ứng_dụng hay văng nên mình phải"

### Electronics | Bàn_phím | POS->NEG (4)
- line 405: target="Bàn_phím" | aspect=Electronics | current=POS | suggested=NEG
  text: "Bàn_phím gõ êm và độ nảy khá tốt. Trái_lại, Nhân_viên nói chuyện khó chịu nên mình ngại hỏi thêm."
  context: "Bàn_phím gõ êm và độ nảy"
- line 2277: target="Bàn_phím" | aspect=Electronics | current=POS | suggested=NEG
  text: "Bàn_phím gõ êm và độ nảy khá tốt. Tuy_nhiên, Phục_vụ lạnh_nhạt nên trải_nghiệm rất tụt mood."
  context: "Bàn_phím gõ êm và độ nảy"
- line 3469: target="Bàn_phím" | aspect=Electronics | current=POS | suggested=NEG
  text: "Bàn_phím gõ êm và độ nảy khá tốt. Bù_lại, Chăm_sóc khách_hàng trả_lời máy_móc và chậm."
  context: "Bàn_phím gõ êm và độ nảy"
- line 5309: target="Bàn_phím" | aspect=Electronics | current=POS | suggested=NEG
  text: "Bàn_phím gõ êm và độ nảy khá tốt nhưng cửa_hàng xử_lý thiếu trách_nhiệm nên rất bực."
  context: "Bàn_phím gõ êm và độ nảy"

### Ship | giao | NEG->POS (4)
- line 784: target="giao" | aspect=Ship | current=NEG | suggested=POS
  text: "có báo làm_việc lại nhưnh chưa thấy chốt lại giao bổ_sung hay sao cả"
  context: "nhưnh chưa thấy chốt lại giao bổ_sung hay sao cả"
- line 1174: target="giao" | aspect=Ship | current=NEG | suggested=POS
  text: "shop giao nhầm dép"
  context: "shop giao nhầm dép"
- line 6994: target="giao" | aspect=Ship | current=NEG | suggested=POS
  text: "áo thì được nhưng shop làm_ăn cẩu_thả không đọc tin nhắn khách bảo đặt 2 áo khác màu đem ssi giao cùng màu thì cũng quỳ"
  context: "áo khác màu đem ssi giao cùng màu thì cũng quỳ"
- line 7020: target="giao" | aspect=Ship | current=NEG | suggested=POS
  text: "mặc_dù có chú thíc rõ là mua 2 màu khác nhau 1 xám và 1 đen nhưng lại bị giao nhầm cả 2 đen"
  context: "1 đen nhưng lại bị giao nhầm cả 2 đen"

### General | hàng | POS->NEU (4)
- line 888: target="hàng" | aspect=General | current=POS | suggested=NEU
  text: "trời ơi nhận được hàng mà nhảy_cẫng lên luôn y , hàng đẹp kinh_khủng luôn"
  context: "trời ơi nhận được hàng mà nhảy_cẫng lên luôn y"
- line 3404: target="hàng" | aspect=General | current=POS | suggested=NEU
  text: "hàng y hình nhé , đường may chất_liệu nhìn chắc_chắn"
  context: "hàng y hình nhé , đường"
- line 5845: target="hàng" | aspect=General | current=POS | suggested=NEU
  text: "hàng mới về xong thì thấy shop up áo hạc xanh đẹp qtqđ , thặc đắng lòng tại_sao shop không up em nó sớm hơn hụ hụ"
  context: "hàng mới về xong thì thấy"
- line 6237: target="hàng" | aspect=General | current=POS | suggested=NEU
  text: "còn mua hàng dài_dài của shop nhé"
  context: "còn mua hàng dài_dài của shop nhé"

### Electronics | màn hình | POS->NEG (4)
- line 1014: target="màn hình" | aspect=Electronics | current=POS | suggested=NEG
  text: "Mọi thứ đều tốt trong tầm giá. Riêng phần mở khoá màn hình , đôi lúc hình mở khoá thì màn hình chỉ hiển thị hình nền thôi, còn những tác vụ đều ko hiển thị . Thời gian ngày giờ cũng vậy và những app sẵn trong máy cũng như app tải về đều ko có. Có thể xem xét lại dùm mình ko ?? Mình mới mua máy 1 tuần."
  context: "giá. Riêng phần mở khoá màn hình , đôi lúc hình mở"
- line 6174: target="màn hình" | aspect=Electronics | current=POS | suggested=NEG
  text: "Xài đc 1 tuần..  Tổng thể thiết kế không chê vào đâu đc... Camera chụp hình bao đẹp.. Chơi pubg, liên quân bao mượt.. Trong tầm giá.. Ko biết có phải do màn hình giọt nc phân giải cao hay không nhưng mình thấy pin con này so với con 5redmi 5plus thì con này hao pin nhanh hơn. Nhược điểm  nữa là mic thu âm ở những chỗ nhạc lớn hay bị rè ko rõ tiếng.. Còn lại OK. Nhân viên TGDĐ ở 184 Bùi Văn Hòa, Biên Hòa phục vụ nhiệt tình, chu đáo, nhanh gọn.. 10 điểm phục vụ"
  context: "Ko biết có phải do màn hình giọt nc phân giải cao"
- line 7245: target="màn hình" | aspect=Electronics | current=POS | suggested=NEG
  text: "Máy sử dụng rất tốt. Với giá tiền này là quá ok.Máy chạy cực mượt với các ứng dụng Google Go, Zalo, Facebook, Web thoải máy. Phù hợp với nhu cầu cơ bản. Chỉ có màn hình máy với độ phân giải chưa cao thôi, nhưng với mức giá tiền này thì tốt rồi."
  context: "cầu cơ bản. Chỉ có màn hình máy với độ phân giải"
- line 7353: target="màn hình" | aspect=Electronics | current=POS | suggested=NEG
  text: "5* cho nhân viên TGDD 
Máy mình bị lổi có viền sáng quanh màn hình
Mới được đổi hôm qua
Rất ưng ý....những sau 1 ngày sử dụng giờ nó lại phát sinh lổi củ như máy trước nhưng có vẻ nặng hơn cái trước(ánh sáng quanh viền sáng hơn và rộng hơn) giờ có cách gì giải quyết được vấn đề này hả các bạn bên TGDD chứ như ri mất thời gian quá"
  context: "lổi có viền sáng quanh màn hình Mới được đổi hôm qua"

### Service | chủ shop | POS->NEU (4)
- line 1299: target="chủ shop" | aspect=Service | current=POS | suggested=NEU
  text: "chị chủ shop nói_chuyện dễ_thương"
  context: "chị chủ shop nói_chuyện dễ_thương"
- line 3221: target="chủ shop" | aspect=Service | current=POS | suggested=NEU
  text: "chủ shop rất dễ_thương lại nhiệt_tình"
  context: "chủ shop rất dễ_thương lại nhiệt_tình"
- line 3862: target="chủ shop" | aspect=Service | current=POS | suggested=NEU
  text: "chủ shop dễ_thương nữa , thanks"
  context: "chủ shop dễ_thương nữa , thanks"
- line 4104: target="chủ shop" | aspect=Service | current=POS | suggested=NEU
  text: "chủ shop nói chiện dễ_thương"
  context: "chủ shop nói chiện dễ_thương"

### Ship | gửi | NEG->POS (4)
- line 1330: target="gửi" | aspect=Ship | current=NEG | suggested=POS
  text: "Sóng sánh kém lắm,giữa đất thị trấn mà chỉ đc 2-3 vạch. Wifi vào phòng trong cách khoảng 5m mà bắt đc 3 vạch. Đã gửi đi hãng thẩm định. Ổ_cứng qua đêm tắt hết ứng dụng,mạng mà sáng dậy tụt 12%.
Chơi liên quân đôi khi vẫn bị khựng lại chút.đc cái màn nét."
  context: "bắt đc 3 vạch. Đã gửi đi hãng thẩm định. Ổ_cứng"
- line 1385: target="gửi" | aspect=Ship | current=NEG | suggested=POS
  text: "Dt mới mua vài tháng. Nói chung hình thức thì đẹp. Nhưng nay máy mất sóng liên tục. Gọi k đc có reset cũng vậy. Lên bảo hành thì kêu gửi hãng cũng gần 1 tháng mới xong. Chán"
  context: "Lên bảo hành thì kêu gửi hãng cũng gần 1 tháng"
- line 2045: target="gửi" | aspect=Ship | current=NEG | suggested=POS
  text: "Oppo A91 chụp rất nét nhưng sao gửi hình ảnh lên trang khác rất mờ và k đọc được???"
  context: "chụp rất nét nhưng sao gửi hình ảnh lên trang khác"
- line 7428: target="gửi" | aspect=Ship | current=NEG | suggested=POS
  text: "Thường xuyên bị mất tín hiệu sim phải khởi động máy lại. Và có những tin nhắc lạ gửi về làm tài khoản bị trừ tiền"
  context: "có những tin nhắc lạ gửi về làm tài khoản bị"

### Service | khách_hàng | POS->NEG (4)
- line 1902: target="khách_hàng" | aspect=Service | current=POS | suggested=NEG
  text: "ok đảm_bảo quyền_lợi khách_hàng"
  context: "ok đảm_bảo quyền_lợi khách_hàng"
- line 3806: target="khách_hàng" | aspect=Service | current=POS | suggested=NEG
  text: "ứng_dụng có_thể thêm cách tìm_kiếm sản_phẩm bằng hình_ảnh để khách_hàng dễ tìm_kiếm sản_phẩm"
  context: "tìm_kiếm sản_phẩm bằng hình_ảnh để khách_hàng dễ tìm_kiếm sản_phẩm"
- line 6712: target="khách_hàng" | aspect=Service | current=POS | suggested=NEG
  text: "app có_thể thêm cách tìm_kiếm sản_phẩm bằng hình_ảnh để khách_hàng dễ tìm_kiếm sản_phẩm"
  context: "tìm_kiếm sản_phẩm bằng hình_ảnh để khách_hàng dễ tìm_kiếm sản_phẩm"
- line 7288: target="khách_hàng" | aspect=Service | current=POS | suggested=NEG
  text: "chú_ý đến khách_hàng voucher nhiều tiện_lợi good"
  context: "chú_ý đến khách_hàng voucher nhiều tiện_lợi good"

### Service | khách_hàng | POS->NEU (4)
- line 1935: target="khách_hàng" | aspect=Service | current=POS | suggested=NEU
  text: "trải_nghiệm mua_sắm tốt tiện_lợi giá_cả cạnh_tranh shopee giải_quyết các vấn_đề trục_trặc phát_sinh phù_hợp tạo sự tin_tưởng cho khách_hàng cảm_ơn"
  context: "phù_hợp tạo sự tin_tưởng cho khách_hàng cảm_ơn"
- line 4564: target="khách_hàng" | aspect=Service | current=POS | suggested=NEU
  text: "11 1 2026 khá hài_lòng khi chọn mua sản_phẩm tuy còn có những sản_phẩm chưa được ưng_ý về mọi mặt nhưng nhìn_chung thì tương_đối hài_lòng và các chính_sách đổi trả nhanh_chóng thuận_tiện sau một thờigian dùng app từ 2020 đến nay đã sang năm thứ_sáu 2026 hi_vọng shopee sẽ cải_thiện về chất_lượng sản_phẩm hơn_nữa cũng như các chương_trình khuyến_mãi dành cho khách_hàng và giao hàng cẩn_thận chuyên_nghiệp hơn_nữa 2 2 2026 vừa nhận hàng rất là hài_lòng nên lại gửi tặng shopee 5 sao nữa về chất_lượng"
  context: "các chương_trình khuyến_mãi dành cho khách_hàng và giao hàng cẩn_thận chuyên_nghiệp"
- line 6769: target="khách_hàng" | aspect=Service | current=POS | suggested=NEU
  text: "mong ti_ki đem lại trải_nghiệm cho khách_hàng nhiều hơn về vấn_đề bảo_hành sản_phẩm được nhanh hơn đe sử_dụng"
  context: "ti_ki đem lại trải_nghiệm cho khách_hàng nhiều hơn về vấn_đề bảo_hành"
- line 7390: target="khách_hàng" | aspect=Service | current=POS | suggested=NEU
  text: "em có ý nên tặng voucher giảm 100 k và free ship 500 k giống shoppe để ưu_đãi khách_hàng mới ạ"
  context: "k giống shoppe để ưu_đãi khách_hàng mới ạ"

### Electronics | máy | NEG->POS (4)
- line 2294: target="máy" | aspect=Electronics | current=NEG | suggested=POS
  text: "Lần đầu thử mua máy hãng trung quốc xài mà quá thất vọng, máy chậm rì, lag giật khi mở ứng dụng nhẹ như zalo hay uc, fb dù không cài game nào trong máy, lắp thẻ nhớ vào thư viện 5 tiếng sau vẫn load hình ảnh trên thẻ nhớ chưa xong dù chỉ xài thẻ 32gb,"
  context: "Lần đầu thử mua máy hãng trung quốc xài mà"
- line 3520: target="máy" | aspect=Electronics | current=NEG | suggested=POS
  text: "Lỗi 1 xim ko nhận chua dùng dc 1 tháng.mua máy mới nhung ko dc bóc  hộp. Nhân viên lây cho 1 cái hộp  mở sẵn.máy cung dc dán decan đẹp.chac hang đổi trả  rep mới  lại bán"
  context: "chua dùng dc 1 tháng.mua máy mới nhung ko dc bóc"
- line 4130: target="máy" | aspect=Electronics | current=NEG | suggested=POS
  text: "Mua cho vợ dùng xem youtube . Dùng 1 thời gian nó loạn cảm ứng . Phải ấn nút nguồn tắt mh , bật lại mới ok . 
Đi bảo hành họ reset lại máy nhưng chả ăn thua gì . Đúng là tào lao ."
  context: "bảo hành họ reset lại máy nhưng chả ăn thua gì"
- line 4676: target="máy" | aspect=Electronics | current=NEG | suggested=POS
  text: "Giá sản phẩm vẫn quá là Chát.mặc dù máy đã ra đc gần 3 năm rồi.không biết iphone 11 ra mắt giá 7plus còn chát vậy k?"
  context: "vẫn quá là Chát.mặc dù máy đã ra đc gần 3"

### Fashion | size | NEG->POS (4)
- line 2459: target="size" | aspect=Fashion | current=NEG | suggested=POS
  text: "quảng cao là free size dưới 58kg mặc được vay mà mình đặt 3 áo thì shop gửi cho mình 3 ao 3 size khác nhau xl , l , s"
  context: "quảng cao là free size dưới 58kg mặc được vay"
- line 4162: target="size" | aspect=Fashion | current=NEG | suggested=POS
  text: "phải tăng lên tận 2 size mới đúng"
  context: "phải tăng lên tận 2 size mới đúng"
- line 5560: target="size" | aspect=Fashion | current=NEG | suggested=POS
  text: "size l vừa người nhưng dài quá"
  context: "size l vừa người nhưng dài"
- line 6714: target="size" | aspect=Fashion | current=NEG | suggested=POS
  text: "size 34 mà khung ngực nhỏ quá"
  context: "size 34 mà khung ngực nhỏ"

### App | Cập_nhật | POS->NEG (4)
- line 2466: target="Cập_nhật" | aspect=App | current=POS | suggested=NEG
  text: "Cập_nhật mới giúp app chạy đỡ giật hẳn. Bù_lại, Shipper gọi muộn rồi giao còn khá cẩu_thả."
  context: "Cập_nhật mới giúp app chạy đỡ"
- line 2521: target="Cập_nhật" | aspect=App | current=POS | suggested=NEG
  text: "Cập_nhật mới giúp app chạy đỡ giật hẳn. Trái_lại, Đơn_hàng về trễ nên trải_nghiệm tụt hẳn."
  context: "Cập_nhật mới giúp app chạy đỡ"
- line 2657: target="Cập_nhật" | aspect=App | current=POS | suggested=NEG
  text: "Cập_nhật mới giúp app chạy đỡ giật hẳn mà giao_hàng quá ẩu nên nhận món hơi nản."
  context: "Cập_nhật mới giúp app chạy đỡ"
- line 4050: target="Cập_nhật" | aspect=App | current=POS | suggested=NEG
  text: "Cập_nhật mới giúp app chạy đỡ giật hẳn. Bù_lại, Đơn_hàng về trễ nên trải_nghiệm tụt hẳn."
  context: "Cập_nhật mới giúp app chạy đỡ"

### Electronics | bàn_phím | POS->NEG (4)
- line 2793: target="bàn_phím" | aspect=Electronics | current=POS | suggested=NEG
  text: "mấy app kia shiper đứng ngoài đầu hẻm gọi mình ra còn shiper tiki đứng trc cửa kêu mình dậy lấy bàn_phím lun"
  context: "cửa kêu mình dậy lấy bàn_phím lun"
- line 5329: target="bàn_phím" | aspect=Electronics | current=POS | suggested=NEG
  text: "bàn_phím y mẫu . s tư_vấn nhiệt_tình . ok"
  context: "bàn_phím y mẫu . s tư_vấn"
- line 6723: target="bàn_phím" | aspect=Electronics | current=POS | suggested=NEG
  text: "Giá hợp lý những ai đánh liên quân nên xem bàn_phím này dù k bật đc hd+ nhưng k bị giật lag nha"
  context: "đánh liên quân nên xem bàn_phím này dù k bật đc"
- line 7399: target="bàn_phím" | aspect=Electronics | current=POS | suggested=NEG
  text: "Mới mua em nó về để dùng nghe gọi, zalo fb, zing chạy cũng ổn. Còn bền k phải qua thời gian mới biết. 5sao vì các bạn nhân viên đmx rất nhiệt tình, mua bàn_phím 590k các bạn tư vấn dặn dò chu đáo. Mình mua ở đmx bùng binh mũ Tp bến tre, bạn Bình kỹ thuật và bạn Mi quản lý rất dễ thương nhiệt tình"
  context: "đmx rất nhiệt tình, mua bàn_phím 590k các bạn tư vấn"

### Electronics | Ram | POS->NEU (4)
- line 2820: target="Ram" | aspect=Electronics | current=POS | suggested=NEU
  text: "Ram giữ tác_vụ ổn nên ít phải tải lại. Bù_lại, Phục_vụ lạnh_nhạt nên trải_nghiệm rất tụt mood."
  context: "Ram giữ tác_vụ ổn nên ít"
- line 3869: target="Ram" | aspect=Electronics | current=POS | suggested=NEU
  text: "Ram giữ tác_vụ ổn nên ít phải tải lại mà chăm_sóc khách_hàng trả_lời máy_móc và chậm."
  context: "Ram giữ tác_vụ ổn nên ít"
- line 6784: target="Ram" | aspect=Electronics | current=POS | suggested=NEU
  text: "Ram giữ tác_vụ ổn nên ít phải tải lại. Bù_lại, Bảo_hành hướng_dẫn vòng_vo nên mất thời_gian."
  context: "Ram giữ tác_vụ ổn nên ít"
- line 7155: target="Ram" | aspect=Electronics | current=POS | suggested=NEU
  text: "Ram giữ tác_vụ ổn nên ít phải tải lại mà bảo_hành hướng_dẫn vòng_vo nên mất thời_gian."
  context: "Ram giữ tác_vụ ổn nên ít"

### General | màu | NEG->POS (4)
- line 2872: target="màu" | aspect=General | current=NEG | suggested=POS
  text: "nhưng màu kháu so với ảnh"
  context: "nhưng màu kháu so với ảnh"
- line 5365: target="màu" | aspect=General | current=NEG | suggested=POS
  text: "ra màu kinh_khủng"
  context: "ra màu kinh_khủng"
- line 5976: target="màu" | aspect=General | current=NEG | suggested=POS
  text: "bảo mỗi cái 1 màu lại gủi 2 cái cùng màu"
  context: "bảo mỗi cái 1 màu lại gủi 2 cái cùng"
- line 7036: target="màu" | aspect=General | current=NEG | suggested=POS
  text: "đúng màu đúng kiểu nhưng chỉ có em bé mặc vừa . !"
  context: "đúng màu đúng kiểu nhưng chỉ có"

### Electronics | pin | POS->NEG (3)
- line 36: target="pin" | aspect=Electronics | current=POS | suggested=NEG
  text: "Máy dùng quá ngon, camera chụp ảnh rất đẹp, cấu hình cao cân mọi thể loại game, màn OLED dù chỉ full HD+ nhưng vẫn hiển thị cực sắc nét xem phim bao phê, mặc dù điểm yếu của e nó là ko có google nhưng mình thấy ko ảnh hưởng gì vì nếu muốn vẫn có thể cài được dịch vụ của google vào máy, pin thì nếu mà chơi game liên tục thì được tầm 5-6 tiếng."
  context: "vụ của google vào máy, pin thì nếu mà chơi game"
- line 6981: target="pin" | aspect=Electronics | current=POS | suggested=NEG
  text: "Mình mua s 20 sai mới thư điều ok .chạy rất muoc.đáng sợ tiền mua.có pin hỏi mầu hết.cho 5 sau"
  context: "rất muoc.đáng sợ tiền mua.có pin hỏi mầu hết.cho 5 sau"
- line 7456: target="pin" | aspect=Electronics | current=POS | suggested=NEG
  text: "Máy mới mua sài  rất mượt và ok nhân viên tư vấn nhiệt tình pin sài rất trâu 20% sài gần 2tieng mới hết sạc nhanh nói chung hợp với tầm giá"
  context: "viên tư vấn nhiệt tình pin sài rất trâu 20% sài"

### General | hình | POS->NEU (3)
- line 396: target="hình" | aspect=General | current=POS | suggested=NEU
  text: "đảm_bảo i hình luon"
  context: "đảm_bảo i hình luon"
- line 6526: target="hình" | aspect=General | current=POS | suggested=NEU
  text: "y hình luôn"
  context: "y hình luôn"
- line 7141: target="hình" | aspect=General | current=POS | suggested=NEU
  text: "y chang hình luôn nha , dài và phom to y chang hình , thích lắm luôn"
  context: "y chang hình luôn nha , dài và"

### Service | Phục_vụ | NEG->POS (3)
- line 437: target="Phục_vụ" | aspect=Service | current=NEG | suggested=POS
  text: "Củ_sạc đi kèm dùng ổn và vào điện nhanh. Bù_lại, Phục_vụ lạnh_nhạt nên trải_nghiệm rất tụt mood."
  context: "và vào điện nhanh. Bù_lại, Phục_vụ lạnh_nhạt nên trải_nghiệm rất tụt"
- line 5554: target="Phục_vụ" | aspect=Service | current=NEG | suggested=POS
  text: "Chip xử_lý mượt nên chuyển app rất nhanh. Tuy_nhiên, Phục_vụ lạnh_nhạt nên trải_nghiệm rất tụt mood."
  context: "chuyển app rất nhanh. Tuy_nhiên, Phục_vụ lạnh_nhạt nên trải_nghiệm rất tụt"
- line 7445: target="Phục_vụ" | aspect=Service | current=NEG | suggested=POS
  text: "Chip xử_lý mượt nên chuyển app rất nhanh. Xét_về_mặt_khác, Phục_vụ lạnh_nhạt nên trải_nghiệm rất tụt mood."
  context: "chuyển app rất nhanh. Xét_về_mặt_khác, Phục_vụ lạnh_nhạt nên trải_nghiệm rất tụt"

### Price | voucher | POS->NEU (3)
- line 633: target="voucher" | aspect=Price | current=POS | suggested=NEU
  text: "Quần bị chật phần hông nên đi lại khó; còn voucher nhiều nên tổng tiền xuống khá đẹp."
  context: "nên đi lại khó; còn voucher nhiều nên tổng tiền xuống"
- line 2030: target="voucher" | aspect=Price | current=POS | suggested=NEU
  text: "Vải hơi thô và mặc bí người; còn voucher áp vào giảm được kha_khá."
  context: "và mặc bí người; còn voucher áp vào giảm được kha_khá."
- line 3191: target="voucher" | aspect=Price | current=POS | suggested=NEU
  text: "Không đúng size đặt size l gửi size s bé tẹo mặc kiểu gì; còn nên cho thêm voucher 1 chút là ok"
  context: "gì; còn nên cho thêm voucher 1 chút là ok"

### Service | Shop | POS->NEG (3)
- line 944: target="Shop" | aspect=Service | current=POS | suggested=NEG
  text: "Pin tụt nhanh nên phải sạc liên_tục. Trái_lại, Shop giữ lời nên mình thấy khá tin_tưởng."
  context: "nên phải sạc liên_tục. Trái_lại, Shop giữ lời nên mình thấy"
- line 2454: target="Shop" | aspect=Service | current=POS | suggested=NEG
  text: "Camera lấy nét chậm nên ảnh dễ bệt. Xét_về_mặt_khác, Shop giữ lời nên mình thấy khá tin_tưởng."
  context: "nên ảnh dễ bệt. Xét_về_mặt_khác, Shop giữ lời nên mình thấy"
- line 4780: target="Shop" | aspect=Service | current=POS | suggested=NEG
  text: "Vân_tay nhận chậm nên mở máy hay hụt nhịp. Bù_lại, Shop giữ lời nên mình thấy khá tin_tưởng."
  context: "máy hay hụt nhịp. Bù_lại, Shop giữ lời nên mình thấy"

### Service | bảo hành | POS->NEG (3)
- line 1029: target="bảo hành" | aspect=Service | current=POS | suggested=NEG
  text: "Mình dùng hơn 1 tháng, bị rơi từ 1m úp xuống đất nhưng không sao, game mượt, hàng rất tốt so với giá, yên tâm vì bảo hành 18th, khuyên các bạn mua"
  context: "với giá, yên tâm vì bảo hành 18th, khuyên các bạn mua"
- line 7048: target="bảo hành" | aspect=Service | current=POS | suggested=NEG
  text: "Sản phẩm tốt, nhưng do miui chưa được tối ưu cho mi note 10 lite nên sẽ có hiện tượng cảm ứng bị đơ lag. mình đã thử thêm ứng dụng đơ vào chế độ game turbo thì không bị đơ cảm ứng của ứng dụng đấy nữa, bạn nào gặp tình trạng này có thể thử. mong TGDD sớm phản hồi lại với bên bảo hành để sớm có bản cập nhật phần mềm xử lý ạ"
  context: "phản hồi lại với bên bảo hành để sớm có bản cập"
- line 7233: target="bảo hành" | aspect=Service | current=POS | suggested=NEG
  text: "Mua ở TGDD thì khỏi lo về chính sách bảo hành nha mn.
Hầu như tất cả các đồ điện tử trong nhà mình đều mua ở TGDD_ DMX"
  context: "khỏi lo về chính sách bảo hành nha mn. Hầu như tất"

### Service | tư_vấn | POS->NEG (3)
- line 1083: target="tư_vấn" | aspect=Service | current=POS | suggested=NEG
  text: "đeo rất êm , chị chủ tư_vấn nhiệt_tình mỗi tội giao thiếu móc"
  context: "rất êm , chị chủ tư_vấn nhiệt_tình mỗi tội giao thiếu"
- line 3287: target="tư_vấn" | aspect=Service | current=POS | suggested=NEG
  text: "hàng này hết nên được chị chủ nhắn_tin tư_vấn tận_tình đổi sang mẫu khác màu đỏ luôn , phải nói là quá ưng ạ"
  context: "nên được chị chủ nhắn_tin tư_vấn tận_tình đổi sang mẫu khác"
- line 5329: target="tư_vấn" | aspect=Service | current=POS | suggested=NEG
  text: "bàn_phím y mẫu . s tư_vấn nhiệt_tình . ok"
  context: "bàn_phím y mẫu . s tư_vấn nhiệt_tình . ok"

### Service | bảo hành | NEG->POS (3)
- line 1385: target="bảo hành" | aspect=Service | current=NEG | suggested=POS
  text: "Dt mới mua vài tháng. Nói chung hình thức thì đẹp. Nhưng nay máy mất sóng liên tục. Gọi k đc có reset cũng vậy. Lên bảo hành thì kêu gửi hãng cũng gần 1 tháng mới xong. Chán"
  context: "có reset cũng vậy. Lên bảo hành thì kêu gửi hãng cũng"
- line 3986: target="bảo hành" | aspect=Service | current=NEG | suggested=POS
  text: "Mua của tgdd để dc bảo hành cuối cùng .lại kêu phải trả tiền thất vọng..bít zi mik mua ở ngoài cho rẻ"
  context: "Mua của tgdd để dc bảo hành cuối cùng .lại kêu phải"
- line 4089: target="bảo hành" | aspect=Service | current=NEG | suggested=POS
  text: "Dùng 3 tháng nhưng bảo hành đến 3 lần liên tục vì lỗi sạc không vào. Dù là fan của samsung nhưng lần này là bảo hành không được nữa là cách luôn. Quá tam ba bận"
  context: "Dùng 3 tháng nhưng bảo hành đến 3 lần liên tục"

### Electronics | Pin | POS->NEG (3)
- line 1425: target="Pin" | aspect=Electronics | current=POS | suggested=NEG
  text: "Pin 5000 mà sài hết hơi nhanh,giá thì hơi cao so với máy á,mà lại k có sạc nhanh nữa... Có hơi thất vọng"
  context: "Pin 5000 mà sài hết hơi"
- line 3739: target="Pin" | aspect=Electronics | current=POS | suggested=NEG
  text: "Máy ngón trong tầm giá. Phù hợp cho học sinh. 
Nhân viên bán hàng tư vấn ok. Pin trâu"
  context: "bán hàng tư vấn ok. Pin trâu"
- line 5478: target="Pin" | aspect=Electronics | current=POS | suggested=NEG
  text: "_VỀ SẢN PHẪM:
Sản phẫm tốt trong tầm giá
Game rất mượt..đôi lúc loag do k ăn mạng
Pin khoẻ..
_VỀ TGDD:
Nhân viên nhiệt tình, chu đáo, vui vẻ và hái hước, dể thương
Sản phẫm nhập về rất tốt rất nhanh..đến sưa thị là nhận ngay
Nói chung mọi thứ rất tốt...k chê j đc
Very Good"
  context: "loag do k ăn mạng Pin khoẻ.. _VỀ TGDD: Nhân viên"

### Electronics | pin | NEG->POS (3)
- line 1532: target="pin" | aspect=Electronics | current=NEG | suggested=POS
  text: "vừa mua 1 em này ở tgdd ngã 3 thết bị điện đông anh. nói chung nhân viên nhiệt tình. cực hài lòng. còn về máy vừa lướt xem phim chưa biết như nào nhưng pin cứ 3p tụt 1%. ☺️ ☺️"
  context: "chưa biết như nào nhưng pin cứ 3p tụt 1%. ☺️"
- line 4587: target="pin" | aspect=Electronics | current=NEG | suggested=POS
  text: "Sai lầm khi mua samsung A70,máy thì hao pin,mua 4 tháng thì 2 lần bảo hành cùng một lỗi,bảo hành lần 2 về máy đơ,vào mạng hay chơi game hay bị đứng,xài 10p thì nóng máy,chất lượng máy quá tệ,"
  context: "mua samsung A70,máy thì hao pin,mua 4 tháng thì 2 lần"
- line 7212: target="pin" | aspect=Electronics | current=NEG | suggested=POS
  text: "Chất lượng kém so vs giá sp , pin 5000 mà tụt nhanh quá, camera cũng k đẹp , dt thì thường xuyên bị đơ , lag, vaof ứng dụng bị văng, chán,  tầm này mua redmi xài ok hơn nhìu ,"
  context: "so vs giá sp , pin 5000 mà tụt nhanh quá,"

### App | phần_mềm | NEG->POS (3)
- line 1858: target="phần_mềm" | aspect=App | current=NEG | suggested=POS
  text: "dm quả_cáo gì mà đi phần_mềm nào cũng có_mặt lazada hết bực rồi đó"
  context: "dm quả_cáo gì mà đi phần_mềm nào cũng có_mặt lazada hết"
- line 2318: target="phần_mềm" | aspect=App | current=NEG | suggested=POS
  text: "bắt đăng_nhập lằng nhà lằng_nhằng nói_chung phần_mềm như khấc"
  context: "đăng_nhập lằng nhà lằng_nhằng nói_chung phần_mềm như khấc"
- line 5303: target="phần_mềm" | aspect=App | current=NEG | suggested=POS
  text: "bấm phần_mềm nào cũng hiện link ht"
  context: "bấm phần_mềm nào cũng hiện link ht"

### General | chất_liệu | NEG->POS (3)
- line 1962: target="chất_liệu" | aspect=General | current=NEG | suggested=POS
  text: "chất_liệu giày vans old school khá cứng và nặng , không thích_hợp chạy nhảy lắm"
  context: "chất_liệu giày vans old school khá"
- line 3209: target="chất_liệu" | aspect=General | current=NEG | suggested=POS
  text: "rõ_ràng ghi là chất_liệu kaki nhưng hàng lại là chất vải mềm"
  context: "rõ_ràng ghi là chất_liệu kaki nhưng hàng lại là"
- line 4574: target="chất_liệu" | aspect=General | current=NEG | suggested=POS
  text: "chất_liệu a o len ke mình , len thô , sơ i len thư a nhiê u"
  context: "chất_liệu a o len ke mình"

### App | app | POS->NEU (3)
- line 2320: target="app" | aspect=App | current=POS | suggested=NEU
  text: "yêu mỗi app này tiện mà_còn săn được đồ 0 đ nx"
  context: "yêu mỗi app này tiện mà_còn săn được"
- line 2711: target="app" | aspect=App | current=POS | suggested=NEU
  text: "Samsung đã biết nhận ra điểm yếu của mình rồi , tấm nền amoled dùng cho màng 6.5 hd+ thì nhìn rỗ và nhem màu ở cạnh viền cửa sổ app và màng hình , còn các tấm nền phổ thông dùng cho màng 6.5 hd+ thì lại ko bị các lỗi đó , đem chất lượng tốt tới còn hơn là ép người dùng sử dụng theo nhu cầu :))"
  context: "ở cạnh viền cửa sổ app và màng hình , còn"
- line 6209: target="app" | aspect=App | current=POS | suggested=NEU
  text: "cảm_ơn tiki chiếc app xịn nhất trong máy của mình"
  context: "cảm_ơn tiki chiếc app xịn nhất trong máy của"

### Service | nhân_viên | NEG->POS (3)
- line 3023: target="nhân_viên" | aspect=Service | current=NEG | suggested=POS
  text: "không làm gì cũng cr01 liên_hệ cskh thì nhân_viên cũng ù_ù cạc_cạc chẳng biết cái gì thậm_chí cskh gọi thẳng cho khách bảo không xử_lý được đừng khiếu_nại nữa"
  context: "cũng cr01 liên_hệ cskh thì nhân_viên cũng ù_ù cạc_cạc chẳng biết"
- line 5242: target="nhân_viên" | aspect=Service | current=NEG | suggested=POS
  text: "Vân_tay nhận nhanh nên mở máy tiện nhưng nhân_viên nói chuyện khó chịu nên mình ngại hỏi thêm."
  context: "nên mở máy tiện nhưng nhân_viên nói chuyện khó chịu nên"
- line 5676: target="nhân_viên" | aspect=Service | current=NEG | suggested=POS
  text: "đã giải_thích với nhân_viên tư_vấn là mình chỉ dùng 1 sdt và tk ngân_hàng rồi mà vẫn khóa mua hàng h muốn dùng thì phải thay sdt kèm rất nhiều công_việc 1 sao ngay và luôn"
  context: "đã giải_thích với nhân_viên tư_vấn là mình chỉ dùng"

### Electronics | màn hình | NEG->POS (3)
- line 4698: target="màn hình" | aspect=Electronics | current=NEG | suggested=POS
  text: "Mình mới mua hôm 15/10 Về dùng nói chung màn hình ko nét camara 48 sao chụp chỉ bằng 12 thôi rất thất vọng không bằng Realme 5pro giá rẻ hơn"
  context: "15/10 Về dùng nói chung màn hình ko nét camara 48 sao"
- line 5639: target="màn hình" | aspect=Electronics | current=NEG | suggested=POS
  text: "Lên mua redmi 8 k có tư vấn mua cái máy này . h chỉ muốn lên chọi vào mặt nv :) sản phẩm bị lỗi mà dám đứng đó giới thiệu pr các thứ ??? Mà lỗi cũng hay lắm lúc test vs mới mua về k bị đâu . chưa dc 1 tuần nó cứ cà giật cà giật k xài cái gì lướt lướt ngoài màn hình cũng giật :) cửa hàng lớn có mặt trên cả nước mà làm ăn như lừa đảo ... Sợ . đánh giá hết 1 lần thì k duyệt . lần này k duyệt nữa thì lên FB mà giải thích nha"
  context: "cái gì lướt lướt ngoài màn hình cũng giật :) cửa hàng"
- line 6181: target="màn hình" | aspect=Electronics | current=NEG | suggested=POS
  text: "máy dùng hay bị out ra màn hình chính, một số ứng dụng khởi động lại khi thoát ra màn hình chính chưa đến 30s trong khi máy có ram tới 4GB, Yêu vầu nhà phát triển thêm chức năng cuộc gọi dưới nền để người dùng có một trải nhiệm tốt hơn"
  context: "dùng hay bị out ra màn hình chính, một số ứng dụng"

### Service | nhân viên | NEG->POS (3)
- line 4766: target="nhân viên" | aspect=Service | current=NEG | suggested=POS
  text: "Mới đầu mua mình có nghiên cứu rồi xem nhiều các đánh giá của các bạn đã mua. Nhưng sài được hơn 1 tháng rồi mà máy vẫn ngon pin trâu không hề giật lag như các bạn nói. Tóm lại là rất hài lòng về máy cũng như phục vụ của nhân viên ĐMX."
  context: "cũng như phục vụ của nhân viên ĐMX."
- line 6685: target="nhân viên" | aspect=Service | current=NEG | suggested=POS
  text: "Lúc đầu định mua samsung vào shop nhân viên tư vấn oppo a9. Thất vọng thực sự khi dùng oppo. Màn hình hiển thị tối om. Máy chơi game giật lang khó chịu vl. Sạc thì lâu, k bao giờ dungg oppo nữa."
  context: "định mua samsung vào shop nhân viên tư vấn oppo a9. Thất"
- line 7030: target="nhân viên" | aspect=Service | current=NEG | suggested=POS
  text: "Mới đầu mua mình có nghiên cứu rồi xem nhiều các đánh giá của các bạn đã mua. Nhưng sài được hơn 1 tháng rồi mà máy vẫn ngon ổ_cứng trâu không hề giật lag như các bạn nói. Tóm lại là rất hài lòng về máy cũng như phục vụ của nhân viên ĐMX."
  context: "cũng như phục vụ của nhân viên ĐMX."

### General | màu | POS->NEU (2)
- line 194: target="màu" | aspect=General | current=POS | suggested=NEU
  text: "chỉ có_điều màu ga giường và mặt dưới của chăn màu không như hình"
  context: "chỉ có_điều màu ga giường và mặt dưới"
- line 6218: target="màu" | aspect=General | current=POS | suggested=NEU
  text: "màu đậm hơn so với ảnh nhưng chất vải rất mát , mềm , nhẹ đóng_gói sản_phẩm rất đẹp và chắc_chắn thời_gian giao hàng rất rất nhanh"
  context: "màu đậm hơn so với ảnh"

### Electronics | cáp_sạc | NEG->POS (2)
- line 214: target="cáp_sạc" | aspect=Electronics | current=NEG | suggested=POS
  text: "cáp_sạc free size nên ai khung ng to mặc không đẹp lắm"
  context: "cáp_sạc free size nên ai khung"
- line 6844: target="cáp_sạc" | aspect=Electronics | current=NEG | suggested=POS
  text: "cáp_sạc dùng rồi chán quá"
  context: "cáp_sạc dùng rồi chán quá"

### Ship | giao | POS->NEG (2)
- line 283: target="giao" | aspect=Ship | current=POS | suggested=NEG
  text: "app hai quá hay quá đặt_hàng 2 3 tiếng là giao rồi"
  context: "đặt_hàng 2 3 tiếng là giao rồi"
- line 2894: target="giao" | aspect=Ship | current=POS | suggested=NEG
  text: "Mới mua chiều nay,nhân viên giao tới nhà nhiệt tình thân thiện. Lúc tầm 3h10 mở ra pin 48% tới 5h38 còn 37% pin mặc dù chỉ thao tác tải ứng dụng Zalo,FB,và test thử YouTube thì e ấy còn 37% pin cảm thấy pin tuột nhanh . Còn lại tất cả đều OK"
  context: "Mới mua chiều nay,nhân viên giao tới nhà nhiệt tình thân"

### Service | phục vụ | POS->NEG (2)
- line 339: target="phục vụ" | aspect=Service | current=POS | suggested=NEG
  text: "Máy khá mượt. Chơi game lâu lâu bị lag. Pin mau tụt. Camera không đẹp lắm. Máy ít nóng. Chip Snapdragon 660 nhưng không thể hiện tốt. Bắt wf hơi kém xíu. NV phục vụ nhiệt tình chỉ đáo."
  context: "wf hơi kém xíu. NV phục vụ nhiệt tình chỉ đáo."
- line 6484: target="phục vụ" | aspect=Service | current=POS | suggested=NEG
  text: "Thái độ phục vụ tận tình, chu đáo. Mua máy ở đmx Phạm Hùng, Q8. Cảm thấy vui vẻ, hài lòng.
Máy mạnh, pin trâu loa to, nghe gọi rõ ràng. 2 sim chạy mạnh. Màn hình to, xem phim đã mắt tuy màu hơi nhạt so với các đt khác trong tầm giá.
Cảm thấy OK. Cho 5 sao"
  context: "Thái độ phục vụ tận tình, chu đáo. Mua"

### Electronics | khóa | NEG->POS (2)
- line 427: target="khóa" | aspect=Electronics | current=NEG | suggested=POS
  text: "nhưng ngăn_kéo khóa ít"
  context: "nhưng ngăn_kéo khóa ít"
- line 2935: target="khóa" | aspect=Electronics | current=NEG | suggested=POS
  text: "chỉ có al15 loại kéo khóa cỡ mình mà rất chật"
  context: "chỉ có al15 loại kéo khóa cỡ mình mà rất chật"

### General | sản_phẩm | POS->NEU (2)
- line 659: target="sản_phẩm" | aspect=General | current=POS | suggested=NEU
  text: "mình mua sản_phẩm còn được shop tặng thêm món quà nhỏ rất dễ_thương"
  context: "mình mua sản_phẩm còn được shop tặng thêm"
- line 3240: target="sản_phẩm" | aspect=General | current=POS | suggested=NEU
  text: "sản_phẩm màu dễ_thương"
  context: "sản_phẩm màu dễ_thương"

### Price | giá_tiền | POS->NEU (2)
- line 916: target="giá_tiền" | aspect=Price | current=POS | suggested=NEU
  text: "Giày đi cấn chân và form bị bè ngang; còn giá_tiền như vậy là quá ổn."
  context: "form bị bè ngang; còn giá_tiền như vậy là quá ổn."
- line 1810: target="giá_tiền" | aspect=Price | current=POS | suggested=NEU
  text: "Dép đi trơn và quai khá cấn mà giá_tiền như vậy là quá ổn."
  context: "và quai khá cấn mà giá_tiền như vậy là quá ổn."

### App | Ứng dụng | NEG->POS (2)
- line 1243: target="Ứng dụng" | aspect=App | current=NEG | suggested=POS
  text: "Ứng dụng có sẵn của A31 có chức năng ghi âm, Google drive, Google maps k ạ? Mìn mới lấy ổ_cứng về test thì không có những ứng dụng này. Những dòng Galaxy khác thì lại có."
  context: "Ứng dụng có sẵn của A31 có"
- line 3127: target="Ứng dụng" | aspect=App | current=NEG | suggested=POS
  text: "Ứng dụng có sẵn của A31 có chức năng ghi âm, Google drive, Google maps k ạ? Mìn mới lấy máy về test thì không có những ứng dụng này. Những dòng Galaxy khác thì lại có."
  context: "Ứng dụng có sẵn của A31 có"

### Electronics | máy_hút_bụi | NEG->POS (2)
- line 1293: target="máy_hút_bụi" | aspect=Electronics | current=NEG | suggested=POS
  text: "app bán cho bọn tây hay j mà chọn tiếng việt r cũng tiếng anh máy_hút_bụi thì toàn ở đâu_đâu quá tệ"
  context: "việt r cũng tiếng anh máy_hút_bụi thì toàn ở đâu_đâu quá"
- line 5311: target="máy_hút_bụi" | aspect=Electronics | current=NEG | suggested=POS
  text: "Giá sản phẩm vẫn quá là Chát.mặc dù máy_hút_bụi đã ra đc gần 3 năm rồi.không biết iphone 11 ra mắt giá 7plus còn chát vậy k?"
  context: "vẫn quá là Chát.mặc dù máy_hút_bụi đã ra đc gần 3"

### Fashion | quần | POS->NEG (2)
- line 1303: target="quần" | aspect=Fashion | current=POS | suggested=NEG
  text: "quần đợt 1 đặt thì vải đẹp dáng quần đẹp cũng vừa chân"
  context: "quần đợt 1 đặt thì vải"
- line 1782: target="quần" | aspect=Fashion | current=POS | suggested=NEG
  text: "quần siêu cute"
  context: "quần siêu cute"

### Service | chủ shop | POS->NEG (2)
- line 1419: target="chủ shop" | aspect=Service | current=POS | suggested=NEG
  text: "chủ shop rất nhiệt_tình và có trách_nhiệm với khách"
  context: "chủ shop rất nhiệt_tình và có trách_nhiệm"
- line 4848: target="chủ shop" | aspect=Service | current=POS | suggested=NEG
  text: "bạn chủ shop nhiệt_tình tư_vấn ! !"
  context: "bạn chủ shop nhiệt_tình tư_vấn ! !"

### Fashion | giày | NEG->POS (2)
- line 1685: target="giày" | aspect=Fashion | current=NEG | suggested=POS
  text: "giày đi thì cũng nhẹ , hơi mỏng"
  context: "giày đi thì cũng nhẹ ,"
- line 4979: target="giày" | aspect=Fashion | current=NEG | suggested=POS
  text: "cổ giày chật mang khó_khăn"
  context: "cổ giày chật mang khó_khăn"

### Electronics | điện thoại | NEG->POS (2)
- line 1701: target="điện thoại" | aspect=Electronics | current=NEG | suggested=POS
  text: "Máy mơie mua được 3 tháng mà hao pin quá. Dạo này covid ở nhà nên mình hay mở youtube. Một tuần trước còn xài được nguyên ngày, sang ngày hôm sau mới phải sạc. Nhưng qua mấy ngày nay, mình coi youtube cũng ít lại rồi nhưng điện thoại xà tầm 4h 4h30 đã hết pin. Thật phí tiền. Buồn."
  context: "cũng ít lại rồi nhưng điện thoại xà tầm 4h 4h30 đã"
- line 6749: target="điện thoại" | aspect=Electronics | current=NEG | suggested=POS
  text: "Chơi thì rất ổn cấu hình ổn cho giá tầm 3 triệu này nhưng một điều khiến tôi rất khó chịu khi sử dụng chiếc điện thoại này vì bắt wifi quá yếu mặc dù đã cập nhật phần mềm lên 10 mà vẫn bắt wifi rất yêu,mong nhà sx khắc phục lỗi này."
  context: "chịu khi sử dụng chiếc điện thoại này vì bắt wifi quá"

### Price | tiền | POS->NEG (2)
- line 1708: target="tiền" | aspect=Price | current=POS | suggested=NEG
  text: "rất tốt vì có bán xu và tiền cổ nên cho 5 sao"
  context: "vì có bán xu và tiền cổ nên cho 5 sao"
- line 5406: target="tiền" | aspect=Price | current=POS | suggested=NEG
  text: "Quá đã tiền nào của đó nhé mấy bạn máy quá em nhân viên phục vụ quá nhiệt tình luôn cảm ơn thế giới di động"
  context: "Quá đã tiền nào của đó nhé mấy"

### Service | dễ_thương | POS->NEU (2)
- line 2200: target="dễ_thương" | aspect=Service | current=POS | suggested=NEU
  text: "bà chủ dễ_thương"
  context: "bà chủ dễ_thương"
- line 3693: target="dễ_thương" | aspect=Service | current=POS | suggested=NEU
  text: "chị chủ dễ_thương cực_kì luôn"
  context: "chị chủ dễ_thương cực_kì luôn"

### Service | tiki | POS->NEG (2)
- line 2316: target="tiki" | aspect=Service | current=POS | suggested=NEG
  text: "tiki nhiệt_tình , đặt trưa nay , sáng_mai có hàng rồi"
  context: "tiki nhiệt_tình , đặt trưa nay"
- line 3527: target="tiki" | aspect=Service | current=POS | suggested=NEG
  text: "đóng_gói sản_phẩm chắc_chắn tuy_nhiên vải xấu và may ẩu , tiki tư_vấn nhiệt_tình nên để 4"
  context: "xấu và may ẩu , tiki tư_vấn nhiệt_tình nên để 4"

### App | phần_mềm | POS->NEU (2)
- line 2422: target="phần_mềm" | aspect=App | current=POS | suggested=NEU
  text: "yêu mỗi phần_mềm này tiện mà_còn săn được đồ 0 đ nx"
  context: "yêu mỗi phần_mềm này tiện mà_còn săn được"
- line 7122: target="phần_mềm" | aspect=App | current=POS | suggested=NEU
  text: "rất cảm_ơn lazada đã tạo ra phần_mềm này để thuận_tiện mua_sắm với nhiều chính_sách ưu_đãi dịch_vụ chăm_sóc khách_hàng tốt tôi rất hài_lòng"
  context: "cảm_ơn lazada đã tạo ra phần_mềm này để thuận_tiện mua_sắm với"

### Service | khách_hàng | NEG->POS (2)
- line 2630: target="khách_hàng" | aspect=Service | current=NEG | suggested=POS
  text: "khách_hàng vô_cùng quen_thuộc của shopee nhưng có điểm rất không thích đó là nhận voucher khi hàng giao chậm nhưng không_thể_nào dùng được cảm_giác gọi_là cho có mà thôi"
  context: "khách_hàng vô_cùng quen_thuộc của shopee nhưng"
- line 2991: target="khách_hàng" | aspect=Service | current=NEG | suggested=POS
  text: "app rất chán_cách làm_việc hỗ_trợ khách_hàng cũng chán_quy_tắc lùng_bùng vô_lý có mỗi việ đổi quy_tắc gói hàng sao cho không bị hỏng hóc mà bao năm có làm được đâu không xứng_đáng là trang thương_mại_điện_tử lớn với cái kiểu làm_việc không có tâm không tôn_trọng khách và chăm_chăm lợi_nhuận như_vậy"
  context: "app rất chán_cách làm_việc hỗ_trợ khách_hàng cũng chán_quy_tắc lùng_bùng vô_lý có"

### Electronics | màn hình | POS->NEU (2)
- line 2646: target="màn hình" | aspect=Electronics | current=POS | suggested=NEU
  text: "mình thấy kiểu dáng của ip11 cũng rất đẹp,giá tiền hợp lý trong bộ 3 ip,chỉ có màn hình là bị cắt giảm chưa hợp lý lắm."
  context: "trong bộ 3 ip,chỉ có màn hình là bị cắt giảm chưa"
- line 4744: target="màn hình" | aspect=Electronics | current=POS | suggested=NEU
  text: "Đã mua tại TGDD đường trần hưng đạo, p5. Tp. Cà mau. Nhân viên tư vấn nhiệt tình, phục vụ khăn lạnh, nước uống đầy đủ. Còn nhân viên dán màn hình mặt trước, mặt sau cực kì xấu, dù trước đó rất thích tgdd dán màn hình kĩ và đẹp. Chả hiểu lần này dán quá xấu, cắt dán không đều, thêm do có việc gấp nên ko đề nghị dán lại, em phải đi lẫn về hơn 140km để mua máy nhưng ko vừa ý dán màn hình. Mất thẩm mỹ giá trị của máy. Mình đánh giá sản phẩm 5*.  Phục vụ tư vấn 5*, trang trí dán máy 3*."
  context: "đủ. Còn nhân viên dán màn hình mặt trước, mặt sau cực"

### Service | cửa hàng | POS->NEG (2)
- line 2709: target="cửa hàng" | aspect=Service | current=POS | suggested=NEG
  text: "Nhanh hết pin.thua pin 3000 của Huawei
Lên cửa hàng hỏi thì nhận được trả lời.giờ máy nào dùng nhiều cũng nhanh hết pin"
  context: "pin 3000 của Huawei Lên cửa hàng hỏi thì nhận được trả"
- line 4657: target="cửa hàng" | aspect=Service | current=POS | suggested=NEG
  text: "Cho mình hỏi cửa hàng có hỗ trợ dán viền chống trầy ko vậy tại mình ko thích dùng ốp lưng"
  context: "Cho mình hỏi cửa hàng có hỗ trợ dán viền"

### Fashion | váy | NEG->POS (2)
- line 3253: target="váy" | aspect=Fashion | current=NEG | suggested=POS
  text: "nhưng phần váy đen phai dã_man quá phai hết cả ra phần cổ trắng"
  context: "nhưng phần váy đen phai dã_man quá phai"
- line 4306: target="váy" | aspect=Fashion | current=NEG | suggested=POS
  text: "cái váy khá chật"
  context: "cái váy khá chật"

### Service | phản_hồi | POS->NEG (2)
- line 3266: target="phản_hồi" | aspect=Service | current=POS | suggested=NEG
  text: "nhờ đọc qua phản_hồi tích_cực và nhận được củ_sạc đúng yêu_cầu nên tôi rất hài_lòng"
  context: "nhờ đọc qua phản_hồi tích_cực và nhận được củ_sạc"
- line 3941: target="phản_hồi" | aspect=Service | current=POS | suggested=NEG
  text: "nhờ đọc qua phản_hồi tích_cực và nhận được sản_phẩm đúng yêu_cầu nên tôi rất hài_lòng"
  context: "nhờ đọc qua phản_hồi tích_cực và nhận được sản_phẩm"

### Electronics | wifi | NEG->POS (2)
- line 3449: target="wifi" | aspect=Electronics | current=NEG | suggested=POS
  text: "Công nhận đt iPhone 7lpus giá thì cao mọi thứ sài rất ok. Nhưng có cái 3G và wifi rất yếu thua một cái đt Samsung cùi bắp"
  context: "Nhưng có cái 3G và wifi rất yếu thua một cái"
- line 5052: target="wifi" | aspect=Electronics | current=NEG | suggested=POS
  text: "Công nhận đt iPhone 7lpus giá thì cao mọi thứ sài rất ok. Nhưng có cái 3G và wifi rất yếu"
  context: "Nhưng có cái 3G và wifi rất yếu"

### Service | tư vấn | NEG->POS (2)
- line 3478: target="tư vấn" | aspect=Service | current=NEG | suggested=POS
  text: "Lướt w quá tệ, nhiều trang bị chặn phải 2-3 lần mới vào đc, nhất là trang tienphong online. Tuoitreonline, cảm ứng kém, nếu dùng thêm miếng dán thì sử dụng rất bực, mình đang có ý định đổi ( trả) để dùng máy khác. Nhờ AD tư vấn"
  context: "dùng máy khác. Nhờ AD tư vấn"
- line 5639: target="tư vấn" | aspect=Service | current=NEG | suggested=POS
  text: "Lên mua redmi 8 k có tư vấn mua cái máy này . h chỉ muốn lên chọi vào mặt nv :) sản phẩm bị lỗi mà dám đứng đó giới thiệu pr các thứ ??? Mà lỗi cũng hay lắm lúc test vs mới mua về k bị đâu . chưa dc 1 tuần nó cứ cà giật cà giật k xài cái gì lướt lướt ngoài màn hình cũng giật :) cửa hàng lớn có mặt trên cả nước mà làm ăn như lừa đảo ... Sợ . đánh giá hết 1 lần thì k duyệt . lần này k duyệt nữa thì lên FB mà giải thích nha"
  context: "mua redmi 8 k có tư vấn mua cái máy này ."

### General | bề_mặt | NEG->POS (2)
- line 3635: target="bề_mặt" | aspect=General | current=NEG | suggested=POS
  text: "bề_mặt vải cứng , với giá này thì không đòi_hỏi gì thêm"
  context: "bề_mặt vải cứng , với giá"
- line 5504: target="bề_mặt" | aspect=General | current=NEG | suggested=POS
  text: "mình ở hn bảo mua 2 cái bảo được free ship mà không được free . 2 cái 2 bề_mặt khác nhau vậy shop"
  context: "free . 2 cái 2 bề_mặt khác nhau vậy shop"

### General | sản_phẩm | NEG->POS (2)
- line 3995: target="sản_phẩm" | aspect=General | current=NEG | suggested=POS
  text: "tại_sao mua 2 sản_phẩm cùng 1 địa_chỉ , giao hàng cùng 1 lúc mà shop lại tính 2 lần tiền ship ? ?"
  context: "tại_sao mua 2 sản_phẩm cùng 1 địa_chỉ , giao"
- line 5508: target="sản_phẩm" | aspect=General | current=NEG | suggested=POS
  text: "giá cao so với sản_phẩm cùng loại"
  context: "giá cao so với sản_phẩm cùng loại"

### Electronics | linh_kiện_điện_tử | POS->NEG (2)
- line 4699: target="linh_kiện_điện_tử" | aspect=Electronics | current=POS | suggested=NEG
  text: "Máy mới mua sài  rất mượt và ok nhân viên tư vấn nhiệt tình linh_kiện_điện_tử sài rất trâu 20% sài gần 2tieng mới hết sạc nhanh nói chung hợp với tầm giá"
  context: "viên tư vấn nhiệt tình linh_kiện_điện_tử sài rất trâu 20% sài"
- line 4708: target="linh_kiện_điện_tử" | aspect=Electronics | current=POS | suggested=NEG
  text: "Sản phẩm đẹp hiệu năng chưa trải nghiệm hết nên chưa biết. Nhân viên khỏi nói. Vui tính.nhiệt tình.tận tâm với khách hàng.Mới lấy linh_kiện_điện_tử lúc tối tại ĐMX _ TL43 _ Bình Chiểu (đối diện ủy ban)
Bạn trang nhân viên xinh gái vui tính nhiẹt tình.
Thích bạn ấy mất cơ.hihi"
  context: "tâm với khách hàng.Mới lấy linh_kiện_điện_tử lúc tối tại ĐMX _"

### General | màu | POS->NEG (2)
- line 4921: target="màu" | aspect=General | current=POS | suggested=NEG
  text: "màu hơi nhạt so với hình , nhưng với số tiền như_vậy thì mình cảm_thấy ok lắm"
  context: "màu hơi nhạt so với hình"
- line 5490: target="màu" | aspect=General | current=POS | suggested=NEG
  text: "phan_thị_tươi hỏi giá bộ_đồ màu trắng đen bao_nhiêu vậy cửa_hàng"
  context: "phan_thị_tươi hỏi giá bộ_đồ màu trắng đen bao_nhiêu vậy cửa_hàng"

### Electronics | Điện thoại | NEG->POS (2)
- line 4950: target="Điện thoại" | aspect=Electronics | current=NEG | suggested=POS
  text: "Mới mua được 2 ngày dùng thấy bình thường trong tầm giá. Xong có phần BÀN PHÍM ẤN HẦU NHƯ KHÔNG NHẠY.  Chơi GAME ấn mãi mới được. Bực kinh khủng !   Phải ấn mấy lần mới nhận.  Hơi bức mình những lúc đang vội mà phải nhắn tin. Điện thoại chủ yếu dùng phải ấn các nút hoặc ấn bàn phím. Nhưng C3 này ấn rất khó chịu ! Ấn nhập nhằng phải ấn mấy lần mới được !"
  context: "vội mà phải nhắn tin. Điện thoại chủ yếu dùng phải ấn"
- line 6667: target="Điện thoại" | aspect=Electronics | current=NEG | suggested=POS
  text: "Điện thoại 15 triệu mà mặt lưng nhựa, kính cường lực gorilla glass 3. Xài chất liệu rẻ tiền mà cứ bán giá trên trời!"
  context: "Điện thoại 15 triệu mà mặt lưng"

### Price | Giá | POS->NEU (2)
- line 5002: target="Giá" | aspect=Price | current=POS | suggested=NEU
  text: "Giá phù hợp,sản phẩm nhỏ gọn, máy mượt, thiết kế đẹp. Máy chạy ứng dụng tốt, bắt wifi tốt, IOS đọc báo rất mượt, font chữ đẹp, màu sắc tươi tắn . Pin Xài lâu. Bảo hành ok"
  context: "Giá phù hợp,sản phẩm nhỏ gọn,"
- line 6951: target="Giá" | aspect=Price | current=POS | suggested=NEU
  text: "Giá phù hợp,sản phẩm nhỏ gọn, máy mượt, thiết kế đẹp. Máy chạy ứng dụng tốt, bắt wifi tốt, IOS đọc báo rất mượt, font chữ đẹp, màu sắc tươi tắn . Linh_kiện_điện_tử Xài lâu. Bảo hành ok"
  context: "Giá phù hợp,sản phẩm nhỏ gọn,"

### Service | cửa hàng | NEG->POS (2)
- line 5013: target="cửa hàng" | aspect=Service | current=NEG | suggested=POS
  text: "màn hình bị chấm trắng 1mm sao k nên gửi bảo hành ko cửa hàng tgdd nhưng nhìn kỵ mới thấy"
  context: "nên gửi bảo hành ko cửa hàng tgdd nhưng nhìn kỵ mới"
- line 5422: target="cửa hàng" | aspect=Service | current=NEG | suggested=POS
  text: "Thất vọng thật !
Mua về xài khoảng 5 hôm điện thoại sạc pin lúc thì sạc được 100 lúc đến 66,67% báo pin đầy.. Phải rút ra sạc lại mới vô pin.. Pin k sử dụng bật tiết kiệm pin cũng sục pin... Ra cửa hàng 3 lần rồi về vẫn vậy.. Thất vọng
Ra cửa hàng 3"
  context: "pin cũng sục pin... Ra cửa hàng 3 lần rồi về vẫn"

### Fashion | vải | POS->NEU (2)
- line 5397: target="vải" | aspect=Fashion | current=POS | suggested=NEU
  text: "tiki rất dễ_thương nha , vải mịn mà mát cực ! !"
  context: "tiki rất dễ_thương nha , vải mịn mà mát cực !"
- line 7435: target="vải" | aspect=Fashion | current=POS | suggested=NEU
  text: "shop rất dễ_thương nha , vải mịn mà mát cực ! !"
  context: "shop rất dễ_thương nha , vải mịn mà mát cực !"

### Electronics | linh_kiện_điện_tử | POS->NEU (2)
- line 5978: target="linh_kiện_điện_tử" | aspect=Electronics | current=POS | suggested=NEU
  text: "mua 2 linh_kiện_điện_tử lại còn được giảm_giá"
  context: "mua 2 linh_kiện_điện_tử lại còn được giảm_giá"
- line 7228: target="linh_kiện_điện_tử" | aspect=Electronics | current=POS | suggested=NEU
  text: "giá các linh_kiện_điện_tử cao hơn các trang mua_sắm khác"
  context: "giá các linh_kiện_điện_tử cao hơn các trang mua_sắm"

### Fashion | vải | NEG->POS (2)
- line 6193: target="vải" | aspect=Fashion | current=NEG | suggested=POS
  text: "vải như cái vải mùng lun"
  context: "vải như cái vải mùng lun"
- line 6454: target="vải" | aspect=Fashion | current=NEG | suggested=POS
  text: "vải thì bị bung các cái đen đen ra giặt 2 lần rồi vẫn không hết"
  context: "vải thì bị bung các cái"

### Service | dịch vụ | NEG->POS (2)
- line 6480: target="dịch vụ" | aspect=Service | current=NEG | suggested=POS
  text: "Tính ra thì quá tệ so với tầm giá 😃
Độ mượt kém
Bắt wifi siêu kém
Cảm ứng không nhạy
Cảm biến vân tay + khuôn mặt quá chán
Mới mua đt chưa đc 1 tuần mà muốn đổi đt khác r
Dù s vớt lại dc cái tgdd dịch vụ lúc nào cũng good 😃"
  context: "vớt lại dc cái tgdd dịch vụ lúc nào cũng good 😃"
- line 7285: target="dịch vụ" | aspect=Service | current=NEG | suggested=POS
  text: "Phần mềm của oppo làm chán không chịu đc. Đổi từ samsung sang oppo thấy về dịch vụ và phần mềm chênh lệch nhau quá. Camera cũng ít options hơn bên Samsung nữa. Thậm chí còn ko có darkmode nữa chứ. Mong nhà phát triển sớm cập nhật, chứ tình hình này kéo dài là tiêu luôn."
  context: "samsung sang oppo thấy về dịch vụ và phần mềm chênh lệch"

### General | sản_phẩm | POS->NEG (2)
- line 6712: target="sản_phẩm" | aspect=General | current=POS | suggested=NEG
  text: "app có_thể thêm cách tìm_kiếm sản_phẩm bằng hình_ảnh để khách_hàng dễ tìm_kiếm sản_phẩm"
  context: "app có_thể thêm cách tìm_kiếm sản_phẩm bằng hình_ảnh để khách_hàng dễ"
- line 7014: target="sản_phẩm" | aspect=General | current=POS | suggested=NEG
  text: "sản_phẩm như hình mỗi tội vải hơi mỏng"
  context: "sản_phẩm như hình mỗi tội vải"

### Electronics | chuột | POS->NEG (1)
- line 114: target="chuột" | aspect=Electronics | current=POS | suggested=NEG
  text: "Máy sử dụng rất tốt. Với giá tiền này là quá ok.Máy chạy cực mượt với các ứng dụng Google Go, Zalo, Facebook, Web thoải máy. Phù hợp với nhu cầu cơ bản. Chỉ có chuột máy với độ phân giải chưa cao thôi, nhưng với mức giá tiền này thì tốt rồi."
  context: "cầu cơ bản. Chỉ có chuột máy với độ phân giải"

### Electronics | sóng | POS->NEU (1)
- line 401: target="sóng" | aspect=Electronics | current=POS | suggested=NEU
  text: "sóng căng vứt"
  context: "sóng căng vứt"

### Service | Phục vụ | POS->NEG (1)
- line 577: target="Phục vụ" | aspect=Service | current=POS | suggested=NEG
  text: "Phục vụ tận tình, chu đáo, bàn_phím dùng tốt, thêm chương trình giảm giá nữa quá tuyệt vời. Phải vào đánh giá ngay"
  context: "Phục vụ tận tình, chu đáo, bàn_phím"

### Fashion | form | NEG->POS (1)
- line 769: target="form" | aspect=Fashion | current=NEG | suggested=POS
  text: "form rất to lùng_bùng như trùm cái mền"
  context: "form rất to lùng_bùng như trùm"

### Electronics | điện thoại | POS->NEU (1)
- line 905: target="điện thoại" | aspect=Electronics | current=POS | suggested=NEU
  text: "Phiên bản nâng cấp của A5s , không khác A5s bao nhiêu , được cái rậm và rợm nhiều hơn . Chíp P35 tối ưu hóa pin rất tốt , phần mềm tương đối cùng mượt , mới tấc vụ cơ bản thì ok , những người lớn tuổi phù hợp với điện thoại này lóa to và rõ"
  context: "lớn tuổi phù hợp với điện thoại này lóa to và rõ"

### Electronics | Máy | NEG->POS (1)
- line 1043: target="Máy" | aspect=Electronics | current=NEG | suggested=POS
  text: "Máy bị loạn cảm ứng đa điểm, bạn nào chơi loại game 2-3 ngón thì ko chơi dc, đi bảo hành thì ss báo lí do đủ thứ ko sửa dc. Mua máy 9tr3 vê làm cục gạch."
  context: "Máy bị loạn cảm ứng đa"

### Service | phục_vụ | POS->NEU (1)
- line 1045: target="phục_vụ" | aspect=Service | current=POS | suggested=NEU
  text: "Wifi bắt yếu nên gọi video hay chập_chờn mà phục_vụ lịch_sự nên trải_nghiệm mua dễ chịu."
  context: "gọi video hay chập_chờn mà phục_vụ lịch_sự nên trải_nghiệm mua dễ"

### Ship | giao hàng | POS->NEG (1)
- line 1166: target="giao hàng" | aspect=Ship | current=POS | suggested=NEG
  text: "tôi thấy mấy anh shipper giao hàng rất là thân_thiện lắm với_lại đặt_hàng cái nào cũng y_chang trên cửa_hàng bán chất_lượng"
  context: "tôi thấy mấy anh shipper giao hàng rất là thân_thiện lắm với_lại"

### Service | shopee | POS->NEU (1)
- line 1264: target="shopee" | aspect=Service | current=POS | suggested=NEU
  text: "shopee tư_vấn nhiệt_tình , dễ_thương , đóng_gói sản_phẩm đẹp"
  context: "shopee tư_vấn nhiệt_tình , dễ_thương ,"

### Electronics | Màn hình | POS->NEU (1)
- line 1277: target="Màn hình" | aspect=Electronics | current=POS | suggested=NEU
  text: "Đáng tiền hơn 2 con pro với pro max
Màn hình ko bị rỗ như con XR, trãi nghiệm tốt"
  context: "con pro với pro max Màn hình ko bị rỗ như con"

### Electronics | Ổ_cứng | NEG->POS (1)
- line 1330: target="Ổ_cứng" | aspect=Electronics | current=NEG | suggested=POS
  text: "Sóng sánh kém lắm,giữa đất thị trấn mà chỉ đc 2-3 vạch. Wifi vào phòng trong cách khoảng 5m mà bắt đc 3 vạch. Đã gửi đi hãng thẩm định. Ổ_cứng qua đêm tắt hết ứng dụng,mạng mà sáng dậy tụt 12%.
Chơi liên quân đôi khi vẫn bị khựng lại chút.đc cái màn nét."
  context: "gửi đi hãng thẩm định. Ổ_cứng qua đêm tắt hết ứng"

### Service | sendo | POS->NEG (1)
- line 1360: target="sendo" | aspect=Service | current=POS | suggested=NEG
  text: "sendo làm_ăn mata uy_tín"
  context: "sendo làm_ăn mata uy_tín"

### General | màu_da | POS->NEG (1)
- line 1365: target="màu_da" | aspect=General | current=POS | suggested=NEG
  text: "màu_da hơi sáng và vàng quá . shop phục_vụ tốt"
  context: "màu_da hơi sáng và vàng quá"

### Electronics | chuột | NEG->POS (1)
- line 1368: target="chuột" | aspect=Electronics | current=NEG | suggested=POS
  text: "chuột chưa được ưng cho lắm"
  context: "chuột chưa được ưng cho lắm"

### Price | giá_tiền | NEG->POS (1)
- line 1503: target="giá_tiền" | aspect=Price | current=NEG | suggested=POS
  text: "Vải mặc mát và sờ rất êm nhưng giá_tiền như vậy là chưa đáng."
  context: "và sờ rất êm nhưng giá_tiền như vậy là chưa đáng."

### Electronics | Cáp_sạc | POS->NEG (1)
- line 1627: target="Cáp_sạc" | aspect=Electronics | current=POS | suggested=NEG
  text: "Máy ngón trong tầm giá. Phù hợp cho học sinh. 
Nhân viên bán hàng tư vấn ok. Cáp_sạc trâu"
  context: "bán hàng tư vấn ok. Cáp_sạc trâu"

### Ship | gửi | POS->NEG (1)
- line 1678: target="gửi" | aspect=Ship | current=POS | suggested=NEG
  text: "Vsmart joy 3 nhà sản xuất đã gửi bản cập nhật sửa chữa các tính năng r nha các bạn bắt wifi bao mạnh"
  context: "3 nhà sản xuất đã gửi bản cập nhật sửa chữa"

### Electronics | wifi | POS->NEG (1)
- line 1678: target="wifi" | aspect=Electronics | current=POS | suggested=NEG
  text: "Vsmart joy 3 nhà sản xuất đã gửi bản cập nhật sửa chữa các tính năng r nha các bạn bắt wifi bao mạnh"
  context: "r nha các bạn bắt wifi bao mạnh"

### Service | tư vấn | POS->NEG (1)
- line 1866: target="tư vấn" | aspect=Service | current=POS | suggested=NEG
  text: "Mới mua sáng nay ak ak. Nơi chung là oke. KB sau thì thế nào. E NV tư vấn bán hàng nhẹ nhàng, nhiệt tình, chu đáo. Cho 5* . Sau 1 tháng sẽ rv lại cho ae. Kkk"
  context: "thì thế nào. E NV tư vấn bán hàng nhẹ nhàng, nhiệt"

### Service | khách | POS->NEU (1)
- line 1899: target="khách" | aspect=Service | current=POS | suggested=NEU
  text: "còn có quà cho khách"
  context: "còn có quà cho khách"

### Ship | Shipper | POS->NEG (1)
- line 1919: target="Shipper" | aspect=Ship | current=POS | suggested=NEG
  text: "App hay lag nên mỗi lần đặt đồ đều hơi bực. Tuy_nhiên, Shipper gọi trước nên nhận hàng rất chủ_động."
  context: "đồ đều hơi bực. Tuy_nhiên, Shipper gọi trước nên nhận hàng"

### General | gói hàng | POS->NEG (1)
- line 2124: target="gói hàng" | aspect=General | current=POS | suggested=NEG
  text: "shop gói hàng kĩ ghê , xé hơi mệt"
  context: "shop gói hàng kĩ ghê , xé hơi"

### Price | tầm_giá | POS->NEG (1)
- line 2152: target="tầm_giá" | aspect=Price | current=POS | suggested=NEG
  text: "Dép đi trơn và quai khá cấn mà tầm_giá khá hợp_lý cho nhu_cầu cơ_bản."
  context: "và quai khá cấn mà tầm_giá khá hợp_lý cho nhu_cầu cơ_bản."

### General | nhà_hàng | NEG->POS (1)
- line 2192: target="nhà_hàng" | aspect=General | current=NEG | suggested=POS
  text: "nhưng nhà_hàng làm_việc rất chán"
  context: "nhưng nhà_hàng làm_việc rất chán"

### Electronics | vân tay | POS->NEG (1)
- line 2251: target="vân tay" | aspect=Electronics | current=POS | suggested=NEG
  text: "Mọi thứ đều ok. Cảm biến vân tay ko nhạy bằng j7 prime. Mong muốn có bản cập nhật khắc phục"
  context: "thứ đều ok. Cảm biến vân tay ko nhạy bằng j7 prime."

### Service | tư_vấn | POS->NEU (1)
- line 2252: target="tư_vấn" | aspect=Service | current=POS | suggested=NEU
  text: "chị tư_vấn nhiệt_tình lại còn chu_đáo"
  context: "chị tư_vấn nhiệt_tình lại còn chu_đáo"

### Electronics | máy mới | POS->NEG (1)
- line 2306: target="máy mới" | aspect=Electronics | current=POS | suggested=NEG
  text: "Mới mua dk 3 ngày xài OK với tầm giá a em nên mua xài đi vài bữa hết máy mới đó."
  context: "xài đi vài bữa hết máy mới đó."

### Price | giá_cả | NEG->POS (1)
- line 2490: target="giá_cả" | aspect=Price | current=NEG | suggested=POS
  text: "đặt mua 3 cái nhưng chỉ 2 cái ok , cái còn lại bị lỗi nghiêm_trọng hai bên vai , nhưng giá_cả mềm cách phục_vụ của shop tốt !"
  context: "hai bên vai , nhưng giá_cả mềm cách phục_vụ của shop"

### Ship | shipper | POS->NEU (1)
- line 2548: target="shipper" | aspect=Ship | current=POS | suggested=NEU
  text: "a shipper dễ_thương"
  context: "a shipper dễ_thương"

### Price | tầm_giá | NEG->POS (1)
- line 2550: target="tầm_giá" | aspect=Price | current=NEG | suggested=POS
  text: "Áo mặc mát và màu lên nhìn rất sáng nhưng tầm_giá này mình thấy chưa hợp_lý."
  context: "lên nhìn rất sáng nhưng tầm_giá này mình thấy chưa hợp_lý."

### Ship | lần_giao_đầu | POS->NEG (1)
- line 2601: target="lần_giao_đầu" | aspect=Ship | current=POS | suggested=NEG
  text: "đợt này thấy lần_giao_đầu được báo trước rõ nên nhận hàng thuận tiện, vậy là ổn"
  context: "đợt này thấy lần_giao_đầu được báo trước rõ nên"

### Ship | giao | POS->NEU (1)
- line 2825: target="giao" | aspect=Ship | current=POS | suggested=NEU
  text: "Nhân viên online tư vấn nhiệt tình. Mình mua online giao tận nơi rất uy tín . Máy sử dụng rất tốt. S20 untra đúng là ấn tượng pin ổn (mấy má bật full màn hình, full tốt độ 120 rồi la hao pin vãi thật). Màn hình xuất sắc . Hì hơi bực cái củ sạc chỉ có 25W chứ ko phải 45W. Nhu vay thì ok rồi cảm ơn ad."
  context: "nhiệt tình. Mình mua online giao tận nơi rất uy tín"

### Electronics | linh_kiện_điện_tử | NEG->POS (1)
- line 2990: target="linh_kiện_điện_tử" | aspect=Electronics | current=NEG | suggested=POS
  text: "Không đáng để mình đánh giá 1 sao, quá chán 😬, ngừng sản xuất linh_kiện_điện_tử tầm giá này đi"
  context: "chán 😬, ngừng sản xuất linh_kiện_điện_tử tầm giá này đi"

### Fashion | quần | POS->NEU (1)
- line 3128: target="quần" | aspect=Fashion | current=POS | suggested=NEU
  text: "quần chắc_chắn lên dáng , hy_vọng sẽ mặc bền mà không bai dão !"
  context: "quần chắc_chắn lên dáng , hy_vọng"

### Ship | shipper | POS->NEG (1)
- line 3167: target="shipper" | aspect=Ship | current=POS | suggested=NEG
  text: "đặc_biệt , shipper ghn nhiệt_tình , cutee"
  context: "đặc_biệt , shipper ghn nhiệt_tình , cutee"

### Price | giá tiền | POS->NEG (1)
- line 3310: target="giá tiền" | aspect=Price | current=POS | suggested=NEG
  text: "Sản phẩm ok, Loa to, sản phẩmvừa vs giá tiền, loa thoại hơi bất tiện tí.. Nói chung  là  tam ổn"
  context: "Loa to, sản phẩmvừa vs giá tiền, loa thoại hơi bất tiện"

### Price | Voucher | POS->NEU (1)
- line 3420: target="Voucher" | aspect=Price | current=POS | suggested=NEU
  text: "Giày đi cấn chân và form bị bè ngang. Xét_về_mặt_khác, Voucher nhiều nên tổng tiền xuống khá đẹp."
  context: "form bị bè ngang. Xét_về_mặt_khác, Voucher nhiều nên tổng tiền xuống"

### Service | Nhân viên | NEG->POS (1)
- line 3520: target="Nhân viên" | aspect=Service | current=NEG | suggested=POS
  text: "Lỗi 1 xim ko nhận chua dùng dc 1 tháng.mua máy mới nhung ko dc bóc  hộp. Nhân viên lây cho 1 cái hộp  mở sẵn.máy cung dc dán decan đẹp.chac hang đổi trả  rep mới  lại bán"
  context: "nhung ko dc bóc hộp. Nhân viên lây cho 1 cái hộp"

### Service | phục vụ | POS->NEU (1)
- line 3573: target="phục vụ" | aspect=Service | current=POS | suggested=NEU
  text: "Rất ổn , phục vụ chu đáo , sản phẩm ok , giá cả rất hợp lý  , chất lượng trung bình thấp , cần tối ưu phần mềm"
  context: "Rất ổn , phục vụ chu đáo , sản phẩm"

### Service | lazada | POS->NEG (1)
- line 3651: target="lazada" | aspect=Service | current=POS | suggested=NEG
  text: "nhưng mỗi tội lạc đơn hàng phải đặt lần 2 bù lazada nhiệt_tình nên xí_xóa"
  context: "phải đặt lần 2 bù lazada nhiệt_tình nên xí_xóa"

### App | phần mềm | NEG->POS (1)
- line 3662: target="phần mềm" | aspect=App | current=NEG | suggested=POS
  text: "Dòng Vmart Joy pin rất tệ, xạc đầy để nửa ngày k làm gì là hết, phần mềm HDH ứng dụng chưa hoàn thiện hay bị lỗi vặt"
  context: "k làm gì là hết, phần mềm HDH ứng dụng chưa hoàn"

### Fashion | kích_cỡ | NEG->POS (1)
- line 3666: target="kích_cỡ" | aspect=Fashion | current=NEG | suggested=POS
  text: "kích_cỡ mình nhưng bị chật eo"
  context: "kích_cỡ mình nhưng bị chật eo"

### Electronics | củ_sạc | NEG->POS (1)
- line 3670: target="củ_sạc" | aspect=Electronics | current=NEG | suggested=POS
  text: "không có dây cúc điều_chỉnh to_nhỏ bụng như ở mô_tả củ_sạc"
  context: "to_nhỏ bụng như ở mô_tả củ_sạc"

### Service | nhân_viên | POS->NEU (1)
- line 4249: target="nhân_viên" | aspect=Service | current=POS | suggested=NEU
  text: "giá rẻ chất_lượng tốt mong_áp sẽ cải_tiến nhiều hơn trò_chuyện nhân_viên thân_thiện"
  context: "sẽ cải_tiến nhiều hơn trò_chuyện nhân_viên thân_thiện"

### Electronics | máy_hút_bụi | POS->NEU (1)
- line 4319: target="máy_hút_bụi" | aspect=Electronics | current=POS | suggested=NEU
  text: "Quá tốt trong tầm giá. Mặc dù cụm cam dày quá dễ bị va chạm gây bong tróc. Nhưng cũng không ảnh hưởng gì đến chức năng máy_hút_bụi."
  context: "hưởng gì đến chức năng máy_hút_bụi."

### Price | Giá | NEG->POS (1)
- line 4407: target="Giá" | aspect=Price | current=NEG | suggested=POS
  text: "Review nhẹ nè pin trâu chơi game mượt chụp hình thì tùy mỗi người chứ mình thấy tuyệt vời. Tuy nhiên, Giá thì khá cao so mặt bằng chung"
  context: "thấy tuyệt vời. Tuy nhiên, Giá thì khá cao so mặt"

### Electronics | Củ_sạc | POS->NEG (1)
- line 4432: target="Củ_sạc" | aspect=Electronics | current=POS | suggested=NEG
  text: "_VỀ SẢN PHẪM:
Sản phẫm tốt trong tầm giá
Game rất mượt..đôi lúc loag do k ăn mạng
Củ_sạc khoẻ..
_VỀ TGDD:
Nhân viên nhiệt tình, chu đáo, vui vẻ và hái hước, dể thương
Sản phẫm nhập về rất tốt rất nhanh..đến sưa thị là nhận ngay
Nói chung mọi thứ rất tốt...k chê j đc
Very Good"
  context: "loag do k ăn mạng Củ_sạc khoẻ.. _VỀ TGDD: Nhân viên"

### Ship | giao hàng | POS->NEU (1)
- line 4564: target="giao hàng" | aspect=Ship | current=POS | suggested=NEU
  text: "11 1 2026 khá hài_lòng khi chọn mua sản_phẩm tuy còn có những sản_phẩm chưa được ưng_ý về mọi mặt nhưng nhìn_chung thì tương_đối hài_lòng và các chính_sách đổi trả nhanh_chóng thuận_tiện sau một thờigian dùng app từ 2020 đến nay đã sang năm thứ_sáu 2026 hi_vọng shopee sẽ cải_thiện về chất_lượng sản_phẩm hơn_nữa cũng như các chương_trình khuyến_mãi dành cho khách_hàng và giao hàng cẩn_thận chuyên_nghiệp hơn_nữa 2 2 2026 vừa nhận hàng rất là hài_lòng nên lại gửi tặng shopee 5 sao nữa về chất_lượng"
  context: "khuyến_mãi dành cho khách_hàng và giao hàng cẩn_thận chuyên_nghiệp hơn_nữa 2 2"

### Service | Nhân_viên | POS->NEU (1)
- line 4837: target="Nhân_viên" | aspect=Service | current=POS | suggested=NEU
  text: "Wifi bắt yếu nên gọi video hay chập_chờn. Tuy_nhiên, Nhân_viên tư_vấn có tâm và nói chuyện dễ chịu."
  context: "gọi video hay chập_chờn. Tuy_nhiên, Nhân_viên tư_vấn có tâm và nói"

### Ship | ship | NEG->POS (1)
- line 4907: target="ship" | aspect=Ship | current=NEG | suggested=POS
  text: "tiki cái gi ship cũng 44 0 đ hêt bên ladada co 17 0 đ phí ship đắt quá"
  context: "tiki cái gi ship cũng 44 0 đ hêt"

### Fashion | áo | POS->NEU (1)
- line 4922: target="áo" | aspect=Fashion | current=POS | suggested=NEU
  text: "áo rất dày_dặn , đường may cẩn_thận , quần cũng khá oke"
  context: "áo rất dày_dặn , đường may"

### Ship | bưu_tá | POS->NEG (1)
- line 4938: target="bưu_tá" | aspect=Ship | current=POS | suggested=NEG
  text: "Mới mua chiều nay,nhân viên bưu_tá tới nhà nhiệt tình thân thiện. Lúc tầm 3h10 mở ra pin 48% tới 5h38 còn 37% pin mặc dù chỉ thao tác tải ứng dụng Zalo,FB,và test thử YouTube thì e ấy còn 37% pin cảm thấy pin tuột nhanh . Còn lại tất cả đều OK"
  context: "Mới mua chiều nay,nhân viên bưu_tá tới nhà nhiệt tình thân"

### Ship | thời_gian_ship | POS->NEG (1)
- line 4980: target="thời_gian_ship" | aspect=Ship | current=POS | suggested=NEG
  text: "thời_gian_ship thì được báo trước rõ nên nhận hàng thuận tiện, nhìn chung đáng khen"
  context: "thời_gian_ship thì được báo trước rõ"

### Electronics | Vân tay | POS->NEU (1)
- line 5320: target="Vân tay" | aspect=Electronics | current=POS | suggested=NEU
  text: "Chất lượng tuyệt vời với tầm giá 9tr. Vân tay và nhận diện khuôn mặt cực nhạy. Chụp ảnh thì khỏi bàn cải."
  context: "vời với tầm giá 9tr. Vân tay và nhận diện khuôn mặt"

### Service | tiki | POS->NEU (1)
- line 5397: target="tiki" | aspect=Service | current=POS | suggested=NEU
  text: "tiki rất dễ_thương nha , vải mịn mà mát cực ! !"
  context: "tiki rất dễ_thương nha , vải"

### Electronics | máy | POS->NEU (1)
- line 5445: target="máy" | aspect=Electronics | current=POS | suggested=NEU
  text: "Quá tốt trong tầm giá. Mặc dù cụm cam dày quá dễ bị va chạm gây bong tróc. Nhưng cũng không ảnh hưởng gì đến chức năng máy."
  context: "hưởng gì đến chức năng máy."

### Electronics | camera | POS->NEU (1)
- line 5526: target="camera" | aspect=Electronics | current=POS | suggested=NEU
  text: "Máy lướt mượt, cấu hình mạnh trong tầm giá, camera chụp hình rõ... tin tưởng ViVO"
  context: "hình mạnh trong tầm giá, camera chụp hình rõ... tin tưởng"

### App | cập nhật | NEG->POS (1)
- line 5563: target="cập nhật" | aspect=App | current=NEG | suggested=POS
  text: "Quá tuyệt trong tầm giá.chí thiếu mở khoá bằng tai nghe Bluetooth. Tịnh năng có nhưng chưa ad đựoc. Chờ cập nhật..."
  context: "nhưng chưa ad đựoc. Chờ cập nhật..."

### Electronics | máy_hút_bụi | POS->NEG (1)
- line 5608: target="máy_hút_bụi" | aspect=Electronics | current=POS | suggested=NEG
  text: "Sản phẩm tốt phục vụ chu đáo 
Mà a cho em hỏi máy_hút_bụi này có hỗ trợ xạc không dây không anh"
  context: "Mà a cho em hỏi máy_hút_bụi này có hỗ trợ xạc"

### Price | tầm giá | POS->NEG (1)
- line 5693: target="tầm giá" | aspect=Price | current=POS | suggested=NEG
  text: "Sử dụng được 3 tuần gặp lỗi đứng màn hình khi vô app , pin cũng trâu tạm ổn định , hiệu xuất chơi game cũng tạm ổn  , loa cũng được ,quay video màn hình có 2 đường viền đen không full hết màn hình với tầm giá 6tr này việc chơi game thì rất ok"
  context: "full hết màn hình với tầm giá 6tr này việc chơi game"

### Service | tư vấn | POS->NEU (1)
- line 5813: target="tư vấn" | aspect=Service | current=POS | suggested=NEU
  text: "chị nv rất tận tình khi tư vấn, còn về đt thì Mình ms mua hqua và thấy máy xài rất tốt( tốt nhất trog tầm 3tr). Nhìu bạn ns rmC3 này .... nhưg riêng mình thấy máy rất ổn(để mình xài thêm 1 tg nx coi máy có vc j ko), nếu bạn nào có ý định mua đt trong tầm < 3tr thì đây là sự lựa chọn tốt ko thể tốt hơn. Mấy bạn cứ mua nó đi, mọi ng sẽ ko cảm thấy hối tiếc"
  context: "nv rất tận tình khi tư vấn, còn về đt thì Mình"

### Electronics | camera | POS->NEG (1)
- line 5839: target="camera" | aspect=Electronics | current=POS | suggested=NEG
  text: "Sản phẩm tốt cấu hình mạnh ổn trong tầm giá nhân viên tư vấn nhiệt tình được cái camera lồi dễ xước"
  context: "vấn nhiệt tình được cái camera lồi dễ xước"

### Fashion | Áo | POS->NEU (1)
- line 6006: target="Áo" | aspect=Fashion | current=POS | suggested=NEU
  text: "Áo lên form gọn và mặc khá tôn dáng. Bù_lại, Phí_ship đắt làm mình chùn tay."
  context: "Áo lên form gọn và mặc"

### Electronics | Máy | POS->NEU (1)
- line 6047: target="Máy" | aspect=Electronics | current=POS | suggested=NEU
  text: "Mình mới mua iPhone 8plus128gd hôm 13/9/2020 tại cửa hàng 64A đường Nguyễn văn tiết tp thuận an tỉnh bình dương . Nhân viên phục vụ chu đáo dễ thương  . Máy thì quá OK vừa túi tiền"
  context: "chu đáo dễ thương . Máy thì quá OK vừa túi"

### Electronics | cáp_sạc | POS->NEU (1)
- line 6051: target="cáp_sạc" | aspect=Electronics | current=POS | suggested=NEU
  text: "Theo e đánh giá máy tốt .mở 4g từ 6h30 tối .em lên Youtube xem đến 5h30 sáng cáp_sạc còn khoãn 33% .game liên quân .pubg Mobi .rất mượn .chụp hình e ko xài .chỉ yêu game thôi .máy như thế quá ngon rồi .còn mấy bạn thấy sao mình ko bít .máy mình ko cập nhật hệ thông .còn nguyên zin zin y xì"
  context: "Youtube xem đến 5h30 sáng cáp_sạc còn khoãn 33% .game liên"

### Electronics | Linh_kiện_điện_tử | NEG->POS (1)
- line 6210: target="Linh_kiện_điện_tử" | aspect=Electronics | current=NEG | suggested=POS
  text: "Linh_kiện_điện_tử đúng hàng mã,khó dùng,vất vả cho anh giao hàng rồi.
May nó nhận sim thôi tạm vậy 😆😄😅😎.có 190k không đòi hỏi nhiều."
  context: "Linh_kiện_điện_tử đúng hàng mã,khó dùng,vất vả"

### Ship | giao hàng | NEG->POS (1)
- line 6210: target="giao hàng" | aspect=Ship | current=NEG | suggested=POS
  text: "Linh_kiện_điện_tử đúng hàng mã,khó dùng,vất vả cho anh giao hàng rồi.
May nó nhận sim thôi tạm vậy 😆😄😅😎.có 190k không đòi hỏi nhiều."
  context: "mã,khó dùng,vất vả cho anh giao hàng rồi. May nó nhận sim"

### Fashion | form | POS->NEG (1)
- line 6242: target="form" | aspect=Fashion | current=POS | suggested=NEG
  text: "mặc xinh lắm , chủ shop nhiệt_tình hỗ_trợ đổi form"
  context: "chủ shop nhiệt_tình hỗ_trợ đổi form"

### Price | Voucher | POS->NEG (1)
- line 6654: target="Voucher" | aspect=Price | current=POS | suggested=NEG
  text: "Đường_may hơi ẩu nên nhìn rất thiếu chỉn_chu. Xét_về_mặt_khác, Voucher áp vào giảm được kha_khá."
  context: "nhìn rất thiếu chỉn_chu. Xét_về_mặt_khác, Voucher áp vào giảm được kha_khá."

### Ship | bên_ship | POS->NEU (1)
- line 6702: target="bên_ship" | aspect=Ship | current=POS | suggested=NEU
  text: "bên_ship khá ổn, khâu giao trơn tru, vậy là ổn"
  context: "bên_ship khá ổn, khâu giao trơn"

### General | hộp | NEG->POS (1)
- line 6725: target="hộp" | aspect=General | current=NEG | suggested=POS
  text: "hộp đựng sản_phẩm nhái hàng usa , dễ vỡ rách , nghi hộp giả in ở vn rồi đóng_gói"
  context: "hộp đựng sản_phẩm nhái hàng usa"

### Fashion | phom | POS->NEG (1)
- line 6952: target="phom" | aspect=Fashion | current=POS | suggested=NEG
  text: "phom rất ôm dáng độ dài lại vừa đẹp mặc lên tôn dáng vô_cùng"
  context: "phom rất ôm dáng độ dài"

### General | đặt_hàng | POS->NEG (1)
- line 6965: target="đặt_hàng" | aspect=General | current=POS | suggested=NEG
  text: "mình ở đn 12h trưa hôm trc đặt_hàng , 3h chiều_hôm sau tới tay luôn"
  context: "đn 12h trưa hôm trc đặt_hàng , 3h chiều_hôm sau tới"

### Price | khuyến_mãi | NEG->POS (1)
- line 6969: target="khuyến_mãi" | aspect=Price | current=NEG | suggested=POS
  text: "dạo này tải lại thấy mấy mac khuyến_mãi hay freeship gì chán thật_sự"
  context: "tải lại thấy mấy mac khuyến_mãi hay freeship gì chán thật_sự"

### Ship | freeship | NEG->POS (1)
- line 6969: target="freeship" | aspect=Ship | current=NEG | suggested=POS
  text: "dạo này tải lại thấy mấy mac khuyến_mãi hay freeship gì chán thật_sự"
  context: "thấy mấy mac khuyến_mãi hay freeship gì chán thật_sự"

### Service | trả_lời tin nhắn | POS->NEG (1)
- line 6983: target="trả_lời tin nhắn" | aspect=Service | current=POS | suggested=NEG
  text: "đêm_hôm vẫn trả_lời tin nhắn khách"
  context: "đêm_hôm vẫn trả_lời tin nhắn khách"

### App | phần mềm | POS->NEG (1)
- line 7048: target="phần mềm" | aspect=App | current=POS | suggested=NEG
  text: "Sản phẩm tốt, nhưng do miui chưa được tối ưu cho mi note 10 lite nên sẽ có hiện tượng cảm ứng bị đơ lag. mình đã thử thêm ứng dụng đơ vào chế độ game turbo thì không bị đơ cảm ứng của ứng dụng đấy nữa, bạn nào gặp tình trạng này có thể thử. mong TGDD sớm phản hồi lại với bên bảo hành để sớm có bản cập nhật phần mềm xử lý ạ"
  context: "sớm có bản cập nhật phần mềm xử lý ạ"

### Ship | shipper | NEG->POS (1)
- line 7361: target="shipper" | aspect=Ship | current=NEG | suggested=POS
  text: "dùng như cực shipper éo qt đến chủ của hàng j cả họ gọi sau mik bảo chờ mik 2 p thì nó chửi các thứ"
  context: "dùng như cực shipper éo qt đến chủ của"
