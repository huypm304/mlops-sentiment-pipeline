# Data Train V4 Review

**File**: `data/processed/data_train_v4.jsonl`

## Executive Summary

`data_train_v4` đã đạt mức dùng được như một bộ train chính thức cho vòng huấn luyện tiếp theo.

Điểm mạnh chính:
- Không còn lỗi cấu trúc nghiêm trọng: không duplicate text, không offset mismatch, không overlap span, không target dư space, không record rỗng.
- Phân bố `global_sentiment` khá cân.
- Phân bố `aspect` ở mức chấp nhận được, không có aspect nào quá hiếm.
- Tỷ lệ record đa opinion gần 46%, đủ để mô hình học multi-aspect tốt hơn các bản trước.
- Các cặp contrast mục tiêu đã được bơm lên rõ rệt, đặc biệt `Fashion vs Price`, `App vs Ship`, `Electronics vs Service`, `General vs Ship`.

Rủi ro còn lại:
- Vẫn có một lượng cảnh báo sentiment theo heuristic (`E5`) khá lớn, nhưng đây là cảnh báo mềm chứ không phải lỗi chắc chắn.
- Có 1 record conflict giữa `global_sentiment` và aspect sentiment.
- Một số aspect vẫn lệch nội bộ theo sentiment, đặc biệt `App-Neu`, `Ship-Pos`, `Ship-Neu`.
- Target naming còn chưa được chuẩn hóa hoàn toàn giữa `space`, `_`, và viết hoa.
- Một số target generic xuất hiện rất dày như `shop`, `giá`, `áo`, `giao`, có thể tạo thiên lệch lexical shortcut.

Kết luận thực dụng:
- Có thể chốt `data_train_v4` làm baseline train chính thức.
- Chưa phải một bộ gold hoàn hảo.
- Nếu tiếp tục làm `v5`, nên ưu tiên bổ sung có mục tiêu thay vì làm sạch đại trà thêm.

## Dataset Overview

| Metric | Value |
|---|---:|
| Total records | 7,356 |
| Total opinions | 11,393 |
| Duplicate texts | 0 |
| Unique raw targets | 189 |
| Unique normalized targets | 168 |
| Mean tokens per text | 17.50 |
| Median tokens per text | 12 |
| Max tokens per text | 194 |
| Mean characters per text | 80.68 |
| Median characters per text | 57 |
| Max characters per text | 846 |

Nhận xét:
- Độ dài text nhìn chung hợp lý cho ABSA review ngắn.
- Tail dài vẫn tồn tại: có 265 record dài từ 60 token trở lên.
- Dataset đủ lớn để train một model encoder-based nghiêm túc, nhưng chưa quá lớn để trung hòa hoàn toàn lexical bias.

## Structural Audit

### Fatal Structure Errors

| Code | Meaning | Records |
|---|---|---:|
| E1 | Offset mismatch | 0 |
| E2 | Target has leading or trailing space | 0 |
| E3 | Target is pure opinion word | 0 |
| E4 | Duplicate aspect in same record | 0 |
| E7 | Record has no opinions | 0 |
| E8 | Text too short (<= 2 tokens) | 0 |
| OVERLAP | Overlapping spans | 0 |
| Duplicate text | Repeated full text | 0 |

### Soft Warnings

| Code | Meaning | Records |
|---|---|---:|
| E5 | Heuristic sentiment-context warning | 602 |
| E6 | Global sentiment conflict | 1 |

### Interpretation

- Về mặt format annotation, `data_train_v4` sạch.
- `E5` không nên đọc như 602 lỗi thật. Rule này dựa vào keyword window nên rất dễ flag các câu mixed, câu có đối lập, câu giá trung tính kiểu `tầm giá này ổn`, hoặc câu có cụm `ổn nhưng ...`.
- `E6` chỉ còn 1 record, tức là conflict global đã gần như được xử lý hết.

### Notable Soft-Warning Examples

`E5` điển hình:
- line 14: target `giao hàng` | aspect `Ship` | sentiment `Pos` | context `giao hàng ổn nhưng app hơi`
- line 35: target `giá` | aspect `Price` | sentiment `Pos` | context `pin nó tuột hoi nhanh.. giá tam này là ổn rồi`
- line 73: target `giá` | aspect `Price` | sentiment `Neg` | context `nhưng để nói balô giá 399k giảm còn 99k thì`
- line 83: target `app` | aspect `App` | sentiment `Pos` | context `xài app thì tốt đấy ổn_định nhưng`

`E6` còn lại:
- line 4432: text `giá các sản_phẩm cao hơn các trang mua_sắm khác`
  - aspect sentiment: toàn `Neg`
  - global sentiment: `Pos`

## Label Distribution

### Global Sentiment

| Label | Count | Share |
|---|---:|---:|
| Neg (0) | 2,395 | 32.56% |
| Pos (1) | 2,210 | 30.04% |
| Neu (2) | 2,751 | 37.40% |

