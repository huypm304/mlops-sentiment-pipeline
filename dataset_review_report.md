# Dataset Review Report

Nguon du lieu: dataset.jsonl

Luu y:
- Day la bao cao soat loi de review nhan, khong phai ket luan rang moi dong duoc liet keu deu sai 100%.
- Cac nhom ben duoi la nhung dong co xac suat cao can duoc xem lai truoc khi train final.
- Line number tham chieu theo file dataset.jsonl hien tai.

## Tong quan

- Total rows: 10424
- Conflicting duplicate texts: 0
- empty_aspects_with_polar_global: 2398
- ship_mention_without_ship_label: 87
- negative_global_with_positive_aspect: 68
- positive_global_with_negative_aspect: 265
- ship_labeled_positive_but_negative_text: 159
- ship_labeled_negative_but_positive_text: 79
- price_label_without_clear_price_signal: 208
- very_short_text: 732

## Conflicting duplicate texts

None

## Empty Aspects But Polar Global

Count: 2398

- line 1: global=1 aspects=[] aspect_sentiment={} text=tốt không có gì để chê
- line 4: global=0 aspects=[] aspect_sentiment={} text=what the hell does it have get the hell out of here
- line 7: global=1 aspects=[] aspect_sentiment={} text=gói shopee_vip tuyệt_vời
- line 12: global=0 aspects=[] aspect_sentiment={} text=khá tệ
- line 23: global=0 aspects=[] aspect_sentiment={} text=dẹp đi làm_ăn chẳng ra gì
- line 26: global=1 aspects=[] aspect_sentiment={} text=chưa dừng dùng giúp bạn sao
- line 28: global=1 aspects=[] aspect_sentiment={} text=rất là hài_lòng với cửa_hàng
- line 37: global=1 aspects=[] aspect_sentiment={} text=tam_ok
- line 39: global=1 aspects=[] aspect_sentiment={} text=cần thêm nhiều sách_ngôn_tình trung_quốc
- line 45: global=1 aspects=[] aspect_sentiment={} text=quần đẹp chất mềm không nhăn xù đường kim_mũi chỉ sắc nét sẽ mua ủng_hộ tiếp thêm đủ màu
- line 47: global=0 aspects=[] aspect_sentiment={} text=nhót trừ tiền ngân_hàng_không thông_báo gì
- line 48: global=1 aspects=[] aspect_sentiment={} text=hưưx_ích
- line 54: global=1 aspects=[] aspect_sentiment={} text=tốt cho người dùng
- line 60: global=0 aspects=[] aspect_sentiment={} text=tự_nhiên đánh_mã cr01 dù không làm_gì bất_thường chán
- line 61: global=1 aspects=[] aspect_sentiment={} text=có nhiều sản_phẫm nhìn rất thích nhưng cài_đặt rồi mà vô mua không được
- line 62: global=1 aspects=[] aspect_sentiment={} text=rất hài_lòng mình có ý_kiến như_vầy kẽm nhung trộn nhìu_mẫu thì mọi người sẽ mua nhìu hơn ạ
- line 64: global=0 aspects=[] aspect_sentiment={} text=quảng_cáo kg cần_thiết làm_phiền khi xem bài
- line 68: global=1 aspects=[] aspect_sentiment={} text=rất hay và tuyệt_vời
- line 72: global=1 aspects=[] aspect_sentiment={} text=hay không_thể nói được luôn
- line 84: global=0 aspects=[] aspect_sentiment={} text=tệ bắt phải thanh_toán bằng ví này ví kia trong khi ngt không có atm thí_s
- line 85: global=1 aspects=[] aspect_sentiment={} text=tuyet voi
- line 93: global=1 aspects=[] aspect_sentiment={} text=rất tiện_lợi và hữu_ích
- line 94: global=0 aspects=[] aspect_sentiment={} text=không nghe dk tn thoai không goi dk mest không dung dk zalo
- line 104: global=1 aspects=[] aspect_sentiment={} text=tiên_lợi
- line 118: global=1 aspects=[] aspect_sentiment={} text=rất tiện
- line 120: global=1 aspects=[] aspect_sentiment={} text=ổn áp
- line 121: global=0 aspects=[] aspect_sentiment={} text=toàn giao_đơn đi lung_tung
- line 122: global=1 aspects=[] aspect_sentiment={} text=rất hay và tiện
- line 123: global=1 aspects=[] aspect_sentiment={} text=mỗi tội hình_ảnh và hiện_thực khác hoàn_toàn
- line 138: global=0 aspects=[] aspect_sentiment={} text=tôi đặt bộ quần_áo nam mà gửi cho tôi bộ quần_áo trẻ_em nữ
- line 142: global=0 aspects=[] aspect_sentiment={} text=đổi chương_trình km riết chả có cái gì ra hồn
- line 143: global=1 aspects=[] aspect_sentiment={} text=nhiều mặt_hành_giá lại tốt
- line 144: global=1 aspects=[] aspect_sentiment={} text=dung cham chuc luon vui_ve
- line 148: global=0 aspects=[] aspect_sentiment={} text=nhảy thông_báo khác gì lừa_đảo đâu
- line 149: global=0 aspects=[] aspect_sentiment={} text=thằng loz code trò_chơi lấy xu_nguu vl
- line 151: global=1 aspects=[] aspect_sentiment={} text=quá được
- line 152: global=0 aspects=[] aspect_sentiment={} text=mẹ đặt_hàng dell được
- line 159: global=1 aspects=[] aspect_sentiment={} text=nó lại là nét luôn
- line 167: global=1 aspects=[] aspect_sentiment={} text=tốt bổ_ích
- line 169: global=0 aspects=[] aspect_sentiment={} text=số điện_thoại đã bị ai chiếm_dụng và không_thể thêm số điện_thoại đó được cứ yêu_cầu xác_minh facebook xong kêu người dùng không tồn_tại
- line 170: global=0 aspects=[] aspect_sentiment={} text=muốn tìm nạp điện_thoại mà giấu kĩ quá đề_nghị để ra menu chính cho dễ tìm muốn nạp mà tìm mãi mới được rất bất_tiện
- line 179: global=0 aspects=[] aspect_sentiment={} text=sao đòi_hỏi số điện_thoại mới nữa là sao hả trời lấy đâu ra thêm số nữa vậy bắt tôi mua thêm số điện_thoại nữa hả_lam gì đòi_hỏi vô_lý vậy bị điên rồi đòi_hỏi những thủ_tục rờm_rà vớ vẩn_phí thời_gian
- line 184: global=0 aspects=[] aspect_sentiment={} text=rồi gạo chừng nào có
- line 185: global=0 aspects=[] aspect_sentiment={} text=đồ rất ok
- line 190: global=1 aspects=[] aspect_sentiment={} text=ý_kiến của mình để mình có thẩm_quyền xửa ngày ý_tưởng về thì đi làm
- line 198: global=0 aspects=[] aspect_sentiment={} text=như sịt
- line 211: global=1 aspects=[] aspect_sentiment={} text=ủng_hộ người viet
- line 214: global=1 aspects=[] aspect_sentiment={} text=tất_cả đều ok cho 5
- line 219: global=0 aspects=[] aspect_sentiment={} text=xem thường người sử_dụng lý_do lý_trấu bảo mật
- line 221: global=0 aspects=[] aspect_sentiment={} text=tạo acc mới app_mã vô_sao lại hủy_đơn của tôi
- line 234: global=0 aspects=[] aspect_sentiment={} text=đắp quá
- line 236: global=1 aspects=[] aspect_sentiment={} text=ok rất hài_lòng
- line 237: global=1 aspects=[] aspect_sentiment={} text=hay qua tuyet voi mn ah
- line 250: global=1 aspects=[] aspect_sentiment={} text=trải_nghiệm là thik
- line 251: global=0 aspects=[] aspect_sentiment={} text=đg chơi hiện_thị cai_l j không
- line 252: global=1 aspects=[] aspect_sentiment={} text=áp_ok nha_tải nhanh lắm luôn á
- line 255: global=0 aspects=[] aspect_sentiment={} text=quá kém
- line 259: global=0 aspects=[] aspect_sentiment={} text=ap nđb xác_nhận đell_j lắm thế
- line 262: global=1 aspects=[] aspect_sentiment={} text=tạm ổn nhiều cái hơi tệ nhưng nhìn_chung thì khá ổn
- line 265: global=1 aspects=[] aspect_sentiment={} text=gian_hàng nhanh_chóng
- line 272: global=0 aspects=[] aspect_sentiment={} text=quản_cáo rầm_rộ vậy_mà thực_tế thì
- line 278: global=0 aspects=[] aspect_sentiment={} text=biển tân_thành rất nhiều rác ok
- line 283: global=1 aspects=[] aspect_sentiment={} text=thích thế
- line 285: global=0 aspects=[] aspect_sentiment={} text=dễ sập load lâu như quỉ
- line 288: global=1 aspects=[] aspect_sentiment={} text=tôi rất vui bởi_vì trong đây có đầy_đủ các thứ tôi cần
- line 289: global=1 aspects=[] aspect_sentiment={} text=thư_viện mua_sắm
- line 293: global=1 aspects=[] aspect_sentiment={} text=ok cài_đặt được
- line 295: global=1 aspects=[] aspect_sentiment={} text=tôi rất thích và rất hài_lòng
- line 296: global=0 aspects=[] aspect_sentiment={} text=méo chấp_nhận được
- line 299: global=1 aspects=[] aspect_sentiment={} text=ui tín tốt
- line 310: global=0 aspects=[] aspect_sentiment={} text=quản_cáo trên youtube quá nhiều gây phản_cảm
- line 314: global=0 aspects=[] aspect_sentiment={} text=như lol
- line 317: global=1 aspects=[] aspect_sentiment={} text=tôi muốn có một chiếc tecno pova 2
- line 320: global=1 aspects=[] aspect_sentiment={} text=hài_lòng ạ
- line 331: global=0 aspects=[] aspect_sentiment={} text=tiê n_phí vâ n chuyê n râ t đă t chê
- line 333: global=1 aspects=[] aspect_sentiment={} text=ô kê tuyệt_vời
- line 338: global=0 aspects=[] aspect_sentiment={} text=tôi bị cr01 không biết vì lý_do là gì cảm_thấy lazada_tệ quá
- line 339: global=0 aspects=[] aspect_sentiment={} text=mua bộ quần_áo nam nhìn_hình thì đẹp gửi cái quần_bò rộng thùng thình_áo của phủ nữ_cư như cái dẻ lau nhà
- line 343: global=1 aspects=[] aspect_sentiment={} text=oke lala
- line 347: global=1 aspects=[] aspect_sentiment={} text=rất tuyệt_vời tiện_lợi thuận_tiện và khoa_học cảm_ơn các bạn rất nhiều

