# -*- coding: utf-8 -*-
"""Kiểm thử lõi nghiệp vụ OneUni. Chạy:  python test_oneuni_core.py   (không cần Tkinter)."""
import json
import os
import shutil
import tempfile
import unittest
from datetime import date

import oneuni_core as core
from oneuni_core import NghiepVuError, Service

AQUI = os.path.dirname(os.path.abspath(__file__))
TEP_MAU = ("config", "users", "monhoc", "danh_muc_mon_hoc", "lophocphan", "lichthi", "thanhtoan")


class CoreTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for n in TEP_MAU:
            shutil.copy(os.path.join(AQUI, f"{n}.json"), self.tmp)
        self.sv = Service(self.tmp)
        self.sv.khoi_tao()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def doc(self, ten):
        with open(os.path.join(self.tmp, f"{ten}.json"), encoding="utf-8") as f:
            return json.load(f)

    def lop_moi(self, **ghi_de):
        d = {"ma_lhp": "", "ma_mh": "CNTT101", "ten_giang_vien": "GV Kiểm Thử", "thu": "Thứ 6",
             "tiet_hoc": "1-3", "phong_hoc": "KT101", "si_so_toi_da": 30, "loai_lich": "Lý thuyết",
             "trang_thai_lich": "Bình thường", "ngay_bat_dau": "01/10/2026", "ngay_ket_thuc": "31/01/2027",
             "hoc_phi_moi_tin_chi": 800000, "lop_hoc_du_kien": "DHTI16A", "nhom_th": ""}
        d.update(ghi_de)
        return d


class TestTienIch(unittest.TestCase):
    def test_tach_tiet(self):
        self.assertEqual(core.tach_tiet("1-3"), {1, 2, 3})
        self.assertEqual(core.tach_tiet("1–3"), {1, 2, 3})
        self.assertEqual(core.tach_tiet("1,2,3"), {1, 2, 3})
        self.assertEqual(core.tach_tiet("4 đến 6"), {4, 5, 6})
        self.assertEqual(core.tach_tiet("1-3, 7-9"), {1, 2, 3, 7, 8, 9})
        self.assertEqual(core.tach_tiet("1-20"), set())
        self.assertEqual(core.tach_tiet(None), set())

    def test_dinh_dang_tiet(self):
        self.assertEqual(core.dinh_dang_tiet({1, 2, 3, 7}), "1-3, 7")
        self.assertEqual(core.nhom_tiet({1, 2, 3, 7, 8}), [(1, 3), (7, 8)])

    def test_chuan_hoa_thu(self):
        for s, k in (("Thứ 2", 0), ("thứ hai", 0), ("Thứ Bảy", 5), ("Chủ Nhật", 6), ("CN", 6), ("Thứ 7", 5)):
            self.assertEqual(core.chi_so_thu(s), k, s)
        self.assertIsNone(core.chi_so_thu("abc"))

    def test_parse_date(self):
        self.assertEqual(core.parse_date("15/10/2026"), date(2026, 10, 15))
        self.assertEqual(core.parse_date("2026-10-15"), date(2026, 10, 15))
        self.assertIsNone(core.parse_date("31/02/2026"))
        self.assertIsNone(core.parse_date(""))

    def test_tiet_trung_va_khoang_ngay(self):
        a = {"thu": "Thứ 2", "tiet_hoc": "1-3", "ngay_bat_dau": "2026-10-01", "ngay_ket_thuc": "2026-12-31"}
        b = {"thu": "Thứ Hai", "tiet_hoc": "3-5", "ngay_bat_dau": "2026-11-01", "ngay_ket_thuc": "2027-02-01"}
        c = {"thu": "Thứ 2", "tiet_hoc": "4-6", "ngay_bat_dau": "2026-10-01", "ngay_ket_thuc": "2026-12-31"}
        d = {"thu": "Thứ 2", "tiet_hoc": "1-3", "ngay_bat_dau": "2027-01-10", "ngay_ket_thuc": "2027-05-01"}
        self.assertEqual(core.tiet_trung(a, b), [3])
        self.assertEqual(core.tiet_trung(a, c), [])
        self.assertEqual(core.tiet_trung(a, d), [])     # cùng thứ/tiết nhưng khác học kỳ

    def test_tiet_tu_gio(self):
        self.assertEqual(core.tiet_tu_gio("18:50"), 14)
        self.assertEqual(core.tiet_tu_gio("07:00"), 1)
        self.assertEqual(core.tiet_tu_gio("12:00"), 6)

    def test_mat_khau(self):
        h = core.hash_password("abc123")
        self.assertTrue(core.verify_password("abc123", h))
        self.assertFalse(core.verify_password("abc124", h))
        self.assertFalse(core.verify_password("abc123", "khong-hop-le"))


