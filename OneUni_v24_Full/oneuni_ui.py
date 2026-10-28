# -*- coding: utf-8 -*-
"""
oneuni_ui - bộ thành phần giao diện dùng chung cho OneUni (chỉ dùng thư viện chuẩn: tkinter/ttk).

Gồm: Theme (màu, phông, kiểu ttk), Card, StatCard, DataTable (tìm kiếm/sắp xếp/xuất CSV),
FormGrid (biểu mẫu khai báo), DatePicker, Toast (thông báo nổi) và lớp nền Page.
Chỉ dùng ký tự biểu tượng trong BMP (không dùng emoji) để chạy ổn định trên mọi bản Tk 8.6.
"""
from __future__ import annotations

import calendar
import csv
import os
import tkinter as tk
import unicodedata
from collections import namedtuple
from datetime import date
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

import oneuni_core as core

# ----------------------------------------------------------------------------
# Bảng màu
# ----------------------------------------------------------------------------
P = {
    "bg": "#F3F6FB", "card": "#FFFFFF", "border": "#E1E7F0", "text": "#1F2A3D", "muted": "#6B7A90",
    "primary": "#2563EB", "primary_hover": "#1D4ED8", "primary_soft": "#E8F0FE",
    "navy": "#0F2747", "navy_hover": "#17345E", "navy_active": "#1F4A85", "navy_text": "#C7D5EA",
    "success": "#15803D", "success_soft": "#DCFCE7", "warning": "#B45309", "warning_soft": "#FEF3C7",
    "danger": "#DC2626", "danger_hover": "#B91C1C", "danger_soft": "#FEE2E2",
    "row_alt": "#F8FAFD", "select": "#DBEAFE", "head": "#EEF2F9",
}
# màu ô thời khóa biểu: (nền, viền, chữ)
EVENT_COLORS = {
    "LT": ("#DCFCE7", "#16A34A", "#14532D"),
    "TH": ("#DBEAFE", "#2563EB", "#1E3A8A"),
    "TN": ("#FEE2E2", "#DC2626", "#7F1D1D"),
    "THI": ("#FEF3C7", "#D97706", "#78350F"),
}
FONT_UU_TIEN = ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Inter", "Ubuntu", "Noto Sans", "DejaVu Sans")
Col = namedtuple("Col", "key title width anchor stretch", defaults=("center", False))


def fold(text):
    """Bỏ dấu + chữ thường để tìm kiếm 'lap trinh' khớp 'Lập trình'."""
    s = unicodedata.normalize("NFD", str(text).lower())
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").replace("đ", "d")


def initials(name):
    parts = str(name).split()
    if not parts:
        return "?"
    return (parts[0][:2] if len(parts) == 1 else parts[0][0] + parts[-1][0]).upper()


def fit_text(font, text, max_px):
    """Cắt chuỗi một dòng cho vừa chiều rộng (thêm …)."""
    text = str(text)
    if font.measure(text) <= max_px:
        return text
    while text and font.measure(text + "…") > max_px:
        text = text[:-1]
    return text + "…" if text else ""


def round_rect(canvas, x1, y1, x2, y2, r=8, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2,
           x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def combo_filter(combo, lay_tat_ca):
    """Gõ vào combobox để lọc danh sách giá trị (không dấu cũng được); bấm mũi tên để xem kết quả."""
    def khi_go(e):
        if e.keysym in ("Up", "Down", "Left", "Right", "Return", "Tab", "Escape",
                        "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"):
            return
        q, tat_ca = fold(combo.get().strip()), lay_tat_ca()
        combo.configure(values=[v for v in tat_ca if q in fold(v)] if q else tat_ca)
    combo.bind("<KeyRelease>", khi_go, add="+")


def autowrap(label, pad=24):
    """Tự xuống dòng nhãn theo chiều rộng hiện tại của nó."""
    label.bind("<Configure>", lambda e: label.config(wraplength=max(120, e.width - pad)), add="+")


def open_folder(path):
    """Mở thư mục trong trình quản lý tệp của hệ điều hành."""
    import subprocess
    import sys
    try:
        if sys.platform == "win32":
            os.startfile(path)  # noqa: S606
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])
        return True
    except OSError:
        return False


