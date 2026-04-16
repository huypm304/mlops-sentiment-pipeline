# Autofix Review Group Report
**Input**: data/processed/train_final_v3.autofix_review.jsonl
**Total cases**: 274
**Unique lines**: 172
**Conflict lines**: 172
**Empty-after-cleaning lines**: 74

## Counts By Aspect

| Aspect | Count |
|---|---:|
| Product | 111 |
| <none> | 74 |
| Service | 28 |
| Ship | 25 |
| App | 22 |
| Price | 14 |

## Counts By Reason

| Reason | Count |
|---|---:|
| negative_context | 103 |
| positive_context | 97 |
| empty_after_cleaning | 74 |

## Top Groups

| Group | Count |
|---|---:|
| <none> \| empty_after_cleaning \| empty_after_cleaning | 74 |
| Product \| negative_context \| size_form_fit | 33 |
| Ship \| positive_context \| delivery_speed | 24 |
| App \| negative_context \| app_stability | 16 |
| Product \| positive_context \| generic_product_target | 11 |
| Product \| positive_context \| color_style | 11 |
| Price \| positive_context \| price_level | 8 |
| Product \| negative_context \| battery | 8 |
| Product \| negative_context \| color_style | 7 |
| Product \| negative_context \| generic_product_target | 7 |
| Service \| positive_context \| staff_attitude | 6 |
| Product \| positive_context \| material_quality | 6 |
| Service \| negative_context \| staff_attitude | 6 |
| Product \| positive_context \| battery | 5 |
| Product \| negative_context \| material_quality | 5 |
| App \| positive_context \| app_stability | 5 |
| Service \| positive_context \| shop_reliability | 5 |
| Product \| positive_context \| size_form_fit | 4 |
| Service \| negative_context \| shop_reliability | 4 |
| Price \| negative_context \| price_level | 3 |
| Service \| positive_context \| response_support | 3 |
| Product \| negative_context \| display | 2 |
| Product \| negative_context \| target_máy | 2 |
| Product \| negative_context \| target_hài_lòng | 1 |
| Price \| negative_context \| voucher_promo | 1 |
| Product \| positive_context \| target_mềm | 1 |
| Service \| positive_context \| target_thái_độ | 1 |
| Service \| negative_context \| target_thegioididong | 1 |
| Product \| positive_context \| display | 1 |
| Product \| positive_context \| target_cây_chổi | 1 |

## Group Details

### <none> | empty_after_cleaning | empty_after_cleaning (74)
- line 94 | target="" | sentiment=None | context=""
- line 173 | target="" | sentiment=None | context=""
- line 207 | target="" | sentiment=None | context=""
- line 524 | target="" | sentiment=None | context=""
- line 655 | target="" | sentiment=None | context=""

### Product | negative_context | size_form_fit (33)
- line 77 | target="form" | sentiment=1 | context="form hơi rộng , nhưng chất_lượng"
- line 207 | target="form" | sentiment=1 | context="form hơi nhỏ so với mong_đợi"
- line 655 | target="chất" | sentiment=1 | context="chất thích mà size hơi nhỏ"
- line 1494 | target="size" | sentiment=1 | context="giá mà có size rộng hơn 1 cỡ thì"

### Ship | positive_context | delivery_speed (24)
- line 725 | target="giao" | sentiment=0 | context="tốt và chưa cái nào giao về không đúng yêu_cầu"
- line 843 | target="giao" | sentiment=0 | context="chất_liệu tạm được nhưng giao không đúng mẫu đã đặt"
- line 1767 | target="ship" | sentiment=0 | context="ship không đúng màu"
- line 2171 | target="giao" | sentiment=0 | context="sản_phẩm giao không đúng yêu_cầu"
- line 2534 | target="giao" | sentiment=0 | context="lừa_đảo giao không đúng mẫu chat không"