## Ship Mention Without Ship Label

Count: 87

- line 6: global=0 aspects=['Product', 'App'] aspect_sentiment={'Product': 0, 'App': 0} text=cửa_hàng ơi bảo shipe đừng lấy hàng ngt_dii với_lại toàn lỗi m04
- line 82: global=1 aspects=['Product', 'App'] aspect_sentiment={'Product': 1, 'App': 1} text=mấy app kia shiper đứng ngoài đầu hẻm gọi mình ra còn shiper tiki đứng trc cửa kêu mình dậy lấy hàng lun
- line 111: global=1 aspects=['Service'] aspect_sentiment={'Service': 1} text=sàn giao_dịch rất tốt cho khách_hàng
- line 113: global=0 aspects=['Price'] aspect_sentiment={'Price': 0} text=cho mã_ng mới đặt_hàng không giao_hủy luôn mã giảm hủy còn phải đợi làm_ăn như qq
- line 121: global=0 aspects=[] aspect_sentiment={} text=toàn giao_đơn đi lung_tung
- line 177: global=0 aspects=['App'] aspect_sentiment={'App': 0} text=chữ giao_diện thì nhỏ_tí tí mày làm app để cho ai xem tài_khoản thì méo có xem được ngày tạo bao_nhiêu cửa_hàng thì méo xem được số nó tên gì tạo lâu chưa giao_diện xấu hoắc
- line 217: global=0 aspects=['Price', 'App'] aspect_sentiment={'Price': 0, 'App': 0} text=làm_ăn hơn mấy cha lừa_đảo quả tk google t đổi máy mới tải laz về đn vô thì bảo_khóa vừa lụm được voucher thì bảo giao_dịch mờ_ám không_chỉ 1 mình t đâu ai lập_trình cái app này mà ngu dữ v làm như muốn lùa người dùng về sài_shopee hay j_ý
- line 240: global=0 aspects=['Price', 'App'] aspect_sentiment={'Price': 0, 'App': 0} text=tự_nhiên đang dùng bình_thường xong đùng_một ngày tk tôi không còn sử_dụng mã freeship được nữa không có mã_frsh luôn mặc_dù có mục_voucher làm ơn xem_xét lại dùm
- line 330: global=1 aspects=['Product', 'Service'] aspect_sentiment={'Product': 1, 'Service': 1} text=rất là tốt đặt_hàng rất chất_lượng nhân_viên bán hàng chu_đáo giao_hành siêu nhanh nói_chung là rất là tuyệt_vời
- line 433: global=1 aspects=['Product', 'App'] aspect_sentiment={'Product': 1, 'App': 1} text=dịch_vụ tốt hàng chất_lượng và giá_cả phải_chăng cùng giao_diện dễ dùng đâg thực_sự là một app vượt mạt shoppe
- line 5577: global=0 aspects=['Product', 'App'] aspect_sentiment={'Product': 0, 'App': 0} text=sau cập_nhật giao_diện tiki khó mua hàng quá không thấy được tên cửa_hàng_không tính được khuyến_mãi muốn mua hàng là phải đăng_nhập lại qua 2 3 bước mới được vào mua hàng rồi tới lúc thanh_toán cũng xác_minh này nọ mua hàng mà lu_bu vậy ai muốn mua nữa mỗi lần vào mua hàng là nhức đầu_rối quá rối_tốn hơn 30 p vẫn không mua được doanh_nghiệp cải_tiến ngày_càng tốt hơn mà này cải_tiến xong khách hết mua hàng được luôn gắn_bó với tiki hơn 10 năm rồi mà giờ phải bỏ thôi đúng chán
- line 5589: global=2 aspects=['App'] aspect_sentiment={'App': 2} text=app quá tệ hút máu người dùng giao_diện lag_mạng thì tốt mà viedeo_tải lên cũng không được dịch_vụ quá tệ
- line 5659: global=0 aspects=['Price', 'App'] aspect_sentiment={'Price': 0, 'App': 0} text=chính_sách về tài_khoản quá tệ tài_khoản dùng 8 năm mà khóa hết freeship cả banner trạm bank cũng mất hết vậy thì mua_bán kiểu gì
- line 5700: global=1 aspects=['Price'] aspect_sentiment={'Price': 0} text=lazada sao không cho freeship vậy ạ
- line 5729: global=0 aspects=['Price'] aspect_sentiment={'Price': 0} text=chả có cái freeship nào quảng_cáo thì nhiều mua shoppe ngon hơn
- line 5742: global=0 aspects=['Service', 'App'] aspect_sentiment={'Service': 0, 'App': 0} text=tiki hãm loz bỏ mẹ chả có thiện_cảm gì cả giao_diện ngứa_mắt phục_vụ thậm_tệ khiếu_nại lâu nói_chung đừng sd mn ạ
- line 5788: global=0 aspects=['Price', 'App'] aspect_sentiment={'Price': 0, 'App': 0} text=tớ có hai tài_khoản đăng_nhập qua_lại bây_giờ shopee khóa luôn đến cái mã freeship nó cũng không cho sử_dụng nữa trong khi mình đã mua shopee vip
- line 5814: global=1 aspects=['Product', 'Price', 'App'] aspect_sentiment={'Product': 0, 'Price': 0, 'App': 0} text=1 các đầu_sách và sản_phẩm khác chưa thật_sự đa_dạng giá còn cao khó cạnh_tranh với sàn khác ít_mã khuyến_mãi có_thể áp_dụng 2 giao_diện kết_quả tìm_kiếm trải dài 1 cột như_vậy hơi khó nhìn được tổng_quan 3 rất hi_vọng các sàn thương_mại_điện_tử của việt_nam như tiki sendo sẽ phát_triển hơn_nữa
- line 5892: global=0 aspects=[] aspect_sentiment={} text=đặt_hàng càng_ngày_càng chán_sàn giao_dịch điện_tử giờ kiểu không cần khách hay sao ý
- line 5898: global=1 aspects=['Service'] aspect_sentiment={'Service': 1} text=minh thich shopee mua hang nhanh giao_dung hang mau