# ----------------------------------------------------------------------------
# Theme
# ----------------------------------------------------------------------------
class Theme:
    def __init__(self, root):
        self.root = root
        try:
            dpi = root.winfo_fpixels("1i")
        except tk.TclError:
            dpi = 96
        self.scale = min(2.5, max(1.0, dpi / 96.0))
        co = set(tkfont.families(root))
        mac_dinh = tkfont.nametofont("TkDefaultFont").actual("family")
        self.family = next((f for f in FONT_UU_TIEN if f in co), mac_dinh)
        self._fonts = {}
        self._ap_dung_kieu()

    # --- kích thước / phông
    def px(self, n):
        return int(round(n * self.scale))

    def f(self, size=10, bold=False):
        return (self.family, size, "bold") if bold else (self.family, size)

    def font_obj(self, size=10, bold=False):
        k = (size, bold)
        if k not in self._fonts:
            self._fonts[k] = tkfont.Font(root=self.root, family=self.family, size=size,
                                         weight="bold" if bold else "normal")
        return self._fonts[k]

    # --- widget dựng sẵn
    def label(self, parent, text="", size=10, bold=False, fg=None, bg=None, **kw):
        kw.setdefault("anchor", "w")
        kw.setdefault("justify", "left")
        return tk.Label(parent, text=text, font=self.f(size, bold), fg=fg or P["text"],
                        bg=bg or P["card"], **kw)

    def button(self, parent, text, command=None, kind="secondary", **kw):
        return ttk.Button(parent, text=text, command=command, style=f"{kind.capitalize()}.TButton",
                          cursor="hand2", **kw)

    CHIP = {"ok": (P["success"], P["success_soft"]), "warn": (P["warning"], P["warning_soft"]),
            "bad": (P["danger"], P["danger_soft"]), "info": (P["primary"], P["primary_soft"]),
            "muted": (P["muted"], P["head"])}

    def chip(self, parent, text, kind="info"):
        fg, nen = self.CHIP[kind]
        return tk.Label(parent, text=text, font=self.f(9, True), fg=fg, bg=nen, padx=10, pady=3)

    def set_chip(self, chip, text, kind):
        fg, nen = self.CHIP[kind]
        chip.config(text=text, fg=fg, bg=nen)

    def avatar(self, parent, name, size=38, bg=None, nen=None):
        s = self.px(size)
        c = tk.Canvas(parent, width=s, height=s, bg=bg or P["card"], highlightthickness=0)
        c.create_oval(1, 1, s - 1, s - 1, fill=nen or P["primary"], outline="")
        c.create_text(s / 2, s / 2, text=initials(name), fill="white", font=self.f(11, True))
        return c

    # --- kiểu ttk
    def _nut(self, st, ten, nen, chu, hover, tat="#B8C4D8", vien=None):
        vien = vien or nen
        st.configure(f"{ten}.TButton", background=nen, foreground=chu, bordercolor=vien, lightcolor=nen,
                     darkcolor=nen, borderwidth=1, focusthickness=0, focuscolor=nen, relief="flat",
                     padding=(self.px(16), self.px(8)), font=self.f(10, True))
        mau = [("disabled", tat), ("pressed", hover), ("active", hover)]
        st.map(f"{ten}.TButton", background=mau, lightcolor=mau, darkcolor=mau,
               bordercolor=[("disabled", tat), ("pressed", hover), ("active", hover)],
               foreground=[("disabled", "#FFFFFF" if chu == "white" else P["muted"])])

    def _ap_dung_kieu(self):
        r, st = self.root, ttk.Style(self.root)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        r.configure(bg=P["bg"])
        st.configure(".", font=self.f(10), background=P["bg"], foreground=P["text"])
        self._nut(st, "Primary", P["primary"], "white", P["primary_hover"])
        self._nut(st, "Success", P["success"], "white", "#166534")
        self._nut(st, "Danger", P["danger"], "white", P["danger_hover"])
        self._nut(st, "Secondary", "#EEF2F9", P["navy"], "#DFE7F4", vien="#D5DEEC")
        self._nut(st, "Ghost", P["card"], P["primary"], P["primary_soft"], vien=P["border"])
        self._nut(st, "Icon", "#EEF2F9", P["navy"], "#DFE7F4", vien="#D5DEEC")
        st.configure("Icon.TButton", padding=(self.px(8), self.px(6)))

        for ten in ("TEntry", "TSpinbox", "TCombobox"):
            st.configure(ten, fieldbackground="white", background="white", foreground=P["text"],
                         bordercolor=P["border"], lightcolor=P["border"], darkcolor=P["border"],
                         padding=(self.px(8), self.px(7)), arrowcolor=P["muted"], insertcolor=P["text"])
            st.map(ten, bordercolor=[("focus", P["primary"])], lightcolor=[("focus", P["primary"])],
                   darkcolor=[("focus", P["primary"])])
        st.map("TCombobox", fieldbackground=[("readonly", "white")], foreground=[("readonly", P["text"])],
               selectbackground=[("readonly", "white")], selectforeground=[("readonly", P["text"])])
        st.configure("Card.TCheckbutton", background=P["card"], foreground=P["text"], font=self.f(10))
        st.map("Card.TCheckbutton", background=[("active", P["card"])])

        st.configure("Treeview", background="white", fieldbackground="white", foreground=P["text"],
                     rowheight=self.px(34), font=self.f(10), borderwidth=0, relief="flat")
        st.configure("Treeview.Heading", background=P["head"], foreground=P["navy"], relief="flat",
                     font=self.f(9, True), padding=(self.px(8), self.px(9)), borderwidth=0)
        st.map("Treeview.Heading", background=[("active", "#E2E9F5")])
        st.map("Treeview", background=[("selected", P["select"])], foreground=[("selected", P["navy"])])
        st.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        for h in ("Vertical", "Horizontal"):
            st.configure(f"{h}.TScrollbar", background="#C3CDDC", troughcolor=P["bg"], bordercolor=P["bg"],
                         lightcolor="#C3CDDC", darkcolor="#C3CDDC", arrowcolor=P["muted"], relief="flat")
            st.map(f"{h}.TScrollbar", background=[("active", "#9FB0C8")])

        r.option_add("*TCombobox*Listbox.font", self.f(10))
        r.option_add("*TCombobox*Listbox.background", "white")
        r.option_add("*TCombobox*Listbox.foreground", P["text"])
        r.option_add("*TCombobox*Listbox.selectBackground", P["select"])
        r.option_add("*TCombobox*Listbox.selectForeground", P["navy"])


