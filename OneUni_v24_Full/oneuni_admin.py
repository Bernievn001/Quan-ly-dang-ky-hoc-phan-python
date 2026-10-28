# -*- coding: utf-8 -*-
"""oneuni_admin - các trang dành cho quản trị viên (tổng quan, tài khoản, môn học, lớp học phần, lịch thi, cấu hình)."""
from __future__ import annotations

import os
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, simpledialog, ttk

import oneuni_core as core
from oneuni_ui import (P, Card, Col, DataTable, FormGrid, Page, StatCard, master_detail, open_folder)


def ma_tu_hien_thi(text):
    """'INT101 - Lập trình Python' -> 'INT101'."""
    return str(text).split(" - ")[0].strip().upper()


class AdminPage(Page):
    """Tiện ích chung cho các trang quản trị."""

    def chon_mot(self, ten="mục"):
        r = self.table.selected_row()
        if not r:
            self.app.warn("Chưa chọn", f"Vui lòng chọn một {ten} trong bảng trước.")
        return r

    def hang(self, parent, *nut):
        """Dòng nút bấm: mỗi nút là (text, command, kind)."""
        f = tk.Frame(parent, bg=P["card"])
        f.pack(fill="x", pady=(0, 6))
        for text, cmd, kind in nut:
            self.T.button(f, text, cmd, kind).pack(side="left", padx=(0, 6))
        return f