class TestKhoiTaoVaDangNhap(CoreTestCase):
    def test_bam_mat_khau_va_dang_nhap(self):
        users = self.doc("users")
        self.assertTrue(all("mat_khau" not in u and u["mat_khau_hash"].startswith("pbkdf2$") for u in users))
        self.assertEqual(self.sv.dang_nhap("admin", "Huit@123")["vai_tro"], "admin")
        self.assertEqual(self.sv.dang_nhap("sv01", "SV01@123")["ma_nd"], "SV01")     # không phân biệt hoa/thường
        self.assertNotIn("mat_khau_hash", self.sv.dang_nhap("SV01", "SV01@123"))
        with self.assertRaises(NghiepVuError):
            self.sv.dang_nhap("SV01", "sai")
        with self.assertRaises(NghiepVuError):
            self.sv.dang_nhap("", "")

    def test_khoi_tao_idempotent_va_khong_ghi_de_mat_khau_admin(self):
        self.sv.doi_mat_khau("admin", "Huit@123", "MatKhauMoi9")
        Service(self.tmp).khoi_tao()
        self.assertEqual(self.sv.dang_nhap("admin", "MatKhauMoi9")["ma_nd"], "admin")
        self.assertFalse(self.sv.dang_dung_mat_khau_mac_dinh())

    def test_chuan_hoa_ngay_va_id_lich_thi(self):
        for lhp in self.doc("lophocphan"):
            self.assertRegex(lhp["ngay_bat_dau"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(all(x.get("id") for x in self.doc("lichthi")))

    def test_sao_luu(self):
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, "backup")))
        self.assertTrue(os.listdir(os.path.join(self.tmp, "backup")))

    def test_json_hong_khong_bi_ghi_de(self):
        with open(os.path.join(self.tmp, "monhoc.json"), "w", encoding="utf-8") as f:
            f.write("{khong phai json")
        with self.assertRaises(core.DuLieuError):
            Service(self.tmp).mon_hoc()

    def test_doi_mat_khau(self):
        with self.assertRaises(NghiepVuError):
            self.sv.doi_mat_khau("SV01", "sai", "MatKhauMoi9")
        with self.assertRaises(NghiepVuError):
            self.sv.doi_mat_khau("SV01", "SV01@123", "123")
        self.sv.doi_mat_khau("SV01", "SV01@123", "MatKhauMoi9")
        self.assertEqual(self.sv.dang_nhap("SV01", "MatKhauMoi9")["ma_nd"], "SV01")


class TestTaiKhoan(CoreTestCase):
    def test_tao_khoa_mo_khoa_dat_lai(self):
        kq = self.sv.tao_sinh_vien("SV10", "  Nguyễn   Văn   Test ")
        self.assertEqual(kq["mat_khau"], "SV03@123")
        self.assertEqual(self.sv.get_user("SV10")["ho_ten"], "Nguyễn Văn Test")
        with self.assertRaises(NghiepVuError):
            self.sv.tao_sinh_vien("sv10", "Trùng")
        with self.assertRaises(NghiepVuError):
            self.sv.tao_sinh_vien("a b", "Sai mã")
        self.sv.khoa_tai_khoan("SV10", 7)
        with self.assertRaises(NghiepVuError):
            self.sv.dang_nhap("SV10", "SV03@123")
        self.sv.mo_khoa_tai_khoan("SV10")
        self.assertEqual(self.sv.dang_nhap("SV10", "SV03@123")["ma_nd"], "SV10")
        self.assertEqual(self.sv.dat_lai_mat_khau("SV10"), "SV10@123")
        with self.assertRaises(NghiepVuError):
            self.sv.khoa_tai_khoan("SV10", 0)

    def test_tu_dong_mo_khoa_khi_het_han(self):
        users = self.sv.store.load("users")
        for u in users:
            if u["ma_nd"] == "SV01":
                u["trang_thai"], u["khoa_den"] = "bi_khoa", "2020-01-01 00:00"
        self.sv.store.save("users", users)
        self.assertEqual(self.sv.dang_nhap("SV01", "SV01@123")["trang_thai"], "hoat_dong")

    def test_xoa_sinh_vien_don_du_lieu_lien_quan(self):
        self.assertTrue(any("SV02" in x["danh_sach_sv"] for x in self.doc("lophocphan")))
        tk = self.sv.xoa_sinh_vien("SV02")
        self.assertGreaterEqual(tk["dang_ky"], 1)
        self.assertFalse(any("SV02" in x["danh_sach_sv"] for x in self.doc("lophocphan")))
        self.assertFalse(any(p["ma_nd"] == "SV02" for p in self.doc("thanhtoan")))
        self.assertIsNone(self.sv.get_user("SV02"))
        with self.assertRaises(NghiepVuError):
            self.sv.xoa_sinh_vien("admin")