# ----------------------------------------------------------------------------
# Thẻ
# ----------------------------------------------------------------------------
class Card(tk.Frame):
    def __init__(self, parent, T, title=None, subtitle=None, pad=16, with_body=True, **kw):
        super().__init__(parent, bg=P["card"], highlightbackground=P["border"],
                         highlightcolor=P["border"], highlightthickness=1, bd=0, **kw)
        self.T = T
        if title:
            head = tk.Frame(self, bg=P["card"])
            head.pack(fill="x", padx=pad, pady=(pad - 2, 0))
            T.label(head, title, 12, True, P["navy"]).pack(anchor="w")
            if subtitle:
                T.label(head, subtitle, 9, False, P["muted"]).pack(anchor="w", pady=(2, 0))
        self.body = None
        if with_body:
            self.body = tk.Frame(self, bg=P["card"])
            self.body.pack(fill="both", expand=True, padx=pad, pady=(10 if title else pad, pad))


class StatCard(Card):
    def __init__(self, parent, T, caption, color, icon="●"):
        super().__init__(parent, T, with_body=False)
        tk.Frame(self, bg=color, width=4).pack(side="left", fill="y")
        inner = tk.Frame(self, bg=P["card"])
        inner.pack(side="left", fill="both", expand=True, padx=16, pady=14)
        top = tk.Frame(inner, bg=P["card"])
        top.pack(fill="x")
        T.label(top, caption.upper(), 8, True, P["muted"]).pack(side="left")
        T.label(top, icon, 12, True, color).pack(side="right")
        self.value = T.label(inner, "0", 20, True, P["navy"])
        self.value.pack(anchor="w", pady=(4, 0))
        self.sub = T.label(inner, "", 9, False, P["muted"])
        self.sub.pack(anchor="w")

    def set(self, value, sub=""):
        self.value.config(text=value)
        self.sub.config(text=sub)