Đánh giá:
- Đây là phân bố đẹp.
- Không có nhãn nào bị áp đảo quá mạnh ở cấp record.

### Aspect Distribution

| Aspect | Count | Share |
|---|---:|---:|
| Service | 2,076 | 18.22% |
| General | 2,014 | 17.68% |
| Price | 1,870 | 16.41% |
| Fashion | 1,655 | 14.53% |
| Electronics | 1,429 | 12.54% |
| App | 1,278 | 11.22% |
| Ship | 1,071 | 9.40% |

Đánh giá:
- Aspect nhiều nhất là `Service`, ít nhất là `Ship`.
- Tỷ lệ max/min khoảng `1.94x`, tức là chưa cân bằng hoàn hảo nhưng vẫn trong vùng trainable.
- `Ship` là aspect mỏng nhất, nhưng chưa tới mức nguy hiểm.

## Aspect x Sentiment Distribution

| Aspect | Neg | Pos | Neu | Nhận xét |
|---|---:|---:|---:|---|
| App | 612 | 501 | 165 | Thiếu `Neu` rõ nhất |
| Electronics | 548 | 608 | 273 | Tương đối ổn |
| Fashion | 856 | 526 | 273 | Nghiêng `Neg` |
| General | 982 | 660 | 372 | Nghiêng `Neg` |
| Price | 465 | 685 | 720 | Cân khá đẹp, thiên `Neu/Pos` |
| Service | 669 | 791 | 616 | Cân đẹp nhất |
| Ship | 518 | 323 | 230 | Thiếu `Pos` và `Neu` |

Đánh giá:
- `Service` và `Price` là hai aspect khỏe nhất về cân bằng sentiment.
- `Electronics` dùng được.
- `Fashion`, `General`, `Ship` vẫn mang bias `Neg`.
- `App-Neu` là ô thưa nhất đáng chú ý.

## Opinion Density Per Record

| Opinions per record | Count | Share |
|---|---:|---:|
| 1 | 3,976 | 54.05% |
| 2 | 2,795 | 38.00% |
| 3 | 518 | 7.04% |
| 4 | 62 | 0.84% |
| 5 | 5 | 0.07% |

Đánh giá:
- Record 1-opinion vẫn chiếm đa số.
- Tuy nhiên, record có từ 2 opinion trở lên đạt `45.95%`, đủ để mô hình học multi-aspect thực chất.
- Đây là bước tiến tốt so với trạng thái trước khi bơm contrast data.

## Aspect Coverage Per Record

| Aspect | Records containing aspect | Share of all records |
|---|---:|---:|
| Service | 2,076 | 28.22% |
| General | 2,014 | 27.38% |
| Price | 1,870 | 25.42% |
| Fashion | 1,655 | 22.50% |
| Electronics | 1,429 | 19.43% |
| App | 1,278 | 17.37% |
| Ship | 1,071 | 14.56% |

## Common Multi-Aspect Combinations

| Combo | Count | Share |
|---|---:|---:|
| Electronics + Price | 440 | 5.98% |
| Electronics + Service | 359 | 4.88% |
| Fashion + Price | 297 | 4.04% |
| General + Ship | 278 | 3.78% |
| General + Service | 217 | 2.95% |
| App + Electronics | 216 | 2.94% |
| General + Price | 175 | 2.38% |
| App + Ship | 171 | 2.32% |
| Fashion + Service | 130 | 1.77% |
| Electronics + Price + Service | 115 | 1.56% |

Đánh giá:
- Các combo mạnh nhất khớp với những vùng dữ liệu đã được mở rộng có chủ đích.
- Dù vậy, phổ combination vẫn tập trung vào một nhóm nhỏ. Nhiều tổ hợp còn lại vẫn thưa.

## Contrast Pair Strength

| Contrast pair | Count |
|---|---:|
| Fashion vs Price | 238 |
| App vs Ship | 149 |
| Electronics vs Service | 126 |
| General vs Ship | 99 |
| App vs Price | 45 |
| Electronics vs Price | 43 |
| General vs Price | 36 |
| App vs Service | 32 |
| Price vs Service | 26 |
| App vs Electronics | 24 |

Đánh giá:
- 4 cặp mục tiêu chính đã có mật độ đủ để học pattern đối lập.
- Sau nhóm này, đuôi contrast rơi khá nhanh.
- Nếu muốn model mạnh hơn ở nhiều ngữ cảnh lạ, cần bơm tiếp các cặp yếu như `General vs Service`, `Price vs Ship`, `App vs General`, `App vs Fashion`.

## Target Distribution And Lexical Concentration

### Top Targets Overall

