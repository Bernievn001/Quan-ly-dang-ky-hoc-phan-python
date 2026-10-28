# OneUni v24 — Hệ thống mô phỏng đăng ký học phần HUIT

Ứng dụng desktop viết bằng **Python + Tkinter** (chỉ dùng thư viện chuẩn, không cần `pip install`) mô phỏng quy trình
đăng ký học phần: sinh viên tìm lớp, đăng ký, xem thời khóa biểu/lịch thi, theo dõi học phí; quản trị viên quản lý tài khoản,
môn học, lớp học phần, lịch thi và cấu hình hệ thống.

> **Đây là dự án mô phỏng phục vụ học tập.** Không kết nối hệ thống nhà trường thật. Thanh toán chỉ là *mô phỏng*:
> mã QR (`QR_Link_YouTube.png`) là liên kết demo, không nhận tiền; nút xác nhận chỉ cập nhật trạng thái trong tệp JSON.

---

## 1. Chạy chương trình

Yêu cầu: **Python 3.8 trở lên** (đã có sẵn Tkinter trên Windows/macOS khi cài từ python.org).

```bash
python HUIT_DangKyHocPhan_OneUni_v24.py      # hoặc: py HUIT_DangKyHocPhan_OneUni_v24.py
```

Trên Windows có thể bấm đúp `Chay_OneUni.bat`. Trên Linux nếu báo thiếu Tkinter: `sudo apt install python3-tk`.

Giữ **tất cả tệp `oneuni_*.py` và các tệp `.json` cùng một thư mục** với tệp khởi chạy.

### Tài khoản demo

| Vai trò | Tài khoản | Mật khẩu ban đầu |
|---|---|---|
| Quản trị viên | `admin` | `Huit@123` |
| Sinh viên | `SV01`, `SV02` | `SV01@123`, `SV02@123` |

- Màn hình đăng nhập chỉ hiện gợi ý tài khoản demo **khi chúng còn dùng mật khẩu mặc định**; đổi mật khẩu xong gợi ý tự biến mất.
- Sinh viên do admin tạo mới có mật khẩu khởi tạo `SVxx@123` (xx là số thứ tự tạo, ví dụ `SV03@123`).
  Khi admin *đặt lại mật khẩu*, mật khẩu mới là `<MSSV>@123`.
- Tài khoản không phân biệt hoa/thường khi đăng nhập (`sv01` = `SV01`).

---

## 2. Điểm mới trong v24 (so với v23)

**Giao diện**
- Bố cục mới: thanh điều hướng bên trái, thanh tiêu đề có avatar, thẻ thống kê, thông báo nổi (toast) thay cho hộp thoại thành công.
- Bảng dữ liệu dùng chung: **tìm kiếm không dấu** (gõ `lap trinh` vẫn ra *Lập trình*), **bấm tiêu đề cột để sắp xếp**,
  dòng xen kẽ màu, màu theo trạng thái, **nút Xuất CSV** (mở được bằng Excel).
- Trang **Tổng quan** cho cả sinh viên (lịch hôm nay, lịch thi sắp tới, học phí) và quản trị viên (số liệu, lớp sắp đầy, trạng thái hệ thống).
- **Thời khóa biểu vẽ lại**: tự co giãn theo cửa sổ, cuộn bằng chuột, tô nổi cột hôm nay, chia buổi Sáng/Chiều/Tối,
  xử lý ô chồng nhau, nhấp vào ô để xem chi tiết.
- Biểu mẫu quản trị dạng *danh sách + form*, có **lịch chọn ngày**, combobox **gõ để lọc**, thanh cuộn tự ẩn.
- Tự co theo độ phân giải cao (Windows), phông tự chọn (Segoe UI → SF/Helvetica Neue → Ubuntu → DejaVu).

**Chức năng / nút bấm**
- Đăng ký: hộp thoại xác nhận có học phí; **bảng chi tiết cho biết ngay vì sao chưa đăng ký được**; nhấp đúp để đăng ký nhanh;
  bộ lọc *Đã đăng ký / Chưa đăng ký / Còn chỗ*; hủy đăng ký kiểm tra trước khi hỏi xác nhận.
- Quản trị: **sửa** (không chỉ tạo) tài khoản, môn học, lớp học phần; **xóa** môn và lớp; khóa/mở khóa **nhiều lớp cùng lúc**;
  khóa tài khoản theo số ngày tùy chọn; đặt lại mật khẩu; xóa sinh viên có hỏi xác nhận và **dọn sạch dữ liệu liên quan**.