# ----------------------------------------------------------------------------
# Toast
# ----------------------------------------------------------------------------
class Toast:
    MAU = {"success": ("#166534", "white"), "error": ("#B91C1C", "white"),
           "info": (P["navy"], "white"), "warn": ("#B45309", "white")}

    def __init__(self, root, T):
        self.root, self._job = root, None
        self.lbl = tk.Label(root, font=T.f(10, True), padx=18, pady=11, bd=0)

    def show(self, msg, kind="info", ms=3500):
        nen, chu = self.MAU.get(kind, self.MAU["info"])
        self.lbl.configure(text=msg, bg=nen, fg=chu, wraplength=420, justify="left")
        self.lbl.place(relx=1.0, x=-24, y=22, anchor="ne")
        self.lbl.lift()
        if self._job:
            self.root.after_cancel(self._job)
        self._job = self.root.after(ms, self.hide)

    def hide(self):
        self._job = None
        self.lbl.place_forget()


# ----------------------------------------------------------------------------
# Bảng dữ liệu
# ----------------------------------------------------------------------------
class DataTable(tk.Frame):
    """Treeview có tìm kiếm không dấu, sắp xếp theo cột, zebra, nhãn màu và xuất CSV.

    Mỗi hàng là dict: {"iid": str, "values": tuple, "tags": tuple (tuỳ chọn), "raw": tuple (tuỳ chọn, để sắp xếp số)}.
    Thẻ bắt đầu bằng "bg_" đặt màu nền cả hàng; thẻ ok/warn/bad/muted đổi màu chữ.
    """

    def __init__(self, parent, T, columns, height=12, multi=False, search=True, export=True,
                 on_select=None, on_double=None, notify=None, empty_text="Không có dữ liệu"):
        super().__init__(parent, bg=P["card"])
        self.T, self.cols, self.notify = T, columns, notify
        self.on_select, self.on_double = on_select, on_double
        self._rows, self._view, self._by_iid = [], [], {}
        self._sort_col, self._sort_rev, self._export_name = None, False, "du_lieu"
        self.search_entry = None

        bar = tk.Frame(self, bg=P["card"])
        bar.pack(fill="x", pady=(0, 10))
        self.search_var = tk.StringVar()
        if search:
            box = tk.Frame(bar, bg=P["card"])
            box.pack(side="left")
            T.label(box, "Tìm kiếm:", 9, True, P["muted"]).pack(side="left", padx=(0, 8))
            self.search_entry = ttk.Entry(box, textvariable=self.search_var, width=32)
            self.search_entry.pack(side="left")
            self.search_var.trace_add("write", lambda *_: self._render())
        self.toolbar = tk.Frame(bar, bg=P["card"])
        self.toolbar.pack(side="right")
        self.count_lbl = T.label(bar, "", 9, False, P["muted"])
        self.count_lbl.pack(side="right", padx=12)
        if export:
            T.button(self.toolbar, "Xuất CSV", self.export_csv, "ghost").pack(side="right", padx=(6, 0))

        hsb = ttk.Scrollbar(self, orient="horizontal")
        hsb.pack(side="bottom", fill="x")
        body = tk.Frame(self, bg=P["card"])
        body.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(body, columns=[c.key for c in columns], show="headings", height=height,
                                 selectmode="extended" if multi else "browse")
        vsb = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        hsb.configure(command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)
        for c in columns:
            self.tree.heading(c.key, text=c.title, command=lambda k=c.key: self.sort_by(k))
            self.tree.column(c.key, width=T.px(c.width), minwidth=T.px(40), anchor=c.anchor, stretch=c.stretch)
        for ten, opt in {"odd": {"background": "white"}, "even": {"background": P["row_alt"]},
                         "bg_ok": {"background": P["success_soft"]}, "bg_warn": {"background": P["warning_soft"]},
                         "bg_bad": {"background": P["danger_soft"]}, "bg_info": {"background": P["primary_soft"]},
                         "ok": {"foreground": P["success"]}, "warn": {"foreground": P["warning"]},
                         "bad": {"foreground": P["danger"]}, "muted": {"foreground": P["muted"]}}.items():
            self.tree.tag_configure(ten, **opt)
        self.empty = T.label(body, empty_text, 10, False, P["muted"])
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select and self.on_select())
        self.tree.bind("<Double-1>", self._double)

    # --- dữ liệu
    def set_rows(self, rows, export_name=None):
        self._rows = rows
        self._by_iid = {r["iid"]: r for r in rows}
        if export_name:
            self._export_name = export_name
        self._render()

    @staticmethod
    def _hay(r):
        if "_hay" not in r:
            r["_hay"] = fold(" ".join(str(v) for v in r["values"]))
        return r["_hay"]

    def _key(self, r, idx):
        raw = r.get("raw")
        v = raw[idx] if raw else r["values"][idx]
        return (0, v) if isinstance(v, (int, float)) else (1, fold(v))

    def _render(self):
        giu = set(self.tree.selection())
        q = fold(self.search_var.get().strip())
        view = [r for r in self._rows if not q or q in self._hay(r)]
        if self._sort_col is not None:
            idx = [c.key for c in self.cols].index(self._sort_col)
            view.sort(key=lambda r: self._key(r, idx), reverse=self._sort_rev)
        self._view = view
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(view):
            tags = tuple(r.get("tags", ()))
            if not any(t.startswith("bg_") for t in tags):
                tags += (("odd", "even")[i % 2],)
            self.tree.insert("", "end", iid=r["iid"], values=r["values"], tags=tags)
        con = [i for i in giu if self.tree.exists(i)]
        if con:
            self.tree.selection_set(con)
            self.tree.see(con[0])
        self.count_lbl.config(text=f"{len(view)}/{len(self._rows)} dòng" if q else f"{len(view)} dòng")
        if view:
            self.empty.place_forget()
        else:
            self.empty.place(relx=0.5, rely=0.5, anchor="center")
        for c in self.cols:
            mui = (" ▲" if not self._sort_rev else " ▼") if c.key == self._sort_col else ""
            self.tree.heading(c.key, text=c.title + mui)

    def sort_by(self, key):
        self._sort_rev = (not self._sort_rev) if self._sort_col == key else False
        self._sort_col = key
        self._render()

    def _double(self, e):
        iid = self.tree.identify_row(e.y)
        if iid and self.on_double:
            self.on_double(iid)

    # --- chọn dòng
    def selected(self):
        return list(self.tree.selection())

    def selected_row(self):
        s = self.tree.selection()
        return self._by_iid.get(s[0]) if s else None

    def select(self, iid):
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.see(iid)

    def clear_selection(self):
        self.tree.selection_remove(self.tree.selection())

    # --- xuất CSV
    def export_csv(self):
        path = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(), defaultextension=".csv", filetypes=[("CSV (mở bằng Excel)", "*.csv")],
            initialfile=f"{self._export_name}_{date.today():%Y%m%d}.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow([c.title for c in self.cols])
                for r in self._view:
                    w.writerow(r["values"])
        except OSError as loi:
            messagebox.showerror("Không xuất được", f"Không thể ghi tệp:\n{loi}", parent=self.winfo_toplevel())
            return
        if self.notify:
            self.notify(f"Đã xuất {len(self._view)} dòng ra {os.path.basename(path)}", "success")