### App | negative_context | app_stability (16)
- line 807 | target="ứng_dụng" | sentiment=1 | context="dễ sử_dụng giá_cả cả trên ứng_dụng cũng rẻ"
- line 1581 | target="phần mềm" | sentiment=1 | context="nên cấp nhật lại phần mềm.may chơi gêm hơi yếu. màn"
- line 1685 | target="ứng_dụng" | sentiment=1 | context="ứng_dụng này rất ưng_ý toàn có"
- line 2038 | target="ứng_dụng" | sentiment=1 | context="ứng_dụng bị không phản_hồi hay dừng"

### Product | positive_context | generic_product_target (11)
- line 725 | target="hàng" | sentiment=0 | context="người lười mua_sắm ngoài đường hàng tốt và chưa cái nào"
- line 2112 | target="sản_phẩm" | sentiment=0 | context="bán và giao không đúng sản_phẩm tôi đặt mà không giải_quyết"
- line 2171 | target="sản_phẩm" | sentiment=0 | context="sản_phẩm giao không đúng yêu_cầu"
- line 3105 | target="áo" | sentiment=0 | context="dth với nhiệt_tình ghê tuy áo không dài như mình tưởng"
- line 4052 | target="sản_phẩm" | sentiment=0 | context="rất uy_tính giao hàng_không đúng sản_phẩm có_thể trả hàng lại được"

### Product | positive_context | color_style (11)
- line 1767 | target="màu" | sentiment=0 | context="ship không đúng màu"
- line 2321 | target="màu" | sentiment=0 | context="giao kg đúng màu đã chọn"
- line 2534 | target="mẫu" | sentiment=0 | context="lừa_đảo giao không đúng mẫu chat không ai trả_lời"
- line 3030 | target="quần" | sentiment=0 | context="giao quần không đúng màu"
- line 3834 | target="mẫu" | sentiment=0 | context="giao không đúng mẫu đặt , nghĩ sao đặt"

### Price | positive_context | price_level (8)
- line 1406 | target="giá" | sentiment=0 | context="tốt . không đáng với giá 320k . chân_không dang được"
- line 2575 | target="giá_như" | sentiment=0 | context="nép gấp không đều nhưng giá_như thế hợp_lý rồi"
- line 2739 | target="giá" | sentiment=0 | context="giao hàng khá ổn nhưng giá không quá tốt"
- line 3909 | target="giá" | sentiment=0 | context="quá cao mua cái hàng giá có 15 k mà tổng_trả"
- line 4179 | target="tầm giá" | sentiment=0 | context="4,5tr quá đắt xaeomi với tầm giá 4,5tr dùng tốt hơn nhiều"

### Product | negative_context | battery (8)
- line 2275 | target="pin" | sentiment=1 | context="ko lag giật tuy nhiên pin ko trâu như tưởng tượng"
- line 3230 | target="pin" | sentiment=1 | context="gì cả. mới mua về pin còn mới, nên tụt hơi"
- line 3687 | target="linh_kiện_điện_tử" | sentiment=1 | context="cũ 8 tháng bảo hành .linh_kiện_điện_tử sạc đầy bib 1 tiếng"
- line 4350 | target="máy" | sentiment=1 | context="cũ 8 tháng bảo hành .máy sạc đầy bib 1 tiếng"
- line 6056 | target="Pin" | sentiment=1 | context="bể lun hay dính . pin cũg đc nhưg ko xài"

### Product | negative_context | color_style (7)
- line 917 | target="chất" | sentiment=1 | context="chất sờ cũng mềm , nhưng"
- line 1036 | target="mẫu" | sentiment=1 | context="mẫu cũng đa_dạng"
- line 3544 | target="giày" | sentiment=1 | context="cũng xinh , đi với giày hợp luôn"
- line 3980 | target="chip" | sentiment=1 | context="dụ con a51 giá 8tr chip cũng bt, viền nhựa lưng"
- line 4346 | target="màu" | sentiment=1 | context="sẽ đặt thêm màu khác trong đơn hàng tới"