## Negative Global With Positive Aspect

Count: 68

- line 79: global=0 aspects=['Ship', 'Service', 'App'] aspect_sentiment={'Ship': 1, 'Service': 1, 'App': 1} text=shipper giao hàng_không đúng hẹn dù trên app hiển_thị giao trong ngày gọi lên nv chăm_sóc khách_hàng_không giải_quyết được vấn_đề mất uy_tín với khách_hàng
- line 92: global=0 aspects=['Service', 'App'] aspect_sentiment={'Service': 0, 'App': 1} text=tôi rất thất_vọng đặt_hàng hơn 2 tuần rồi vẫn chưa có hỏi thì cứ xin_lỗi rồi bảo chờ chờ cho tới bao_giờ chăm_sóc khách_hàng cho có chứ làm được gì đâu ứng_dụng này mất uy_tín như thế thì toang
- line 126: global=0 aspects=['Product', 'Ship', 'Service'] aspect_sentiment={'Product': 0, 'Ship': 0, 'Service': 1} text=bị hủy 2 đơn vì lý_do shop và shopee tự hủy tôi mua các hàng khác bình_thường không có gian_lận gì giờ đơn_shop đặt sau 2 ngày bị hủy vì hết hàng và giờ shopee hủy đơn khác vì lý_do giao_dịch bất_thường trước_đây rất ổn tôn_trọng khách_hàng mà sao giờ khách_hàng bị coi_thường vậy
- line 135: global=0 aspects=['App'] aspect_sentiment={'App': 1} text=mua_sắm thì tiện nhưng càng_ngày_càng ngốn ram
- line 161: global=0 aspects=['Product', 'App'] aspect_sentiment={'Product': 1, 'App': 0} text=lazada dạo này thật_sự quá là vô_lý đăng_nhập tài_khoản kêu là tài_khoản của bạn bị khóa vì lý_do bảo_mật ull cc gì đấy không rõ nữa lấy sdt để tạo tài_khoản mới cũng kêu là tài_khoản bị khóa vì lý_do bảo_mật lấy sdt khác tạo cũng vẫn bị nãy_giờ tao bị khóa 6 cái tài_khoản rồi đó nha lazada ạ tôi khuyên những anh_em nào đang có ý_định tải app về sử_dụng mua hàng thì tốt nhất đừng tải_tải về cũng không đăng_ký đăng_nhập được tài_khoản đâu chỉ tốn dung_lượng tốn thời_gian của anh_em mà thôi
- line 202: global=0 aspects=['Product', 'Ship', 'Service', 'App'] aspect_sentiment={'Product': 1, 'Ship': 1, 'Service': 1, 'App': 1} text=app riết như muốn phá_sản muốn gặp nhân_viên gõ kiểu gì cũng là con ai trả_lời dẹp tiệm luôn cho_rồi ngta giao hàng ngày_càng nhanh còn này ngày_càng đi lùi
- line 263: global=0 aspects=['Ship'] aspect_sentiment={'Ship': 1} text=không hài_lòng lắm về đơn_vị vận_chuyển
- line 448: global=0 aspects=['Price', 'Ship'] aspect_sentiment={'Price': 1, 'Ship': 1} text=đó giờ xài ổn giờ bắt ra tủ_đồ lấy hoặc chịu ship cao dù hỏa_tốc vẫn mất 2 ngày chả hiểu
- line 465: global=0 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 0, 'Ship': 1} text=sale mà để ghn giao thì tốt nhất là khỏi sale vì có giao đâu mà nhận cả chục đơn dính mỗi 2 đơn_ngâm nữa tháng vẫn chưa thấy hàng hết kho này đến kho khác ghi khách không nghe máy chặn số trong khi đơn quốc_tế spx đặt sau cả hơn chục ngày lại nhận trước
- line 475: global=0 aspects=['Product'] aspect_sentiment={'Product': 1} text=boom hàng ell uy_tín
- line 5524: global=0 aspects=['Product', 'Price'] aspect_sentiment={'Product': 1, 'Price': 0} text=đang yên_lành đổi chính_sách làm_giá tăng lên còn voucher thì không có nên giá cao hơn shoppee nên qua đó mua hàng ok hơn lại thêm đòi cd khi đặt_hàng nên bay bay lazada
- line 5592: global=0 aspects=['Price', 'Ship', 'App'] aspect_sentiment={'Price': 0, 'Ship': 0, 'App': 1} text=cày xu rất vô_nghĩa_nha muốn xài mã km cũng rất quoằn xu_cày được nhưng chỉ_tiêu được 3 5 giá_trị đơn có cửa_hàng còn không cho xài xu_vô nghĩa_mã km phải lướt chỗ này chỗ kia kiếm chứ không có sẵn lúc thanh_toàn rất mất thời_gian app nào cũng tối_ưu cho khách chốt đơn cho nhanh app này thì bắt khách bỏ nhiều thời_gian để tìm_kiếm cho nó hồi_hộp
- line 5594: global=0 aspects=['Product', 'Service', 'App'] aspect_sentiment={'Product': 1, 'Service': 1, 'App': 0} text=gỡ bớt ứng_dụng này đi mọi người ạ đặt_hàng lâu lắm 15 ngày vẫn chưa xử_lý hàng xong mất uy_tín với khách_hàng
- line 5694: global=0 aspects=['Ship', 'App'] aspect_sentiment={'Ship': 0, 'App': 1} text=mình không đặt đơn nào cả mà nó tự_tạo đơn_ròi tự giao_lun đòi mình trả tiền app xứng_đáng 1 sao
- line 5757: global=0 aspects=['Product', 'Price', 'Ship'] aspect_sentiment={'Product': 0, 'Price': 1, 'Ship': 1} text=mã khuyến_mãi cho đơn hàng 99 k được giảm_giá 15 đặc_đơn hàng 1 triệu mà vẫn không đủ điều_kiện để dùng tiki có mã giảm_giá nhưng chưa bao_giờ tôi dùng được đặc_đơn hàng 85 k tiền ship 90 k ok tiki không dành cho tôi f_u
- line 5818: global=0 aspects=['Service'] aspect_sentiment={'Service': 1} text=toàn lừa_ngta trên tik dùng cũng méo ổn khuyên mn không dùng
- line 5845: global=0 aspects=['Product', 'Ship', 'Service'] aspect_sentiment={'Product': 0, 'Ship': 0, 'Service': 1} text=giao hàng càng_ngày_càng chậm chỉ toàn hứa_hẹn không có chính_sách làm hài_lòng khách_hàng
- line 5868: global=0 aspects=['Product', 'Ship', 'Service'] aspect_sentiment={'Product': 0, 'Ship': 0, 'Service': 1} text=yêu_cầu nhân_viên giải_quyết nhanh đi má dùng số nào nó cũng ban hết tôi đây phải thử 3 4 số đều ban hết mà lúc đang ký xong mới mua được hàng 0 đ thì ban ủa_alo không thích ng khác mua hang ođ nên ban à mà nhiều lúc đặt bên đt khác thì bảo hàng sẽ về trong 2 4 ngày ok_la 10 ngày sau không thấy được một hộp hàng nào được giao về nhìn lại tự hủy hàng của khách bộ mình đang giao cho khách xong tự_nhiên thấy nhớ thương nó nên hủy hàng để mang về ôm ấp rồi chưng hả bức_xúc vãi 1 s khỏi bàn
- line 6055: global=0 aspects=['Price', 'Ship', 'App'] aspect_sentiment={'Price': 0, 'Ship': 0, 'App': 1} text=cày xu rất vô_nghĩa_nha muốn xài mã km cũng rất quoằn xu_cày được nhưng chỉ_tiêu được 3 5 giá_trị đơn có shop còn không cho xài xu_vô nghĩa_mã km phải lướt chỗ này chỗ kia kiếm chứ không có sẵn lúc thanh_toàn rất mất thời_gian app nào cũng tối_ưu cho khách chốt đơn cho nhanh app này thì bắt khách bỏ nhiều thời_gian để tìm_kiếm cho nó hồi_hộp
- line 6087: global=0 aspects=['Product', 'App'] aspect_sentiment={'Product': 1, 'App': 1} text=là app mua hàng tốt nhưng_mà mỗi khi lướt_web hay chơi game đều vô phải link shoppe rất khó_chịu
- line 6119: global=0 aspects=['Price', 'Ship'] aspect_sentiment={'Price': 1, 'Ship': 1} text=đặt_hàng trả tiền ship dang_hoàng cứ bắt ra kho nhận hàng_không được sao ok