# ----------------------------------------------------------------------------
# Chọn ngày
# ----------------------------------------------------------------------------
class DatePicker(tk.Frame):
    """Ô nhập ngày dd/mm/yyyy kèm lịch chọn nhanh."""

    def __init__(self, parent, T, var, bg=None):
        super().__init__(parent, bg=bg or P["card"])
        self.T, self.var, self._win = T, var, None
        self.entry = ttk.Entry(self, textvariable=var)
        self.entry.pack(side="left", fill="x", expand=True)
        T.button(self, "▦", self.open, "icon").pack(side="left", padx=(6, 0))

    def open(self):
        if self._win is not None and self._win.winfo_exists():
            self._win.lift()
            return
        hien_co = core.parse_date(self.var.get())
        d = hien_co or date.today()
        self._y, self._m, self._chon = d.year, d.month, hien_co
        win = self._win = tk.Toplevel(self)
        win.title("Chọn ngày")
        win.resizable(False, False)
        win.configure(bg=P["card"])
        win.transient(self.winfo_toplevel())
        self._khung = tk.Frame(win, bg=P["card"], padx=12, pady=10)
        self._khung.pack()
        self._ve()
        win.update_idletasks()
        win.geometry(f"+{self.winfo_rootx()}+{self.winfo_rooty() + self.winfo_height() + 4}")
        try:
            win.grab_set()
        except tk.TclError:
            pass
        win.bind("<Escape>", lambda e: win.destroy())

    def _doi_thang(self, delta):
        t = self._m - 1 + delta
        self._y, self._m = self._y + t // 12, t % 12 + 1
        self._ve()

    def _ve(self):
        T, k = self.T, self._khung
        for w in k.winfo_children():
            w.destroy()
        dau = tk.Frame(k, bg=P["card"])
        dau.grid(row=0, column=0, columnspan=7, sticky="ew", pady=(0, 6))
        T.button(dau, "◀", lambda: self._doi_thang(-1), "icon").pack(side="left")
        T.button(dau, "▶", lambda: self._doi_thang(1), "icon").pack(side="right")
        T.label(dau, f"Tháng {self._m}/{self._y}", 11, True, P["navy"], anchor="center").pack(fill="x", expand=True)
        for i, ten in enumerate(("T2", "T3", "T4", "T5", "T6", "T7", "CN")):
            T.label(k, ten, 9, True, P["muted"], anchor="center", width=4).grid(row=1, column=i, pady=(0, 2))
        hom_nay = date.today()
        for r, tuan in enumerate(calendar.Calendar(0).monthdayscalendar(self._y, self._m), start=2):
            for c, ngay in enumerate(tuan):
                if not ngay:
                    continue
                d = date(self._y, self._m, ngay)
                la_chon, la_nay = d == self._chon, d == hom_nay
                nen = P["primary"] if la_chon else (P["primary_soft"] if la_nay else P["card"])
                chu = "white" if la_chon else (P["primary"] if la_nay else P["text"])
                lb = tk.Label(k, text=str(ngay), width=4, bg=nen, fg=chu, font=T.f(9, la_chon or la_nay),
                              cursor="hand2", pady=3)
                lb.grid(row=r, column=c, padx=1, pady=1)
                lb.bind("<Button-1>", lambda e, dd=d: self._pick(dd))
                lb.bind("<Enter>", lambda e, w=lb: w.config(bg=P["select"]))
                lb.bind("<Leave>", lambda e, w=lb, n=nen: w.config(bg=n))
        T.button(k, "Hôm nay", lambda: self._pick(hom_nay), "ghost").grid(row=9, column=0, columnspan=7,
                                                                        sticky="ew", pady=(8, 0))

    def _pick(self, d):
        self.var.set(d.strftime(core.FMT_DATE_VN))
        self._win.destroy()