# =============================================================================
# Tổng quan
# =============================================================================
class AdminDashboard(Page):
    def build(self):
        T = self.T
        row = tk.Frame(self, bg=P["bg"])
        row.pack(fill="x")
        spec = (("Sinh viên", P["primary"], "☻"), ("Môn học", "#7C3AED", "☰"), ("Lớp học phần", "#0891B2", "▤"),
                ("Lượt đăng ký", P["success"], "✔"), ("Đã thu (mô phỏng)", P["success"], "₫"),
                ("Còn nợ học phí", P["warning"], "₫"))
        self.stats = [StatCard(row, T, *s) for s in spec]
        for i, c in enumerate(self.stats):
            c.grid(row=i // 3, column=i % 3, sticky="nsew", padx=(0 if i % 3 == 0 else 8, 0), pady=(0 if i < 3 else 12, 0))
        for i in range(3):
            row.columnconfigure(i, weight=1, uniform="a")
        low = tk.Frame(self, bg=P["bg"])
        low.pack(fill="both", expand=True, pady=(14, 0))
        low.rowconfigure(0, weight=1)
        low.columnconfigure(0, weight=3, uniform="l")
        low.columnconfigure(1, weight=2, uniform="l")
        self.fill_card = Card(low, T, "Lớp có tỉ lệ lấp đầy cao", "Tối đa 6 lớp theo sĩ số đã đăng ký")
        self.fill_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.sys_card = Card(low, T, "Trạng thái hệ thống")
        self.sys_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    def refresh(self):
        T, tk_ = self.T, self.svc.thong_ke_admin()
        for c, (v, sub) in zip(self.stats, (
                (tk_["sinh_vien"], "tài khoản sinh viên"), (tk_["mon_hoc"], "môn trong danh mục"),
                (tk_["lop"], f"{tk_['lop_tam_ngung']} lớp đang tạm ngưng"),
                (tk_["luot_dk"], "tổng số lượt đăng ký"), (core.fmt_money(tk_["da_thu"]), "VNĐ"),
                (core.fmt_money(tk_["con_no"]), "VNĐ"))):
            c.set(str(v), sub)

        self.clear(self.fill_card.body)
        if not tk_["lop_sap_day"]:
            T.label(self.fill_card.body, "Chưa có lớp nào có sinh viên đăng ký.", 10, False, P["muted"]).pack(anchor="w", pady=14)
        for x in tk_["lop_sap_day"]:
            r = tk.Frame(self.fill_card.body, bg=P["card"])
            r.pack(fill="x", pady=5)
            T.label(r, f"{x['ma_lhp']} · {x['ma_mh']}", 10, True, P["navy"], width=18).pack(side="left")
            nen = tk.Frame(r, bg=P["head"], height=T.px(10), width=T.px(100))
            nen.pack(side="left", fill="x", expand=True, padx=10)
            mau = P["danger"] if x["ti_le"] >= 0.9 else (P["warning"] if x["ti_le"] >= 0.7 else P["primary"])
            tk.Frame(nen, bg=mau).place(relx=0, rely=0, relwidth=min(1.0, x["ti_le"]), relheight=1)
            T.label(r, f"{x['si_so']}/{x['toi_da']}", 9, True, P["muted"], width=7, anchor="e").pack(side="left")

        s = self.sys_card.body
        self.clear(s)
        mo, tin = self.svc.trang_thai_dang_ky()
        T.chip(s, "● Đăng ký đang mở" if mo else "● Đăng ký đã đóng", "ok" if mo else "bad").pack(anchor="w")
        T.label(s, tin, 9, False, P["muted"], wraplength=T.px(300)).pack(anchor="w", pady=(6, 10))
        T.label(s, f"Lịch thi đã tạo: {tk_['lich_thi']}", 10, False, P["text"]).pack(anchor="w", pady=2)
        T.label(s, f"Lớp tạm ngưng: {tk_['lop_tam_ngung']}", 10, False, P["text"]).pack(anchor="w", pady=2)
        tk.Frame(s, bg=P["border"], height=1).pack(fill="x", pady=12)
        for text, cmd, kind in (("Tạo lớp học phần", lambda: self.app.shell.show("lop"), "primary"),
                                ("Quản lý tài khoản sinh viên", lambda: self.app.shell.show("users"), "secondary"),
                                ("Sao lưu dữ liệu ngay", self.sao_luu, "ghost")):
            T.button(s, text, cmd, kind).pack(fill="x", pady=3)

    def sao_luu(self):
        ok, dich = self.app.call(self.svc.sao_luu)
        if ok:
            self.app.toast.show(f"Đã sao lưu dữ liệu vào backup/{os.path.basename(dich or '')}", "success")


# =============================================================================
# Tài khoản sinh viên
# =============================================================================
class AdminUsersPage(AdminPage):
    def build(self):
        T = self.T
        left, right = master_detail(self, T, "Thông tin sinh viên",
                                    "Chọn một dòng để sửa; bấm “Làm mới form” để tạo tài khoản mới.")
        cols = [Col("ma", "MSSV", 90), Col("ten", "Họ tên", 200, "w", True), Col("nganh", "Ngành", 90),
                Col("lop", "Lớp", 90), Col("gpa", "GPA", 55), Col("cb", "Cảnh báo", 70), Col("so", "Số lớp", 65),
                Col("no", "Còn nợ (VNĐ)", 105, "e"), Col("tt", "Trạng thái", 95), Col("den", "Khóa đến", 125)]
        self.table = DataTable(left.body, T, cols, height=14, on_select=self.khi_chon, notify=self.app.toast.show)
        self.table.pack(fill="both", expand=True)
        T.button(self.table.toolbar, "Làm mới", self.refresh, "secondary").pack(side="right", padx=(6, 0))

        self.mode = T.label(right, "", 10, True, P["primary"])
        self.mode.pack(anchor="w", pady=(0, 10))
        self.form = FormGrid(right, T, [
            {"key": "ma_nd", "label": "MSSV / TÀI KHOẢN"},
            {"key": "nganh", "label": "NGÀNH", "default": "CNTT"},
            {"key": "ho_ten", "label": "HỌ TÊN", "span": 2},
            {"key": "lop", "label": "LỚP", "kind": "combo_edit", "values": []},
            {"key": "gpa", "label": "GPA (0–4)", "kind": "spin", "from": 0, "to": 4, "step": 0.1, "default": "3.0"},
            {"key": "canh_bao", "label": "CẢNH BÁO HỌC VỤ", "kind": "spin", "from": 0, "to": 5, "default": "0"},
            {"key": "da_dong", "label": "", "kind": "check", "text": "Đã đóng học phí các kỳ trước",
             "default": True, "span": 2}], columns=2)
        self.form.pack(fill="x")
        self.hang(right, ("Tạo tài khoản", self.tao, "primary"), ("Lưu thay đổi", self.luu, "secondary"),
                  ("Làm mới form", self.moi, "ghost"))
        tk.Frame(right, bg=P["border"], height=1).pack(fill="x", pady=12)
        T.label(right, "Tác vụ với tài khoản đang chọn", 10, True, P["navy"]).pack(anchor="w", pady=(0, 8))
        f = tk.Frame(right, bg=P["card"])
        f.pack(fill="x", pady=(0, 6))
        self.v_ngay = tk.StringVar(value="7")
        ttk.Spinbox(f, from_=1, to=365, width=5, textvariable=self.v_ngay).pack(side="left")
        T.label(f, " ngày", 10, False, P["muted"]).pack(side="left", padx=(2, 8))
        T.button(f, "Khóa tạm", self.khoa, "secondary").pack(side="left", padx=(0, 6))
        T.button(f, "Mở khóa", self.mo_khoa, "secondary").pack(side="left")
        self.hang(right, ("Đặt lại mật khẩu", self.dat_lai, "secondary"), ("Xóa tài khoản", self.xoa, "danger"))
        self.moi()

    def refresh(self):
        so_lop, no = self.svc.tom_tat_sinh_vien()
        self.users = {u["ma_nd"]: u for u in self.svc.sinh_vien()}
        rows = []
        for u in self.users.values():
            ma, khoa = u["ma_nd"], u.get("trang_thai") == "bi_khoa"
            v = (ma, u.get("ho_ten", ""), u.get("nganh", ""), u.get("lop", ""), u.get("gpa", ""),
                 u.get("canh_bao_hoc_vu", 0), so_lop.get(ma, 0), core.fmt_money(no.get(ma, 0)),
                 "Bị khóa" if khoa else "Hoạt động", u.get("khoa_den") or "—")
            raw = list(v)
            raw[4], raw[5], raw[7] = core.to_float(u.get("gpa")), core.to_int(u.get("canh_bao_hoc_vu")), no.get(ma, 0)
            rows.append({"iid": ma, "values": v, "raw": tuple(raw), "tags": ("bad",) if khoa else ()})
        self.table.set_rows(rows, "tai_khoan_sinh_vien")
        lop = sorted(({str(x.get("lop_hoc_du_kien", "")).strip() for x in self.svc.lop_hoc_phan()} | set(core.LOP_MAU)) - {""})
        self.form.set_choices("lop", lop)

    def khi_chon(self):
        r = self.table.selected_row()
        if not r:
            return
        u = self.users.get(r["iid"])
        if not u:
            return
        self.form.set_values({"ma_nd": u["ma_nd"], "ho_ten": u.get("ho_ten", ""), "nganh": u.get("nganh", ""),
                              "lop": u.get("lop", ""), "gpa": u.get("gpa", 3.0), "canh_bao": u.get("canh_bao_hoc_vu", 0),
                              "da_dong": u.get("da_dong_hoc_phi", True)})
        self.form.lock("ma_nd", True)
        self.mode.config(text=f"Đang sửa tài khoản {u['ma_nd']}")

    def moi(self):
        self.table.clear_selection()
        self.form.clear()
        self.form.lock("ma_nd", False)
        self.mode.config(text="Đang tạo tài khoản sinh viên mới")
        self.form.focus_first()

    def tao(self):
        f = self.form.values()
        ok, kq = self.app.call(self.svc.tao_sinh_vien, f["ma_nd"], f["ho_ten"], f["nganh"], f["lop"], f["gpa"],
                               title="Không thể tạo tài khoản")
        if not ok:
            return
        messagebox.showinfo("Tạo tài khoản thành công",
                            f"MSSV: {kq['ma_nd']}\nLớp: {kq['lop']}\nMật khẩu khởi tạo: {kq['mat_khau']}\n\n"
                            "Hãy gửi mật khẩu này cho sinh viên; sinh viên có thể đổi trong mục Tài khoản.", parent=self.app.root)
        self.refresh()
        self.moi()
        self.table.select(kq["ma_nd"])

    def luu(self):
        r = self.chon_mot("sinh viên")
        if not r:
            return
        f = self.form.values()
        ok, _ = self.app.call(self.svc.cap_nhat_sinh_vien, r["iid"], f["ho_ten"], f["nganh"], f["lop"], f["gpa"],
                              f["canh_bao"], f["da_dong"], title="Không thể lưu thay đổi")
        if ok:
            self.app.toast.show(f"Đã cập nhật thông tin {r['iid']}.", "success")
            self.refresh()

    def khoa(self):
        r = self.chon_mot("sinh viên")
        if not r:
            return
        ok, den = self.app.call(self.svc.khoa_tai_khoan, r["iid"], self.v_ngay.get(), title="Không thể khóa tài khoản")
        if ok:
            self.app.toast.show(f"Đã khóa {r['iid']} đến {den}.", "warn")
            self.refresh()

    def mo_khoa(self):
        r = self.chon_mot("sinh viên")
        if r:
            ok, _ = self.app.call(self.svc.mo_khoa_tai_khoan, r["iid"])
            if ok:
                self.app.toast.show(f"Đã mở khóa {r['iid']}.", "success")
                self.refresh()

    def dat_lai(self):
        r = self.chon_mot("sinh viên")
        if not r or not self.app.confirm("Đặt lại mật khẩu", f"Đặt lại mật khẩu của {r['iid']} về mật khẩu khởi tạo?"):
            return
        ok, mk = self.app.call(self.svc.dat_lai_mat_khau, r["iid"])
        if ok:
            self.app.demo_hints = self.svc.goi_y_demo()
            messagebox.showinfo("Đã đặt lại mật khẩu", f"Mật khẩu mới của {r['iid']}: {mk}", parent=self.app.root)

    def xoa(self):
        r = self.chon_mot("sinh viên")
        if not r or not self.app.confirm(
                "Xóa vĩnh viễn tài khoản",
                f"Xóa tài khoản {r['iid']}?\n\nCác đăng ký học phần, khoản học phí và lịch thi của sinh viên này cũng bị xóa. "
                "Không thể hoàn tác (bản sao lưu nằm trong thư mục backup)."):
            return
        ok, tk_ = self.app.call(self.svc.xoa_sinh_vien, r["iid"], title="Không thể xóa")
        if ok:
            self.app.toast.show(f"Đã xóa {r['iid']} (gỡ {tk_['dang_ky']} đăng ký, {tk_['hoc_phi']} khoản phí, "
                                f"{tk_['lich_thi']} lịch thi).", "info", 5000)
            self.refresh()
            self.moi()


# =============================================================================
# Môn học
# =============================================================================
class AdminSubjectsPage(AdminPage):
    def build(self):
        T = self.T
        left, right = master_detail(self, T, "Thông tin môn học",
                                    "Chọn một dòng để sửa; bấm “Làm mới form” để thêm môn mới.", 360)
        cols = [Col("ma", "Mã môn", 95), Col("ten", "Tên môn học", 280, "w", True), Col("tc", "TC", 50),
                Col("tq", "Tiên quyết", 95), Col("nganh", "Ngành áp dụng", 170, "w"), Col("lop", "Số lớp", 65)]
        self.table = DataTable(left.body, T, cols, height=15, on_select=self.khi_chon, notify=self.app.toast.show)
        self.table.pack(fill="both", expand=True)
        T.button(self.table.toolbar, "Nạp danh mục mở rộng", self.nap, "secondary").pack(side="right", padx=(6, 0))

        self.mode = T.label(right, "", 10, True, P["primary"])
        self.mode.pack(anchor="w", pady=(0, 10))
        self.form = FormGrid(right, T, [
            {"key": "ma_mh", "label": "MÃ MÔN"},
            {"key": "so_tc", "label": "SỐ TÍN CHỈ", "kind": "spin", "from": 1, "to": 10, "default": "3"},
            {"key": "ten_mh", "label": "TÊN MÔN HỌC", "span": 2},
            {"key": "tien_quyet", "label": "MÔN TIÊN QUYẾT (nếu có)", "kind": "combo_edit", "filter": True, "span": 2},
            {"key": "nganh", "label": "NGÀNH ÁP DỤNG (tùy chọn)", "span": 2}], columns=2)
        self.form.pack(fill="x")
        self.hang(right, ("Thêm môn", self.them, "primary"), ("Lưu thay đổi", self.luu, "secondary"))
        self.hang(right, ("Xóa môn", self.xoa, "danger"), ("Làm mới form", self.moi, "ghost"))
        T.label(right, "Sau khi thêm môn, vào “Lớp học phần” để mở lớp cho sinh viên đăng ký.", 9, False, P["muted"],
                wraplength=T.px(320)).pack(anchor="w", pady=(8, 0))
        self.moi()

    def refresh(self):
        dem = {}
        for x in self.svc.lop_hoc_phan():
            dem[x.get("ma_mh")] = dem.get(x.get("ma_mh"), 0) + 1
        self.mons = {m.get("ma_mh"): m for m in self.svc.mon_hoc()}
        rows = []
        for ma in sorted(self.mons, key=str):
            m = self.mons[ma]
            tc = core.to_int(m.get("so_tin_chi", m.get("so_tc")), 0)
            v = (ma, m.get("ten_mh", ""), tc, m.get("tien_quyet") or "—", m.get("nganh_ap_dung", ""), dem.get(ma, 0))
            rows.append({"iid": str(ma), "values": v})
        self.table.set_rows(rows, "mon_hoc")
        self.form.set_choices("tien_quyet", [""] + [f"{ma} - {m.get('ten_mh', '')}" for ma, m in self.mons.items()])

    def khi_chon(self):
        r = self.table.selected_row()
        m = self.mons.get(r["iid"]) if r else None
        if not m:
            return
        tq = str(m.get("tien_quyet", "") or "")
        self.form.set_values({"ma_mh": m["ma_mh"], "ten_mh": m.get("ten_mh", ""),
                              "so_tc": m.get("so_tin_chi", m.get("so_tc", 3)),
                              "tien_quyet": f"{tq} - {self.mons[tq].get('ten_mh', '')}" if tq in self.mons else tq,
                              "nganh": m.get("nganh_ap_dung", "")})
        self.form.lock("ma_mh", True)
        self.mode.config(text=f"Đang sửa môn {m['ma_mh']}")

    def moi(self):
        self.table.clear_selection()
        self.form.clear()
        self.form.lock("ma_mh", False)
        self.mode.config(text="Đang thêm môn học mới")
        self.form.focus_first()

    def _doc(self):
        f = self.form.values()
        return f["ma_mh"], f["ten_mh"], f["so_tc"], ma_tu_hien_thi(f["tien_quyet"]), f["nganh"]

    def them(self):
        ok, mon = self.app.call(self.svc.them_mon, *self._doc(), title="Không thể thêm môn học")
        if ok:
            self.app.toast.show(f"Đã thêm môn {mon['ma_mh']} - {mon['ten_mh']}.", "success")
            self.refresh()
            self.moi()
            self.table.select(mon["ma_mh"])

    def luu(self):
        r = self.chon_mot("môn học")
        if r:
            ok, _ = self.app.call(self.svc.cap_nhat_mon, *self._doc(), title="Không thể lưu thay đổi")
            if ok:
                self.app.toast.show(f"Đã cập nhật môn {r['iid']}.", "success")
                self.refresh()

    def xoa(self):
        r = self.chon_mot("môn học")
        if not r or not self.app.confirm("Xóa môn học", f"Xóa môn {r['iid']} khỏi danh mục?"):
            return
        ok, _ = self.app.call(self.svc.xoa_mon, r["iid"], title="Không thể xóa môn học")
        if ok:
            self.app.toast.show(f"Đã xóa môn {r['iid']}.", "info")
            self.refresh()
            self.moi()

    def nap(self):
        ok, n = self.app.call(self.svc.nap_danh_muc)
        if ok:
            self.app.toast.show(f"Đã bổ sung {n} môn từ danh mục mở rộng." if n else
                                "Danh mục mở rộng không có môn mới để bổ sung.", "success" if n else "info")
            self.refresh()


# =============================================================================
# Lớp học phần
# =============================================================================
class AdminClassesPage(AdminPage):
    def build(self):
        T = self.T
        left, right = master_detail(self, T, "Thông tin lớp học phần",
                                    "Chọn một dòng để sửa; bấm “Làm mới form” để tạo lớp mới.", 420)
        cols = [Col("ma", "Mã LHP", 85), Col("mh", "Mã môn", 85), Col("ten", "Tên môn học", 210, "w", True),
                Col("gv", "Giảng viên", 140, "w"), Col("thu", "Thứ", 75), Col("tiet", "Tiết", 60), Col("phong", "Phòng", 70),
                Col("loai", "Loại", 85), Col("si", "Sĩ số", 70), Col("gia", "VNĐ/TC", 95, "e"),
                Col("bd", "Bắt đầu", 90), Col("kt", "Kết thúc", 90), Col("lop", "Lớp dự kiến", 90), Col("tt", "Trạng thái", 95)]
        self.table = DataTable(left.body, T, cols, height=14, multi=True, on_select=self.khi_chon,
                               notify=self.app.toast.show)
        self.table.pack(fill="both", expand=True)
        for text, cmd, kind in (("Tạo lớp ngẫu nhiên", self.ngau_nhien, "secondary"),
                                ("Mở khóa", lambda: self.doi_tt(core.TT_BINH_THUONG), "secondary"),
                                ("Khóa học phần", lambda: self.doi_tt(core.TT_TAM_NGUNG), "danger")):
            T.button(self.table.toolbar, text, cmd, kind).pack(side="right", padx=(6, 0))

        self.mode = T.label(right, "", 10, True, P["primary"])
        self.mode.pack(anchor="w", pady=(0, 10))
        cfg = self.svc.cau_hinh()
        self.form = FormGrid(right, T, [
            {"key": "ma_lhp", "label": "MÃ LHP (trống = tự sinh)"},
            {"key": "lop", "label": "LỚP DỰ KIẾN", "default": "DHTI16A"},
            {"key": "mon", "label": "MÔN HỌC", "kind": "combo_edit", "filter": True, "span": 2},
            {"key": "gv", "label": "GIẢNG VIÊN"},
            {"key": "phong", "label": "PHÒNG HỌC"},
            {"key": "thu", "label": "THỨ", "kind": "combo", "values": list(core.THU), "default": core.THU[0]},
            {"key": "tiet", "label": "TIẾT (vd 1-3)", "default": "1-3"},
            {"key": "loai", "label": "LOẠI LỊCH", "kind": "combo", "values": list(core.LOAI_LICH), "default": core.LOAI_LICH[0]},
            {"key": "nhom", "label": "NHÓM TH", "default": "—"},
            {"key": "si", "label": f"SĨ SỐ TỐI ĐA (≤ {cfg['si_so_toi_da_moi_lop']})", "kind": "spin", "from": 1,
             "to": 1000, "default": str(cfg["si_so_toi_da_moi_lop"])},
            {"key": "gia", "label": "GIÁ MỖI TÍN CHỈ (VNĐ)", "default": str(cfg["hoc_phi_ly_thuyet_moi_tin_chi"])},
            {"key": "bd", "label": "NGÀY BẮT ĐẦU", "kind": "date", "default": lambda: date.today().strftime(core.FMT_DATE_VN)},
            {"key": "kt", "label": "NGÀY KẾT THÚC", "kind": "date",
             "default": lambda: (date.today() + timedelta(days=120)).strftime(core.FMT_DATE_VN)}], columns=2)
        self.form.pack(fill="x")
        self.form.widgets["loai"].bind("<<ComboboxSelected>>", self.goi_y_gia)
        self.hang(right, ("Tạo lớp", self.tao, "primary"), ("Lưu thay đổi", self.luu, "secondary"))
        self.hang(right, ("Xóa lớp", self.xoa, "danger"), ("Làm mới form", self.moi, "ghost"))
        self.moi()

    def refresh(self):
        mons = self.svc.mon_map()
        self.lops = {x["ma_lhp"]: x for x in self.svc.lop_hoc_phan()}
        rows = []
        for ma, x in self.lops.items():
            bd, kt = core.khoang_ngay(x)
            tt = x.get("trang_thai_lich", core.TT_BINH_THUONG)
            si = len(x.get("danh_sach_sv", []))
            v = (ma, x.get("ma_mh", ""), mons.get(x.get("ma_mh"), {}).get("ten_mh") or x.get("ten_mon", ""),
                 x.get("ten_giang_vien", ""), x.get("thu", ""), x.get("tiet_hoc", ""), x.get("phong_hoc", ""),
                 x.get("loai_lich", ""), f"{si}/{x.get('si_so_toi_da', '')}", core.fmt_money(self.svc.don_gia(x)),
                 bd.strftime(core.FMT_DATE_VN), kt.strftime(core.FMT_DATE_VN), x.get("lop_hoc_du_kien", ""), tt)
            raw = list(v)
            raw[8], raw[9], raw[10], raw[11] = si, self.svc.don_gia(x), bd.toordinal(), kt.toordinal()
            rows.append({"iid": ma, "values": v, "raw": tuple(raw),
                         "tags": ("bad",) if tt == core.TT_TAM_NGUNG else ()})
        self.table.set_rows(rows, "lop_hoc_phan")
        self.hien_thi_mon = [f"{m.get('ma_mh', '')} - {m.get('ten_mh', '')}" for m in self.svc.mon_hoc()]
        self.form.set_choices("mon", self.hien_thi_mon)

    def goi_y_gia(self, _e=None):
        if self.table.selected():                       # đang sửa lớp có sẵn: không tự đổi giá
            return
        cfg = self.svc.cau_hinh()
        th = self.form.get("loai") == core.LOAI_LICH[1]
        self.form.set("gia", cfg["hoc_phi_thuc_hanh_moi_tin_chi" if th else "hoc_phi_ly_thuyet_moi_tin_chi"])

    def khi_chon(self):
        sel = self.table.selected()
        if len(sel) > 1:
            self.mode.config(text=f"Đã chọn {len(sel)} lớp · dùng nút Khóa/Mở khóa ở trên bảng")
            return
        x = self.lops.get(sel[0]) if sel else None
        if not x:
            return
        bd, kt = core.khoang_ngay(x)
        mh = x.get("ma_mh", "")
        ten = self.svc.mon_map().get(mh, {}).get("ten_mh", "")
        self.form.set_values({
            "ma_lhp": x["ma_lhp"], "lop": x.get("lop_hoc_du_kien", ""), "mon": f"{mh} - {ten}" if ten else mh,
            "gv": x.get("ten_giang_vien", ""), "phong": x.get("phong_hoc", ""), "thu": x.get("thu", core.THU[0]),
            "tiet": x.get("tiet_hoc", ""), "loai": x.get("loai_lich", core.LOAI_LICH[0]), "nhom": x.get("nhom_th", "—"),
            "si": x.get("si_so_toi_da", ""), "gia": self.svc.don_gia(x), "bd": bd.strftime(core.FMT_DATE_VN),
            "kt": kt.strftime(core.FMT_DATE_VN)})
        self.form.lock("ma_lhp", True)
        self.mode.config(text=f"Đang sửa lớp {x['ma_lhp']} · {len(x.get('danh_sach_sv', []))} sinh viên đã đăng ký")

    def moi(self):
        self.table.clear_selection()
        self.form.clear()
        self.form.lock("ma_lhp", False)
        self.mode.config(text="Đang tạo lớp học phần mới")

    def _du_lieu(self, trang_thai=core.TT_BINH_THUONG):
        f = self.form.values()
        return {"ma_lhp": f["ma_lhp"], "ma_mh": ma_tu_hien_thi(f["mon"]), "ten_giang_vien": f["gv"], "thu": f["thu"],
                "tiet_hoc": f["tiet"], "phong_hoc": f["phong"], "si_so_toi_da": f["si"], "loai_lich": f["loai"],
                "trang_thai_lich": trang_thai, "hoc_phi_moi_tin_chi": f["gia"].replace(".", "").replace(",", ""),
                "lop_hoc_du_kien": f["lop"], "nhom_th": f["nhom"], "ngay_bat_dau": f["bd"], "ngay_ket_thuc": f["kt"]}

    def tao(self):
        ok, lop = self.app.call(self.svc.tao_lhp, self._du_lieu(), title="Không thể tạo lớp học phần")
        if ok:
            self.app.toast.show(f"Đã tạo lớp {lop['ma_lhp']} · {lop['ma_mh']}.", "success")
            self.refresh()
            self.moi()
            self.table.select(lop["ma_lhp"])

    def luu(self):
        sel = self.table.selected()
        if len(sel) != 1:
            self.app.warn("Chưa chọn", "Vui lòng chọn đúng một lớp học phần trong bảng để sửa.")
            return
        tt = self.lops[sel[0]].get("trang_thai_lich", core.TT_BINH_THUONG)
        ok, _ = self.app.call(self.svc.sua_lhp, sel[0], self._du_lieu(tt), title="Không thể lưu thay đổi")
        if ok:
            self.app.toast.show(f"Đã cập nhật lớp {sel[0]}.", "success")
            self.refresh()

    def xoa(self):
        sel = self.table.selected()
        if len(sel) != 1:
            self.app.warn("Chưa chọn", "Vui lòng chọn đúng một lớp học phần trong bảng để xóa.")
            return
        so_sv = len(self.lops.get(sel[0], {}).get("danh_sach_sv", []))
        if not self.app.confirm("Xác nhận xóa lớp học phần",
                                f"Xóa lớp {sel[0]}?\n\nSinh viên đang đăng ký: {so_sv}\nLớp sẽ bị gỡ khỏi danh sách đăng ký "
                                "và các khoản phí chưa thanh toán liên quan sẽ bị xóa. Không thể hoàn tác."):
            return
        ok, _ = self.app.call(self.svc.xoa_lhp, sel[0], title="Không thể xóa lớp học phần")
        if ok:
            self.app.toast.show(f"Đã xóa lớp {sel[0]}.", "info")
            self.refresh()
            self.moi()

    def doi_tt(self, trang_thai):
        sel = self.table.selected()
        if not sel:
            self.app.warn("Chưa chọn học phần", "Chọn một hoặc nhiều học phần trong bảng (giữ Ctrl/Shift để chọn nhiều).")
            return
        ok, n = self.app.call(self.svc.doi_trang_thai_lhp, sel, trang_thai)
        if ok:
            khoa = trang_thai == core.TT_TAM_NGUNG
            self.app.toast.show(f"Đã {'khóa' if khoa else 'mở khóa'} {n} học phần"
                                + (" (không hủy đăng ký/hoàn tiền sinh viên đã đăng ký trước đó)." if khoa else "."),
                                "warn" if khoa else "success", 4500)
            self.refresh()

    def ngau_nhien(self):
        n = simpledialog.askinteger("Tạo lớp học phần ngẫu nhiên",
                                    "Số lớp muốn tạo (1–100).\nGiảng viên, phòng, lịch và giá được chọn ngẫu nhiên,\n"
                                    "không trùng phòng/giảng viên với lớp khác:", initialvalue=12, minvalue=1,
                                    maxvalue=100, parent=self.app.root)
        if n is None:
            return
        ok, tao = self.app.call(self.svc.tao_lhp_ngau_nhien, n)
        if ok:
            self.app.toast.show(f"Đã tạo {tao}/{n} lớp ngẫu nhiên" + ("" if tao == n else " (bỏ bớt lớp bị trùng phòng/giảng viên)."),
                                "success" if tao else "warn")
            self.refresh()


# =============================================================================
# Lịch thi
# =============================================================================
class AdminExamsPage(AdminPage):
    def build(self):
        T = self.T
        left, right = master_detail(self, T, "Tạo lịch thi", "Chọn sinh viên, môn, ngày, tiết và phòng; giờ thi tự xác định theo tiết.", 380)
        cols = [Col("ma", "MSSV", 85), Col("ten", "Họ tên", 150, "w"), Col("mon", "Môn thi", 220, "w", True),
                Col("ngay", "Ngày thi", 95), Col("thu", "Thứ", 75), Col("gio", "Giờ", 60), Col("tiet", "Tiết", 55),
                Col("phong", "Phòng", 75), Col("ghi", "Ghi chú", 160, "w")]
        self.table = DataTable(left.body, T, cols, height=14, notify=self.app.toast.show)
        self.table.pack(fill="both", expand=True)
        T.button(self.table.toolbar, "Xóa lịch thi đã chọn", self.xoa, "danger").pack(side="right", padx=(6, 0))

        self.form = FormGrid(right, T, [
            {"key": "sv", "label": "SINH VIÊN", "kind": "combo_edit", "filter": True, "span": 2},
            {"key": "mon", "label": "MÔN THI", "kind": "combo_edit", "filter": True, "span": 2},
            {"key": "ngay", "label": "NGÀY THI", "kind": "date",
             "default": lambda: (date.today() + timedelta(days=14)).strftime(core.FMT_DATE_VN)},
            {"key": "tiet", "label": "TIẾT THI", "kind": "combo", "default": "Tiết 1 (07:00)",
             "values": [f"Tiết {t} ({g})" for t, g in core.GIO_THI_THEO_TIET.items()]},
            {"key": "phong", "label": "PHÒNG THI", "kind": "combo_edit", "span": 2},
            {"key": "ghi", "label": "GHI CHÚ", "span": 2}], columns=2)
        self.form.pack(fill="x")
        self.hang(right, ("Tạo lịch thi", self.tao, "primary"), ("Làm mới form", self.form.clear, "ghost"))

    def refresh(self):
        svs = self.svc.sinh_vien()
        self.sv_map = {f"{u['ma_nd']} - {u.get('ho_ten', '')}": u["ma_nd"] for u in svs}
        ten = {u["ma_nd"]: u.get("ho_ten", "") for u in svs}
        self.mon_map = {f"{m.get('ma_mh', '')} - {m.get('ten_mh', '')}": m.get("ten_mh", "") for m in self.svc.mon_hoc()}
        phong = sorted({str(x.get("phong_hoc", "")).strip() for x in self.svc.lop_hoc_phan()} - {""})
        self.form.set_choices("sv", list(self.sv_map))
        self.form.set_choices("mon", list(self.mon_map))
        self.form.set_choices("phong", phong)
        rows = []
        for x in self.svc.lich_thi():
            d = x["ngay_date"]
            v = (x.get("ma_nd", ""), ten.get(x.get("ma_nd"), ""), x.get("mon", ""), f"{d:%d/%m/%Y}", core.THU[d.weekday()],
                 x.get("gio", ""), x["tiet_thi"], x.get("phong", ""), x.get("ghi_chu", ""))
            raw = list(v)
            raw[3], raw[6] = d.toordinal(), x["tiet_thi"]
            rows.append({"iid": x["id"], "values": v, "raw": tuple(raw), "tags": ("muted",) if d < date.today() else ()})
        self.table.set_rows(rows, "lich_thi")

    def tao(self):
        f = self.form.values()
        ma = self.sv_map.get(f["sv"])
        if not ma:
            self.app.warn("Chưa chọn sinh viên", "Hãy chọn sinh viên từ danh sách (gõ để lọc).")
            return
        mon = self.mon_map.get(f["mon"], f["mon"].split(" - ", 1)[-1])
        tiet = f["tiet"].replace("Tiết", "").split()[0] if f["tiet"] else ""
        ok, rec = self.app.call(self.svc.tao_lich_thi, ma, mon, f["ngay"], tiet, f["phong"], f["ghi"],
                                title="Không thể tạo lịch thi")
        if ok:
            self.app.toast.show(f"Đã tạo lịch thi {rec['mon']} cho {ma} lúc {rec['gio']}.", "success")
            self.form.set("ghi", "")
            self.refresh()
            self.table.select(rec["id"])

    def xoa(self):
        r = self.chon_mot("lịch thi")
        if r and self.app.confirm("Xóa lịch thi", f"Xóa lịch thi {r['values'][2]} của {r['values'][0]}?"):
            ok, _ = self.app.call(self.svc.xoa_lich_thi, r["iid"])
            if ok:
                self.app.toast.show("Đã xóa lịch thi.", "info")
                self.refresh()


# =============================================================================
# Cấu hình & dữ liệu
# =============================================================================
class AdminConfigPage(Page):
    def build(self):
        T = self.T
        row = tk.Frame(self, bg=P["bg"])
        row.pack(fill="both", expand=True)
        row.columnconfigure(0, weight=3, uniform="c")
        row.columnconfigure(1, weight=2, uniform="c")
        c1 = Card(row, T, "Thời gian, đợt đăng ký, học phí", "Áp dụng ngay cho toàn bộ sinh viên sau khi lưu.")
        c1.grid(row=0, column=0, sticky="new", padx=(0, 8))
        self.form = FormGrid(c1.body, T, [
            {"key": "bd", "label": "BẮT ĐẦU (YYYY-MM-DD HH:MM)"}, {"key": "kt", "label": "KẾT THÚC (YYYY-MM-DD HH:MM)"},
            {"key": "so_dot", "label": "SỐ ĐỢT TỐI ĐA", "kind": "spin", "from": 1, "to": 10},
            {"key": "dot", "label": "ĐỢT HIỆN TẠI", "kind": "spin", "from": 1, "to": 10},
            {"key": "lt", "label": "HỌC PHÍ LÝ THUYẾT / TÍN CHỈ (VNĐ)"},
            {"key": "th", "label": "HỌC PHÍ THỰC HÀNH / TÍN CHỈ (VNĐ)"},
            {"key": "si", "label": "SĨ SỐ TỐI ĐA MỖI LỚP", "kind": "spin", "from": 1, "to": 1000}], columns=2)
        self.form.pack(fill="x")
        T.button(c1.body, "Lưu cấu hình", self.luu, "primary").pack(anchor="w", pady=(4, 0))
        T.label(c1.body, "Học phí thực hành phải lớn hơn lý thuyết. Giá riêng của từng lớp (nếu có) được ưu tiên khi tính học phí.",
                9, False, P["muted"], wraplength=T.px(520)).pack(anchor="w", pady=(10, 0))

        c2 = Card(row, T, "Dữ liệu và sao lưu", "Dữ liệu lưu trong các tệp JSON cạnh chương trình.")
        c2.grid(row=0, column=1, sticky="new", padx=(8, 0))
        self.info = T.label(c2.body, "", 10, False, P["text"], wraplength=T.px(380))
        self.info.pack(anchor="w", pady=(0, 12))
        for text, cmd, kind in (("Sao lưu dữ liệu ngay", self.sao_luu, "primary"),
                                ("Mở thư mục dữ liệu", lambda: self.mo(core.BASE_DIR), "secondary"),
                                ("Mở thư mục sao lưu", lambda: self.mo(os.path.join(core.BASE_DIR, "backup")), "secondary")):
            T.button(c2.body, text, cmd, kind).pack(fill="x", pady=3)
        T.label(c2.body, "Chương trình tự sao lưu mỗi lần khởi động và giữ 10 bản gần nhất. Hãy thoát ứng dụng trước khi sửa JSON bằng tay.",
                9, False, P["muted"], wraplength=T.px(380)).pack(anchor="w", pady=(12, 0))

    def refresh(self):
        c = self.svc.cau_hinh()
        self.form.set_values({"bd": c["thoi_gian_bat_dau"], "kt": c["thoi_gian_ket_thuc"], "so_dot": c["so_dot_toi_da"],
                              "dot": c["dot_dang_ky_hien_tai"], "lt": c["hoc_phi_ly_thuyet_moi_tin_chi"],
                              "th": c["hoc_phi_thuc_hanh_moi_tin_chi"], "si": c["si_so_toi_da_moi_lop"]})
        goc = os.path.join(core.BASE_DIR, "backup")
        so_ban = len([d for d in os.listdir(goc) if os.path.isdir(os.path.join(goc, d))]) if os.path.isdir(goc) else 0
        self.info.config(text=f"Thư mục dữ liệu:\n{core.BASE_DIR}\n\nSố bản sao lưu hiện có: {so_ban}")

    def luu(self):
        f = self.form.values()
        ok, _ = self.app.call(self.svc.luu_cau_hinh, f["bd"], f["kt"], f["so_dot"], f["dot"],
                              f["lt"].replace(".", ""), f["th"].replace(".", ""), f["si"], title="Cấu hình chưa hợp lệ")
        if ok:
            self.app.toast.show("Đã lưu cấu hình.", "success")
            self.refresh()

    def sao_luu(self):
        ok, dich = self.app.call(self.svc.sao_luu)
        if ok:
            self.app.toast.show(f"Đã sao lưu vào backup/{os.path.basename(dich or '')}", "success")
            self.refresh()

    def mo(self, path):
        os.makedirs(path, exist_ok=True)
        if not open_folder(path):
            self.app.warn("Không mở được thư mục", path)


ADMIN_MENU = (("dashboard", "▦", "Tổng quan"), ("users", "☻", "Tài khoản sinh viên"), ("mon", "☰", "Môn học"),
              ("lop", "▤", "Lớp học phần"), ("thi", "✎", "Lịch thi"), ("config", "⚙", "Cấu hình & dữ liệu"))
ADMIN_PAGES = {
    "dashboard": ("Tổng quan hệ thống", "Số liệu nhanh về sinh viên, lớp học phần và học phí", AdminDashboard),
    "users": ("Tài khoản sinh viên", "Tạo, sửa, khóa/mở khóa, đặt lại mật khẩu và xóa tài khoản", AdminUsersPage),
    "mon": ("Môn học", "Danh mục môn học và môn tiên quyết", AdminSubjectsPage),
    "lop": ("Lớp học phần", "Tạo/sửa lớp, khóa hoặc mở khóa đăng ký", AdminClassesPage),
    "thi": ("Lịch thi", "Tạo lịch thi cho sinh viên theo tiết thi", AdminExamsPage),
    "config": ("Cấu hình & dữ liệu", "Thời gian đăng ký, học phí, sao lưu", AdminConfigPage),
}