class TestDangKy(CoreTestCase):
    def test_dang_ky_va_huy(self):
        info = self.sv.dang_ky("SV01", "LHP03")
        self.assertEqual(info["tin_chi"], 3)
        self.assertEqual(info["hoc_phi"], 3 * 700000)
        self.assertIn("SV01", self.doc("lophocphan")[2]["danh_sach_sv"])
        khoan = [p for p in self.doc("thanhtoan") if p["ma_nd"] == "SV01"]
        self.assertEqual(len(khoan), 1)
        self.assertEqual(self.sv.tong_no("SV01"), 2100000)
        self.sv.huy_dang_ky("SV01", "LHP03")
        self.assertEqual(self.sv.tong_no("SV01"), 0)
        self.assertFalse([p for p in self.doc("thanhtoan") if p["ma_nd"] == "SV01"])

    def test_khong_dang_ky_hai_lop_cung_mon(self):
        self.sv.dang_ky("SV01", "LHP03")                   # INT101 - Thứ 5
        with self.assertRaises(NghiepVuError) as cm:
            self.sv.dang_ky("SV01", "LHP05")               # INT101 khác lớp
        self.assertIn("LHP03", str(cm.exception))

    def test_mon_tien_quyet(self):
        with self.assertRaises(NghiepVuError) as cm:
            self.sv.dang_ky("SV01", "LHP02")               # INT102 cần INT101
        self.assertIn("INT101", str(cm.exception))
        self.sv.dang_ky("SV01", "LHP03")
        self.assertEqual(self.sv.dang_ky("SV01", "LHP02")["ma_mh"], "INT102")

    def test_trung_lich(self):
        self.sv.dang_ky("SV01", "LHP03")                   # Thứ 5, tiết 1-3
        moi = self.sv.tao_lhp(self.lop_moi(ma_lhp="XL01", thu="Thứ 5", tiet_hoc="3-5",
                                           ten_giang_vien="GV Khác", phong_hoc="KT202"))
        with self.assertRaises(NghiepVuError) as cm:
            self.sv.dang_ky("SV01", moi["ma_lhp"])
        self.assertIn("Tiết bị trùng: 3", str(cm.exception))
        ok = self.sv.tao_lhp(self.lop_moi(ma_lhp="XL02", thu="Thứ 5", tiet_hoc="4-6",
                                          ten_giang_vien="GV Khác 2", phong_hoc="KT203"))
        self.assertEqual(self.sv.dang_ky("SV01", ok["ma_lhp"])["ma_lhp"], "XL02")

    def test_lop_tam_ngung_va_day_si_so(self):
        self.sv.doi_trang_thai_lhp(["LHP03"], "Tạm ngưng")
        with self.assertRaises(NghiepVuError):
            self.sv.dang_ky("SV01", "LHP03")
        self.sv.doi_trang_thai_lhp(["LHP03"], "Bình thường")
        lop = self.sv.tao_lhp(self.lop_moi(ma_lhp="NHO1", si_so_toi_da=1, thu="Thứ 7", tiet_hoc="7-9"))
        self.sv.dang_ky("SV01", lop["ma_lhp"])
        with self.assertRaises(NghiepVuError) as cm:
            self.sv.dang_ky("SV02", lop["ma_lhp"])
        self.assertIn("sĩ số", str(cm.exception))

    def test_het_han_dang_ky_va_canh_bao_hoc_vu(self):
        cfg = self.doc("config")
        cfg["thoi_gian_ket_thuc"] = "2020-02-01 00:00"
        self.sv.store.save("config", cfg)
        with self.assertRaises(NghiepVuError):
            self.sv.dang_ky("SV01", "LHP03")
        self.sv.luu_cau_hinh("2020-01-01 00:00", "2030-12-31 23:59", 3, 1, 700000, 1000000, 60)
        self.sv.cap_nhat_sinh_vien("SV01", "Hứa Quốc Đông", "CNTT", "DHTI16A", 3.2, 2, True)
        with self.assertRaises(NghiepVuError) as cm:
            self.sv.dang_ky("SV01", "LHP03")
        self.assertIn("cảnh báo học vụ", str(cm.exception))

    def test_khong_huy_khi_da_thanh_toan(self):
        self.sv.dang_ky("SV01", "LHP03")
        kq = self.sv.thanh_toan_tat_ca("SV01", "MoMo")
        self.assertEqual((kq["so_khoan"], kq["tong"]), (1, 2100000))
        self.assertEqual(self.sv.tong_no("SV01"), 0)
        with self.assertRaises(NghiepVuError):
            self.sv.huy_dang_ky("SV01", "LHP03")
        with self.assertRaises(NghiepVuError):
            self.sv.thanh_toan_tat_ca("SV01", "MoMo")
        self.assertEqual(len(self.sv.hoc_phan_da_dong("SV01")), 1)

    def test_hoc_phi_theo_gia_tung_lop(self):
        lop = self.sv.tao_lhp(self.lop_moi(ma_lhp="GIA1", hoc_phi_moi_tin_chi=900000, thu="Thứ 3", tiet_hoc="7-9"))
        self.assertEqual(self.sv.dang_ky("SV01", lop["ma_lhp"])["hoc_phi"], 3 * 900000)

    def test_bang_dang_ky_va_tong_ket(self):
        hang = {h["ma_lhp"]: h for h in self.sv.bang_dang_ky("SV02")}
        self.assertTrue(hang["LHP01"]["da_dk"])
        self.assertEqual(hang["LHP01"]["thu_phi"], "Đã thu")
        self.assertFalse(hang["LHP03"]["da_dk"])
        tk = self.sv.tong_ket_dang_ky("SV02")
        self.assertEqual(tk["so_lop"], 4)
        self.assertEqual(tk["tin_chi"], 12)