# ----------------------------------------------------------------------------
# Biểu mẫu khai báo
# ----------------------------------------------------------------------------
class FormGrid(tk.Frame):
    """Tạo biểu mẫu từ danh sách khai báo.

    field = {"key", "label", "kind": entry|combo|combo_edit|spin|date|check, "values", "default" (giá trị hoặc hàm),
             "span": số cột chiếm, "filter": True (combo_edit gõ để lọc), "show", "from"/"to"/"step", "text"}
    """

    def __init__(self, parent, T, fields, columns=1, bg=None):
        super().__init__(parent, bg=bg or P["card"])
        self.T, self.bg, self.fields = T, bg or P["card"], {f["key"]: f for f in fields}
        self.vars, self.widgets, self.choices = {}, {}, {}
        for c in range(columns):
            self.columnconfigure(c, weight=1, uniform="fg")
        row = col = 0
        for f in fields:
            span = min(f.get("span", 1), columns)
            if col + span > columns:
                row, col = row + 1, 0
            cell = tk.Frame(self, bg=self.bg)
            cell.grid(row=row, column=col, columnspan=span, sticky="ew", pady=(0, 10),
                      padx=(0 if col == 0 else 6, 6 if col + span < columns else 0))
            if f.get("kind") != "check":
                T.label(cell, f["label"], 9, True, P["muted"], self.bg).pack(anchor="w", pady=(0, 3))
            self.widgets[f["key"]] = self._tao(cell, f)
            self.widgets[f["key"]].pack(fill="x")
            col += span
            if col >= columns:
                row, col = row + 1, 0
        self.clear()

    def _tao(self, cell, f):
        kind, key = f.get("kind", "entry"), f["key"]
        if kind == "check":
            var = tk.BooleanVar()
            w = ttk.Checkbutton(cell, text=f.get("text", f["label"]), variable=var, style="Card.TCheckbutton")
        elif kind in ("combo", "combo_edit"):
            var = tk.StringVar()
            self.choices[key] = list(f.get("values", []))
            w = ttk.Combobox(cell, textvariable=var, values=self.choices[key],
                             state="readonly" if kind == "combo" else "normal")
            if f.get("filter"):
                combo_filter(w, lambda k=key: self.choices[k])
        elif kind == "spin":
            var = tk.StringVar()
            w = ttk.Spinbox(cell, textvariable=var, from_=f.get("from", 0), to=f.get("to", 100),
                            increment=f.get("step", 1), wrap=False)
        elif kind == "date":
            var = tk.StringVar()
            w = DatePicker(cell, self.T, var, self.bg)
        else:
            var = tk.StringVar()
            w = ttk.Entry(cell, textvariable=var, show=f.get("show", ""))
        self.vars[key] = var
        return w

    # --- đọc/ghi
    def get(self, key):
        v = self.vars[key].get()
        return v if isinstance(v, bool) else str(v).strip()

    def values(self):
        return {k: self.get(k) for k in self.vars}

    def set(self, key, value):
        if isinstance(self.vars[key], tk.BooleanVar):
            self.vars[key].set(bool(value))
        else:
            self.vars[key].set("" if value is None else str(value))

    def set_values(self, d):
        for k, v in d.items():
            if k in self.vars:
                self.set(k, v)

    def clear(self):
        for k, f in self.fields.items():
            d = f.get("default", False if f.get("kind") == "check" else "")
            self.set(k, d() if callable(d) else d)

    def set_choices(self, key, values):
        self.choices[key] = list(values)
        self.widgets[key].configure(values=self.choices[key])

    def lock(self, key, khoa=True):
        w, kind = self.widgets[key], self.fields[key].get("kind", "entry")
        mo = "readonly" if kind == "combo" else "normal"
        w.configure(state="readonly" if khoa else mo)

    def focus_first(self):
        for w in self.widgets.values():
            try:
                w.focus_set()
                return
            except tk.TclError:
                continue