- Sinh viên có trang **Lịch thi** riêng (trước đây không có trang này) và **Đổi mật khẩu**.
- Cấu hình: thêm học phí lý thuyết/thực hành, sĩ số tối đa, nút **Sao lưu ngay** và **Mở thư mục dữ liệu**.

**Lỗi đã sửa so với v23**

| Vấn đề ở v23 | Cách xử lý ở v24 |
|---|---|
| Mật khẩu admin bị **ghi đè về `Huit@123` mỗi lần mở app** | Chỉ tạo admin khi chưa có; mật khẩu đổi được và được giữ nguyên |
| Mật khẩu lưu **văn bản thường** trong `users.json` | Băm **PBKDF2-SHA256** có muối; tự chuyển dữ liệu cũ khi khởi động |
| Ngày bắt đầu/kết thúc dạng `dd/mm/yyyy` bị đọc sai → thời khóa biểu hiện lớp **cả năm** | Nhận cả `dd/mm/yyyy` và `YYYY-MM-DD`, chuẩn hóa về `YYYY-MM-DD` |
| Học phí tính theo cấu hình, **bỏ qua giá riêng của từng lớp** admin nhập | Ưu tiên giá của lớp; lớp không có giá mới dùng giá theo loại lịch trong cấu hình |
| Có thể đăng ký **hai lớp của cùng một môn** | Chặn, nêu rõ lớp đã đăng ký |
| Xóa sinh viên để lại đăng ký/học phí/lịch thi mồ côi | Xóa kèm toàn bộ dữ liệu liên quan |
| Trùng lịch chỉ xét thứ/tiết, **bỏ qua khoảng ngày** (khác học kỳ vẫn báo trùng) | Chỉ trùng khi cả tiết lẫn khoảng ngày giao nhau |
| Khi khởi động, v23 **âm thầm sửa dữ liệu**: cắt sĩ số từng lớp về giới hạn cấu hình (mặc định 60) | Kiểm tra giới hạn khi tạo/sửa lớp; không tự đổi dữ liệu khi khởi động |
| Mã chết `tab_lich_thi`, `tree_tkb` (không tồn tại) | Loại bỏ; thay bằng trang Lịch thi thật |
| Tiêu đề cửa sổ ghi v11; ghi file không an toàn, không sao lưu | Tiêu đề đúng phiên bản; **ghi nguyên tử** + **sao lưu tự động** |
| Lớp ngẫu nhiên có thể trùng phòng/giảng viên | Tự tránh trùng khi sinh; tạo/sửa thủ công cũng bị chặn |

**Mã nguồn gọn và kiểm thử được** — tách nghiệp vụ khỏi giao diện (xem mục 6), có 36 bài kiểm thử tự động.

---

## 3. Hướng dẫn sử dụng

### Sinh viên
| Mục | Công dụng |
|---|---|
| **Tổng quan** | Lịch học/thi hôm nay, lịch thi sắp tới, số tín chỉ, học phí còn nợ, trạng thái đợt đăng ký |
| **Đăng ký học phần** | Chọn lớp → xem chi tiết/lý do → *Đăng ký học phần* (hoặc nhấp đúp). *Hủy đăng ký* chỉ khi chưa thanh toán |
| **Thời khóa biểu** | Lịch tuần: lý thuyết (xanh lá), thực hành (xanh dương), tạm ngưng (đỏ), lịch thi (vàng) |
| **Lịch thi** | Danh sách lịch thi được gán, có “Còn N ngày” |
| **Học phí / Thanh toán** | Các khoản phí, thanh toán mô phỏng qua QR (ngân hàng hoặc MoMo), nhận mã giao dịch |
| **Học phần đã đóng phí** | Các lớp đã được ghi nhận thanh toán |
| **Tài khoản** | Thông tin cá nhân, đổi mật khẩu |

### Quản trị viên
| Mục | Công dụng |
|---|---|
| **Tổng quan hệ thống** | Số liệu nhanh, lớp sắp đầy, sao lưu nhanh |
| **Tài khoản sinh viên** | Tạo/sửa, GPA, cảnh báo học vụ, cờ “đã đóng học phí kỳ trước”; khóa tạm N ngày, mở khóa, đặt lại mật khẩu, xóa |
| **Môn học** | Thêm/sửa/xóa môn, môn tiên quyết (có kiểm tra vòng lặp), nạp danh mục mở rộng |
| **Lớp học phần** | Tạo/sửa/xóa lớp; **Khóa/Mở khóa** nhiều lớp (giữ Ctrl/Shift để chọn nhiều); *Tạo lớp ngẫu nhiên* |
| **Lịch thi** | Gán lịch thi cho sinh viên theo tiết thi; giờ thi tự xác định theo tiết |
| **Cấu hình & dữ liệu** | Thời gian/đợt đăng ký, học phí, sĩ số tối đa, sao lưu |