class TestQuanTri(CoreTestCase):
    def test_tao_lop_kiem_tra_du_lieu(self):
        sai = (dict(ma_mh="KHONGCO"), dict(thu="Thứ 9"), dict(tiet_hoc="20-25"), dict(si_so_toi_da=999),
               dict(hoc_phi_moi_tin_chi=0), dict(ngay_ket_thuc="01/01/2020"), dict(ngay_bat_dau="abc"),
               dict(loai_lich="Thực hành", hoc_phi_moi_tin_chi=500000), dict(ten_giang_vien=""))
        for ghi_de in sai:
            with self.assertRaises(NghiepVuError, msg=str(ghi_de)):
                self.sv.tao_lhp(self.lop_moi(**ghi_de))

    def test_tao_lop_tu_sinh_ma_va_chan_trung_phong_giang_vien(self):
        a = self.sv.tao_lhp(self.lop_moi())
        self.assertTrue(a["ma_lhp"].startswith("LHP"))
        with self.assertRaises(NghiepVuError) as cm:
            self.sv.tao_lhp(self.lop_moi(ma_lhp="B1", ten_giang_vien="Người Khác"))      # cùng phòng
        self.assertIn("Phòng", str(cm.exception))
        with self.assertRaises(NghiepVuError) as cm:
            self.sv.tao_lhp(self.lop_moi(ma_lhp="B2", phong_hoc="KT999"))                 # cùng giảng viên
        self.assertIn("Giảng viên", str(cm.exception))
        with self.assertRaises(NghiepVuError):
            self.sv.tao_lhp(self.lop_moi(ma_lhp=a["ma_lhp"], thu="Thứ 7"))               # trùng mã
        self.sv.tao_lhp(self.lop_moi(ma_lhp="B3", thu="Thứ 7"))                           # khác thứ -> hợp lệ

    def test_sua_lop(self):
        with self.assertRaises(NghiepVuError):                                            # sĩ số < số SV
            d = self.sv.get_lhp("LHP01")
            self.sv.sua_lhp("LHP01", {**d, "si_so_toi_da": 0})
        d = dict(self.sv.get_lhp("LHP01"))
        d["ten_giang_vien"] = "Giảng Viên Mới"
        d["ngay_bat_dau"], d["ngay_ket_thuc"] = "15/10/2026", "12/02/2027"
        self.assertEqual(self.sv.sua_lhp("LHP01", d)["ten_giang_vien"], "Giảng Viên Mới")
        d["ma_mh"] = "INT102"
        with self.assertRaises(NghiepVuError):                                            # đã có SV: không đổi môn
            self.sv.sua_lhp("LHP01", d)

    def test_xoa_lop(self):
        lop = self.sv.tao_lhp(self.lop_moi(ma_lhp="XOA1", thu="Thứ 7", tiet_hoc="10-12"))
        self.sv.dang_ky("SV01", lop["ma_lhp"])
        self.assertEqual(self.sv.xoa_lhp("XOA1"), 1)
        self.assertEqual(self.sv.tong_no("SV01"), 0)
        self.assertIsNone(self.sv.get_lhp("XOA1"))
        with self.assertRaises(NghiepVuError):                                            # LHP01 đã thanh toán
            self.sv.xoa_lhp("LHP01")

    def test_khoa_mo_khoa_nhieu_lop(self):
        self.assertEqual(self.sv.doi_trang_thai_lhp(["LHP01", "LHP02", "KHONGCO"], "Tạm ngưng"), 2)
        self.assertEqual(self.sv.get_lhp("LHP02")["trang_thai_lich"], "Tạm ngưng")
        with self.assertRaises(NghiepVuError):
            self.sv.doi_trang_thai_lhp(["KHONGCO"], "Tạm ngưng")

    def test_tao_lop_ngau_nhien(self):
        cu = {x["ma_lhp"] for x in self.sv.lop_hoc_phan()}
        tao = self.sv.tao_lhp_ngau_nhien(30)
        self.assertGreater(tao, 20)
        lops = self.sv.lop_hoc_phan()
        self.assertEqual(len(lops), len(cu) + tao)
        moi = [x for x in lops if x["ma_lhp"] not in cu]
        self.assertEqual(len(moi), tao)
        for a in moi:                              # lớp sinh ngẫu nhiên không trùng phòng/giảng viên với bất kỳ lớp nào
            for b in lops:
                if a["ma_lhp"] != b["ma_lhp"] and core.tiet_trung(a, b):
                    self.assertNotEqual(a["phong_hoc"], b["phong_hoc"], (a["ma_lhp"], b["ma_lhp"]))
                    self.assertNotEqual(a["ten_giang_vien"], b["ten_giang_vien"], (a["ma_lhp"], b["ma_lhp"]))
        with self.assertRaises(NghiepVuError):
            self.sv.tao_lhp_ngau_nhien(0)

    def test_mon_hoc(self):
        self.sv.them_mon("ABC1", "Môn Thử", 2, "INT101", "CNTT")
        with self.assertRaises(NghiepVuError):
            self.sv.them_mon("ABC1", "Trùng", 2)
        with self.assertRaises(NghiepVuError):
            self.sv.them_mon("ABC2", "Sai TC", 0)
        with self.assertRaises(NghiepVuError):
            self.sv.them_mon("ABC3", "Tiên quyết lạ", 2, "KHONGCO")
        with self.assertRaises(NghiepVuError):                                            # vòng lặp tiên quyết
            self.sv.cap_nhat_mon("INT101", "Lập trình Python", 3, "ABC1")
        self.sv.cap_nhat_mon("ABC1", "Môn Thử 2", 4, "", "")
        self.assertEqual(self.sv.mon_map()["ABC1"]["so_tin_chi"], 4)
        with self.assertRaises(NghiepVuError):                                            # đang có lớp
            self.sv.xoa_mon("INT101")
        self.sv.xoa_mon("ABC1")
        self.assertNotIn("ABC1", self.sv.mon_map())
        self.assertEqual(self.sv.nap_danh_muc(), 0)                                       # đã nạp đủ từ trước

    def test_lich_thi(self):
        with self.assertRaises(NghiepVuError):                                            # trùng ngày + tiết
            self.sv.tao_lich_thi("SV01", "Mạng máy tính", "15/10/2026", 14, "A205")
        rec = self.sv.tao_lich_thi("SV01", "Cơ sở dữ liệu", "20/11/2026", 3, "B302", "Mang CCCD")
        self.assertEqual((rec["gio"], rec["ngay"]), ("08:40", "2026-11-20"))
        with self.assertRaises(NghiepVuError):
            self.sv.tao_lich_thi("SV01", "X", "ngày sai", 3, "B302")
        with self.assertRaises(NghiepVuError):
            self.sv.tao_lich_thi("SV01", "X", "20/11/2026", 17, "B302")
        with self.assertRaises(NghiepVuError):
            self.sv.tao_lich_thi("admin", "X", "20/11/2026", 3, "B302")
        self.assertEqual([x["mon"] for x in self.sv.lich_thi("SV01")], ["Mạng máy tính", "Cơ sở dữ liệu"])
        self.sv.xoa_lich_thi(rec["id"])
        with self.assertRaises(NghiepVuError):
            self.sv.xoa_lich_thi(rec["id"])

    def test_cau_hinh(self):
        with self.assertRaises(NghiepVuError):
            self.sv.luu_cau_hinh("sai", "2030-01-01 00:00", 3, 1, 700000, 1000000, 60)
        with self.assertRaises(NghiepVuError):
            self.sv.luu_cau_hinh("2026-01-01 00:00", "2025-01-01 00:00", 3, 1, 700000, 1000000, 60)
        with self.assertRaises(NghiepVuError):
            self.sv.luu_cau_hinh("2026-01-01 00:00", "2027-01-01 00:00", 3, 4, 700000, 1000000, 60)
        with self.assertRaises(NghiepVuError):
            self.sv.luu_cau_hinh("2026-01-01 00:00", "2027-01-01 00:00", 3, 1, 900000, 800000, 60)
        self.sv.luu_cau_hinh("2026-01-01 00:00", "2027-01-01 00:00", 4, 2, 650000, 950000, 50)
        cfg = self.sv.cau_hinh()
        self.assertEqual((cfg["so_dot_toi_da"], cfg["dot_dang_ky_hien_tai"], cfg["si_so_toi_da_moi_lop"]), (4, 2, 50))