### Product | negative_context | generic_product_target (7)
- line 1287 | target="hàng" | sentiment=1 | context="lần nào mua hàng của c cũng ưng hết"
- line 4241 | target="hàng" | sentiment=1 | context="tiếp_nhận đơn hàng và đưa cho bên vận_chuyển"
- line 4641 | target="hàng" | sentiment=1 | context="nhưng mỗi tội lạc đơn hàng phải đặt lần 2 bù"
- line 5205 | target="sản_phẩm" | sentiment=1 | context="giá các sản_phẩm cao hơn các trang mua_sắm"
- line 6013 | target="chất" | sentiment=1 | context="52kg mặc không vừa , chất lại không co_giãn thành_ra mua"

### Service | positive_context | staff_attitude (6)
- line 313 | target="shop" | sentiment=0 | context="chuột không ưng_ý lắm nhưng shop phục_vụ nhanh"
- line 3209 | target="nhân viên" | sentiment=0 | context="cấu hình phù hợp từ nhân viên văn phòng bình thường, sinh"
- line 3918 | target="Nhân viên" | sentiment=0 | context="tuần 1 lần lên sửa. nhân viên dễ thương"
- line 4416 | target="phục vụ" | sentiment=0 | context="thấy ok nhưng thái độ phục vụ của a kỹ thuật thì"
- line 6008 | target="phục vụ" | sentiment=0 | context="thấy ok nhưng thái độ phục vụ của a kỹ thuật thì"

### Product | positive_context | material_quality (6)
- line 344 | target="đường may" | sentiment=0 | context="với giá thì ổn nhưng đường may xấu , chỉ lòi ra"
- line 780 | target="chất" | sentiment=0 | context="chất không mịn , nhưng ok"
- line 2516 | target="vải" | sentiment=0 | context="vải áo chưa thật_sự tốt lắm"
- line 4465 | target="sản_phẩm" | sentiment=0 | context="sản_phẩm làm cứng lên thì ok"
- line 5596 | target="màu" | sentiment=0 | context="giao không đúng màu . đặt màu hồng mà"

### Service | negative_context | staff_attitude (6)
- line 606 | target="nhân viên" | sentiment=1 | context="lỗi gì. các anh chị nhân viên phục vụ rất tận tình"
- line 984 | target="nhân viên" | sentiment=1 | context="lỗi gì. các anh chị nhân viên phục vụ rất tận tình"
- line 2270 | target="nhân viên" | sentiment=1 | context="phát hiện lỗi gì , nhân viên ttdd thân thiện phục vụ"
- line 2520 | target="nhân viên lẫn" | sentiment=1 | context="hài lòng nhân viên lẫn sản phẩm:-).nhưng cũng phải đợi"
- line 3833 | target="shop" | sentiment=1 | context="vẫn cho shop 5 sao vì phục_vụ cũng"

### Product | positive_context | battery (5)
- line 107 | target="linh_kiện_điện_tử" | sentiment=0 | context="ổn để chiến game + linh_kiện_điện_tử trâu. đồ phân giải nói"
- line 4209 | target="màn hình" | sentiment=0 | context="mới ổn, cam chưa tốt, màn hình đẹp pin được 2 ngày"
- line 6235 | target="pin" | sentiment=0 | context="chơi pubg mất mẹ 12% pin, nhưng ok đây hiểu. nhưng"
- line 6415 | target="vân tay" | sentiment=0 | context="đến chơi game k có vân tay 5.000 k có sạc nhanh"
- line 6566 | target="pin" | sentiment=0 | context="pin gì mà tuột nhanh dữ"

