# -*- coding: utf-8 -*-
"""oneuni_screens - màn hình đăng nhập, khung điều hướng, các trang sinh viên và trang tài khoản."""
from __future__ import annotations

import os
import tkinter as tk
import traceback
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk

import oneuni_core as core
from oneuni_core import DuLieuError, NghiepVuError
from oneuni_ui import (EVENT_COLORS, P, Card, Col, DataTable, FormGrid, Page, StatCard, Theme, Toast,
                       autowrap, fit_text, round_rect)

TT_TAM_NGUNG = core.TT_TAM_NGUNG


def thu_ngay(d):
    return f"{core.THU[d.weekday()]}, {d:%d/%m/%Y}"


# =============================================================================
# Điều hướng
# =============================================================================
class NavItem(tk.Frame):
    def __init__(self, parent, T, key, icon, text, command):
        super().__init__(parent, bg=P["navy"], cursor="hand2")
        self.key, self.active = key, False
        self.bar = tk.Frame(self, bg=P["navy"], width=4)
        self.bar.pack(side="left", fill="y")
        self.icon = tk.Label(self, text=icon, bg=P["navy"], fg=P["navy_text"], font=T.f(12), width=3)
        self.icon.pack(side="left", pady=11)
        self.txt = tk.Label(self, text=text, bg=P["navy"], fg=P["navy_text"], font=T.f(10, True), anchor="w")
        self.txt.pack(side="left", fill="x", expand=True)
        for w in (self, self.icon, self.txt, self.bar):
            w.bind("<Button-1>", lambda e: command(key))
            w.bind("<Enter>", lambda e: self._ve(True))
            w.bind("<Leave>", lambda e: self._ve(False))

    def _ve(self, hover=False):
        nen = P["navy_active"] if self.active else (P["navy_hover"] if hover else P["navy"])
        chu = "white" if (self.active or hover) else P["navy_text"]
        for w in (self, self.icon, self.txt):
            w.config(bg=nen)
        self.icon.config(fg=chu)
        self.txt.config(fg=chu)
        self.bar.config(bg="#60A5FA" if self.active else nen)

    def set_active(self, active):
        self.active = active
        self._ve(False)