class TestThoiKhoaBieuVaThongKe(CoreTestCase):
    def test_su_kien_tuan(self):
        tuan_co = core.dau_tuan_cua(date(2026, 10, 19))           # LHP01 (SV02): Thứ 2, tiết 1-3, từ 15/10/2026
        ev = [e for e in self.sv.su_kien_tuan("SV02", tuan_co) if e["tieu_de"] == "Lập trình Python"]
        self.assertTrue(any(e["ngay_idx"] == 0 and (e["tiet_bd"], e["tiet_kt"]) == (1, 3) for e in ev))
        truoc_khi_bat_dau = core.dau_tuan_cua(date(2026, 9, 14))
        self.assertEqual(self.sv.su_kien_tuan("SV02", truoc_khi_bat_dau), [])
        thi = self.sv.su_kien_tuan("SV01", core.dau_tuan_cua(date(2026, 10, 15)))
        self.assertTrue(any(e["loai"] == "THI" and e["tiet_bd"] == 14 and e["ngay_idx"] == 3 for e in thi))

    def test_thong_ke(self):
        tk = self.sv.thong_ke_admin()
        self.assertEqual((tk["sinh_vien"], tk["mon_hoc"], tk["lop"]), (2, 236, 26))
        self.assertEqual(tk["luot_dk"], 4)
        self.assertEqual(tk["da_thu"], 2100000 * 3 + 3000000)
        self.assertEqual(tk["con_no"], 0)
        sv = self.sv.thong_ke_sinh_vien("SV01")
        self.assertEqual((sv["so_lop"], sv["thi_sap_toi"]), (0, []))


if __name__ == "__main__":
    unittest.main(verbosity=2)