| Target | Count |
|---|---:|
| shop | 901 |
| giá | 778 |
| áo | 668 |
| hàng | 527 |
| app | 453 |
| giao | 450 |
| nhân viên | 373 |
| pin | 350 |
| tiền | 322 |
| tầm giá | 321 |

### Target Concentration By Aspect

| Aspect | Most frequent target | Count | Share inside aspect |
|---|---|---:|---:|
| Service | shop | 901 | 43.40% |
| Price | giá | 778 | 41.60% |
| Fashion | áo | 668 | 40.36% |
| Ship | giao | 450 | 42.02% |
| App | app | 453 | 35.45% |
| General | hàng | 527 | 26.17% |
| Electronics | pin | 350 | 24.49% |

Đánh giá:
- Có sự tập trung target khá mạnh ở một số aspect.
- Đây không phải lỗi annotation, nhưng là một rủi ro học shortcut lexical.
- Đặc biệt `Service -> shop`, `Price -> giá`, `Fashion -> áo`, `Ship -> giao` có thể khiến model overfit vào từ khóa thay vì học context sâu.

## Target Normalization Noise

Số liệu:
- `189` raw target forms
- `168` normalized target forms sau khi lower-case và đổi `_` thành space

Điều này cho thấy vẫn còn một lượng nhỏ không nhất quán bề mặt, chủ yếu do:
- khác biệt viết hoa đầu câu
- khác biệt `space` vs `_`

### Frequent Variant Groups

| Normalized form | Total | Main variants |
|---|---:|---|
| nhân viên | 434 | `nhân viên`, `Nhân viên`, `nhân_viên`, `Nhân_viên` |
| ứng dụng | 403 | `ứng_dụng`, `ứng dụng`, `Ứng_dụng`, `Ứng dụng` |
| tầm giá | 367 | `tầm giá`, `tầm_giá`, `Tầm_giá`, `Tầm giá` |
| phần mềm | 204 | `phần_mềm`, `phần mềm`, `Phần_mềm`, `Phần mềm` |
| giao hàng | 201 | `giao hàng`, `Giao_hàng`, `giao_hàng`, `Giao hàng` |
| màn hình | 207 | `màn hình`, `Màn hình`, `màn_hình`, `Màn_hình` |

Đánh giá:
- Mức noise này không phá dataset, nhưng vẫn làm vocabulary target bị phân mảnh.
- Nếu sau này làm `v5`, nên chuẩn hóa target surface form ở bước post-process trước khi merge.

## Length Tail Review

Số liệu:
- `265` record có độ dài từ `60` token trở lên.
- Record dài nhất đạt `194` token.

Rủi ro:
- Review quá dài thường chứa nhiều clause, nhiều contrast, nhiều background info ngoài target.
- Đây là dạng dữ liệu làm span sentiment khó hơn đáng kể.

Nhận xét:
- Không cần loại toàn bộ tail dài.
- Nhưng nếu sau này tối ưu thêm, có thể cân nhắc tách hoặc làm sạch một số review quá dài, đặc biệt những câu review kiểu liệt kê dài nhiều dòng.

## Overall Assessment

### What Is Good

- Cấu trúc annotation sạch.
- Aspect taxonomy mới đã đi vào dữ liệu ổn định.
- Phân bố global label cân.
- Aspect distribution không méo nặng.
- Multi-aspect coverage đã đạt mức dùng được.
- Các cặp contrast mục tiêu đã được tăng đáng kể.

### What Is Still Imperfect

- `E5` heuristic warnings còn cao, phản ánh còn nhiều câu mixed khó hơn là lỗi format.
- Một số aspect còn lệch sentiment nội bộ, nhất là `App` và `Ship`.
- Tập target còn khá concentrated theo vài từ khóa phổ biến.
- Surface form target chưa chuẩn hóa tuyệt đối.
- Long-tail review dài vẫn còn đáng kể.

## Final Verdict

`data_train_v4` đạt chuẩn để dùng làm bộ train chính thức cho vòng huấn luyện tiếp theo.

Mức đánh giá:
- **Structure quality**: tốt
- **Label balance**: khá tốt
- **Aspect balance**: chấp nhận được
- **Contrast readiness**: tốt ở các cặp mục tiêu chính, trung bình ở phần đuôi
- **Production readiness for training**: đạt

Nếu dừng ở đây để train tiếp, quyết định đó là hợp lý.

## Priority Recommendations For A Future V5

1. Bổ sung có mục tiêu cho `App-Neu`, `Ship-Pos`, `Ship-Neu`.
2. Tăng contrast ở các cặp yếu: `General-Service`, `Price-Ship`, `App-General`, `App-Fashion`.
3. Chuẩn hóa bề mặt target: viết thường, thống nhất `_` và `space`.
4. Giảm lexical concentration bằng cách đa dạng hóa target trong `Service`, `Price`, `Fashion`, `Ship`.
5. Review riêng nhóm record rất dài để giảm nhiễu context cho span sentiment.