## Positive Global With Negative Aspect

Count: 265

- line 119: global=1 aspects=['Product', 'Service'] aspect_sentiment={'Product': 0, 'Service': 0} text=shoppe không bảo_mật thông_tin khách_hàng các bạn nhà bán và mua hàng phải cẩn_thận đánh_giá 3 sao trở xuống sẽ bị khủng_bố điện_thoại cho đến khi các bạn chịu nói các bạn đánh_giá nhầm
- line 201: global=1 aspects=['Product', 'App'] aspect_sentiment={'Product': 0, 'App': 0} text=app như lờ_tạo mã_giảm cho nhiều vào khi ngt_áp thì cứ lỗi rồi đặt kiểu gì
- line 216: global=1 aspects=['Product'] aspect_sentiment={'Product': 0} text=có_thể mua hàng mà không cần đi đâu cả
- line 228: global=1 aspects=['Service', 'App'] aspect_sentiment={'Service': 0, 'App': 0} text=lúc trước tôi có tài_khoản shopee sau đó thì gỡ cài_đặt đến bây_giờ tôi tải lại nhưng shopee cứ thông_báo rằng tài_khoản của tôi bị khóa mong được phản_hồi tích_cực
- line 245: global=1 aspects=['Product', 'App'] aspect_sentiment={'Product': 0, 'App': 0} text=tôi thấy nhiều quảng_cáo của lazada hiện mọi lúc mọi nơi trên điện_thoại của tôi ngay khi tôi đang dùng ứng_dụng khác hay làm_việc gây cho tôi cảm_thấy bị làm_phiền và ảnh_hưởng đến công_việc tôi đã phải gỡ hết ứng_dụng và mọi thứ liên_quan đến lazada và có_thể sẽ không bao_giờ mua hàng trên lazada vì sự mất lịch_sự này
- line 257: global=1 aspects=['Product', 'Price', 'Ship', 'App'] aspect_sentiment={'Product': 0, 'Price': 1, 'Ship': 1, 'App': 1} text=lazada tạo ứng_dụng giao_diện mới đi ạ giao_diện hiện khó xem mua hàng quá à giao_diện y_shopee đẹp dễ mua tìm_kiếm tích lũy xu các cửa_hàng live dễ hơn giảm bớt miễn_phí vận_chuyển thấy cao quá à
- line 284: global=1 aspects=['Product'] aspect_sentiment={'Product': 0} text=lúc khi muốn đạt hàng mà không được shopping_hải xem_lại
- line 351: global=1 aspects=['Ship', 'Service', 'App'] aspect_sentiment={'Ship': 0, 'Service': 0, 'App': 0} text=lừa_đảo phải không kêu người ta mời bạn_bè người ta đã mời rồi và người được tôi mời cũng đã đăng_kí và tải rồi mà không nhận được bất_kì một phản_hồi nào từ lazada hết vậy nhảy tới số 282 029 cái là nó dừng luôn à
- line 361: global=1 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 0, 'Ship': 0} text=mua_sắm đơn_giản tuy_nhiên với những đơn hàng cồng_kềnh giao lâu
- line 399: global=1 aspects=['App'] aspect_sentiment={'App': 0} text=đôi_khi nhấn hơi đơ trở về của máy phải nhấn mũi_tên thoát ra trên app nhạc chuông thông_báo giật cả mình
- line 457: global=1 aspects=['Product'] aspect_sentiment={'Product': 0} text=đặt shopee là không sợ hàng kém chất_lượng tùy mình chọn hàng_hợp với túi_tiền không thôi
- line 473: global=1 aspects=['App'] aspect_sentiment={'App': 0} text=cập_nhật địa_chỉ mới thôi ad app chứ tôi không cài lại địa_chỉ mới được
- line 489: global=1 aspects=['Product'] aspect_sentiment={'Product': 0} text=thấy miễn_phí cho không mà không biết thiệt hay giả
- line 491: global=1 aspects=['Service'] aspect_sentiment={'Service': 0} text=khi tôi gặp khó_khăn tổng_đài shoppe làm_việc rất uy_tín_tối rất hài_lòng
- line 5508: global=1 aspects=['Product', 'Ship', 'App'] aspect_sentiment={'Product': 0, 'Ship': 0, 'App': 0} text=nên cập_nhật tính_năng xác_nhận địa_điểm giao hàng khi đặt app có hỏi vị_trí mình đang đặt mà cuối cũng vẫn giao ra địa_chỉ mặc_định trước đó làm rất bực_mình
- line 5531: global=1 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 0, 'Ship': 0} text=tôi mua hàng trên lazada sip hàng đến tôi không có nhà hẹn 2 ngày sau giao lại 2 ngày sau tôi về đến nhà thì chời đã tối tôi nhắn_tin lại cho sip hẹn hôm sau thứ 2 giao hàng cho tôi không thấy giao và gửi tin đến là không nhận hàng một sự nói_láo trắng_trợn
- line 5539: global=1 aspects=['Product'] aspect_sentiment={'Product': 0} text=mua thoải_mái vì sản_phẩm được hoàn_trả dễ_dàng khi không đúng yêu_cầu
- line 5551: global=1 aspects=['Product', 'Ship', 'Service'] aspect_sentiment={'Product': 0, 'Ship': 0, 'Service': 1} text=uy_tín và đảm_bảo với khách_hàng nếu hàng nhận không đúng hoặc kém chất_lượng sẽ được hoàn_trả lại ngay_lập_tức 9 điểm
- line 5579: global=1 aspects=['Product'] aspect_sentiment={'Product': 0} text=toàn thấy feedback nhà bán hàng lừa_đảo mà không thấy lazada có động_thái gì có lazada reward giảm được nhiều phết
- line 5587: global=1 aspects=['Product', 'Ship', 'App'] aspect_sentiment={'Product': 0, 'Ship': 0, 'App': 0} text=giá_cả cạnh_tranh đa mẫu_mã còn một_vài lỗi là hay giao sai sân_phẩm ần khắc_phục