### Product | negative_context | material_quality (5)
- line 1555 | target="chất_liệu" | sentiment=1 | context="nhất là hàng của tiki chất_liệu tuyệt_vời dù_sao cũng mong tiki"
- line 1770 | target="ổ_cứng" | sentiment=1 | context="chưa biết như nào nhưng ổ_cứng cứ 3p tụt 1%. ☺️"
- line 1926 | target="chất_lượng" | sentiment=1 | context="nhất là hàng của tiki chất_lượng tuyệt_vời dù_sao cũng mong tiki"
- line 5913 | target="chất_lượng sản_phẩm" | sentiment=1 | context="hi_vọng shopee sẽ cải_thiện về chất_lượng sản_phẩm hơn_nữa cũng như các chương_trình"
- line 7357 | target="chất_lượng" | sentiment=1 | context="cũng y_chang trên cửa_hàng bán chất_lượng"

### App | positive_context | app_stability (5)
- line 3890 | target="ứng dụng" | sentiment=0 | context="facebook và nhắn messenger, các ứng dụng ngầm khác đã tắt hết,"
- line 3909 | target="app" | sentiment=0 | context="mà tổng_trả gần 50 k app như cái l"
- line 4899 | target="app" | sentiment=0 | context="nhanh, tắt màn hình(không có app chạy ngầm) để không 2"
- line 6039 | target="Ứng dụng" | sentiment=0 | context="ứng dụng hằng ngày chưa ổn định"
- line 6064 | target="app" | sentiment=0 | context="hàng tương đối tốt nhưng app không quá tốt"

### Service | positive_context | shop_reliability (5)
- line 4900 | target="shop" | sentiment=0 | context="chất vải oki . nhưng shop như kiểu thải các áo"
- line 5000 | target="shop" | sentiment=0 | context="cơ_mà shop gói chưa cẩn_thận nên làm"
- line 5152 | target="shop" | sentiment=0 | context="shop giao không đúng hàng"
- line 5490 | target="shop" | sentiment=0 | context="vải đường may ok nhưng shop chưa tận_tâm , mình nhờ"
- line 6219 | target="shop" | sentiment=0 | context="shop giao không đúng size"

### Product | positive_context | size_form_fit (4)
- line 94 | target="form" | sentiment=0 | context="form giày cứng_cáp . đóng_gói ổn"
- line 3688 | target="hàng" | sentiment=0 | context="giao hàng_không đúng kích_cỡ kích_thước hàng đôi dày 1 nhỏ 1"
- line 5285 | target="màu" | sentiment=0 | context="giao không đúng màu , có 1cái giao size"
- line 6219 | target="size" | sentiment=0 | context="shop giao không đúng size"

### Service | negative_context | shop_reliability (4)
- line 524 | target="shop" | sentiment=1 | context="là đặt 2 chiếc , shop cũng có tâm là chỉ"
- line 2666 | target="shop" | sentiment=1 | context="không hài_lòng việc đã nhắn shop không ghi rõ thông_tin ngoài"
- line 3817 | target="shop" | sentiment=1 | context="là ních không vừa ủng_hộ shop bán hàng 5"
- line 7200 | target="shop" | sentiment=1 | context="hơi rộng mà thôi cho shop 5 sak"

### Price | negative_context | price_level (3)
- line 1494 | target="giá" | sentiment=1 | context="giá mà có size rộng hơn"
- line 5725 | target="sale" | sentiment=1 | context="sale mạnh kinh_khủng_shipper lúc_nào cũng dễ_thương"
- line 5825 | target="giá" | sentiment=1 | context="cũng có và tiện_lợi và giá hợp_lí"

### Service | positive_context | response_support (3)
- line 1894 | target="shop" | sentiment=0 | context="giá_cả hợp_lý , nhắn_tin cho shop không thấy trả_lời cho shop"
- line 5957 | target="khách_hàng" | sentiment=0 | context="toàn bot nói nuốt tiền khách_hàng gọi lên tổng_đài thì bị"
- line 6980 | target="trả_lời" | sentiment=0 | context="hình nhưng nên cải_thiện hãy trả_lời ib nhiệt_tình chút ib không"