# =============================================================================
# Đăng nhập
# =============================================================================
class LoginView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=P["bg"])
        self.pack(fill="both", expand=True)
        self.app, T = app, app.theme

        left = tk.Frame(self, bg=P["navy"], width=T.px(460))
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        T.label(left, "HUIT", 34, True, "white", P["navy"]).pack(anchor="w", padx=52, pady=(84, 0))
        T.label(left, "OneUni", 20, False, "#8FB4F5", P["navy"]).pack(anchor="w", padx=54)
        T.label(left, "Hệ thống đăng ký học phần", 12, False, P["navy_text"], P["navy"]).pack(
            anchor="w", padx=54, pady=(6, 44))
        for text in ("Đăng ký nhanh, tự kiểm tra trùng lịch và điều kiện",
                     "Thời khóa biểu theo tuần kèm lịch thi",
                     "Học phí và thanh toán mô phỏng",
                     "Quản trị lớp, môn học, tài khoản, lịch thi"):
            row = tk.Frame(left, bg=P["navy"])
            row.pack(anchor="w", padx=54, pady=6)
            T.label(row, "✔", 11, True, "#5EEAA8", P["navy"]).pack(side="left", padx=(0, 10))
            T.label(row, text, 10, False, "#DCE7F7", P["navy"]).pack(side="left")
        T.label(left, f"Phiên bản v{core.APP_VERSION}  ·  Dự án mô phỏng phục vụ học tập, không kết nối hệ thống chính thức",
                8, False, "#7F98BD", P["navy"], wraplength=T.px(360)).pack(side="bottom", anchor="w", padx=54, pady=26)

        right = tk.Frame(self, bg=P["bg"])
        right.pack(side="left", fill="both", expand=True)
        card = tk.Frame(right, bg=P["card"], highlightbackground=P["border"], highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", width=T.px(430))
        inner = tk.Frame(card, bg=P["card"])
        inner.pack(fill="x", padx=36, pady=34)
        T.label(inner, "Đăng nhập", 22, True, P["navy"]).pack(anchor="w")
        T.label(inner, "Dùng tài khoản sinh viên hoặc quản trị viên của bạn.", 10, False, P["muted"]).pack(
            anchor="w", pady=(2, 22))

        self.v_user, self.v_pw = tk.StringVar(), tk.StringVar()
        T.label(inner, "MÃ SINH VIÊN / TÀI KHOẢN", 9, True, P["muted"]).pack(anchor="w", pady=(0, 4))
        self.e_user = ttk.Entry(inner, textvariable=self.v_user)
        self.e_user.pack(fill="x")
        T.label(inner, "MẬT KHẨU", 9, True, P["muted"]).pack(anchor="w", pady=(14, 4))
        self.e_pw = ttk.Entry(inner, textvariable=self.v_pw, show="•")
        self.e_pw.pack(fill="x")
        self.v_show = tk.BooleanVar(value=False)
        ttk.Checkbutton(inner, text="Hiện mật khẩu", variable=self.v_show, style="Card.TCheckbutton",
                        command=lambda: self.e_pw.config(show="" if self.v_show.get() else "•")).pack(
            anchor="w", pady=(8, 0))
        self.err = T.label(inner, "", 9, True, P["danger"], wraplength=T.px(350))
        self.err.pack(anchor="w", pady=(8, 0))
        T.button(inner, "ĐĂNG NHẬP", self.submit, "primary").pack(fill="x", pady=(10, 0), ipady=3)
        for e in (self.e_user, self.e_pw):
            e.bind("<Return>", lambda ev: self.submit())

        if app.demo_hints:
            box = tk.Frame(inner, bg=P["primary_soft"])
            box.pack(fill="x", pady=(22, 0))
            T.label(box, "Tài khoản demo (bấm để điền sẵn)", 9, True, P["primary"], P["primary_soft"]).pack(
                anchor="w", padx=12, pady=(8, 2))
            for ma, mk, nhan in app.demo_hints:
                lb = T.label(box, f"{nhan}:  {ma}  /  {mk}", 9, False, P["navy"], P["primary_soft"], cursor="hand2")
                lb.pack(anchor="w", padx=12, pady=(0, 2))
                lb.bind("<Button-1>", lambda e, m=ma, k=mk: (self.v_user.set(m), self.v_pw.set(k), self.e_pw.focus_set()))
            tk.Frame(box, height=6, bg=P["primary_soft"]).pack()
        self.e_user.focus_set()

    def submit(self):
        try:
            user = self.app.svc.dang_nhap(self.v_user.get(), self.v_pw.get())
        except NghiepVuError as loi:
            self.err.config(text=str(loi))
            self.e_pw.focus_set()
            return
        except DuLieuError as loi:
            messagebox.showerror("Lỗi dữ liệu", f"{loi}\n\nHãy khôi phục tệp từ thư mục backup.", parent=self.app.root)
            return
        self.app.user = user
        self.app.show_main()
        self.app.toast.show(f"Xin chào {user.get('ho_ten', user['ma_nd'])}!", "success")


# =============================================================================
# Khung chính (thanh bên + thanh tiêu đề + vùng nội dung)
# =============================================================================
class Shell(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=P["bg"])
        self.pack(fill="both", expand=True)
        self.app, T = app, app.theme
        self.pages, self.items, self.current = {}, {}, None
        la_admin = app.user.get("vai_tro") == "admin"
        self.menu, self.registry = ((ADMIN_MENU, ADMIN_PAGES) if la_admin else (STUDENT_MENU, STUDENT_PAGES))

        side = tk.Frame(self, bg=P["navy"], width=T.px(252))
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        brand = tk.Frame(side, bg=P["navy"])
        brand.pack(fill="x", padx=24, pady=(26, 24))
        T.label(brand, "HUIT", 20, True, "white", P["navy"]).pack(side="left")
        T.label(brand, "  OneUni", 12, False, "#8FB4F5", P["navy"]).pack(side="left", pady=(6, 0))
        T.label(side, "MENU", 8, True, "#6E86AD", P["navy"]).pack(anchor="w", padx=26, pady=(0, 6))
        for key, icon, text in self.menu:
            it = NavItem(side, T, key, icon, text, self.show)
            it.pack(fill="x", pady=1)
            self.items[key] = it
        foot = tk.Frame(side, bg=P["navy"])
        foot.pack(side="bottom", fill="x", padx=22, pady=20)
        T.label(foot, f"OneUni v{core.APP_VERSION}", 8, False, "#6E86AD", P["navy"]).pack(anchor="w", pady=(0, 8))
        out = tk.Label(foot, text="⏻  Đăng xuất", bg=P["navy_hover"], fg="white", font=T.f(10, True), pady=9,
                       cursor="hand2")
        out.pack(fill="x")
        out.bind("<Button-1>", lambda e: app.logout())
        out.bind("<Enter>", lambda e: out.config(bg=P["navy_active"]))
        out.bind("<Leave>", lambda e: out.config(bg=P["navy_hover"]))

        main = tk.Frame(self, bg=P["bg"])
        main.pack(side="left", fill="both", expand=True)
        top = tk.Frame(main, bg=P["card"])
        top.pack(fill="x")
        tk.Frame(main, bg=P["border"], height=1).pack(fill="x")
        tl = tk.Frame(top, bg=P["card"])
        tl.pack(side="left", padx=26, pady=14)
        self.title = T.label(tl, "", 16, True, P["navy"])
        self.title.pack(anchor="w")
        self.sub = T.label(tl, "", 9, False, P["muted"])
        self.sub.pack(anchor="w")
        tr = tk.Frame(top, bg=P["card"])
        tr.pack(side="right", padx=26, pady=12)
        ten = app.user.get("ho_ten", app.user["ma_nd"])
        T.avatar(tr, ten, 40, P["card"]).pack(side="left", padx=(0, 10))
        who = tk.Frame(tr, bg=P["card"])
        who.pack(side="left")
        T.label(who, ten, 10, True, P["navy"]).pack(anchor="w")
        T.label(who, "Quản trị viên" if la_admin else f"Sinh viên · {app.user.get('lop', '')}", 9, False,
                P["muted"]).pack(anchor="w")

        self.container = tk.Frame(main, bg=P["bg"])
        self.container.pack(fill="both", expand=True, padx=24, pady=20)
        self.show("dashboard")

    def show(self, key):
        if self.current is not None:
            self.pages[self.current].pack_forget()
            self.pages[self.current].on_hide()
            self.items[self.current].set_active(False)
        tieu_de, phu, cls = self.registry[key]
        if key not in self.pages:
            self.pages[key] = cls(self.container, self.app)
        page = self.pages[key]
        page.pack(fill="both", expand=True)
        self.current = key
        self.items[key].set_active(True)
        self.title.config(text=tieu_de)
        self.sub.config(text=phu)
        self.update_idletasks()
        page.on_show()

    def refresh_current(self):
        if self.current:
            self.pages[self.current].refresh()

    def focus_search(self):
        if self.current:
            self.pages[self.current].focus_search()


# =============================================================================
# Trang dành cho sinh viên
# =============================================================================
class StudentDashboard(Page):
    def build(self):
        T = self.T
        self.hero = Card(self, T)
        self.hero.pack(fill="x")
        row = tk.Frame(self, bg=P["bg"])
        row.pack(fill="x", pady=14)
        self.stats = [StatCard(row, T, "Lớp đã đăng ký", P["primary"], "☰"),
                      StatCard(row, T, "Tín chỉ đã đăng ký", "#7C3AED", "★"),
                      StatCard(row, T, "Học phí chưa đóng", P["warning"], "₫"),
                      StatCard(row, T, "Lịch thi sắp tới", P["danger"], "✎")]
        for i, c in enumerate(self.stats):
            c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            row.columnconfigure(i, weight=1, uniform="st")
        low = tk.Frame(self, bg=P["bg"])
        low.pack(fill="both", expand=True)
        low.rowconfigure(0, weight=1)
        for i in (0, 1):
            low.columnconfigure(i, weight=1, uniform="lo")
        self.today = Card(low, T, "Lịch học hôm nay", "Các lớp và lịch thi của bạn trong ngày")
        self.today.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.exams = Card(low, T, "Lịch thi sắp tới", "Tối đa 4 lịch thi gần nhất")
        self.exams.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    def refresh(self):
        T, app = self.T, self.app
        u = app.fresh_user()
        s = self.svc.thong_ke_sinh_vien(u["ma_nd"])
        mo, tin = self.svc.trang_thai_dang_ky()

        self.clear(self.hero.body)
        left = tk.Frame(self.hero.body, bg=P["card"])
        left.pack(side="left", fill="x", expand=True)
        T.label(left, f"Xin chào, {u.get('ho_ten', '')}", 17, True, P["navy"]).pack(anchor="w")
        T.label(left, f"Hôm nay là {thu_ngay(date.today())}.", 10, False, P["muted"]).pack(anchor="w", pady=(2, 10))
        chips = tk.Frame(left, bg=P["card"])
        chips.pack(anchor="w")
        for text in (f"MSSV {u['ma_nd']}", f"Ngành {u.get('nganh', '')}", f"Lớp {u.get('lop', '')}", f"GPA {u.get('gpa', '')}"):
            T.chip(chips, text, "muted").pack(side="left", padx=(0, 6))
        T.chip(chips, "● Đăng ký đang mở" if mo else "● Đăng ký đã đóng", "ok" if mo else "bad").pack(side="left", padx=(6, 0))
        T.label(left, tin, 9, False, P["muted"]).pack(anchor="w", pady=(8, 0))
        right = tk.Frame(self.hero.body, bg=P["card"])
        right.pack(side="right")
        T.button(right, "Đăng ký học phần", lambda: app.shell.show("dangky"), "primary").pack(side="left", padx=4)
        T.button(right, "Thời khóa biểu", lambda: app.shell.show("tkb")).pack(side="left", padx=4)

        self.stats[0].set(str(s["so_lop"]), "lớp học phần")
        self.stats[1].set(str(s["tin_chi"]), "tổng số tín chỉ")
        self.stats[2].set(core.fmt_money(s["con_no"]), f"VNĐ · tổng học phí {core.fmt_money(s['hoc_phi'])}")
        self.stats[3].set(str(len(s["thi_sap_toi"])), f"trong {s['so_thi']} lịch thi được gán")

        self.clear(self.today.body)
        if not s["hom_nay"]:
            T.label(self.today.body, "Hôm nay bạn không có lịch học hoặc lịch thi.", 10, False, P["muted"]).pack(
                anchor="w", pady=18)
        for e in s["hom_nay"]:
            fill, edge, chu = EVENT_COLORS[e["loai"]]
            row = tk.Frame(self.today.body, bg=fill)
            row.pack(fill="x", pady=3)
            tk.Frame(row, bg=edge, width=4).pack(side="left", fill="y")
            box = tk.Frame(row, bg=fill)
            box.pack(side="left", fill="x", expand=True, padx=12, pady=8)
            tiet = f"Tiết {e['tiet_bd']}" + (f"–{e['tiet_kt']}" if e["tiet_kt"] != e["tiet_bd"] else "")
            T.label(box, f"{tiet}  ·  {e['tieu_de']}", 10, True, chu, fill).pack(anchor="w")
            T.label(box, f"{e['dong2']}  ·  {e['dong3']}".strip(" ·"), 9, False, chu, fill).pack(anchor="w")

        self.clear(self.exams.body)
        if not s["thi_sap_toi"]:
            T.label(self.exams.body, "Chưa có lịch thi sắp tới.", 10, False, P["muted"]).pack(anchor="w", pady=18)
        for x in s["thi_sap_toi"]:
            con = (x["ngay_date"] - date.today()).days
            row = tk.Frame(self.exams.body, bg=P["card"])
            row.pack(fill="x", pady=4)
            blk = tk.Frame(row, bg=P["warning_soft"], width=T.px(56), height=T.px(52))
            blk.pack(side="left")
            blk.pack_propagate(False)
            T.label(blk, f"{x['ngay_date']:%d}", 15, True, P["warning"], P["warning_soft"], anchor="center").pack(
                fill="x", pady=(5, 0))
            T.label(blk, f"Th {x['ngay_date']:%m}", 8, True, P["warning"], P["warning_soft"], anchor="center").pack(fill="x")
            box = tk.Frame(row, bg=P["card"])
            box.pack(side="left", fill="x", expand=True, padx=12)
            T.label(box, x.get("mon", ""), 10, True, P["navy"]).pack(anchor="w")
            T.label(box, f"{x.get('gio', '')}  ·  Tiết {x['tiet_thi']}  ·  Phòng {x.get('phong', '')}", 9, False,
                    P["muted"]).pack(anchor="w")
            T.chip(row, "Hôm nay" if con == 0 else f"Còn {con} ngày", "bad" if con <= 3 else "info").pack(side="right")


class RegistrationPage(Page):
    FILTERS = ("Tất cả lớp", "Đã đăng ký", "Chưa đăng ký", "Còn chỗ")

    def build(self):
        T = self.T
        top = tk.Frame(self, bg=P["bg"])
        top.pack(fill="x", pady=(0, 12))
        self.status_chip = T.chip(top, "", "ok")
        self.status_chip.pack(side="left")
        self.status_txt = T.label(top, "", 9, False, P["muted"], P["bg"])
        self.status_txt.pack(side="left", padx=10)
        self.summary = T.label(top, "", 10, True, P["navy"], P["bg"])
        self.summary.pack(side="right")

        card = Card(self, T, pad=14)
        card.pack(fill="both", expand=True)
        cols = [Col("ma_lhp", "Mã LHP", 90), Col("ma_mh", "Mã môn", 90), Col("ten", "Tên môn học", 230, "w", True),
                Col("gv", "Giảng viên", 150, "w"), Col("lop", "Lớp dự kiến", 100), Col("tc", "TC", 50),
                Col("si", "Sĩ số", 80), Col("thu", "Thứ", 80), Col("tiet", "Tiết", 70), Col("phong", "Phòng", 75),
                Col("loai", "Loại", 90), Col("hp", "Học phí (VNĐ)", 115, "e"), Col("thu_phi", "Thu phí", 80),
                Col("ngay", "Ngày ĐK", 95), Col("tt", "Trạng thái lớp", 105)]
        self.table = DataTable(card.body, T, cols, height=11, on_select=self.show_detail,
                               on_double=self.on_double, notify=self.app.toast.show)
        self.table.pack(fill="both", expand=True)
        self.filter = ttk.Combobox(self.table.toolbar, values=self.FILTERS, state="readonly", width=13)
        self.filter.current(0)
        self.filter.pack(side="right", padx=(0, 6))
        self.filter.bind("<<ComboboxSelected>>", lambda e: self.fill())

        bottom = Card(self, T, pad=14)
        bottom.pack(fill="x", pady=(12, 0))
        info = tk.Frame(bottom.body, bg=P["card"])
        info.pack(side="left", fill="x", expand=True)
        self.d_title = T.label(info, "", 11, True, P["navy"])
        self.d_title.pack(anchor="w")
        self.d_info = T.label(info, "", 9, False, P["muted"])
        self.d_info.pack(anchor="w", pady=(2, 4))
        self.d_reason = T.label(info, "", 10, False, P["text"])
        self.d_reason.pack(anchor="w", fill="x")
        autowrap(self.d_reason, 40)
        btns = tk.Frame(bottom.body, bg=P["card"])
        btns.pack(side="right", padx=(16, 0))
        T.button(btns, "Đăng ký học phần", self.dang_ky, "primary").pack(side="left", padx=4)
        T.button(btns, "Hủy đăng ký", self.huy, "danger").pack(side="left", padx=4)
        T.button(btns, "Làm mới", self.refresh, "secondary").pack(side="left", padx=4)

    def refresh(self):
        ma = self.app.user["ma_nd"]
        self.data = {h["ma_lhp"]: h for h in self.svc.bang_dang_ky(ma)}
        mo, tin = self.svc.trang_thai_dang_ky()
        self.T.set_chip(self.status_chip, "● Đang mở" if mo else "● Đã đóng", "ok" if mo else "bad")
        self.status_txt.config(text=tin)
        tk_ = self.svc.tong_ket_dang_ky(ma)
        self.summary.config(text=f"Đã đăng ký {tk_['so_lop']} lớp · {tk_['tin_chi']} tín chỉ · "
                                 f"Học phí {core.fmt_money(tk_['hoc_phi'])} VNĐ · Chưa đóng {core.fmt_money(self.svc.tong_no(ma))} VNĐ")
        self.fill()
        self.show_detail()

    def fill(self):
        loc, rows = self.filter.get(), []
        for h in self.data.values():
            lhp = h["lhp"]
            tt = lhp.get("trang_thai_lich", core.TT_BINH_THUONG)
            day = h["si_so"] >= h["si_so_max"]
            if (loc == "Đã đăng ký" and not h["da_dk"]) or (loc == "Chưa đăng ký" and h["da_dk"]):
                continue
            if loc == "Còn chỗ" and (day or tt == TT_TAM_NGUNG):
                continue
            tags = ["bg_ok"] if h["da_dk"] else (["bad"] if tt == TT_TAM_NGUNG else (["muted"] if day else []))
            v = [h["ma_lhp"], h["ma_mh"], h["ten_mon"], lhp.get("ten_giang_vien", "Chưa phân công"),
                 lhp.get("lop_hoc_du_kien", "—"), h["tin_chi"], f"{h['si_so']}/{h['si_so_max']}",
                 lhp.get("thu", ""), lhp.get("tiet_hoc", ""), lhp.get("phong_hoc", ""), lhp.get("loai_lich", ""),
                 core.fmt_money(h["hoc_phi"]), h["thu_phi"], h["ngay_dk"], tt]
            raw = list(v)
            raw[6], raw[11] = h["si_so"], h["hoc_phi"]
            rows.append({"iid": h["ma_lhp"], "values": tuple(v), "raw": tuple(raw), "tags": tuple(tags)})
        self.table.set_rows(rows, "dang_ky_hoc_phan")

    def show_detail(self):
        r = self.table.selected_row()
        if not r:
            self.d_title.config(text="Chọn một lớp học phần trong bảng để xem chi tiết")
            self.d_info.config(text="Nhấp đúp vào một lớp chưa đăng ký để đăng ký nhanh.")
            self.d_reason.config(text="")
            return
        h, ma = self.data[r["iid"]], self.app.user["ma_nd"]
        lhp = h["lhp"]
        self.d_title.config(text=f"{h['ma_lhp']} · {h['ten_mon']}")
        self.d_info.config(text=(f"GV {lhp.get('ten_giang_vien', '—')} · {lhp.get('thu', '')}, tiết {lhp.get('tiet_hoc', '')} · "
                                 f"Phòng {lhp.get('phong_hoc', '')} · {h['tin_chi']} TC · "
                                 f"{core.fmt_money(h['hoc_phi'])} VNĐ · Sĩ số {h['si_so']}/{h['si_so_max']}"))
        if h["da_dk"]:
            ly_do = self.svc.ly_do_khong_huy(ma, h["ma_lhp"])
            self.d_reason.config(text="✔ Bạn đã đăng ký lớp này. " + (f"Không thể hủy: {ly_do}" if ly_do else "Có thể hủy đăng ký."),
                                 fg=P["success"])
        else:
            ly_do = self.svc.ly_do_khong_dang_ky(ma, lhp)
            self.d_reason.config(text=f"✖ Không thể đăng ký: {ly_do}" if ly_do else "✔ Đủ điều kiện đăng ký lớp này.",
                                 fg=P["danger"] if ly_do else P["success"])

    def on_double(self, iid):
        if not self.data[iid]["da_dk"]:
            self.dang_ky(iid)

    def dang_ky(self, iid=None):
        r = self.table._by_iid.get(iid) if iid else self.table.selected_row()
        if not r:
            self.app.warn("Chưa chọn lớp", "Vui lòng chọn lớp học phần cần đăng ký.")
            return
        ma = self.app.user["ma_nd"]
        ok, info = self.app.call(self.svc.xem_truoc_dang_ky, ma, r["iid"], title="Không thể đăng ký")
        if not ok:
            self.refresh()
            return
        if not self.app.confirm("Xác nhận đăng ký",
                                f"Bạn xác nhận đăng ký học phần sau?\n\nMã LHP: {info['ma_lhp']}\nMôn học: {info['ten_mon']}\n"
                                f"Số tín chỉ: {info['tin_chi']}\nHọc phí dự kiến: {core.fmt_money(info['hoc_phi'])} VNĐ\n"
                                f"Đợt đăng ký: {info['dot']}"):
            return
        ok, info = self.app.call(self.svc.dang_ky, ma, r["iid"], title="Không thể đăng ký")
        if ok:
            self.app.toast.show(f"Đã đăng ký {info['ma_lhp']} · {info['ten_mon']}. Khoản học phí "
                                f"{core.fmt_money(info['hoc_phi'])} VNĐ đã được tạo.", "success", 5000)
        self.refresh()

    def huy(self):
        r = self.table.selected_row()
        if not r:
            self.app.warn("Chưa chọn lớp", "Chọn lớp học phần muốn hủy đăng ký.")
            return
        ma = self.app.user["ma_nd"]
        ly_do = self.svc.ly_do_khong_huy(ma, r["iid"])
        if ly_do:
            self.app.warn("Không thể hủy", ly_do)
            return
        if not self.app.confirm("Xác nhận hủy", f"Bạn chắc chắn muốn hủy đăng ký lớp {r['iid']}?\n"
                                                 "Khoản học phí chưa thanh toán của lớp này sẽ được gỡ."):
            return
        ok, _ = self.app.call(self.svc.huy_dang_ky, ma, r["iid"], title="Không thể hủy")
        if ok:
            self.app.toast.show(f"Đã hủy đăng ký lớp {r['iid']}.", "info")
        self.refresh()


class TimetablePage(Page):
    LEGEND = (("LT", "Lý thuyết"), ("TH", "Thực hành"), ("TN", "Tạm ngưng"), ("THI", "Lịch thi"))

    def build(self):
        T = self.T
        self.week, self._job = core.dau_tuan_cua(date.today()), None
        bar = tk.Frame(self, bg=P["bg"])
        bar.pack(fill="x", pady=(0, 12))
        T.button(bar, "◀ Tuần trước", lambda: self.doi_tuan(-1)).pack(side="left")
        T.button(bar, "Tuần hiện tại", self.ve_hom_nay, "ghost").pack(side="left", padx=6)
        T.button(bar, "Tuần sau ▶", lambda: self.doi_tuan(1)).pack(side="left")
        self.lbl = T.label(bar, "", 12, True, P["navy"], P["bg"])
        self.lbl.pack(side="left", padx=16)
        for ma, ten in reversed(self.LEGEND):
            fill, edge, chu = EVENT_COLORS[ma]
            tk.Label(bar, text=f"  {ten}  ", bg=fill, fg=chu, font=T.f(9, True), highlightbackground=edge,
                     highlightthickness=1).pack(side="right", padx=3)
        card = Card(self, T, pad=0)
        card.pack(fill="both", expand=True)
        wrap = tk.Frame(card.body, bg=P["card"])
        wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(wrap, bg="white", highlightthickness=0)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", self._lap_ve)
        self.canvas.bind("<Enter>", lambda e: self._wheel(True))
        self.canvas.bind("<Leave>", lambda e: self._wheel(False))
        self.detail = T.label(self, "Nhấp vào một ô lịch để xem chi tiết.", 10, False, P["muted"], P["bg"])
        self.detail.pack(fill="x", pady=(10, 0))
        autowrap(self.detail, 10)

    # --- điều hướng tuần
    def doi_tuan(self, so_tuan):
        ngay_min, ngay_max = core.lay_gioi_han_lich()
        moi = self.week + timedelta(days=7 * so_tuan)
        if moi < ngay_min or moi + timedelta(days=6) > ngay_max:
            self.app.toast.show(f"Chỉ xem được lịch từ {ngay_min:%d/%m/%Y} đến {ngay_max:%d/%m/%Y}.", "warn")
            return
        self.week = moi
        self.ve()

    def ve_hom_nay(self):
        self.week = core.dau_tuan_cua(date.today())
        self.ve()

    def refresh(self):
        self.ve()

    def on_hide(self):
        self._wheel(False)

    def destroy(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except tk.TclError:
                pass
        super().destroy()

    def _lap_ve(self, _e=None):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(80, self.ve)

    def _wheel(self, bat):
        c = self.canvas
        for s in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            if bat:
                c.bind_all(s, self._cuon)
            else:
                c.unbind_all(s)

    def _cuon(self, e):
        self.canvas.yview_scroll((-2 if (getattr(e, "num", 0) == 4 or getattr(e, "delta", 0) > 0) else 2), "units")

    # --- vẽ
    def ve(self):
        self._job = None
        T, c = self.T, self.canvas
        ngay_min, ngay_max = core.lay_gioi_han_lich()
        if self.week < ngay_min or self.week + timedelta(days=6) > ngay_max:
            self.week = core.dau_tuan_cua(date.today())
        cuoi = self.week + timedelta(days=6)
        self.lbl.config(text=f"Tuần {self.week:%d/%m} – {cuoi:%d/%m/%Y}")
        W = max(c.winfo_width(), T.px(760))
        gutter, head_h, row_h = T.px(66), T.px(54), T.px(46)
        col_w = (W - gutter - 2) / 7
        H = head_h + core.MAX_TIET * row_h + 4
        c.delete("all")
        c.configure(scrollregion=(0, 0, W, H))
        hom_nay = date.today()

        for a, b, nen in ((1, 6, "#FFFFFF"), (7, 12, "#FAFBFE"), (13, 16, "#F4F6FB")):
            c.create_rectangle(gutter, head_h + (a - 1) * row_h, W, head_h + b * row_h, fill=nen, outline="")
        for i in range(7):
            if self.week + timedelta(days=i) == hom_nay:
                c.create_rectangle(gutter + i * col_w, head_h, gutter + (i + 1) * col_w, H, fill="#EEF4FF", outline="")
        for t in range(core.MAX_TIET + 1):
            y, dam = head_h + t * row_h, t in (6, 12)
            c.create_line(0, y, W, y, fill="#C4D0E3" if dam else "#E8EDF5", width=2 if dam else 1)
        for i in range(8):
            c.create_line(gutter + i * col_w, head_h, gutter + i * col_w, H, fill="#E8EDF5")
        c.create_rectangle(0, 0, W, head_h, fill=P["head"], outline="")
        for i in range(7):
            d, x0 = self.week + timedelta(days=i), gutter + i * col_w
            nay = d == hom_nay
            if nay:
                round_rect(c, x0 + 5, 7, x0 + col_w - 5, head_h - 7, 9, fill=P["primary"], outline="")
            c.create_text(x0 + col_w / 2, head_h / 2 - 8, text=core.THU[i], font=T.f(9, True),
                          fill="white" if nay else P["navy"])
            c.create_text(x0 + col_w / 2, head_h / 2 + 10, text=f"{d:%d/%m}", font=T.f(9),
                          fill="white" if nay else P["muted"])
        for t in range(1, core.MAX_TIET + 1):
            y = head_h + (t - 0.5) * row_h
            c.create_text(gutter / 2, y + 4, text=f"Tiết {t}", font=T.f(9), fill=P["muted"])
        for t, ten in ((1, "SÁNG"), (7, "CHIỀU"), (13, "TỐI")):
            c.create_text(8, head_h + (t - 1) * row_h + 5, text=ten, anchor="nw", font=T.f(7, True), fill=P["primary"])

        events = self.svc.su_kien_tuan(self.app.user["ma_nd"], self.week)
        theo_ngay = {}
        for e in events:
            theo_ngay.setdefault(e["ngay_idx"], []).append(e)
        for idx, evs in theo_ngay.items():
            if not 0 <= idx <= 6:
                continue
            evs.sort(key=lambda e: (e["tiet_bd"], e["tiet_kt"]))
            lanes = []
            for e in evs:
                for li, cuoi_lane in enumerate(lanes):
                    if e["tiet_bd"] > cuoi_lane:
                        lanes[li], e["_lane"] = e["tiet_kt"], li
                        break
                else:
                    lanes.append(e["tiet_kt"])
                    e["_lane"] = len(lanes) - 1
            for e in evs:
                self._ve_o(e, gutter + idx * col_w, col_w / len(lanes), head_h, row_h)
        if not events:
            c.create_text(gutter + (W - gutter) / 2, head_h + 3 * row_h, font=T.f(12), fill=P["muted"],
                          text="Không có lịch học hoặc lịch thi trong tuần này.")

    def _ve_o(self, e, x0, lw, head_h, row_h):
        T, c = self.T, self.canvas
        fill, edge, chu = EVENT_COLORS[e["loai"]]
        x1, x2 = x0 + e["_lane"] * lw + 3, x0 + (e["_lane"] + 1) * lw - 3
        y1, y2 = head_h + (e["tiet_bd"] - 1) * row_h + 3, head_h + e["tiet_kt"] * row_h - 3
        tag = f"ev{id(e)}"
        round_rect(c, x1, y1, x2, y2, 9, fill=fill, outline=edge, width=1, tags=(tag,))
        c.create_line(x1 + 6, y1 + 8, x1 + 6, y2 - 8, fill=edge, width=3, capstyle="round", tags=(tag,))
        rong, dong = x2 - x1 - 24, T.px(14)
        dong_toi_da = max(1, int((y2 - y1 - 6) // dong))
        y = y1 + 6
        for i, (text, fo, ft) in enumerate(((e["tieu_de"], T.font_obj(9, True), T.f(9, True)),
                                             (e["dong2"], T.font_obj(8), T.f(8)),
                                             (e["dong3"], T.font_obj(8), T.f(8)))):
            if i >= dong_toi_da:
                break
            if text:
                c.create_text(x1 + 16, y, anchor="nw", text=fit_text(fo, text, rong), font=ft, fill=chu, tags=(tag,))
                y += dong
        c.tag_bind(tag, "<Button-1>", lambda ev, ct=e["chi_tiet"]: self.detail.config(
            text=ct.replace("\n", "   ·   "), fg=P["text"]))
        c.tag_bind(tag, "<Enter>", lambda ev: c.config(cursor="hand2"))
        c.tag_bind(tag, "<Leave>", lambda ev: c.config(cursor=""))


class ExamListPage(Page):
    def build(self):
        T = self.T
        card = Card(self, T, pad=14)
        card.pack(fill="both", expand=True)
        T.label(card.body, "Lịch thi do quản trị viên tạo. Bạn chỉ xem được lịch thi được gán cho mình.", 10, False,
                P["muted"]).pack(anchor="w", pady=(0, 10))
        cols = [Col("mon", "Môn thi", 260, "w", True), Col("ngay", "Ngày thi", 110), Col("thu", "Thứ", 90),
                Col("gio", "Giờ thi", 80), Col("tiet", "Tiết", 60), Col("phong", "Phòng", 90),
                Col("ghi_chu", "Ghi chú", 220, "w"), Col("con", "Còn lại", 110)]
        self.table = DataTable(card.body, T, cols, height=14, notify=self.app.toast.show)
        self.table.pack(fill="both", expand=True)
        T.button(self.table.toolbar, "Làm mới", self.refresh, "secondary").pack(side="right", padx=(6, 0))

    def refresh(self):
        rows, hom_nay = [], date.today()
        for x in self.svc.lich_thi(self.app.user["ma_nd"]):
            d = x["ngay_date"]
            con = (d - hom_nay).days
            tt = "Đã thi" if con < 0 else ("Hôm nay" if con == 0 else f"Còn {con} ngày")
            tags = ("muted",) if con < 0 else (("bg_warn",) if con <= 7 else ())
            vals = (x.get("mon", ""), f"{d:%d/%m/%Y}", core.THU[d.weekday()], x.get("gio", ""),
                    x["tiet_thi"], x.get("phong", ""), x.get("ghi_chu", ""), tt)
            raw = list(vals)
            raw[1], raw[4], raw[7] = d.toordinal(), x["tiet_thi"], con
            rows.append({"iid": x["id"], "tags": tags, "values": vals, "raw": tuple(raw)})
        self.table.set_rows(rows, "lich_thi")


class PaymentPage(Page):
    def build(self):
        T = self.T
        top = tk.Frame(self, bg=P["bg"])
        top.pack(fill="x")
        self.c_no = StatCard(top, T, "Chưa thanh toán", P["warning"], "₫")
        self.c_da = StatCard(top, T, "Đã thanh toán", P["success"], "✔")
        self.c_no.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.c_da.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        top.columnconfigure(0, weight=1, uniform="p")
        top.columnconfigure(1, weight=1, uniform="p")
        warn = tk.Label(self, bg=P["warning_soft"], fg=P["warning"], font=T.f(9, True), anchor="w", justify="left",
                        padx=14, pady=10, text="Lưu ý: đây là mô phỏng. QR chỉ là liên kết demo, không nhận tiền thật; "
                                               "nút xác nhận chỉ cập nhật trạng thái trong tệp dữ liệu.")
        warn.pack(fill="x", pady=12)
        autowrap(warn, 30)
        card = Card(self, T, pad=14)
        card.pack(fill="both", expand=True)
        cols = [Col("ma_lhp", "Mã LHP", 90), Col("ma_mh", "Mã môn", 90), Col("ten", "Tên môn học", 230, "w", True),
                Col("tc", "TC", 55), Col("tien", "Số tiền (VNĐ)", 120, "e"), Col("tt", "Trạng thái", 120),
                Col("ngay_tao", "Ngày tạo", 130), Col("pt", "Phương thức", 110), Col("ngay_tt", "Ngày thanh toán", 130)]
        self.table = DataTable(card.body, T, cols, height=9, notify=self.app.toast.show)
        self.table.pack(fill="both", expand=True)
        T.button(self.table.toolbar, "Thanh toán qua ngân hàng (mô phỏng)", lambda: self.thanh_toan("Chuyển khoản ngân hàng"),
                 "primary").pack(side="right", padx=(6, 0))
        T.button(self.table.toolbar, "Thanh toán qua MoMo (mô phỏng)", lambda: self.thanh_toan("MoMo"),
                 "secondary").pack(side="right", padx=(6, 0))

    def refresh(self):
        ma, rows, no, da = self.app.user["ma_nd"], [], 0, 0
        for i, p in enumerate(self.svc.khoan_phi_cua(ma)):
            tien, chua = core.to_int(p.get("so_tien")), self.svc.chua_dong(p)
            no, da = (no + tien, da) if chua else (no, da + tien)
            vals = (p.get("ma_lhp", ""), p.get("ma_mh", ""), p.get("ten_mon", ""), p.get("so_tin_chi", 0),
                    core.fmt_money(tien), core.TT_CHUA_THANH_TOAN if chua else core.TT_DA_THANH_TOAN,
                    p.get("ngay_tao", ""), p.get("phuong_thuc", "—"), p.get("ngay_thanh_toan", "—"))
            raw = list(vals)
            raw[3], raw[4] = core.to_int(p.get("so_tin_chi")), tien
            rows.append({"iid": str(i), "tags": ("warn",) if chua else ("ok",), "values": vals, "raw": tuple(raw)})
        self.table.set_rows(rows, "hoc_phi")
        self.c_no.set(core.fmt_money(no), "VNĐ · các khoản chờ thanh toán")
        self.c_da.set(core.fmt_money(da), "VNĐ · đã được ghi nhận")

    def thanh_toan(self, phuong_thuc):
        ma = self.app.user["ma_nd"]
        con_no = [p for p in self.svc.khoan_phi_cua(ma) if self.svc.chua_dong(p)]
        if not con_no:
            self.app.toast.show("Bạn không có khoản học phí nào đang chờ thanh toán.", "info")
            return
        tong = sum(core.to_int(p.get("so_tien")) for p in con_no)
        win = tk.Toplevel(self.app.root)
        win.title(f"Thanh toán toàn bộ - {phuong_thuc}")
        win.configure(bg=P["card"])
        win.resizable(False, False)
        win.transient(self.app.root)
        T = self.T
        T.label(win, f"THANH TOÁN TOÀN BỘ · {phuong_thuc.upper()}", 12, True, P["navy"], anchor="center",
                wraplength=T.px(400)).pack(padx=30, pady=(22, 8))
        T.label(win, f"Mã sinh viên: {ma}\nSố học phần chưa thanh toán: {len(con_no)}\nTổng tiền: {core.fmt_money(tong)} VNĐ",
                11, True, P["text"], anchor="center", justify="center").pack(pady=4)
        T.label(win, "Các lớp học phần: " + ", ".join(str(p.get("ma_lhp", "")) for p in con_no), 9, False, P["muted"],
                anchor="center", justify="center", wraplength=T.px(400)).pack(pady=(2, 8))
        kh = tk.Canvas(win, width=T.px(230), height=T.px(230), bg="white", highlightthickness=1,
                       highlightbackground=P["border"])
        kh.pack(pady=6)
        try:
            img = tk.PhotoImage(file=os.path.join(core.BASE_DIR, "QR_Link_YouTube.png"))
            lon = max(img.width(), img.height())
            if lon > T.px(220):
                img = img.subsample(-(-lon // T.px(220)))
            self._qr = img
            kh.create_image(T.px(115), T.px(115), image=img)
        except tk.TclError as loi:
            kh.create_text(T.px(115), T.px(115), text=f"Không tải được ảnh QR\n{loi}", fill=P["danger"],
                           width=T.px(200), justify="center")
        T.label(win, "QR chỉ là demo, không phải mã nhận tiền.", 9, True, P["warning"], anchor="center").pack(pady=4)

        def xac_nhan():
            if not self.app.confirm("Xác nhận thanh toán (mô phỏng)",
                                    f"Cập nhật thanh toán mô phỏng cho {len(con_no)} học phần?\n\nTổng cộng: "
                                    f"{core.fmt_money(tong)} VNĐ\nPhương thức: {phuong_thuc}\n\n"
                                    "Đây chỉ là thao tác demo, không có giao dịch hay chuyển tiền thật.", parent=win):
                return
            ok, kq = self.app.call(self.svc.thanh_toan_tat_ca, ma, phuong_thuc, title="Không thể thanh toán")
            win.destroy()
            self.refresh()
            if ok:
                messagebox.showinfo("Thanh toán thành công (mô phỏng)",
                                    f"Mã giao dịch: {kq['ma_gd']}\nSố học phần: {kq['so_khoan']}\n"
                                    f"Tổng tiền: {core.fmt_money(kq['tong'])} VNĐ\nPhương thức: {phuong_thuc}",
                                    parent=self.app.root)

        frm = tk.Frame(win, bg=P["card"])
        frm.pack(pady=(8, 22))
        T.button(frm, "Xác nhận thanh toán (mô phỏng)", xac_nhan, "success").pack(side="left", padx=5)
        T.button(frm, "Đóng", win.destroy, "secondary").pack(side="left", padx=5)
        win.update_idletasks()
        win.geometry(f"+{self.app.root.winfo_rootx() + 160}+{self.app.root.winfo_rooty() + 40}")
        try:
            win.grab_set()
        except tk.TclError:
            pass


class PaidPage(Page):
    def build(self):
        T = self.T
        card = Card(self, T, pad=14)
        card.pack(fill="both", expand=True)
        T.label(card.body, "Chỉ hiển thị các lớp học phần đã đăng ký và được ghi nhận đã thanh toán.", 10, False,
                P["muted"]).pack(anchor="w", pady=(0, 10))
        cols = [Col("ma_lhp", "Mã LHP", 90), Col("ma_mh", "Mã môn", 90), Col("ten", "Tên môn học", 230, "w", True),
                Col("gv", "Giảng viên", 150, "w"), Col("thu", "Thứ", 80), Col("tiet", "Tiết", 70), Col("phong", "Phòng", 80),
                Col("loai", "Loại", 90), Col("tc", "TC", 55), Col("hp", "Học phí (VNĐ)", 115, "e"),
                Col("ngay", "Ngày thanh toán", 130), Col("gd", "Mã giao dịch", 130)]
        self.table = DataTable(card.body, T, cols, height=14, notify=self.app.toast.show)
        self.table.pack(fill="both", expand=True)
        T.button(self.table.toolbar, "Làm mới", self.refresh, "secondary").pack(side="right", padx=(6, 0))

    def refresh(self):
        rows = []
        for x in self.svc.hoc_phan_da_dong(self.app.user["ma_nd"]):
            lhp, p = x["lhp"], x["phi"]
            tien = core.to_int(p.get("so_tien"))
            vals = (lhp["ma_lhp"], lhp.get("ma_mh", ""), x["ten_mon"], lhp.get("ten_giang_vien", "Chưa phân công"),
                    lhp.get("thu", ""), lhp.get("tiet_hoc", ""), lhp.get("phong_hoc", ""), lhp.get("loai_lich", ""),
                    x["tin_chi"], core.fmt_money(tien), p.get("ngay_thanh_toan", ""), p.get("ma_giao_dich", "—"))
            raw = list(vals)
            raw[8], raw[9] = x["tin_chi"], tien
            rows.append({"iid": lhp["ma_lhp"], "values": vals, "raw": tuple(raw)})
        self.table.set_rows(rows, "hoc_phan_da_dong_phi")


# =============================================================================
# Tài khoản (dùng chung cho sinh viên và quản trị viên)
# =============================================================================
class AccountPage(Page):
    def build(self):
        T = self.T
        row = tk.Frame(self, bg=P["bg"])
        row.pack(fill="both", expand=True)
        row.columnconfigure(0, weight=1, uniform="a")
        row.columnconfigure(1, weight=1, uniform="a")
        self.profile = Card(row, T, "Thông tin tài khoản")
        self.profile.grid(row=0, column=0, sticky="new", padx=(0, 8))
        pw = Card(row, T, "Đổi mật khẩu", "Mật khẩu mới tối thiểu 6 ký tự và khác mật khẩu hiện tại.")
        pw.grid(row=0, column=1, sticky="new", padx=(8, 0))
        self.form = FormGrid(pw.body, T, [
            {"key": "cu", "label": "MẬT KHẨU HIỆN TẠI", "show": "•"},
            {"key": "moi", "label": "MẬT KHẨU MỚI", "show": "•"},
            {"key": "lap", "label": "NHẬP LẠI MẬT KHẨU MỚI", "show": "•"}])
        self.form.pack(fill="x")
        self.v_show = tk.BooleanVar(value=False)
        ttk.Checkbutton(pw.body, text="Hiện mật khẩu", variable=self.v_show, style="Card.TCheckbutton",
                        command=self.doi_hien).pack(anchor="w", pady=(0, 12))
        T.button(pw.body, "Cập nhật mật khẩu", self.doi_mat_khau, "primary").pack(anchor="w")

    def doi_hien(self):
        for k in ("cu", "moi", "lap"):
            self.form.widgets[k].config(show="" if self.v_show.get() else "•")

    def refresh(self):
        T, u = self.T, self.app.fresh_user()
        self.clear(self.profile.body)
        head = tk.Frame(self.profile.body, bg=P["card"])
        head.pack(fill="x", pady=(0, 12))
        T.avatar(head, u.get("ho_ten", u["ma_nd"]), 56).pack(side="left", padx=(0, 14))
        box = tk.Frame(head, bg=P["card"])
        box.pack(side="left")
        T.label(box, u.get("ho_ten", ""), 14, True, P["navy"]).pack(anchor="w")
        T.chip(box, "Quản trị viên" if u.get("vai_tro") == "admin" else "Sinh viên", "info").pack(anchor="w", pady=(4, 0))
        dong = [("Tài khoản", u["ma_nd"])]
        if u.get("vai_tro") == "sinh_vien":
            dong += [("Ngành", u.get("nganh", "")), ("Lớp", u.get("lop", "")), ("GPA", u.get("gpa", "")),
                     ("Cảnh báo học vụ", u.get("canh_bao_hoc_vu", 0)),
                     ("Đã đóng học phí kỳ trước", "Có" if u.get("da_dong_hoc_phi", True) else "Chưa")]
        for k, v in dong:
            r = tk.Frame(self.profile.body, bg=P["card"])
            r.pack(fill="x", pady=3)
            T.label(r, k, 10, False, P["muted"], width=24).pack(side="left")
            T.label(r, str(v), 10, True, P["text"]).pack(side="left")

    def doi_mat_khau(self):
        v = self.form.values()
        if v["moi"] != v["lap"]:
            self.app.warn("Mật khẩu không khớp", "Mật khẩu mới và phần nhập lại chưa giống nhau.")
            return
        ok, _ = self.app.call(self.svc.doi_mat_khau, self.app.user["ma_nd"], v["cu"], v["moi"],
                              title="Không thể đổi mật khẩu")
        if ok:
            self.form.clear()
            self.app.demo_hints = self.svc.goi_y_demo()
            self.app.toast.show("Đã cập nhật mật khẩu.", "success")


# =============================================================================
# Danh mục trang
# =============================================================================
STUDENT_MENU = (("dashboard", "▦", "Tổng quan"), ("dangky", "☰", "Đăng ký học phần"), ("tkb", "▤", "Thời khóa biểu"),
                ("lichthi", "✎", "Lịch thi"), ("hocphi", "₫", "Học phí / Thanh toán"),
                ("dadong", "✔", "Học phần đã đóng phí"), ("taikhoan", "☺", "Tài khoản"))
STUDENT_PAGES = {
    "dashboard": ("Tổng quan", "Tình hình học tập và đăng ký của bạn", StudentDashboard),
    "dangky": ("Đăng ký học phần", "Tìm lớp, kiểm tra điều kiện và đăng ký", RegistrationPage),
    "tkb": ("Thời khóa biểu", "Lịch học và lịch thi theo tuần (xem trong phạm vi 2 năm trước/sau)", TimetablePage),
    "lichthi": ("Lịch thi", "Các lịch thi được gán cho bạn", ExamListPage),
    "hocphi": ("Học phí / Thanh toán", "Theo dõi khoản phí và thanh toán mô phỏng", PaymentPage),
    "dadong": ("Học phần đã đóng phí", "Danh sách học phần đã được ghi nhận thanh toán", PaidPage),
    "taikhoan": ("Tài khoản", "Thông tin cá nhân và mật khẩu", AccountPage),
}

from oneuni_admin import ADMIN_MENU as _ADMIN_MENU, ADMIN_PAGES as _ADMIN_PAGES  # noqa: E402

ADMIN_MENU = _ADMIN_MENU + (("taikhoan", "☺", "Tài khoản"),)
ADMIN_PAGES = {**_ADMIN_PAGES, "taikhoan": STUDENT_PAGES["taikhoan"]}


# =============================================================================
# Bộ điều khiển ứng dụng
# =============================================================================
class OneUniApp:
    def __init__(self, root, svc):
        self.root, self.svc, self.user, self.screen, self.shell = root, svc, None, None, None
        self.theme = Theme(root)
        self.toast = Toast(root, self.theme)
        self.demo_hints = svc.goi_y_demo()
        root.title(f"OneUni v{core.APP_VERSION} — Hệ thống đăng ký học phần HUIT")
        w, h = self.theme.px(1380), self.theme.px(840)
        x, y = max(0, (root.winfo_screenwidth() - w) // 2), max(0, (root.winfo_screenheight() - h) // 2 - 20)
        root.geometry(f"{w}x{h}+{x}+{y}")
        root.minsize(self.theme.px(1120), self.theme.px(700))
        root.report_callback_exception = self.on_unhandled
        root.bind_all("<F5>", lambda e: self.shell and self.shell.refresh_current())
        root.bind_all("<Control-f>", lambda e: self.shell and self.shell.focus_search())
        self.show_login()

    def _doi_man_hinh(self):
        if self.screen is not None:
            self.screen.destroy()
        self.screen = tk.Frame(self.root, bg=P["bg"])
        self.screen.pack(fill="both", expand=True)
        self.toast.hide()
        return self.screen

    def show_login(self):
        self.user = self.shell = None
        LoginView(self._doi_man_hinh(), self)

    def show_main(self):
        self.shell = Shell(self._doi_man_hinh(), self)

    def logout(self):
        self.show_login()

    def fresh_user(self):
        moi = self.svc.get_user(self.user["ma_nd"])
        if moi:
            self.user = moi
        return self.user

    # --- hộp thoại / gọi nghiệp vụ
    def warn(self, tieu_de, noi_dung):
        messagebox.showwarning(tieu_de, noi_dung, parent=self.root)

    def confirm(self, tieu_de, noi_dung, parent=None):
        return messagebox.askyesno(tieu_de, noi_dung, parent=parent or self.root)

    def call(self, fn, *args, title="Không thực hiện được"):
        """Gọi hàm nghiệp vụ; trả về (thành công?, kết quả) và tự hiển thị lỗi cho người dùng."""
        try:
            return True, fn(*args)
        except NghiepVuError as loi:
            messagebox.showerror(title, str(loi), parent=self.root)
        except DuLieuError as loi:
            messagebox.showerror("Lỗi dữ liệu", f"{loi}\n\nHãy khôi phục tệp từ thư mục backup.", parent=self.root)
        return False, None

    def on_unhandled(self, exc, val, tb):
        chi_tiet = "".join(traceback.format_exception(exc, val, tb))
        try:
            with open(os.path.join(core.BASE_DIR, "oneuni_error.log"), "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}]\n{chi_tiet}")
        except OSError:
            pass
        messagebox.showerror("Lỗi không mong muốn",
                             f"Ứng dụng gặp lỗi: {val}\n\nChi tiết đã được ghi vào oneuni_error.log. "
                             "Dữ liệu của bạn không bị ảnh hưởng.", parent=self.root)