## Ship Labeled Positive But Negative Text

Count: 159

- line 79: global=0 aspects=['Ship', 'Service', 'App'] aspect_sentiment={'Ship': 1, 'Service': 1, 'App': 1} text=shipper giao hàng_không đúng hẹn dù trên app hiển_thị giao trong ngày gọi lên nv chăm_sóc khách_hàng_không giải_quyết được vấn_đề mất uy_tín với khách_hàng
- line 128: global=1 aspects=['Ship'] aspect_sentiment={'Ship': 1} text=đặt giao nhanh 48 h 3 ngày vẫn chưa thấy giao
- line 238: global=1 aspects=['Ship'] aspect_sentiment={'Ship': 1} text=giá_cả phải_chăng tuy_nhiên shopee nên làm_việc lại với các đơn_vị bán tấm pvc nhựa trong trãi bàn quảng_cáo trên trang_web của shopee là độ dày 2 mm nhưng giao chỉ có 0 5 mm còn đơn_vị khác ghi đầy 3 mm tôi đặt mua thì chỉ giao 1 8 mm rồi đơn_vị khác bán ghi dày 2 5 mm nhưng giao 1 mm tất_cả các đơn_vị đó đều trả_lời thắc_mắc của tôi về sai_lệch độ dày thì đều chung câu trả_lời có sai_lệch do đo thủ_công thế thì shopee xem sai_lệch do đo thủ_công từ 1 1 2 mm thì shopee sao
- line 395: global=1 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 1, 'Ship': 1} text=giao hàng nhanh râ t thích đă t sách trên tiki
- line 465: global=0 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 0, 'Ship': 1} text=sale mà để ghn giao thì tốt nhất là khỏi sale vì có giao đâu mà nhận cả chục đơn dính mỗi 2 đơn_ngâm nữa tháng vẫn chưa thấy hàng hết kho này đến kho khác ghi khách không nghe máy chặn số trong khi đơn quốc_tế spx đặt sau cả hơn chục ngày lại nhận trước
- line 485: global=1 aspects=['Product', 'Ship', 'App'] aspect_sentiment={'Product': 1, 'Ship': 1, 'App': 1} text=giao hàng nhanh hàng_không lỗi ok 5 sao
- line 517: global=1 aspects=['App', 'Product', 'Service', 'Ship'] aspect_sentiment={'App': 1, 'Product': 1, 'Service': 1, 'Ship': 1} text=shopee thông_tin vận_chuyển rõ_ràng hỗ_trợ trả hàng hủy đơn nhanh_chóng nhân_viên giao_nhận vui_vẻ mong rằng shopee đưa vào các cửa_hàng làm_ăn chân_chính loại_bỏ các cửa_hàng giao hàng giới_thiệu không đúng có dấu_hiệu lừa_gạt khách_hàng
- line 597: global=1 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 1, 'Ship': 1} text=shopee quá tệ giao hàng_không đúng hẹn gì đợi không quá dở làm_ăn quá_thức đức
- line 756: global=1 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 1, 'Ship': 1} text=giao hàng rất lâu_sao không dùng vietqr để thanh_toán mà dùng mỗi visa credit vậy nhỉ
- line 766: global=1 aspects=['Price', 'Product', 'Ship'] aspect_sentiment={'Price': 1, 'Product': 1, 'Ship': 1} text=mua_sắm còn hạn_chế tìm_kiếm khó giao hàng chậm phí giá hàng còn quá cao ít khuyến_mại
- line 769: global=1 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 1, 'Ship': 1} text=giao hàng quá chậm
- line 837: global=1 aspects=['Price', 'Product', 'Ship'] aspect_sentiment={'Price': 1, 'Product': 1, 'Ship': 1} text=shopee thì mình có cảm_nghĩ khá thú_vị đó điểm mình thấy hay bán đủ thứ trên đời quần_áo đồ học_tập phụ_kiện điện_thoại giá_cả đa_dạng hay có flash sale có nhiều voucher freeship nên tiết_kiệm được tiền nhưng cũng có_mặt cần lưu_ý chất_lượng sản_phẩm tùy cửa_hàng phải đọc đánh_giá kỹ dễ nghiện mua_sắm vì lướt là thấy muốn mua có_khi hình_ảnh đẹp mà hàng thật không giống lắm nói_chung shopee tiện_lợi và phù_hợp với thời_đại mua_sắm online nhưng cần tỉnh_táo khi chọn sh
- line 882: global=1 aspects=['Ship'] aspect_sentiment={'Ship': 1} text=shiper gọi kiểu nháy_máy không kịp đổ chuông xong tự hủy đơn luôn
- line 935: global=1 aspects=['App', 'Product', 'Ship'] aspect_sentiment={'App': 1, 'Product': 1, 'Ship': 1} text=có một_số shop giao hàng_không giống như hình_ảnh quảng_cáo cần khắc_phục lỗi này xin cảm_ơn
- line 1068: global=1 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 1, 'Ship': 1} text=tôi thấy mấy anh shipper giao hàng rất là thân_thiện lắm với_lại đặt_hàng cái nào cũng y_chang trên cửa_hàng bán chất_lượng
- line 1337: global=1 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 1, 'Ship': 1} text=giao lâu còn bị hủy đơn hàng
- line 1363: global=2 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 1, 'Ship': 1} text=giao hàng ok giao đồ_ăn siêu_chậm
- line 1479: global=1 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 1, 'Ship': 1} text=đặt_hàng không thấy điện_thoại lấy hàng máy_thần giao hàng nhằm khi không giao luôn rồi tự chả về rồi lazada cho gần bơm hàng rồi không cho nhận hàng rồi thanh_toán oc chó giao hàng cũng làm biến cmn
- line 1672: global=2 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 1, 'Ship': 1} text=giao hàng lâu_vãi chưởng shoppe nhanh hơn
- line 1684: global=1 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 1, 'Ship': 1} text=gì cũng 10 điểm hết mỗi tội giao hàng lâu ơi_là lâu luôn

