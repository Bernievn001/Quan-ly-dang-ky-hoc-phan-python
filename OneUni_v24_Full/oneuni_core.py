# -*- coding: utf-8 -*-
"""
OneUni core - lõi nghiệp vụ của hệ thống mô phỏng đăng ký học phần HUIT.

Module này KHÔNG phụ thuộc Tkinter nên có thể kiểm thử độc lập (xem test_oneuni_core.py).
Giao diện (oneuni_ui.py và HUIT_DangKyHocPhan_OneUni_v24.py) chỉ gọi các hàm ở đây.

Quy ước:
  * NghiepVuError  : vi phạm quy tắc nghiệp vụ, thông điệp hiển thị thẳng cho người dùng.
  * DuLieuError    : tệp JSON hỏng/không đọc được (không tự ghi đè để tránh mất dữ liệu).
  * Mọi hàm đọc trả về BẢN SAO dữ liệu; muốn thay đổi phải gọi hàm nghiệp vụ tương ứng.
"""
from __future__ import annotations

import copy
import hashlib
import hmac
import json
import os
import random
import re
import secrets
import shutil
import string
import unicodedata
import uuid
from datetime import date, datetime, timedelta

APP_VERSION = "24"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------
# Hằng số
# ----------------------------------------------------------------------------
FMT_DATE_VN = "%d/%m/%Y"
FMT_DATE_ISO = "%Y-%m-%d"
FMT_DATETIME = "%Y-%m-%d %H:%M"

THU = ("Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật")
LOAI_LICH = ("Lý thuyết", "Thực hành")
TT_BINH_THUONG, TT_TAM_NGUNG = "Bình thường", "Tạm ngưng"
TT_DA_THANH_TOAN, TT_CHUA_THANH_TOAN = "Đã thanh toán", "Chưa thanh toán"
LOAI_DI_THI = "Đi thi"            # loại lịch cũ, không hiển thị như lớp học
MAX_TIET = 16
NAM_MIN, NAM_MAX = 2020, 2030

ADMIN_ID = "admin"
ADMIN_MAT_KHAU_MAC_DINH = "Huit@123"

GIO_THI_THEO_TIET = {
    1: "07:00", 2: "07:50", 3: "08:40", 4: "09:30", 5: "10:20", 6: "11:10",
    7: "12:30", 8: "13:20", 9: "14:10", 10: "15:30", 11: "16:20", 12: "17:10",
    13: "18:00", 14: "18:50", 15: "19:40", 16: "20:30",
}

CONFIG_MAC_DINH = {
    "thoi_gian_bat_dau": "2020-01-01 00:00",
    "thoi_gian_ket_thuc": "2030-12-31 23:59",
    "so_dot_toi_da": 3,
    "dot_dang_ky_hien_tai": 1,
    "hoc_phi_moi_tin_chi": 700000,
    "hoc_phi_ly_thuyet_moi_tin_chi": 700000,
    "hoc_phi_thuc_hanh_moi_tin_chi": 1000000,
    "si_so_toi_da_moi_lop": 60,
}
_CONFIG_SO = ("so_dot_toi_da", "dot_dang_ky_hien_tai", "hoc_phi_moi_tin_chi",
              "hoc_phi_ly_thuyet_moi_tin_chi", "hoc_phi_thuc_hanh_moi_tin_chi", "si_so_toi_da_moi_lop")

DATA_FILES = ("users", "config", "monhoc", "danh_muc_mon_hoc", "lophocphan", "lichthi", "thanhtoan")
_KIEU_RONG = {"config": dict}      # tệp nào không khai báo thì mặc định là list

GIANG_VIEN_MAU = ("Nguyễn Văn An", "Trần Thị Bình", "Lê Minh Tuấn", "Phạm Hoàng Mai",
                  "Võ Quốc Huy", "Đặng Thu Hà", "Bùi Thanh Tùng", "Nguyễn Thị Lan")
PHONG_MAU = ("A101", "A203", "B302", "B405", "C201", "C305", "D102", "LAB01", "LAB02")
LOP_MAU = ("DHTI16A", "DHTI16B", "DHTI16C", "DHTI16D", "DHTI17A", "DHTI17B")


class NghiepVuError(Exception):
    """Vi phạm quy tắc nghiệp vụ; nội dung được hiển thị trực tiếp cho người dùng."""


class DuLieuError(Exception):
    """Tệp dữ liệu JSON bị lỗi cú pháp hoặc không đọc được."""


# ----------------------------------------------------------------------------
# Tiện ích thuần (không phụ thuộc trạng thái)
# ----------------------------------------------------------------------------
def to_int(value, default=0):
    try:
        return int(float(str(value).strip().replace(",", ".")))
    except (ValueError, TypeError):
        return default


def to_float(value, default=0.0):
    try:
        return float(str(value).strip().replace(",", "."))
    except (ValueError, TypeError):
        return default