### Product | negative_context | display (2)
- line 311 | target="màn hình" | sentiment=1 | context="lòng lắm là độ sáng màn hình. mắt mình yếu nên chỉnh"
- line 7063 | target="chuột" | sentiment=1 | context="lòng lắm là độ sáng chuột. mắt mình yếu nên chỉnh"

### Product | negative_context | target_máy (2)
- line 2810 | target="máy" | sentiment=1 | context="game nặng thì tiền mua máy cũng phải nặng nhé !"
- line 7166 | target="Máy" | sentiment=1 | context="máy thấy cũng dk tùy giá"

### Product | negative_context | target_hài_lòng (1)
- line 173 | target="hài_lòng" | sentiment=1 | context="lần nào mua cũng hài_lòng"

### Price | negative_context | voucher_promo (1)
- line 1345 | target="khuyến_mãi" | sentiment=1 | context="chương_trình miễn_phí síp cũng như khuyến_mãi"

### Product | positive_context | target_mềm (1)
- line 2004 | target="mềm" | sentiment=0 | context="gối rất mềm , giá_cả hợp_lý"

### Service | positive_context | target_thái_độ (1)
- line 3170 | target="thái_độ" | sentiment=0 | context="tất đẹp nhưng thái_độ của ship quá chán !"

### Service | negative_context | target_thegioididong (1)
- line 3632 | target="thegioididong" | sentiment=1 | context="mỹ nhưng cũng hay lên thegioididong đọc tin tức công nghệ,"

### Product | positive_context | display (1)
- line 3632 | target="màn hình" | sentiment=0 | context="máy rất đẹp, được dán màn hình sẵn như s10+. trải nghiệm"

### Product | positive_context | target_cây_chổi (1)
- line 4068 | target="cây_chổi" | sentiment=0 | context="người lười mua_sắm ngoài đường cây_chổi tốt và chưa cái nào"

### Price | positive_context | money_value (1)
- line 4409 | target="tiền" | sentiment=0 | context="xài kg ngon với số tiền mình bỏ ra hát nhạc"

### Service | negative_context | target_sendo (1)
- line 4724 | target="sendo" | sentiment=1 | context="đặt 3 cái áo của sendo rồi , lần nào cũng"

### Product | positive_context | target_cskh (1)
- line 4815 | target="cskh" | sentiment=0 | context="cskh chưa tốt"

### App | negative_context | app_update_os (1)
- line 4845 | target="cập nhật" | sentiment=1 | context="mọi người nói ko nên cập nhật miui nên thôi k cập"

### Price | negative_context | money_value (1)
- line 5407 | target="tiền" | sentiment=1 | context="bớt. nhưng cũng vừa túi tiền rồi.😀"

### Product | positive_context | target_sóng (1)
- line 5461 | target="sóng" | sentiment=0 | context="thì lâu lâu thì mất sóng .còn lại cx ok nhưng"

### Product | positive_context | target_đóng_gói (1)
- line 5792 | target="đóng_gói" | sentiment=0 | context="đóng_gói chưa cẩn_thận lắm"

### Product | negative_context | target_sáp (1)
- line 5803 | target="sáp" | sentiment=1 | context="sáp loại nào cũng thơm"

### Product | positive_context | camera (1)
- line 5870 | target="camera" | sentiment=0 | context="rất ok trong tầm giá camera thì bình thường rất hài"

### Product | negative_context | target_quần_lót (1)
- line 6663 | target="quần_lót" | sentiment=1 | context="quần_lót mặc 1 lần vậy cũng"

### Service | negative_context | target_cửa_hàng (1)
- line 6754 | target="cửa hàng" | sentiment=1 | context="hề nóng luôn. lúc đến cửa hàng là tính mua note 8"

### Ship | negative_context | delivery_speed (1)
- line 6912 | target="giao hàng" | sentiment=1 | context="giao tôi liên_lạc với nhân_viên giao hàng theo đơn hàng 2 ngày"