## Ship Labeled Negative But Positive Text

Count: 79

- line 86: global=2 aspects=['Product', 'Ship', 'Service'] aspect_sentiment={'Product': 0, 'Ship': 0, 'Service': 0} text=chính_sách trả hàng hoàn tiền bịp bắt trước shopee nhưng làm nửa mùa nv thẩm_định hoàn_hàng không có kiến_thức kiểm_xong hỏng hàng hơn cskh nhét chữ vào mồm khách có video chứng_minh hàng giao đi còn nguyên_vẹn nhưng khi vận_chuyển ẩu hàng móp thì đổ hết tại khách làm móp dù đã cung_cấp video hàng nguyên_vẹn khi gửi đi gửi hoàn_khách không thèm bọc_tử_tế lại lúc đi chẳng sao nhận về không khác_gì con quỷ nên để không phải xảy ra chuyện hoàn_hàng thì mn tốt nhất không đặt từ đầu đỡ bị chèn ép
- line 349: global=0 aspects=['Product', 'Ship', 'Service'] aspect_sentiment={'Product': 0, 'Ship': 0, 'Service': 0} text=tôi mua nồi cơm điện laz_mall nhưng lớp phủ không dính không tốt dính cơm đầy thành nồi thoát nước kém nước bám đầy nắp nồi cơm để từ trưa đến chiều đã dính trắng quanh nồi như mốc vậy sản_phẩm không giống quảng_cáo và laz báo được đổi trả 30 ngày nhưng xạo làm đơn đổi trả thì từ_chối dù đã gửi hình và clip bằng_chứng theo yêu_cầu làm yêu_cầu trả hàng từ ngày 6 10 đến 22 10 hành_hạ gửi tùm_lum chờ tới chờ_lui cuối_cùng báo không xử_lý quá thất_vọng cho 1 dịch_vụ đổi qua xài shopee
- line 506: global=0 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 0, 'Ship': 0} text=vì quá giao hàng nhanh tốt nên tôi cho 1 sao
- line 626: global=0 aspects=['Product', 'Service', 'Ship'] aspect_sentiment={'Product': 0, 'Service': 0, 'Ship': 0} text=ngta hiếm lắm ms đặt được đơn 0 đ cái tự nhin giao thành_công xog báo lên tổng_đài r kiu bấm hoàn_hàng j đó xog r khiếu_nại xog r đợi 2 ngày cái bị từ_chối ns_nv này nọ chán ghê
- line 648: global=0 aspects=['Price', 'Product', 'Service', 'Ship'] aspect_sentiment={'Price': 0, 'Product': 0, 'Service': 0, 'Ship': 0} text=tết đến cần mua nhiều đồ shopee làm_ăn vớ vẩn mình không đặt được đồ về địa_chỉ cứ ấn địa_chỉ đấy là phần địa_chỉ bị ẩn không hiện đvvc nhanh nữa bắt dùng tủ để đồ mà chỗ mình làm_gì có tủ làm_ăn vớ_vẩn hết_sức khiếu_nại với nhân_viên mà giải_thích mãi không hiểu ngu
- line 736: global=0 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 0, 'Ship': 0} text=shopping giao hàng_không uy_tín_va khanh_hàng không có quyền_lợi mât liền tín_chao
- line 776: global=0 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 0, 'Ship': 0} text=đặt_hàng song đến ngày giao tự_động chả hàng trong khi tôi đã đặt 2 lần cùng một hàng shop dạo này làm_ăn không tốt
- line 782: global=0 aspects=['Price', 'Product', 'Ship'] aspect_sentiment={'Price': 0, 'Product': 0, 'Ship': 0} text=được cái giao hàng nhanh còn chẳng có mã giảm_giá nào ra trò
- line 1041: global=0 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 0, 'Ship': 0} text=trải_nghiệm mua_sắm 2 lần nhưng không lần nào giao đúng hẹn hiện_tại đơn hàng tôi mua ngày 23 9 đã thanh_toán hẹn dự_kiến 6 10 giao hôm_nay 12 10 không thấy gì cũng không thông_báo cho tôi lý_do châ m tôi không hài_lòng với cách làm này
- line 1190: global=0 aspects=['App', 'Price', 'Product', 'Ship'] aspect_sentiment={'App': 0, 'Price': 0, 'Product': 0, 'Ship': 0} text=lúc mới tạo app rất ổn hiện_tại phí giao hàng còn đắt hơn món hàng thì nên xem_lại
- line 1258: global=2 aspects=['App', 'Price', 'Ship'] aspect_sentiment={'App': 0, 'Price': 0, 'Ship': 0} text=shipper không hề ổn app cũng được nhưng không có nhiều voucher phải trả 100 tiền ship
- line 1318: global=0 aspects=['Price', 'Service', 'Ship'] aspect_sentiment={'Price': 0, 'Service': 0, 'Ship': 0} text=mong shoppe xem_xét lại cái kho của đơn_vị vận_chuyển nhanh ở hòa_khánh cái bè tiền_giang vì em đặt liên_tục 2 đơn mà sao chả nghe ai gọi gì mà toàn bị hoàn_trả
- line 1355: global=0 aspects=['App', 'Price', 'Product', 'Service', 'Ship'] aspect_sentiment={'App': 0, 'Price': 0, 'Product': 0, 'Service': 0, 'Ship': 0} text=tui hỏi nhân_viên 1 cách tôn_trọng mà không trả_lời được 1 câu đặt 1 cây viết mà 1 tuần chưa gia còn giá cắt_cổ nửa chứ tiền ship là 44 là sao tui mong cửa_hàng giao nhanh giùm tôi
- line 1494: global=0 aspects=['Product', 'Ship'] aspect_sentiment={'Product': 0, 'Ship': 0} text=làm_ăn chán các shop không uy_tín giao sai hàng
- line 1515: global=0 aspects=['Product', 'Service', 'Ship'] aspect_sentiment={'Product': 0, 'Service': 0, 'Ship': 0} text=trong trường_hợp thay_đổi địa_chỉ mới nên bổ_sung là sau khi thay_đổi thì địa_chỉ mới so với địa_chỉ cũ ra sao tự_dưng đổi rồi sửa theo đúng thực_tế lại sai trạm hên là đơn nhỏ chứ đơn hàng lớn gấp thì thôi luôn không tốt chút nào