**Phím tắt:** `F5` làm mới trang · `Ctrl+F` đặt con trỏ vào ô tìm kiếm · `Enter` đăng nhập · nhấp đúp để đăng ký nhanh.

> Khóa một lớp **không** tự hủy đăng ký hay hoàn tiền cho sinh viên đã đăng ký trước đó; nó chỉ chặn đăng ký mới.

---

## 4. Quy tắc nghiệp vụ

**Điều kiện đăng ký** (kiểm tra theo thứ tự, dừng ở lý do đầu tiên):
1. Là tài khoản sinh viên, không bị khóa.
2. Đang trong thời gian đăng ký và đợt hiện tại hợp lệ (`1 ≤ đợt ≤ số đợt tối đa`).
3. Đã đóng học phí các kỳ trước.
4. Không bị hạn chế học vụ: GPA ≥ 1.0 và cảnh báo học vụ < 2.
5. Lớp không ở trạng thái *Tạm ngưng*; chưa đăng ký lớp này; **chưa đăng ký lớp khác của cùng môn**.
6. Đã đăng ký một lớp của **môn tiên quyết** (nếu có).
7. Lớp còn chỗ (sĩ số < tối đa).
8. Không trùng lịch: cùng thứ, giao nhau về **tiết** và giao nhau về **khoảng ngày** với một lớp đã đăng ký.

> Lưu ý: “đã học môn tiên quyết” được mô phỏng bằng việc *đã đăng ký* một lớp của môn đó, vì dự án không lưu bảng điểm.

**Học phí** = số tín chỉ × giá mỗi tín chỉ **của lớp**. Nếu lớp không có giá thì dùng giá theo loại lịch trong cấu hình
(mặc định lý thuyết 700.000, thực hành 1.000.000 VNĐ/tín chỉ). Khoản phí được tạo khi đăng ký và gỡ khi hủy (nếu chưa thanh toán).

**Tạo/sửa lớp:** tiết hợp lệ 1–16 (`1-3`, `1,2,3`, `1-3, 7-9`); sĩ số 1…(giới hạn cấu hình); giá thực hành phải cao hơn giá lý thuyết;
không trùng phòng hoặc giảng viên với lớp khác cùng thời điểm (lớp *Tạm ngưng* không tính); không đổi môn của lớp đã có sinh viên;
sĩ số không được nhỏ hơn số sinh viên đã đăng ký; không xóa lớp có khoản học phí đã thanh toán.

**Xem thời khóa biểu:** trong phạm vi 2 năm trước/sau hôm nay và kẹp trong 2020–2030.

**Khung giờ thi theo tiết** (chỉ áp dụng cho lịch thi; dữ liệu không quy định giờ vào lớp của tiết học):

| Tiết | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Giờ | 07:00 | 07:50 | 08:40 | 09:30 | 10:20 | 11:10 | 12:30 | 13:20 | 14:10 | 15:30 | 16:20 | 17:10 | 18:00 | 18:50 | 19:40 | 20:30 |

---

## 5. Dữ liệu

Dữ liệu là các tệp JSON (UTF-8) cạnh chương trình. **Hãy thoát ứng dụng trước khi sửa tay.**

| Tệp | Nội dung |
|---|---|
| `users.json` | Tài khoản: `ma_nd`, `mat_khau_hash`, `ho_ten`, `vai_tro`, `nganh`, `lop`, `gpa`, `canh_bao_hoc_vu`, `da_dong_hoc_phi`, `trang_thai`, `khoa_den` |
| `monhoc.json` | Môn học: `ma_mh`, `ten_mh`, `so_tin_chi`, `tien_quyet`, `nganh_ap_dung` (tùy chọn) |
| `danh_muc_mon_hoc.json` | Danh mục mở rộng; được bổ sung vào `monhoc.json` khi khởi động hoặc bấm *Nạp danh mục mở rộng* |
| `lophocphan.json` | Lớp: lịch, phòng, giảng viên, sĩ số, giá, `danh_sach_sv`, `dot_theo_sv`, `ngay_dk_theo_sv` |
| `thanhtoan.json` | Khoản học phí và trạng thái thanh toán |
| `lichthi.json` | Lịch thi (mỗi bản ghi có `id`) |
| `config.json` | Thời gian/đợt đăng ký, học phí, sĩ số tối đa |
| `backup/` | Bản sao lưu tự động mỗi lần khởi động và khi bấm *Sao lưu* (giữ 10 bản gần nhất) |

