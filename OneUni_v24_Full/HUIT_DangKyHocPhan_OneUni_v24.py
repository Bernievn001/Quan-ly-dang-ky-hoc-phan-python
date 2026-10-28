# -*- coding: utf-8 -*-
"""
OneUni v24 - Hệ thống mô phỏng đăng ký học phần HUIT (Python + Tkinter, không cần cài thêm thư viện).

Chạy:   python HUIT_DangKyHocPhan_OneUni_v24.py      (hoặc:  py HUIT_DangKyHocPhan_OneUni_v24.py)
Cấu trúc: oneuni_core.py (nghiệp vụ + dữ liệu) · oneuni_ui.py (thành phần giao diện)
          oneuni_screens.py (đăng nhập, khung, trang sinh viên) · oneuni_admin.py (trang quản trị)
Xem README.md để biết chi tiết.
"""
import sys


def main():
    if sys.platform == "win32":                   # chữ nét hơn trên màn hình độ phân giải cao
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    try:
        import oneuni_core as core
        svc = core.Service()
        svc.khoi_tao()
        from oneuni_screens import OneUniApp
        OneUniApp(root, svc)
    except Exception as loi:                      # lỗi khởi động: báo rõ thay vì đóng im lặng
        root.withdraw()
        goi_y = ("Hãy sửa hoặc khôi phục tệp từ thư mục backup rồi mở lại."
                 if loi.__class__.__name__ == "DuLieuError" else
                 "Hãy chắc chắn các tệp oneuni_*.py nằm cùng thư mục với tệp này.")
        messagebox.showerror("Không khởi động được OneUni", f"{loi}\n\n{goi_y}")
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