## Price Label Without Clear Price Signal

Count: 208

- line 105: global=1 aspects=['Product', 'Price', 'Ship'] aspect_sentiment={'Product': 1, 'Price': 1, 'Ship': 1} text=cực tốt shiper nhiệt_tình ship nhanh hàng đẹp chất_lượng nhưng 1 vài cửa_hàng bán hàng_không uy_tín
- line 117: global=1 aspects=['Price', 'Ship'] aspect_sentiment={'Price': 1, 'Ship': 1} text=5 sao r hãy cho tôi mp ship ok
- line 153: global=1 aspects=['Product', 'Price'] aspect_sentiment={'Product': 1, 'Price': 1} text=good good uy_tín chất_lượng đảm_bảo mua mặt_hàng trên tiki là yên_tâm nhất dù hơi mắc hơn chút nhưng mọi thứ là yên_tâm chất_lượng
- line 448: global=0 aspects=['Price', 'Ship'] aspect_sentiment={'Price': 1, 'Ship': 1} text=đó giờ xài ổn giờ bắt ra tủ_đồ lấy hoặc chịu ship cao dù hỏa_tốc vẫn mất 2 ngày chả hiểu
- line 571: global=1 aspects=['Price', 'Product', 'Ship'] aspect_sentiment={'Price': 1, 'Product': 1, 'Ship': 1} text=shipper đi giao mấy chỗ đông dân_cư là y_như_rằng ngồi_tụm lại 1 chỗ với ship của các nền_tảng khác chả biết ông nào giữ hàng của mình tôi đã phải đi hỏi từng ng 1 lúc này chưa có kinh_nghiệm sau đó là mỗi lần nhận hàng toàn phải hỏi qua đt ship ngồi đâu trc_r mới lấy được hàng bộ nền_tảng không có đồng_phục à đấy là còn chưa nói tới thái_độ của shipper
- line 595: global=1 aspects=['Price'] aspect_sentiment={'Price': 1} text=giảm dung_lượng
- line 622: global=1 aspects=['App', 'Price', 'Product', 'Ship'] aspect_sentiment={'App': 1, 'Price': 1, 'Product': 1, 'Ship': 1} text=ứng_dụng mua hàng tốt được cái tiki nó giảm nhiều hơn so với shopee giao còn nhanh nữa làm_ăn rất có tâm hôm_nay đặt hôm sau đã có nhưng cái điểm chưa được của tiki là hàng ít quá không đa_dạng như shopee mình muốn tìm cái này nhưng tra ra nó không ra thứ mình muốn tìm mong_tiki sẽ khắc_phục sau_này cho bán hàng đa_dạng lên chắc_chắn sẽ nổi hơn shopee nếu không thiếu điều này
- line 828: global=1 aspects=['App', 'Price', 'Product', 'Ship'] aspect_sentiment={'App': 1, 'Price': 1, 'Product': 1, 'Ship': 1} text=tôi đặt 5 món gồm 3 đồng_hồ treo tường và 2 ổ điện dây 1 8 m nhưng lại giao thiếu 1 ổ_điện nhìn cách gói hàng nghi_ngờ lắm nhưng vì mua nhiều lần nên tôi tin_tưởng không quay clip dù_sao thì cũng rút ra được kinh_nghiệm lớn
- line 1010: global=1 aspects=['Price', 'Product', 'Service'] aspect_sentiment={'Price': 1, 'Product': 1, 'Service': 1} text=có phần trả hàng hoàn_tiền nên xài yên_tâm không lo bị lừa_shoppi làm_ăn càng_ngày_càng ngon_lành
- line 1298: global=1 aspects=['Price', 'Product'] aspect_sentiment={'Price': 1, 'Product': 1} text=mình đặt sách trên tiki từ năm 2016 vẫn luôn đồng_hành cùng tiki đến bây_giờ cũng có nhiều nền_tảng mua được sách nhưng mình vẫn quen dùng tiki mong tiki ngày_càng phát_triển hơn nhé
- line 1309: global=1 aspects=['Price', 'Product', 'Service'] aspect_sentiment={'Price': 1, 'Product': 1, 'Service': 1} text=riêng mình rất thích mua_sắm trên shopee mọi thắc_mắc đơn trả hàng rất nhanh_chóng tiền hoàn về rất đúng rất uy_tính
- line 1348: global=1 aspects=['App', 'Price', 'Product'] aspect_sentiment={'App': 1, 'Price': 1, 'Product': 1} text=shopee dạo này cũng cải_cách nhiều nhưng tôi lại bị trừ tiền qua aap ngân_hàng 1 cách lãng_nhách 290 không biết gì luôn đăng_ký khách_hàng vip bị trừ 29 k hàng tháng
- line 1400: global=1 aspects=['Price', 'Service'] aspect_sentiment={'Price': 1, 'Service': 1} text=quá thất_vọng vì không_thể đặt câu hỏi cho nhà bán_lẻ cũng như tiki không phản_hồi thắc_mắc cứ thế_này sẽ bye bye tiki thôi
- line 1623: global=1 aspects=['Price', 'Ship'] aspect_sentiment={'Price': 1, 'Ship': 1} text=vấn_đề về tiền không thanh_toán được số tài_khoản dư ở shoppe
- line 1634: global=1 aspects=['Price'] aspect_sentiment={'Price': 1} text=kiếm tiền không vốn vào ktien vn