**Tương thích với v23:** dùng thẳng dữ liệu cũ. Lần chạy đầu v24 sẽ sao lưu rồi chuẩn hóa dữ liệu (băm mật khẩu, chuẩn hóa ngày, thêm `id` cho lịch thi).
Vì mật khẩu được băm nên **v23 không đọc được `users.json` đã chuyển**; muốn quay lại v23, chép lại các tệp từ thư mục `backup/` tương ứng.

Nếu một tệp JSON bị hỏng cú pháp, chương trình **báo lỗi và không tự ghi đè** để tránh mất dữ liệu — hãy sửa hoặc khôi phục từ `backup/`.

---

## 6. Cấu trúc mã nguồn

```
OneUni_v24_Full/
├─ HUIT_DangKyHocPhan_OneUni_v24.py   # điểm khởi chạy
├─ oneuni_core.py        # nghiệp vụ + lưu trữ + bảo mật (KHÔNG phụ thuộc Tkinter)
├─ oneuni_ui.py          # theme, thẻ, bảng, biểu mẫu, chọn ngày, toast
├─ oneuni_screens.py     # đăng nhập, khung điều hướng, các trang sinh viên, tài khoản
├─ oneuni_admin.py       # các trang quản trị
├─ test_oneuni_core.py   # 36 bài kiểm thử nghiệp vụ
├─ Chay_OneUni.bat       # chạy nhanh trên Windows
├─ *.json, QR_Link_YouTube.png
└─ README.md
```

Thêm một trang mới: viết lớp kế thừa `Page` (hoặc `AdminPage`), triển khai `build()`/`refresh()`, rồi khai báo trong `STUDENT_PAGES`
hoặc `ADMIN_PAGES`. Mọi quy tắc nghiệp vụ nằm trong `Service` của `oneuni_core.py`, giao diện chỉ gọi hàm và hiển thị kết quả
(`NghiepVuError` được hiển thị trực tiếp cho người dùng).

### Kiểm thử

```bash
python test_oneuni_core.py        # hoặc: python -m unittest -v test_oneuni_core
```

Các bài kiểm thử chạy trên **bản sao** dữ liệu mẫu trong thư mục tạm, không đụng tới dữ liệu thật.

---

## 7. Giới hạn và lưu ý

- Bảo mật ở mức **học tập**: mật khẩu đã băm nhưng dữ liệu vẫn là tệp JSON cục bộ, không phân quyền ở mức hệ điều hành.
- Một người dùng tại một thời điểm; không hỗ trợ nhiều máy cùng ghi vào một thư mục dữ liệu.
- Thanh toán, QR và mã giao dịch chỉ để minh họa luồng nghiệp vụ.
- Biểu tượng dùng ký tự Unicode cơ bản (không dùng emoji) để chạy ổn định trên mọi bản Tk 8.6.

## 8. Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| `No module named tkinter` | Linux: `sudo apt install python3-tk`; macOS/Windows: cài lại Python từ python.org |
| Báo lỗi dữ liệu khi mở | Mở `backup/<thời gian>/` và chép tệp JSON tương ứng ra thư mục chính |
| Hộp thoại “Lỗi không mong muốn” | Chi tiết nằm trong `oneuni_error.log` cạnh chương trình — gửi tệp này khi cần hỗ trợ |
| Chữ nhỏ/mờ trên màn hình 4K | Đã bật nhận biết DPI trên Windows; nếu vẫn nhỏ, chỉnh *Display scaling* của hệ điều hành |
| Quên mật khẩu admin | Xóa dòng admin trong `users.json` (sau khi thoát app); lần mở sau sẽ tạo lại `admin / Huit@123` |

---

## 9. Nhật ký thay đổi

**v24** — Viết lại giao diện (thanh bên, thẻ thống kê, bảng tìm/sắp xếp/xuất CSV, thời khóa biểu mới, lịch chọn ngày, toast);
tách `oneuni_core` khỏi giao diện và bổ sung 36 bài kiểm thử; băm mật khẩu và ngừng ghi đè mật khẩu admin; học phí theo giá từng lớp;
chặn đăng ký trùng môn, kiểm tra trùng lịch theo khoảng ngày, chặn trùng phòng/giảng viên; sửa/xóa môn và lớp; khóa nhiều lớp;
xóa sinh viên dọn dữ liệu liên quan; trang Lịch thi và Đổi mật khẩu; ghi tệp nguyên tử và sao lưu tự động.

**v1–v23** — Lịch sử các phiên bản trước (đăng ký học phần, đợt đăng ký, thanh toán QR mô phỏng, lịch thi, quản trị lớp/môn/tài khoản…)
được giữ trong `README.txt` của gói v23.