def parse_date(value):
    """Nhận date/datetime hoặc chuỗi YYYY-MM-DD, dd/mm/yyyy, dd-mm-yyyy; sai định dạng trả về None."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    for fmt in (FMT_DATE_ISO, FMT_DATE_VN, "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def fmt_date(value):
    d = parse_date(value)
    return d.strftime(FMT_DATE_VN) if d else ""


def fmt_money(value):
    return f"{to_int(value):,}".replace(",", ".")


def cong_nam(d, so_nam):
    """Cộng/trừ số năm cho một ngày (xử lý 29/02)."""
    try:
        return d.replace(year=d.year + so_nam)
    except ValueError:
        return d.replace(year=d.year + so_nam, day=28)


def lay_gioi_han_lich():
    """Cửa sổ xem thời khóa biểu: tối đa 2 năm trước/sau hôm nay, kẹp trong 2020-2030."""
    hom_nay = date.today()
    ngay_min = max(cong_nam(hom_nay, -2), date(NAM_MIN, 1, 1))
    ngay_max = min(cong_nam(hom_nay, 2), date(NAM_MAX, 12, 31))
    return ngay_min, ngay_max


def dau_tuan_cua(d):
    return d - timedelta(days=d.weekday())


def chuan_hoa_thu(thu):
    """'Thứ 2' / 'thứ hai' / 'CN' -> '2'..'8' (8 = Chủ nhật); không nhận ra thì trả về chuỗi đã chuẩn hóa."""
    if thu is None:
        return ""
    s = unicodedata.normalize("NFD", str(thu).strip().lower())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn").replace("đ", "d")
    s = re.sub(r"\s+", " ", s)
    ten = {"thu hai": "2", "thu ba": "3", "thu tu": "4", "thu nam": "5", "thu sau": "6",
           "thu bay": "7", "chu nhat": "8", "cn": "8"}
    if s in ten:
        return ten[s]
    so = re.search(r"\d+", s)
    return str(int(so.group(0))) if so else s


def chi_so_thu(thu):
    """Chỉ số cột 0..6 (Thứ 2 .. Chủ nhật) hoặc None nếu không hợp lệ."""
    n = chuan_hoa_thu(thu)
    return int(n) - 2 if n.isdigit() and 2 <= int(n) <= 8 else None


def tach_tiet(text):
    """'1-3', '1–3', '1,2,3', '4 đến 6' -> {1,2,3}. Chỉ nhận tiết 1..16."""
    s = unicodedata.normalize("NFKC", str(text or "")).lower()
    s = re.sub(r"\b(đến|tới|to)\b", "-", s)
    tiet = set()

    def them_khoang(m):
        a, b = int(m.group(1)), int(m.group(2))
        if 1 <= a <= b <= MAX_TIET:
            tiet.update(range(a, b + 1))
        return " "

    con_lai = re.sub(r"(?<!\d)(\d+)\s*[-–—]\s*(\d+)(?!\d)", them_khoang, s)
    tiet.update(n for n in map(int, re.findall(r"\d+", con_lai)) if 1 <= n <= MAX_TIET)
    return tiet


def nhom_tiet(tiet):
    """{1,2,3,7,8} -> [(1,3),(7,8)]."""
    cac_doan, dau, cuoi = [], None, None
    for t in sorted(tiet):
        if dau is None:
            dau = cuoi = t
        elif t == cuoi + 1:
            cuoi = t
        else:
            cac_doan.append((dau, cuoi))
            dau = cuoi = t
    if dau is not None:
        cac_doan.append((dau, cuoi))
    return cac_doan


def dinh_dang_tiet(tiet):
    return ", ".join(f"{a}-{b}" if a != b else str(a) for a, b in nhom_tiet(tiet))


def tiet_tu_gio(gio):
    """Quy đổi giờ thi (HH:MM) của dữ liệu cũ sang tiết thi gần nhất không muộn hơn giờ đó."""
    try:
        h, m = map(int, str(gio).split(":"))
    except (ValueError, TypeError):
        return 1
    phut = h * 60 + m
    ket_qua = 1
    for t, g in GIO_THI_THEO_TIET.items():
        gh, gm = map(int, g.split(":"))
        if gh * 60 + gm <= phut:
            ket_qua = t
    return ket_qua


def khoang_ngay(lhp):
    """(ngày bắt đầu, ngày kết thúc) của lớp; thiếu thì lấy theo cả năm lịch."""
    nam = to_int(lhp.get("nam_lich"), date.today().year)
    bd = parse_date(lhp.get("ngay_bat_dau")) or date(nam, 1, 1)
    kt = parse_date(lhp.get("ngay_ket_thuc")) or date(nam, 12, 31)
    return bd, kt


def tiet_trung(a, b):
    """Danh sách tiết giao nhau giữa hai lớp (cùng thứ, khoảng ngày chồng nhau); rỗng nếu không trùng."""
    da, db = chi_so_thu(a.get("thu")), chi_so_thu(b.get("thu"))
    if da is None or da != db:
        return []
    chung = tach_tiet(a.get("tiet_hoc")) & tach_tiet(b.get("tiet_hoc"))
    if not chung:
        return []
    (a1, a2), (b1, b2) = khoang_ngay(a), khoang_ngay(b)
    if a2 < b1 or b2 < a1:
        return []
    return sorted(chung)


# ----------------------------------------------------------------------------
# Mật khẩu (PBKDF2-SHA256, không lưu văn bản thường)
# ----------------------------------------------------------------------------
_PBKDF2_VONG = 120_000


def hash_password(mat_khau):
    muoi = secrets.token_hex(8)
    dk = hashlib.pbkdf2_hmac("sha256", mat_khau.encode("utf-8"), muoi.encode(), _PBKDF2_VONG).hex()
    return f"pbkdf2${_PBKDF2_VONG}${muoi}${dk}"


def verify_password(mat_khau, da_luu):
    try:
        kieu, vong, muoi, dk = str(da_luu).split("$")
        if kieu != "pbkdf2":
            return False
        thu = hashlib.pbkdf2_hmac("sha256", mat_khau.encode("utf-8"), muoi.encode(), int(vong)).hex()
        return hmac.compare_digest(thu, dk)
    except (ValueError, TypeError):
        return False


def public_user(u):
    """Bản sao tài khoản không chứa mật khẩu."""
    return {k: v for k, v in u.items() if k != "mat_khau_hash"}


# ----------------------------------------------------------------------------
# Lưu trữ JSON: cache theo mtime, ghi nguyên tử, sao lưu
# ----------------------------------------------------------------------------
class Store:
    def __init__(self, folder=BASE_DIR):
        self.folder = folder
        self._cache = {}

    def path(self, name):
        return os.path.join(self.folder, f"{name}.json")

    def exists(self, name):
        return os.path.exists(self.path(name))

    @staticmethod
    def _rong(name):
        return _KIEU_RONG.get(name, list)()

    def load(self, name):
        p = self.path(name)
        try:
            st = os.stat(p)
        except OSError:
            return self._rong(name)
        khoa = (st.st_mtime_ns, st.st_size)
        hit = self._cache.get(name)
        if not hit or hit[0] != khoa:
            try:
                with open(p, "r", encoding="utf-8-sig") as f:
                    noi_dung = f.read()
                data = json.loads(noi_dung) if noi_dung.strip() else self._rong(name)
            except (OSError, ValueError) as loi:
                raise DuLieuError(f"Không đọc được {name}.json: {loi}") from loi
            if not isinstance(data, type(self._rong(name))):
                raise DuLieuError(f"{name}.json có cấu trúc không đúng (cần {type(self._rong(name)).__name__}).")
            self._cache[name] = (khoa, data)
        return copy.deepcopy(self._cache[name][1])

    def save(self, name, data):
        p = self.path(name)
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
        st = os.stat(p)
        self._cache[name] = ((st.st_mtime_ns, st.st_size), copy.deepcopy(data))


# ----------------------------------------------------------------------------
# Dịch vụ nghiệp vụ
# ----------------------------------------------------------------------------
def _so_tc(mon, lhp=None):
    return to_int(mon.get("so_tin_chi", mon.get("so_tc", (lhp or {}).get("so_tin_chi", 3))), 3)


def _ten_mon(mon, lhp):
    return mon.get("ten_mh") or lhp.get("ten_mon") or lhp.get("ma_mh", "")


class Service:
    def __init__(self, folder=BASE_DIR):
        self.store = Store(folder)

    # ------------------------------------------------------------------ khởi tạo
    def khoi_tao(self):
        """Tạo dữ liệu mẫu còn thiếu, chuẩn hóa dữ liệu cũ (v1-v23) và băm mật khẩu. Idempotent."""
        st = self.store
        self.sao_luu()                              # luôn có bản dự phòng trước khi chuẩn hóa

        users = st.load("users")
        doi = False
        for u in users:
            if u.get("ma_nd") == ADMIN_ID and u.get("vai_tro") != "admin":
                u["vai_tro"], doi = "admin", True
        if not any(u.get("vai_tro") == "admin" for u in users):
            users.append({"ma_nd": ADMIN_ID, "mat_khau_hash": hash_password(ADMIN_MAT_KHAU_MAC_DINH),
                          "ho_ten": "Quản Trị Viên", "vai_tro": "admin",
                          "trang_thai": "hoat_dong", "khoa_den": ""})
            doi = True
        for u in users:
            if "mat_khau" in u:                     # dữ liệu cũ: mật khẩu văn bản thường
                u["mat_khau_hash"] = hash_password(str(u.pop("mat_khau")))
                doi = True
            if not u.get("mat_khau_hash"):
                u["mat_khau_hash"] = hash_password(f"{u.get('ma_nd', '')}@123")
                doi = True
            for k, v in (("trang_thai", "hoat_dong"), ("khoa_den", "")):
                if k not in u:
                    u[k], doi = v, True
        if doi:
            st.save("users", users)

        cfg = st.load("config")
        doi = any(k not in cfg for k in CONFIG_MAC_DINH) or "so_hoc_phan_moi_dot" in cfg
        if doi:
            for k, v in CONFIG_MAC_DINH.items():
                cfg.setdefault(k, v)
            cfg.pop("so_hoc_phan_moi_dot", None)
            st.save("config", cfg)

        if not st.exists("monhoc"):
            st.save("monhoc", [
                {"ma_mh": "INT101", "ten_mh": "Lập trình Python", "so_tin_chi": 3, "tien_quyet": ""},
                {"ma_mh": "INT102", "ten_mh": "Cơ sở dữ liệu", "so_tin_chi": 3, "tien_quyet": "INT101"}])
        try:
            self.nap_danh_muc()
        except DuLieuError:
            pass                                    # danh mục mở rộng hỏng không được làm hỏng ứng dụng

        cfg = self.cau_hinh()
        if not st.exists("lophocphan"):
            st.save("lophocphan", [{
                "ma_lhp": "LHP01", "ma_mh": "INT101", "ten_giang_vien": "Nguyễn Văn A", "thu": "Thứ 2",
                "tiet_hoc": "1-3", "phong_hoc": "B302", "si_so_toi_da": 40, "loai_lich": "Lý thuyết",
                "trang_thai_lich": TT_BINH_THUONG, "nam_lich": date.today().year,
                "hoc_phi_moi_tin_chi": cfg["hoc_phi_ly_thuyet_moi_tin_chi"], "lop_hoc_du_kien": "DHTI16A",
                "nhom_th": "—", "danh_sach_sv": [], "dot_theo_sv": {}, "ngay_dk_theo_sv": {}}])
        lops = st.load("lophocphan")
        doi = False
        for lhp in lops:
            mac_dinh = {"nam_lich": date.today().year, "dot_theo_sv": {}, "ngay_dk_theo_sv": {},
                        "danh_sach_sv": [], "nhom_th": "—", "lop_hoc_du_kien": "",
                        "trang_thai_lich": TT_BINH_THUONG, "loai_lich": LOAI_LICH[0],
                        "hoc_phi_moi_tin_chi": cfg["hoc_phi_thuc_hanh_moi_tin_chi"]
                        if lhp.get("loai_lich") == LOAI_LICH[1] else cfg["hoc_phi_ly_thuyet_moi_tin_chi"]}
            for k, v in mac_dinh.items():
                if k not in lhp:
                    lhp[k], doi = v, True
            for k in ("ngay_bat_dau", "ngay_ket_thuc"):   # thống nhất định dạng ISO
                d = parse_date(lhp.get(k))
                if d and lhp.get(k) != d.isoformat():
                    lhp[k], doi = d.isoformat(), True
        if doi:
            st.save("lophocphan", lops)

        for ten in ("thanhtoan", "lichthi"):
            if not st.exists(ten):
                st.save(ten, [])
        lichs = st.load("lichthi")
        if any("id" not in x for x in lichs):
            for x in lichs:
                x.setdefault("id", uuid.uuid4().hex[:10])
            st.save("lichthi", lichs)

    def sao_luu(self, giu=10):
        """Sao chép các tệp dữ liệu vào backup/<thời gian>/, chỉ giữ `giu` bản gần nhất."""
        co = [n for n in DATA_FILES if self.store.exists(n)]
        if not co:
            return None
        goc = os.path.join(self.store.folder, "backup")
        dich = os.path.join(goc, datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(dich, exist_ok=True)
        for n in co:
            shutil.copy2(self.store.path(n), dich)
        cac_ban = sorted(d for d in os.listdir(goc) if os.path.isdir(os.path.join(goc, d)))
        for d in cac_ban[:-giu]:
            shutil.rmtree(os.path.join(goc, d), ignore_errors=True)
        return dich

    # ------------------------------------------------------------------ truy vấn cơ bản
    def cau_hinh(self):
        cfg = dict(CONFIG_MAC_DINH)
        cfg.update(self.store.load("config"))
        for k in _CONFIG_SO:
            cfg[k] = to_int(cfg.get(k), CONFIG_MAC_DINH[k])
        return cfg

    def sinh_vien(self):
        return [public_user(u) for u in self.store.load("users") if u.get("vai_tro") == "sinh_vien"]

    def get_user(self, ma_nd):
        u = next((x for x in self.store.load("users") if x.get("ma_nd") == ma_nd), None)
        return public_user(u) if u else None

    def mon_hoc(self):
        return self.store.load("monhoc")

    def mon_map(self):
        return {m.get("ma_mh"): m for m in self.mon_hoc()}

    def lop_hoc_phan(self):
        return [x for x in self.store.load("lophocphan") if x.get("loai_lich") != LOAI_DI_THI]

    def get_lhp(self, ma_lhp):
        return next((x for x in self.lop_hoc_phan() if x.get("ma_lhp") == ma_lhp), None)

    # ------------------------------------------------------------------ tài khoản
    def tu_dong_mo_khoa(self):
        users, now, doi = self.store.load("users"), datetime.now(), False
        for u in users:
            if u.get("trang_thai") == "bi_khoa" and u.get("khoa_den"):
                try:
                    if now > datetime.strptime(u["khoa_den"], FMT_DATETIME):
                        u["trang_thai"], u["khoa_den"], doi = "hoat_dong", "", True
                except ValueError:
                    u["trang_thai"], u["khoa_den"], doi = "hoat_dong", "", True
        if doi:
            self.store.save("users", users)

    def dang_nhap(self, ma_nd, mat_khau):
        ma_nd = str(ma_nd).strip()
        if not ma_nd or not mat_khau:
            raise NghiepVuError("Vui lòng nhập đầy đủ mã tài khoản và mật khẩu.")
        self.tu_dong_mo_khoa()
        u = next((x for x in self.store.load("users")
                  if str(x.get("ma_nd", "")).lower() == ma_nd.lower()), None)
        if not u or not verify_password(mat_khau, u.get("mat_khau_hash", "")):
            raise NghiepVuError("Sai mã tài khoản hoặc mật khẩu.")
        if u.get("trang_thai") == "bi_khoa":
            raise NghiepVuError(f"Tài khoản đang bị khóa đến {u.get('khoa_den') or 'khi quản trị viên mở khóa'}.")
        return public_user(u)

    def dang_dung_mat_khau_mac_dinh(self):
        """True nếu admin vẫn dùng mật khẩu demo (để màn hình đăng nhập hiện gợi ý)."""
        u = next((x for x in self.store.load("users") if x.get("ma_nd") == ADMIN_ID), None)
        return bool(u) and verify_password(ADMIN_MAT_KHAU_MAC_DINH, u.get("mat_khau_hash", ""))

    def goi_y_demo(self):
        """Các tài khoản demo còn dùng mật khẩu mặc định: [(mã, mật khẩu, nhãn)] - để màn hình đăng nhập gợi ý."""
        mac_dinh = ((ADMIN_ID, ADMIN_MAT_KHAU_MAC_DINH, "Quản trị viên"), ("SV01", "SV01@123", "Sinh viên"))
        users = {u.get("ma_nd"): u for u in self.store.load("users")}
        return [(ma, mk, nhan) for ma, mk, nhan in mac_dinh
                if ma in users and verify_password(mk, users[ma].get("mat_khau_hash", ""))]

    def tom_tat_sinh_vien(self):
        """({mssv: số lớp đã đăng ký}, {mssv: học phí còn nợ}) - tính một lượt cho bảng quản trị."""
        so_lop, no = {}, {}
        for lhp in self.lop_hoc_phan():
            for ma in lhp.get("danh_sach_sv", []):
                so_lop[ma] = so_lop.get(ma, 0) + 1
        for p in self.store.load("thanhtoan"):
            if self.chua_dong(p):
                no[p.get("ma_nd")] = no.get(p.get("ma_nd"), 0) + to_int(p.get("so_tien"))
        return so_lop, no

    def doi_mat_khau(self, ma_nd, cu, moi):
        if len(moi) < 6:
            raise NghiepVuError("Mật khẩu mới phải có ít nhất 6 ký tự.")
        if moi == cu:
            raise NghiepVuError("Mật khẩu mới phải khác mật khẩu hiện tại.")
        users = self.store.load("users")
        u = next((x for x in users if x.get("ma_nd") == ma_nd), None)
        if not u or not verify_password(cu, u.get("mat_khau_hash", "")):
            raise NghiepVuError("Mật khẩu hiện tại không đúng.")
        u["mat_khau_hash"] = hash_password(moi)
        self.store.save("users", users)

    def _tim_sv(self, users, ma_nd):
        u = next((x for x in users if x.get("ma_nd") == ma_nd and x.get("vai_tro") == "sinh_vien"), None)
        if not u:
            raise NghiepVuError(f"Không tìm thấy sinh viên {ma_nd}.")
        return u

    def tao_sinh_vien(self, mssv, ho_ten, nganh="CNTT", lop="", gpa=3.0):
        mssv, ho_ten = str(mssv).strip(), " ".join(str(ho_ten).split())
        if not mssv or not ho_ten:
            raise NghiepVuError("Nhập đầy đủ MSSV và họ tên.")
        if not re.fullmatch(r"[A-Za-z0-9_-]{3,20}", mssv):
            raise NghiepVuError("MSSV chỉ gồm chữ, số, gạch ngang/gạch dưới (3–20 ký tự).")
        users = self.store.load("users")
        if any(str(u.get("ma_nd", "")).lower() == mssv.lower() for u in users):
            raise NghiepVuError("Mã sinh viên này đã tồn tại.")
        gpa = to_float(gpa, -1)
        if not 0 <= gpa <= 4:
            raise NghiepVuError("GPA phải nằm trong khoảng 0–4.")
        so = 0
        for u in users:
            if u.get("vai_tro") == "sinh_vien":
                so = max(so, to_int(u.get("so_thu_tu_tao")))
                m = re.fullmatch(r"SV(\d+)", str(u.get("ma_nd", "")).upper())
                if m:
                    so = max(so, int(m.group(1)))
        so += 1
        mat_khau = f"SV{so:02d}@123"
        lop = str(lop).strip()
        if not lop:
            cac_lop = sorted({str(x.get("lop_hoc_du_kien", "")).strip() for x in self.lop_hoc_phan()} - {""})
            lop = random.choice(cac_lop or list(LOP_MAU))
        users.append({"ma_nd": mssv, "mat_khau_hash": hash_password(mat_khau), "so_thu_tu_tao": so,
                      "ho_ten": ho_ten, "vai_tro": "sinh_vien", "nganh": str(nganh).strip() or "CNTT",
                      "lop": lop, "da_dong_hoc_phi": True, "gpa": round(gpa, 2), "canh_bao_hoc_vu": 0,
                      "trang_thai": "hoat_dong", "khoa_den": ""})
        self.store.save("users", users)
        return {"ma_nd": mssv, "lop": lop, "mat_khau": mat_khau}

    def cap_nhat_sinh_vien(self, ma_nd, ho_ten, nganh, lop, gpa, canh_bao, da_dong_hoc_phi):
        users = self.store.load("users")
        u = self._tim_sv(users, ma_nd)
        ho_ten = " ".join(str(ho_ten).split())
        gpa = to_float(gpa, -1)
        if not ho_ten:
            raise NghiepVuError("Họ tên không được để trống.")
        if not 0 <= gpa <= 4:
            raise NghiepVuError("GPA phải nằm trong khoảng 0–4.")
        canh_bao = to_int(canh_bao, -1)
        if not 0 <= canh_bao <= 5:
            raise NghiepVuError("Số lần cảnh báo học vụ phải từ 0 đến 5.")
        u.update(ho_ten=ho_ten, nganh=str(nganh).strip(), lop=str(lop).strip(), gpa=round(gpa, 2),
                 canh_bao_hoc_vu=canh_bao, da_dong_hoc_phi=bool(da_dong_hoc_phi))
        self.store.save("users", users)

    def dat_lai_mat_khau(self, ma_nd):
        users = self.store.load("users")
        u = self._tim_sv(users, ma_nd)
        mat_khau = f"{ma_nd}@123"
        u["mat_khau_hash"] = hash_password(mat_khau)
        self.store.save("users", users)
        return mat_khau

    def khoa_tai_khoan(self, ma_nd, so_ngay):
        so_ngay = to_int(so_ngay, 0)
        if not 1 <= so_ngay <= 365:
            raise NghiepVuError("Số ngày khóa phải từ 1 đến 365.")
        users = self.store.load("users")
        u = self._tim_sv(users, ma_nd)
        u["trang_thai"] = "bi_khoa"
        u["khoa_den"] = (datetime.now() + timedelta(days=so_ngay)).strftime(FMT_DATETIME)
        self.store.save("users", users)
        return u["khoa_den"]

    def mo_khoa_tai_khoan(self, ma_nd):
        users = self.store.load("users")
        u = self._tim_sv(users, ma_nd)
        u["trang_thai"], u["khoa_den"] = "hoat_dong", ""
        self.store.save("users", users)

    def xoa_sinh_vien(self, ma_nd):
        """Xóa tài khoản và dọn đăng ký, học phí, lịch thi liên quan. Trả về thống kê đã xóa."""
        users = self.store.load("users")
        self._tim_sv(users, ma_nd)
        self.store.save("users", [u for u in users if u.get("ma_nd") != ma_nd])
        lops, so_dk = self.store.load("lophocphan"), 0
        for lhp in lops:
            if ma_nd in lhp.get("danh_sach_sv", []):
                lhp["danh_sach_sv"].remove(ma_nd)
                so_dk += 1
            lhp.get("dot_theo_sv", {}).pop(ma_nd, None)
            lhp.get("ngay_dk_theo_sv", {}).pop(ma_nd, None)
        self.store.save("lophocphan", lops)
        pays = self.store.load("thanhtoan")
        con_lai = [p for p in pays if p.get("ma_nd") != ma_nd]
        self.store.save("thanhtoan", con_lai)
        lichs = self.store.load("lichthi")
        lich_con = [x for x in lichs if x.get("ma_nd") != ma_nd]
        self.store.save("lichthi", lich_con)
        return {"dang_ky": so_dk, "hoc_phi": len(pays) - len(con_lai), "lich_thi": len(lichs) - len(lich_con)}

    # ------------------------------------------------------------------ môn học
    def nap_danh_muc(self):
        """Bổ sung danh_muc_mon_hoc.json vào monhoc.json (bỏ qua môn trùng mã hoặc trùng tên)."""
        if not self.store.exists("danh_muc_mon_hoc"):
            return 0
        mons = self.mon_hoc()
        ma_co = {str(m.get("ma_mh", "")).upper() for m in mons}
        ten_co = {str(m.get("ten_mh", "")).strip().casefold() for m in mons}
        them = 0
        for m in self.store.load("danh_muc_mon_hoc"):
            ma, ten = str(m.get("ma_mh", "")).upper(), str(m.get("ten_mh", "")).strip().casefold()
            if ma and ten and ma not in ma_co and ten not in ten_co:
                mons.append(m)
                ma_co.add(ma)
                ten_co.add(ten)
                them += 1
        if them:
            self.store.save("monhoc", mons)
        return them

    def _kiem_tra_mon(self, ma, ten, tc, tien_quyet, mons, moi):
        ma, ten, tien_quyet = str(ma).strip().upper(), " ".join(str(ten).split()), str(tien_quyet).strip().upper()
        if not ma or not ten:
            raise NghiepVuError("Vui lòng nhập mã môn học và tên môn học.")
        if not re.fullmatch(r"[A-Z0-9_-]{2,20}", ma):
            raise NghiepVuError("Mã môn chỉ gồm chữ in hoa, số, gạch ngang hoặc gạch dưới (2–20 ký tự).")
        tc = to_int(tc, 0)
        if not 1 <= tc <= 10:
            raise NghiepVuError("Số tín chỉ phải từ 1 đến 10.")
        if moi and any(str(m.get("ma_mh", "")).upper() == ma for m in mons):
            raise NghiepVuError(f"Mã môn {ma} đã tồn tại.")
        if tien_quyet:
            if tien_quyet == ma:
                raise NghiepVuError("Một môn học không thể là tiên quyết của chính nó.")
            theo_ma = {str(m.get("ma_mh", "")).upper(): m for m in mons}
            if tien_quyet not in theo_ma:
                raise NghiepVuError(f"Mã môn tiên quyết {tien_quyet} chưa tồn tại. Hãy để trống nếu không có.")
            cur, da_di = tien_quyet, set()          # chống vòng lặp tiên quyết
            while cur and cur not in da_di:
                if cur == ma:
                    raise NghiepVuError("Môn tiên quyết tạo thành vòng lặp (A cần B, B cần A).")
                da_di.add(cur)
                cur = str(theo_ma.get(cur, {}).get("tien_quyet", "")).upper()
        return ma, ten, tc, tien_quyet

    def them_mon(self, ma, ten, tc, tien_quyet="", nganh=""):
        mons = self.mon_hoc()
        ma, ten, tc, tq = self._kiem_tra_mon(ma, ten, tc, tien_quyet, mons, moi=True)
        mon = {"ma_mh": ma, "ten_mh": ten, "so_tin_chi": tc, "tien_quyet": tq}
        if str(nganh).strip():
            mon["nganh_ap_dung"] = str(nganh).strip()
        mons.append(mon)
        mons.sort(key=lambda m: str(m.get("ma_mh", "")))
        self.store.save("monhoc", mons)
        return mon

    def cap_nhat_mon(self, ma, ten, tc, tien_quyet="", nganh=""):
        mons = self.mon_hoc()
        mon = next((m for m in mons if m.get("ma_mh") == ma), None)
        if not mon:
            raise NghiepVuError(f"Không tìm thấy môn {ma}.")
        _, ten, tc, tq = self._kiem_tra_mon(ma, ten, tc, tien_quyet, mons, moi=False)
        mon.update(ten_mh=ten, so_tin_chi=tc, tien_quyet=tq)
        mon.pop("so_tc", None)
        if str(nganh).strip():
            mon["nganh_ap_dung"] = str(nganh).strip()
        else:
            mon.pop("nganh_ap_dung", None)
        self.store.save("monhoc", mons)

    def xoa_mon(self, ma):
        mons = self.mon_hoc()
        if not any(m.get("ma_mh") == ma for m in mons):
            raise NghiepVuError(f"Không tìm thấy môn {ma}.")
        dung = [x["ma_lhp"] for x in self.lop_hoc_phan() if x.get("ma_mh") == ma]
        if dung:
            raise NghiepVuError(f"Không thể xóa: môn đang có {len(dung)} lớp học phần ({', '.join(dung[:5])}"
                                f"{'…' if len(dung) > 5 else ''}). Hãy xóa các lớp này trước.")
        phu_thuoc = [m["ma_mh"] for m in mons if str(m.get("tien_quyet", "")).upper() == ma.upper()]
        if phu_thuoc:
            raise NghiepVuError(f"Không thể xóa: môn là tiên quyết của {', '.join(phu_thuoc[:5])}.")
        self.store.save("monhoc", [m for m in mons if m.get("ma_mh") != ma])

    # ------------------------------------------------------------------ lớp học phần
    def don_gia(self, lhp, cfg=None):
        gia = to_int(lhp.get("hoc_phi_moi_tin_chi"), 0)
        if gia > 0:
            return gia
        cfg = cfg or self.cau_hinh()
        return cfg["hoc_phi_thuc_hanh_moi_tin_chi" if lhp.get("loai_lich") == LOAI_LICH[1]
                   else "hoc_phi_ly_thuyet_moi_tin_chi"]

    def _ma_lhp_moi(self, ds):
        da_co = {str(x.get("ma_lhp", "")).upper() for x in ds}
        while True:
            ma = ("LHP" + "".join(random.choices(string.ascii_uppercase, k=2))
                  + "".join(random.choices(string.digits, k=3)))
            if ma not in da_co:
                return ma

    def _xung_dot_tai_nguyen(self, lhp, cac_lop):
        """Phòng hoặc giảng viên bị chồng lịch với lớp khác (bỏ qua lớp đang tạm ngưng)."""
        gv, phong = str(lhp.get("ten_giang_vien", "")).strip().casefold(), str(lhp.get("phong_hoc", "")).strip().casefold()
        for o in cac_lop:
            if o.get("ma_lhp") == lhp.get("ma_lhp") or o.get("trang_thai_lich") == TT_TAM_NGUNG:
                continue
            chung = tiet_trung(lhp, o)
            if not chung:
                continue
            mo_ta = f"{o.get('ma_lhp')} ({o.get('thu')}, tiết {o.get('tiet_hoc')})"
            if phong and phong == str(o.get("phong_hoc", "")).strip().casefold():
                return f"Phòng {lhp.get('phong_hoc')} đã có lớp {mo_ta} cùng thời gian."
            if gv and gv == str(o.get("ten_giang_vien", "")).strip().casefold():
                return f"Giảng viên {lhp.get('ten_giang_vien')} đã dạy lớp {mo_ta} cùng thời gian."
        return None

    def _chuan_hoa_lhp(self, d, cfg, mons):
        ma_mh = str(d.get("ma_mh", "")).strip()
        if ma_mh not in mons:
            raise NghiepVuError("Vui lòng chọn môn học hợp lệ.")
        gv, phong = " ".join(str(d.get("ten_giang_vien", "")).split()), str(d.get("phong_hoc", "")).strip()
        lop = str(d.get("lop_hoc_du_kien", "")).strip()
        if not (gv and phong and lop):
            raise NghiepVuError("Vui lòng nhập đầy đủ giảng viên, phòng học và lớp dự kiến.")
        idx = chi_so_thu(d.get("thu"))
        if idx is None:
            raise NghiepVuError("Vui lòng chọn thứ học hợp lệ.")
        tiet = tach_tiet(d.get("tiet_hoc"))
        if not tiet:
            raise NghiepVuError(f"Tiết học không hợp lệ. Nhập dạng 1-3 hoặc 1,2,3 (tiết từ 1 đến {MAX_TIET}).")
        loai = d.get("loai_lich") or LOAI_LICH[0]
        if loai not in LOAI_LICH:
            raise NghiepVuError("Loại lịch phải là Lý thuyết hoặc Thực hành.")
        trang_thai = d.get("trang_thai_lich") or TT_BINH_THUONG
        if trang_thai not in (TT_BINH_THUONG, TT_TAM_NGUNG):
            raise NghiepVuError("Trạng thái lớp không hợp lệ.")
        gioi_han = cfg["si_so_toi_da_moi_lop"]
        si_so = to_int(d.get("si_so_toi_da"), -1)
        if not 1 <= si_so <= gioi_han:
            raise NghiepVuError(f"Sĩ số tối đa phải từ 1 đến {gioi_han} (giới hạn trong cấu hình).")
        phi = to_int(d.get("hoc_phi_moi_tin_chi"), 0)
        if phi <= 0:
            raise NghiepVuError("Giá tín chỉ phải là số nguyên dương.")
        phi_lt = cfg["hoc_phi_ly_thuyet_moi_tin_chi"]
        if loai == LOAI_LICH[1] and phi <= phi_lt:
            raise NghiepVuError(f"Giá tín chỉ lớp thực hành phải cao hơn giá lý thuyết ({fmt_money(phi_lt)} VNĐ).")
        bd, kt = parse_date(d.get("ngay_bat_dau")), parse_date(d.get("ngay_ket_thuc"))
        if not bd or not kt:
            raise NghiepVuError("Ngày bắt đầu/kết thúc không hợp lệ (định dạng dd/mm/yyyy).")
        if kt < bd:
            raise NghiepVuError("Ngày kết thúc phải bằng hoặc sau ngày bắt đầu.")
        if not (NAM_MIN <= bd.year <= NAM_MAX and NAM_MIN <= kt.year <= NAM_MAX):
            raise NghiepVuError(f"Ngày bắt đầu và kết thúc phải nằm trong khoảng năm {NAM_MIN}–{NAM_MAX}.")
        return {"ma_mh": ma_mh, "ten_giang_vien": gv, "thu": THU[idx], "tiet_hoc": dinh_dang_tiet(tiet),
                "phong_hoc": phong, "si_so_toi_da": si_so, "loai_lich": loai, "trang_thai_lich": trang_thai,
                "nam_lich": bd.year, "ngay_bat_dau": bd.isoformat(), "ngay_ket_thuc": kt.isoformat(),
                "hoc_phi_moi_tin_chi": phi, "lop_hoc_du_kien": lop,
                "nhom_th": str(d.get("nhom_th", "")).strip() or "—"}

    def tao_lhp(self, d):
        raw, cfg = self.store.load("lophocphan"), self.cau_hinh()
        data = self._chuan_hoa_lhp(d, cfg, self.mon_map())
        ma = str(d.get("ma_lhp", "")).strip().upper() or self._ma_lhp_moi(raw)
        if not re.fullmatch(r"[A-Z0-9_-]{2,20}", ma):
            raise NghiepVuError("Mã lớp học phần chỉ gồm chữ in hoa, số, gạch ngang/gạch dưới (2–20 ký tự).")
        if any(str(x.get("ma_lhp", "")).upper() == ma for x in raw):
            raise NghiepVuError("Mã lớp học phần đã tồn tại. Vui lòng nhập mã khác.")
        data["ma_lhp"] = ma
        loi = self._xung_dot_tai_nguyen(data, raw)
        if loi:
            raise NghiepVuError(loi)
        data.update(danh_sach_sv=[], dot_theo_sv={}, ngay_dk_theo_sv={})
        raw.append(data)
        raw.sort(key=lambda x: str(x.get("ma_lhp", "")))
        self.store.save("lophocphan", raw)
        return data

    def sua_lhp(self, ma_lhp, d):
        raw = self.store.load("lophocphan")
        lhp = next((x for x in raw if x.get("ma_lhp") == ma_lhp), None)
        if not lhp:
            raise NghiepVuError("Lớp học phần không còn tồn tại. Hãy làm mới danh sách.")
        data = self._chuan_hoa_lhp(d, self.cau_hinh(), self.mon_map())
        sv = lhp.get("danh_sach_sv", [])
        if data["si_so_toi_da"] < len(sv):
            raise NghiepVuError(f"Sĩ số tối đa không được nhỏ hơn số sinh viên đã đăng ký ({len(sv)}).")
        if sv and data["ma_mh"] != lhp.get("ma_mh"):
            raise NghiepVuError("Không thể đổi môn học của lớp đã có sinh viên đăng ký.")
        moi = {**lhp, **data}
        doi_lich = any(str(moi.get(k)) != str(lhp.get(k)) for k in
                       ("thu", "tiet_hoc", "phong_hoc", "ten_giang_vien", "ngay_bat_dau", "ngay_ket_thuc"))
        if doi_lich:
            khac = [x for x in raw if x.get("ma_lhp") != ma_lhp and x.get("loai_lich") != LOAI_DI_THI]
            loi = self._xung_dot_tai_nguyen(moi, khac)
            if loi:
                raise NghiepVuError(loi)
            for ma_sv in sv:
                kq = self.tim_trung_lich(khac, moi, ma_sv)
                if kq:
                    raise NghiepVuError(f"Lịch mới làm sinh viên {ma_sv} bị trùng với lớp {kq[0].get('ma_lhp')}.")
        lhp.update(data)
        self.store.save("lophocphan", raw)
        return lhp

    def doi_trang_thai_lhp(self, ds_ma, trang_thai):
        if trang_thai not in (TT_BINH_THUONG, TT_TAM_NGUNG):
            raise NghiepVuError("Trạng thái lớp không hợp lệ.")
        raw, tap, dem = self.store.load("lophocphan"), set(ds_ma), 0
        for lhp in raw:
            if lhp.get("ma_lhp") in tap:
                lhp["trang_thai_lich"] = trang_thai
                dem += 1
        if not dem:
            raise NghiepVuError("Không tìm thấy lớp học phần đã chọn. Hãy làm mới danh sách.")
        self.store.save("lophocphan", raw)
        return dem

    def xoa_lhp(self, ma_lhp):
        raw = self.store.load("lophocphan")
        lhp = next((x for x in raw if x.get("ma_lhp") == ma_lhp), None)
        if not lhp:
            raise NghiepVuError("Lớp học phần không còn tồn tại trong dữ liệu.")
        pays = self.store.load("thanhtoan")
        if any(p.get("ma_lhp") == ma_lhp and p.get("trang_thai") == TT_DA_THANH_TOAN for p in pays):
            raise NghiepVuError("Lớp đang có khoản học phí đã thanh toán. Hãy xử lý khoản thanh toán trước khi xóa "
                                "để tránh mất dữ liệu tài chính.")
        self.store.save("lophocphan", [x for x in raw if x.get("ma_lhp") != ma_lhp])
        self.store.save("thanhtoan", [p for p in pays if p.get("ma_lhp") != ma_lhp])
        return len(lhp.get("danh_sach_sv", []))

    def tao_lhp_ngau_nhien(self, so_luong):
        so_luong = to_int(so_luong, 0)
        if not 1 <= so_luong <= 100:
            raise NghiepVuError("Số lượng phải là số nguyên từ 1 đến 100.")
        mons = self.mon_hoc()
        if not mons:
            raise NghiepVuError("Hãy tạo môn học trước khi sinh lớp ngẫu nhiên.")
        raw, cfg = self.store.load("lophocphan"), self.cau_hinh()
        bd = date.today()
        kt = bd + timedelta(days=120)
        tao = 0
        for _ in range(so_luong):
            for _thu in range(40):                  # thử nhiều lần để tránh trùng phòng/giảng viên
                loai = random.choice(LOAI_LICH)
                phi_lt = cfg["hoc_phi_ly_thuyet_moi_tin_chi"]
                lop = {
                    "ma_lhp": self._ma_lhp_moi(raw), "ma_mh": random.choice(mons).get("ma_mh", ""),
                    "ten_giang_vien": random.choice(GIANG_VIEN_MAU), "thu": random.choice(THU[:6]),
                    "tiet_hoc": random.choice(("1-3", "4-6", "7-9", "10-12")), "phong_hoc": random.choice(PHONG_MAU),
                    "si_so_toi_da": min(cfg["si_so_toi_da_moi_lop"], random.choice((30, 35, 40, 45, 50, 60))),
                    "loai_lich": loai, "trang_thai_lich": TT_BINH_THUONG, "nam_lich": bd.year,
                    "ngay_bat_dau": bd.isoformat(), "ngay_ket_thuc": kt.isoformat(),
                    "hoc_phi_moi_tin_chi": (random.randrange(phi_lt + 100000, phi_lt + 800001, 50000)
                                            if loai == LOAI_LICH[1] else random.randrange(500000, phi_lt + 300001, 50000)),
                    "lop_hoc_du_kien": random.choice(LOP_MAU),
                    "nhom_th": f"N{random.randint(1, 6)}" if loai == LOAI_LICH[1] else "—",
                    "danh_sach_sv": [], "dot_theo_sv": {}, "ngay_dk_theo_sv": {}}
                if not self._xung_dot_tai_nguyen(lop, raw):
                    raw.append(lop)
                    tao += 1
                    break
        if tao:
            raw.sort(key=lambda x: str(x.get("ma_lhp", "")))
            self.store.save("lophocphan", raw)
        return tao

    # ------------------------------------------------------------------ đăng ký học phần
    def trang_thai_dang_ky(self, cfg=None):
        """(đang mở?, thông điệp) theo thời gian và đợt đăng ký trong cấu hình."""
        cfg = cfg or self.cau_hinh()
        try:
            bd = datetime.strptime(cfg["thoi_gian_bat_dau"], FMT_DATETIME)
            kt = datetime.strptime(cfg["thoi_gian_ket_thuc"], FMT_DATETIME)
        except (ValueError, TypeError, KeyError):
            return False, "Quản trị viên chưa cấu hình thời gian đăng ký hợp lệ."
        now = datetime.now()
        if now < bd:
            return False, f"Chưa tới thời gian đăng ký (mở lúc {bd:%d/%m/%Y %H:%M})."
        if now > kt:
            return False, f"Đã hết hạn đăng ký (đóng lúc {kt:%d/%m/%Y %H:%M})."
        dot, toi_da = cfg["dot_dang_ky_hien_tai"], cfg["so_dot_toi_da"]
        if not 1 <= dot <= toi_da:
            return False, "Đợt đăng ký hiện tại không hợp lệ hoặc đã vượt số đợt cho phép."
        return True, f"Đang mở · Đợt {dot}/{toi_da} · đến {kt:%d/%m/%Y %H:%M}"

    def tim_trung_lich(self, cac_lop, lhp_moi, ma_nd):
        """(lớp đã đăng ký bị trùng, [tiết trùng]) hoặc None."""
        for cu in cac_lop:
            if cu.get("ma_lhp") == lhp_moi.get("ma_lhp") or ma_nd not in cu.get("danh_sach_sv", []):
                continue
            chung = tiet_trung(lhp_moi, cu)
            if chung:
                return cu, chung
        return None

    def ly_do_khong_dang_ky(self, ma_nd, lhp, cac_lop=None):
        """Lý do không thể đăng ký lớp này (chuỗi, có thể nhiều dòng) hoặc None nếu hợp lệ."""
        sv = self.get_user(ma_nd)
        if not sv or sv.get("vai_tro") != "sinh_vien":
            return "Chỉ tài khoản sinh viên mới được đăng ký học phần."
        if sv.get("trang_thai") == "bi_khoa":
            return "Tài khoản của bạn đang bị khóa."
        mo, thong_bao = self.trang_thai_dang_ky()
        if not mo:
            return thong_bao
        if not sv.get("da_dong_hoc_phi", True):
            return "Bạn chưa đóng học phí đầy đủ các kỳ trước."
        if to_float(sv.get("gpa"), 3.0) < 1.0 or to_int(sv.get("canh_bao_hoc_vu")) >= 2:
            return "Bị hạn chế đăng ký do cảnh báo học vụ."
        if lhp.get("trang_thai_lich") == TT_TAM_NGUNG:
            return "Lớp học phần này đang tạm ngưng."
        ds = lhp.get("danh_sach_sv", [])
        if ma_nd in ds:
            return "Bạn đã đăng ký lớp học phần này rồi."
        cac_lop = self.lop_hoc_phan() if cac_lop is None else cac_lop
        trung_mon = next((o for o in cac_lop if o.get("ma_lhp") != lhp.get("ma_lhp")
                          and o.get("ma_mh") == lhp.get("ma_mh") and ma_nd in o.get("danh_sach_sv", [])), None)
        if trung_mon:
            return (f"Bạn đã đăng ký môn này ở lớp {trung_mon.get('ma_lhp')}. "
                    "Hãy hủy lớp đó trước nếu muốn đổi lớp.")
        mons = self.mon_map()
        tq = mons.get(lhp.get("ma_mh"), {}).get("tien_quyet")
        if tq and not any(o.get("ma_mh") == tq and ma_nd in o.get("danh_sach_sv", []) for o in cac_lop):
            return f"Chưa học học phần tiên quyết: {tq} - {mons.get(tq, {}).get('ten_mh', '')}".rstrip(" -") + "."
        if len(ds) >= to_int(lhp.get("si_so_toi_da"), 40):
            return "Lớp học phần này đã đạt sĩ số tối đa."
        kq = self.tim_trung_lich(cac_lop, lhp, ma_nd)
        if kq:
            cu, tiet = kq
            ten = _ten_mon(mons.get(cu.get("ma_mh"), {}), cu)
            return (f"Trùng lịch học với lớp {cu.get('ma_lhp')} - {ten}\n"
                    f"Lớp đã đăng ký: {cu.get('thu')}, tiết {cu.get('tiet_hoc')}\n"
                    f"Lớp muốn đăng ký: {lhp.get('thu')}, tiết {lhp.get('tiet_hoc')}\n"
                    f"Tiết bị trùng: {', '.join(map(str, tiet))}")
        return None

    def _chuan_bi_dang_ky(self, ma_nd, ma_lhp):
        raw = self.store.load("lophocphan")
        cac_lop = [x for x in raw if x.get("loai_lich") != LOAI_DI_THI]
        lhp = next((x for x in cac_lop if x.get("ma_lhp") == ma_lhp), None)
        if not lhp:
            raise NghiepVuError("Không tìm thấy lớp học phần (có thể đã bị xóa). Hãy làm mới danh sách.")
        ly_do = self.ly_do_khong_dang_ky(ma_nd, lhp, cac_lop)
        if ly_do:
            raise NghiepVuError(ly_do)
        cfg, mon = self.cau_hinh(), self.mon_map().get(lhp.get("ma_mh"), {})
        tc = _so_tc(mon, lhp)
        info = {"ma_lhp": ma_lhp, "ma_mh": lhp.get("ma_mh", ""), "ten_mon": _ten_mon(mon, lhp),
                "tin_chi": tc, "hoc_phi": tc * self.don_gia(lhp, cfg), "dot": cfg["dot_dang_ky_hien_tai"]}
        return raw, lhp, info

    def xem_truoc_dang_ky(self, ma_nd, ma_lhp):
        return self._chuan_bi_dang_ky(ma_nd, ma_lhp)[2]

    def dang_ky(self, ma_nd, ma_lhp):
        raw, lhp, info = self._chuan_bi_dang_ky(ma_nd, ma_lhp)
        lhp.setdefault("danh_sach_sv", []).append(ma_nd)
        lhp.setdefault("dot_theo_sv", {})[ma_nd] = info["dot"]
        lhp.setdefault("ngay_dk_theo_sv", {})[ma_nd] = date.today().strftime(FMT_DATE_VN)
        self.store.save("lophocphan", raw)
        pays = self.store.load("thanhtoan")
        if not any(p.get("ma_nd") == ma_nd and p.get("ma_lhp") == ma_lhp for p in pays):
            pays.append({"ma_nd": ma_nd, "ma_lhp": ma_lhp, "ma_mh": info["ma_mh"], "ten_mon": info["ten_mon"],
                         "so_tin_chi": info["tin_chi"], "so_tien": info["hoc_phi"],
                         "trang_thai": TT_CHUA_THANH_TOAN, "ngay_tao": datetime.now().strftime(FMT_DATETIME)})
            self.store.save("thanhtoan", pays)
        return info

    def ly_do_khong_huy(self, ma_nd, ma_lhp):
        lhp = self.get_lhp(ma_lhp)
        if not lhp or ma_nd not in lhp.get("danh_sach_sv", []):
            return "Bạn chưa đăng ký lớp này."
        if any(p.get("ma_nd") == ma_nd and p.get("ma_lhp") == ma_lhp and p.get("trang_thai") == TT_DA_THANH_TOAN
               for p in self.store.load("thanhtoan")):
            return "Học phần đã được đánh dấu thanh toán. Vui lòng liên hệ quản trị viên để xử lý."
        return None

    def huy_dang_ky(self, ma_nd, ma_lhp):
        ly_do = self.ly_do_khong_huy(ma_nd, ma_lhp)
        if ly_do:
            raise NghiepVuError(ly_do)
        raw = self.store.load("lophocphan")
        lhp = next(x for x in raw if x.get("ma_lhp") == ma_lhp)
        lhp["danh_sach_sv"].remove(ma_nd)
        lhp.get("dot_theo_sv", {}).pop(ma_nd, None)
        lhp.get("ngay_dk_theo_sv", {}).pop(ma_nd, None)
        self.store.save("lophocphan", raw)
        pays = self.store.load("thanhtoan")
        self.store.save("thanhtoan", [p for p in pays if not (p.get("ma_nd") == ma_nd and p.get("ma_lhp") == ma_lhp)])

    def bang_dang_ky(self, ma_nd):
        """Dữ liệu bảng đăng ký cho sinh viên (đã tính sẵn học phí, trạng thái thu phí...)."""
        cfg, mons = self.cau_hinh(), self.mon_map()
        pays = {(p.get("ma_nd"), p.get("ma_lhp")): p for p in self.store.load("thanhtoan")}
        hang = []
        for lhp in self.lop_hoc_phan():
            mon, ds = mons.get(lhp.get("ma_mh"), {}), lhp.get("danh_sach_sv", [])
            tc, da_dk = _so_tc(mon, lhp), ma_nd in lhp.get("danh_sach_sv", [])
            pay = pays.get((ma_nd, lhp.get("ma_lhp")))
            thu_phi = "—"
            if da_dk:
                thu_phi = "Đã thu" if pay and pay.get("trang_thai") == TT_DA_THANH_TOAN else "Chưa thu"
            hang.append({"lhp": lhp, "ma_lhp": lhp.get("ma_lhp", ""), "ma_mh": lhp.get("ma_mh", ""),
                         "ten_mon": _ten_mon(mon, lhp), "tin_chi": tc, "hoc_phi": tc * self.don_gia(lhp, cfg),
                         "da_dk": da_dk, "si_so": len(ds),
                         "si_so_max": to_int(lhp.get("si_so_toi_da"), cfg["si_so_toi_da_moi_lop"]),
                         "thu_phi": thu_phi, "ngay_dk": lhp.get("ngay_dk_theo_sv", {}).get(ma_nd, "—")})
        return hang

    def tong_ket_dang_ky(self, ma_nd):
        da_dk = [h for h in self.bang_dang_ky(ma_nd) if h["da_dk"]]
        return {"so_lop": len(da_dk), "tin_chi": sum(h["tin_chi"] for h in da_dk),
                "hoc_phi": sum(h["hoc_phi"] for h in da_dk)}

    # ------------------------------------------------------------------ học phí / thanh toán
    def khoan_phi_cua(self, ma_nd):
        return [p for p in self.store.load("thanhtoan") if p.get("ma_nd") == ma_nd]

    @staticmethod
    def chua_dong(p):
        return p.get("trang_thai", TT_CHUA_THANH_TOAN) != TT_DA_THANH_TOAN

    def tong_no(self, ma_nd):
        return sum(to_int(p.get("so_tien")) for p in self.khoan_phi_cua(ma_nd) if self.chua_dong(p))

    def thanh_toan_tat_ca(self, ma_nd, phuong_thuc):
        """Ghi nhận thanh toán MÔ PHỎNG cho mọi khoản còn nợ của sinh viên."""
        pays = self.store.load("thanhtoan")
        can_dong = [p for p in pays if p.get("ma_nd") == ma_nd and self.chua_dong(p)]
        if not can_dong:
            raise NghiepVuError("Không còn khoản học phí nào cần thanh toán.")
        now = datetime.now()
        ma_gd = now.strftime("GD%y%m%d%H%M%S")
        for p in can_dong:
            p.update(trang_thai=TT_DA_THANH_TOAN, phuong_thuc=phuong_thuc, ma_giao_dich=ma_gd,
                     ngay_thanh_toan=now.strftime(FMT_DATETIME))
        self.store.save("thanhtoan", pays)
        return {"so_khoan": len(can_dong), "tong": sum(to_int(p.get("so_tien")) for p in can_dong), "ma_gd": ma_gd}

    def hoc_phan_da_dong(self, ma_nd):
        mons = self.mon_map()
        pays = {p.get("ma_lhp"): p for p in self.khoan_phi_cua(ma_nd) if p.get("trang_thai") == TT_DA_THANH_TOAN}
        ket_qua = []
        for lhp in self.lop_hoc_phan():
            if ma_nd in lhp.get("danh_sach_sv", []) and lhp.get("ma_lhp") in pays:
                mon, p = mons.get(lhp.get("ma_mh"), {}), pays[lhp["ma_lhp"]]
                ket_qua.append({"lhp": lhp, "ten_mon": _ten_mon(mon, lhp), "tin_chi": _so_tc(mon, lhp), "phi": p})
        return ket_qua

    # ------------------------------------------------------------------ lịch thi
    def lich_thi(self, ma_nd=None):
        """Lịch thi (kèm tiet_thi đã quy đổi cho dữ liệu cũ), sắp xếp theo ngày và tiết."""
        ket_qua = []
        for x in self.store.load("lichthi"):
            if ma_nd is not None and x.get("ma_nd") != ma_nd:
                continue
            d = parse_date(x.get("ngay"))
            if not d:
                continue
            tiet = to_int(x.get("tiet_thi"), 0)
            tiet = tiet if 1 <= tiet <= MAX_TIET else tiet_tu_gio(x.get("gio", "07:00"))
            ket_qua.append({**x, "ngay_date": d, "tiet_thi": tiet})
        ket_qua.sort(key=lambda x: (x["ngay_date"], x["tiet_thi"]))
        return ket_qua

    def tao_lich_thi(self, ma_nd, mon, ngay, tiet, phong, ghi_chu=""):
        d, tiet = parse_date(ngay), to_int(tiet, 0)
        mon, phong = str(mon).strip(), str(phong).strip()
        if not (ma_nd and mon and phong):
            raise NghiepVuError("Chọn sinh viên, môn thi, ngày, tiết thi và phòng thi.")
        if not d:
            raise NghiepVuError("Ngày thi không hợp lệ (dùng dd/mm/yyyy hoặc YYYY-MM-DD).")
        if tiet not in GIO_THI_THEO_TIET:
            raise NghiepVuError("Tiết thi phải từ 1 đến 16.")
        self._tim_sv(self.store.load("users"), ma_nd)
        if any(x["ma_nd"] == ma_nd and x["ngay_date"] == d and x["tiet_thi"] == tiet for x in self.lich_thi(ma_nd)):
            raise NghiepVuError("Sinh viên đã có lịch thi khác trong cùng ngày và tiết này.")
        lichs = self.store.load("lichthi")
        rec = {"id": uuid.uuid4().hex[:10], "ma_nd": ma_nd, "mon": mon, "ngay": d.isoformat(),
               "gio": GIO_THI_THEO_TIET[tiet], "tiet_thi": tiet, "phong": phong, "ghi_chu": str(ghi_chu).strip()}
        lichs.append(rec)
        self.store.save("lichthi", lichs)
        return rec

    def xoa_lich_thi(self, id_lich):
        lichs = self.store.load("lichthi")
        con_lai = [x for x in lichs if x.get("id") != id_lich]
        if len(con_lai) == len(lichs):
            raise NghiepVuError("Không tìm thấy lịch thi đã chọn. Hãy làm mới danh sách.")
        self.store.save("lichthi", con_lai)

    # ------------------------------------------------------------------ thời khóa biểu
    def su_kien_tuan(self, ma_nd, dau_tuan):
        """Các ô lịch (lớp học + lịch thi) của một sinh viên trong tuần bắt đầu từ `dau_tuan` (thứ 2)."""
        cuoi_tuan, mons, ev = dau_tuan + timedelta(days=6), self.mon_map(), []
        for lhp in self.lop_hoc_phan():
            if ma_nd not in lhp.get("danh_sach_sv", []):
                continue
            bd, kt = khoang_ngay(lhp)
            idx = chi_so_thu(lhp.get("thu"))
            if idx is None or kt < dau_tuan or bd > cuoi_tuan:
                continue
            ten = _ten_mon(mons.get(lhp.get("ma_mh"), {}), lhp)
            loai = "TN" if lhp.get("trang_thai_lich") == TT_TAM_NGUNG else ("TH" if lhp.get("loai_lich") == LOAI_LICH[1] else "LT")
            for a, b in nhom_tiet(tach_tiet(lhp.get("tiet_hoc"))):
                ev.append({"loai": loai, "ngay_idx": idx, "tiet_bd": a, "tiet_kt": b, "tieu_de": ten,
                           "dong2": f"GV: {lhp.get('ten_giang_vien', '')}", "dong3": f"P. {lhp.get('phong_hoc', '')}",
                           "chi_tiet": (f"{lhp.get('ma_lhp')} · {ten}\n{lhp.get('thu')}, tiết {lhp.get('tiet_hoc')} "
                                        f"· Phòng {lhp.get('phong_hoc')}\n"
                                        f"Giảng viên: {lhp.get('ten_giang_vien')} · {lhp.get('loai_lich')} · "
                                        f"{lhp.get('trang_thai_lich')}")})
        for x in self.lich_thi(ma_nd):
            if dau_tuan <= x["ngay_date"] <= cuoi_tuan:
                ev.append({"loai": "THI", "ngay_idx": (x["ngay_date"] - dau_tuan).days,
                           "tiet_bd": x["tiet_thi"], "tiet_kt": x["tiet_thi"], "tieu_de": f"THI: {x.get('mon', '')}",
                           "dong2": f"{x.get('gio', '')} · P. {x.get('phong', '')}", "dong3": x.get("ghi_chu", ""),
                           "chi_tiet": (f"LỊCH THI · {x.get('mon')}\n{x['ngay_date']:%d/%m/%Y} lúc {x.get('gio')} "
                                        f"(tiết {x['tiet_thi']}) · Phòng {x.get('phong')}"
                                        + (f"\nGhi chú: {x['ghi_chu']}" if x.get("ghi_chu") else ""))})
        return ev

    # ------------------------------------------------------------------ thống kê
    def thong_ke_admin(self):
        lops, pays = self.lop_hoc_phan(), self.store.load("thanhtoan")
        paid = sum(to_int(p.get("so_tien")) for p in pays if not self.chua_dong(p))
        no = sum(to_int(p.get("so_tien")) for p in pays if self.chua_dong(p))

        def ti_le(x):
            return len(x.get("danh_sach_sv", [])) / max(1, to_int(x.get("si_so_toi_da"), 1))

        sap_day = sorted((x for x in lops if x.get("danh_sach_sv")), key=ti_le, reverse=True)[:6]
        return {"sinh_vien": len(self.sinh_vien()), "mon_hoc": len(self.mon_hoc()), "lop": len(lops),
                "lop_tam_ngung": sum(1 for x in lops if x.get("trang_thai_lich") == TT_TAM_NGUNG),
                "luot_dk": sum(len(x.get("danh_sach_sv", [])) for x in lops),
                "da_thu": paid, "con_no": no, "lich_thi": len(self.store.load("lichthi")),
                "lop_sap_day": [{"ma_lhp": x["ma_lhp"], "ma_mh": x.get("ma_mh", ""),
                                 "si_so": len(x["danh_sach_sv"]), "toi_da": to_int(x.get("si_so_toi_da"), 1),
                                 "ti_le": ti_le(x)} for x in sap_day]}

    def thong_ke_sinh_vien(self, ma_nd):
        tk = self.tong_ket_dang_ky(ma_nd)
        hom_nay = date.today()
        sap_toi = [x for x in self.lich_thi(ma_nd) if x["ngay_date"] >= hom_nay][:4]
        hom_nay_ev = sorted((e for e in self.su_kien_tuan(ma_nd, dau_tuan_cua(hom_nay))
                             if e["ngay_idx"] == hom_nay.weekday()), key=lambda e: e["tiet_bd"])
        return {**tk, "con_no": self.tong_no(ma_nd), "thi_sap_toi": sap_toi, "hom_nay": hom_nay_ev,
                "so_thi": len(self.lich_thi(ma_nd))}

    # ------------------------------------------------------------------ cấu hình
    def luu_cau_hinh(self, bat_dau, ket_thuc, so_dot, dot_hien_tai, phi_ly_thuyet, phi_thuc_hanh, si_so):
        try:
            bd, kt = datetime.strptime(bat_dau.strip(), FMT_DATETIME), datetime.strptime(ket_thuc.strip(), FMT_DATETIME)
        except ValueError:
            raise NghiepVuError("Thời gian phải có dạng YYYY-MM-DD HH:MM, ví dụ 2026-11-20 08:00.") from None
        if kt <= bd:
            raise NghiepVuError("Thời điểm kết thúc phải sau thời điểm bắt đầu.")
        so_dot, dot = to_int(so_dot, 0), to_int(dot_hien_tai, 0)
        if so_dot < 1 or not 1 <= dot <= so_dot:
            raise NghiepVuError("Đợt hiện tại phải nằm trong khoảng từ 1 đến số đợt tối đa.")
        lt, th, si_so = to_int(phi_ly_thuyet, 0), to_int(phi_thuc_hanh, 0), to_int(si_so, 0)
        if lt <= 0 or th <= lt:
            raise NghiepVuError("Học phí thực hành phải lớn hơn học phí lý thuyết và cả hai phải là số dương.")
        if not 1 <= si_so <= 1000:
            raise NghiepVuError("Sĩ số tối đa mỗi lớp phải từ 1 đến 1000.")
        cfg = self.store.load("config")
        cfg.update(thoi_gian_bat_dau=bat_dau.strip(), thoi_gian_ket_thuc=ket_thuc.strip(), so_dot_toi_da=so_dot,
                   dot_dang_ky_hien_tai=dot, hoc_phi_ly_thuyet_moi_tin_chi=lt, hoc_phi_thuc_hanh_moi_tin_chi=th,
                   hoc_phi_moi_tin_chi=lt, si_so_toi_da_moi_lop=si_so)
        cfg.pop("so_hoc_phan_moi_dot", None)
        self.store.save("config", cfg)