## Very Short Text

Count: 732

- line 12: global=0 aspects=[] aspect_sentiment={} text=khá tệ
- line 37: global=1 aspects=[] aspect_sentiment={} text=tam_ok
- line 48: global=1 aspects=[] aspect_sentiment={} text=hưưx_ích
- line 85: global=1 aspects=[] aspect_sentiment={} text=tuyet voi
- line 104: global=1 aspects=[] aspect_sentiment={} text=tiên_lợi
- line 118: global=1 aspects=[] aspect_sentiment={} text=rất tiện
- line 120: global=1 aspects=[] aspect_sentiment={} text=ổn áp
- line 132: global=0 aspects=['App'] aspect_sentiment={'App': 0} text=app lừa_đảo
- line 151: global=1 aspects=[] aspect_sentiment={} text=quá được
- line 162: global=1 aspects=['Service'] aspect_sentiment={'Service': 1} text=lazada ok
- line 167: global=1 aspects=[] aspect_sentiment={} text=tốt bổ_ích
- line 188: global=2 aspects=[] aspect_sentiment={} text=tạm ổn
- line 198: global=0 aspects=[] aspect_sentiment={} text=như sịt
- line 218: global=2 aspects=[] aspect_sentiment={} text=wow sale
- line 234: global=0 aspects=[] aspect_sentiment={} text=đắp quá
- line 248: global=1 aspects=['App'] aspect_sentiment={'App': 1} text=app tiên_lợi
- line 255: global=0 aspects=[] aspect_sentiment={} text=quá kém
- line 256: global=2 aspects=[] aspect_sentiment={} text=cũm cũm
- line 265: global=1 aspects=[] aspect_sentiment={} text=gian_hàng nhanh_chóng
- line 270: global=2 aspects=[] aspect_sentiment={} text=ok fen
- line 283: global=1 aspects=[] aspect_sentiment={} text=thích thế
- line 289: global=1 aspects=[] aspect_sentiment={} text=thư_viện mua_sắm
- line 314: global=0 aspects=[] aspect_sentiment={} text=như lol
- line 319: global=1 aspects=['Product'] aspect_sentiment={'Product': 1} text=ok chất_lượng
- line 320: global=1 aspects=[] aspect_sentiment={} text=hài_lòng ạ
- line 343: global=1 aspects=[] aspect_sentiment={} text=oke lala
- line 358: global=1 aspects=[] aspect_sentiment={} text=ngày_càng hoàn_thiện
- line 392: global=0 aspects=[] aspect_sentiment={} text=quảng_cáo hoài_phiền
- line 405: global=0 aspects=[] aspect_sentiment={} text=như đb
- line 416: global=0 aspects=[] aspect_sentiment={} text=toàn lừa_đảo
- line 423: global=1 aspects=[] aspect_sentiment={} text=khá ổn
- line 440: global=1 aspects=[] aspect_sentiment={} text=sướng đời
- line 460: global=1 aspects=[] aspect_sentiment={} text=ok tiện_lợi
- line 464: global=2 aspects=[] aspect_sentiment={} text=cũng tạm
- line 492: global=0 aspects=[] aspect_sentiment={} text=không an_toàn
- line 497: global=1 aspects=[] aspect_sentiment={} text=rất tuyệt
- line 499: global=1 aspects=[] aspect_sentiment={} text=ok men
- line 510: global=0 aspects=['Price'] aspect_sentiment={'Price': 0} text=bán mắc
- line 515: global=1 aspects=[] aspect_sentiment={} text=chất sếp
- line 516: global=1 aspects=[] aspect_sentiment={} text=áo đẹp
- line 524: global=1 aspects=['Product'] aspect_sentiment={'Product': 1} text=đặt_hàng ổn
- line 529: global=1 aspects=['Price'] aspect_sentiment={'Price': 1} text=rất xuất_xắc
- line 572: global=1 aspects=[] aspect_sentiment={} text=rât tôt
- line 585: global=1 aspects=[] aspect_sentiment={} text=rất oke
- line 587: global=0 aspects=[] aspect_sentiment={} text=như bùồi

## Goi y uu tien review

1. Empty Aspects But Polar Global
2. Ship Mention Without Ship Label
3. Ship Labeled Positive But Negative Text
4. Positive Global With Negative Aspect
5. Negative Global With Positive Aspect
6. Price Label Without Clear Price Signal
7. Very Short Text

## Cach dung bao cao

- Review theo line number trong dataset.jsonl.
- Uu tien sua nhung dong co nhan xung_dot truoc.
- Sau khi sua, chay lai thong ke de xem count cua tung nhom co giam xuong hay khong.