# ----------------------------------------------------------------------------
# Khung cuộn + bố cục danh sách/biểu mẫu
# ----------------------------------------------------------------------------
class ScrollFrame(tk.Frame):
    """Khung có thanh cuộn dọc (tự ẩn khi nội dung vừa) và cuộn bằng chuột khi con trỏ nằm trong khung."""

    def __init__(self, parent, bg=None):
        nen = bg or P["card"]
        super().__init__(parent, bg=nen)
        self.canvas = tk.Canvas(self, bg=nen, highlightthickness=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.inner = tk.Frame(self.canvas, bg=nen)
        self._cua_so = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner.bind("<Configure>", self._cap_nhat)
        self.canvas.bind("<Configure>", self._cap_nhat)
        self.bind("<Enter>", lambda e: self._wheel(True))
        self.bind("<Leave>", self._roi)

    def _cap_nhat(self, e=None):
        self.canvas.itemconfigure(self._cua_so, width=self.canvas.winfo_width())
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        can_cuon = self.inner.winfo_reqheight() > self.canvas.winfo_height() > 1
        if can_cuon and not self.vsb.winfo_ismapped():
            self.vsb.pack(side="right", fill="y")
        elif not can_cuon and self.vsb.winfo_ismapped():
            self.vsb.pack_forget()
            self.canvas.yview_moveto(0)

    def _roi(self, e):
        try:
            w = self.winfo_containing(e.x_root, e.y_root)
        except (KeyError, tk.TclError):
            return
        if w is None or not str(w).startswith(str(self)):
            self._wheel(False)

    def _wheel(self, bat):
        for s in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            if bat:
                self.bind_all(s, self._cuon)
            else:
                self.unbind_all(s)

    def _cuon(self, e):
        if self.inner.winfo_reqheight() > self.canvas.winfo_height():
            self.canvas.yview_scroll(-2 if (getattr(e, "num", 0) == 4 or getattr(e, "delta", 0) > 0) else 2, "units")


def master_detail(parent, T, title, subtitle=None, form_width=380):
    """Trả về (thẻ bên trái để đặt bảng, khung bên phải để đặt biểu mẫu)."""
    wrap = tk.Frame(parent, bg=P["bg"])
    wrap.pack(fill="both", expand=True)
    wrap.rowconfigure(0, weight=1)
    wrap.columnconfigure(0, weight=1)
    wrap.columnconfigure(1, minsize=T.px(form_width))
    left = Card(wrap, T, pad=14)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
    right = Card(wrap, T, title, subtitle, pad=16)
    right.grid(row=0, column=1, sticky="nsew")
    sf = ScrollFrame(right.body)
    sf.pack(fill="both", expand=True)
    return left, sf.inner


# ----------------------------------------------------------------------------
# Lớp nền cho trang
# ----------------------------------------------------------------------------
class Page(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=P["bg"])
        self.app, self.T, self.svc = app, app.theme, app.svc
        self.build()

    def build(self):
        pass

    def refresh(self):
        pass

    def on_show(self):
        self.refresh()

    def on_hide(self):
        pass

    def focus_search(self):
        t = getattr(self, "table", None)
        if t is not None and t.search_entry is not None:
            t.search_entry.focus_set()

    @staticmethod
    def clear(frame):
        for w in frame.winfo_children():
            w.destroy()
