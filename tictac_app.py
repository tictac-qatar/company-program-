import sqlite3
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox

# --- إعداد قاعدة البيانات المحلية ---
def init_db():
    conn = sqlite3.connect('tictac_maintenance.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,          -- 'revenue' (إيراد / عقد) أو 'expense' (مصروف / مشتريات)
            category TEXT,      -- التصنيف
            description TEXT,   -- التفاصيل
            amount REAL,        -- المبلغ
            date TEXT           -- التاريخ بصيغة YYYY-MM-DD
        )
    ''')
    conn.commit()
    conn.close()

# --- نافذة تطبيق Tic Tac ---
class TicTacApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic Tac for Building Maintenance - نظام الحسابات والمشتريات")
        self.root.geometry("1050x700")
        self.root.configure(bg="#F4F6F9")
        
        # ألوان الهوية المستوحاة من الشعار (كحلي وبرونزي)
        self.navy = "#14213d"      # اللون الكحلي الداكن للشعار
        self.gold = "#c59b27"      # اللون البرونزي النحاسي المميز
        self.light_bg = "#ffffff"
        self.text_dark = "#111111"
        
        init_db()
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # الشريط العلوي للشعار والاسم
        header_frame = tk.Frame(self.root, bg=self.navy, height=90)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="TIC TAC لصيانة المباني", font=("Arial", 20, "bold"), fg=self.gold, bg=self.navy)
        title_label.pack(side=tk.LEFT, padx=25, pady=10)
        
        sub_label = tk.Label(header_frame, text="Building Maintenance - نظام الإدارة، الحسابات، والمشتريات", font=("Arial", 11), fg="#ffffff", bg=self.navy)
        sub_label.pack(side=tk.LEFT, pady=25)

        # الحاوية الرئيسية
        main_container = tk.Frame(self.root, bg="#F4F6F9")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # الإطار الأيسر: نموذج الإدخال (Data Entry Form)
        form_frame = tk.LabelFrame(main_container, text=" تسجيل معاملة جديدة (إيراد / مشتريات) ", font=("Arial", 11, "bold"), fg=self.navy, bg=self.light_bg, bd=2, relief=tk.GROOVE)
        form_frame.place(relx=0, rely=0, relwidth=0.38, relheight=1.0)

        # نوع المعاملة
        tk.Label(form_frame, text="نوع المعاملة:", font=("Arial", 10, "bold"), bg=self.light_bg, fg=self.text_dark).pack(anchor="w", padx=15, pady=(15, 5))
        self.type_var = tk.StringVar(value="revenue")
        type_frame = tk.Frame(form_frame, bg=self.light_bg)
        type_frame.pack(anchor="w", padx=15)
        tk.Radiobutton(type_frame, text="إيراد (عقد صيانة / خدمة)", variable=self.type_var, value="revenue", font=("Arial", 10), bg=self.light_bg).pack(side=tk.LEFT, padx=(0, 15))
        tk.Radiobutton(type_frame, text="مصروف / مشتريات قطع", variable=self.type_var, value="expense", font=("Arial", 10), bg=self.light_bg).pack(side=tk.LEFT)

        # التصنيف
        tk.Label(form_frame, text="التصنيف:", font=("Arial", 10, "bold"), bg=self.light_bg, fg=self.text_dark).pack(anchor="w", padx=15, pady=(15, 5))
        self.category_combo = ttk.Combobox(form_frame, values=["عقد صيانة دورية", "إصلاح طارئ", "شراء قطع غيار ومواد", "أجور عمالة وفنيين", "مصروفات تشغيلية"], font=("Arial", 10), state="readonly")
        self.category_combo.pack(fill=tk.X, padx=15)
        self.category_combo.current(0)

        # الوصف
        tk.Label(form_frame, text="وصف المعاملة / اسم العميل أو المورد:", font=("Arial", 10, "bold"), bg=self.light_bg, fg=self.text_dark).pack(anchor="w", padx=15, pady=(15, 5))
        self.desc_entry = tk.Entry(form_frame, font=("Arial", 11), bd=1, relief=tk.SOLID)
        self.desc_entry.pack(fill=tk.X, padx=15, ipady=4)

        # المبلغ
        tk.Label(form_frame, text="المبلغ:", font=("Arial", 10, "bold"), bg=self.light_bg, fg=self.text_dark).pack(anchor="w", padx=15, pady=(15, 5))
        self.amount_entry = tk.Entry(form_frame, font=("Arial", 11), bd=1, relief=tk.SOLID)
        self.amount_entry.pack(fill=tk.X, padx=15, ipady=4)

        # التاريخ
        tk.Label(form_frame, text="التاريخ (YYYY-MM-DD):", font=("Arial", 10, "bold"), bg=self.light_bg, fg=self.text_dark).pack(anchor="w", padx=15, pady=(15, 5))
        self.date_entry = tk.Entry(form_frame, font=("Arial", 11), bd=1, relief=tk.SOLID)
        self.date_entry.pack(fill=tk.X, padx=15, ipady=4)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # زر الحفظ
        save_btn = tk.Button(form_frame, text="حفظ المعاملة في النظام", font=("Arial", 11, "bold"), bg=self.navy, fg="#ffffff", activebackground=self.gold, activeforeground=self.navy, relief=tk.FLAT, command=self.save_transaction)
        save_btn.pack(fill=tk.X, padx=15, pady=25, ipady=8)

        # الإطار الأيمن: التقارير وجدول البيانات
        right_frame = tk.Frame(main_container, bg="#F4F6F9")
        right_frame.place(relx=0.40, rely=0, relwidth=0.60, relheight=1.0)

        # شريط أزرار التقارير الفورية
        report_frame = tk.LabelFrame(right_frame, text=" تقارير الحسابات (يومي، أسبوعي، شهري، سنوي) ", font=("Arial", 11, "bold"), fg=self.navy, bg=self.light_bg, bd=2, relief=tk.GROOVE)
        report_frame.pack(fill=tk.X, pady=(0, 15))

        btn_style = {"font": ("Arial", 9, "bold"), "bg": self.gold, "fg": self.navy, "relief": tk.FLAT, "padx": 8, "pady": 6}
        
        tk.Button(report_frame, text="تقرير يومي", command=lambda: self.generate_report('daily'), **btn_style).pack(side=tk.LEFT, padx=8, pady=10)
        tk.Button(report_frame, text="تقرير أسبوعي", command=lambda: self.generate_report('weekly'), **btn_style).pack(side=tk.LEFT, padx=8, pady=10)
        tk.Button(report_frame, text="تقرير شهري", command=lambda: self.generate_report('monthly'), **btn_style).pack(side=tk.LEFT, padx=8, pady=10)
        tk.Button(report_frame, text="تقرير سنوي", command=lambda: self.generate_report('yearly'), **btn_style).pack(side=tk.LEFT, padx=8, pady=10)
        tk.Button(report_frame, text="عرض الكل", command=self.load_data, **btn_style).pack(side=tk.LEFT, padx=8, pady=10)

        # جدول عرض البيانات (Treeview)
        table_container = tk.Frame(right_frame, bg=self.light_bg)
        table_container.pack(fill=tk.BOTH, expand=True)

        columns = ("ID", "Type", "Category", "Description", "Amount", "Date")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("ID", text="م")
        self.tree.heading("Type", text="النوع")
        self.tree.heading("Category", text="التصنيف")
        self.tree.heading("Description", text="الوصف والجهة")
        self.tree.heading("Amount", text="المبلغ")
        self.tree.heading("Date", text="التاريخ")

        self.tree.column("ID", width=35, anchor="center")
        self.tree.column("Type", width=75, anchor="center")
        self.tree.column("Category", width=110, anchor="center")
        self.tree.column("Description", width=150, anchor="w")
        self.tree.column("Amount", width=85, anchor="center")
        self.tree.column("Date", width=85, anchor="center")

        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def save_transaction(self):
        t_type = self.type_var.get()
        category = self.category_combo.get()
        description = self.desc_entry.get().strip()
        amount_str = self.amount_entry.get().strip()
        date_str = self.date_entry.get().strip()

        if not description or not amount_str or not date_str:
            messagebox.showerror("خطأ", "الرجاء إدخال جميع الحقول المطلوبة!")
            return

        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showerror("خطأ", "المبلغ يجب أن يكون رقماً صحيحاً أو عشرياً!")
            return

        conn = sqlite3.connect('tictac_maintenance.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO transactions (type, category, description, amount, date) VALUES (?, ?, ?, ?, ?)",
                       (t_type, category, description, amount, date_str))
        conn.commit()
        conn.close()

        messagebox.showinfo("نجاح", "تم حفظ المعاملة بنجاح في قاعدة البيانات!")
        self.desc_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.load_data()

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = sqlite3.connect('tictac_maintenance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, category, description, amount, date FROM transactions ORDER BY date DESC, id DESC")
        rows = cursor.fetchall()
        conn.close()

        for r in rows:
            t_type_ar = "إيراد" if r[1] == 'revenue' else "مصروف/شراء"
            self.tree.insert("", tk.END, values=(r[0], t_type_ar, r[2], r[3], f"{r[4]:.2f}", r[5]))

    def generate_report(self, period):
        today = datetime.now().date()
        
        if period == 'daily':
            start_date = today.strftime("%Y-%m-%d")
            title = f"التقرير اليومي ({start_date})"
            query = "SELECT id, type, category, description, amount, date FROM transactions WHERE date = ?"
            params = (start_date,)
        elif period == 'weekly':
            start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            title = f"التقرير الأسبوعي (من {start_date} إلى {end_date})"
            query = "SELECT id, type, category, description, amount, date FROM transactions WHERE date BETWEEN ? AND ?"
            params = (start_date, end_date)
        elif period == 'monthly':
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            title = f"التقرير الشهري ({today.strftime('%B %Y')})"
            query = "SELECT id, type, category, description, amount, date FROM transactions WHERE date BETWEEN ? AND ?"
            params = (start_date, end_date)
        elif period == 'yearly':
            start_date = today.replace(month=1, day=1).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            title = f"التقرير السنوي ({today.strftime('%Y')})"
            query = "SELECT id, type, category, description, amount, date FROM transactions WHERE date BETWEEN ? AND ?"
            params = (start_date, end_date)

        conn = sqlite3.connect('tictac_maintenance.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        total_rev = sum([r[4] for r in rows if r[1] == 'revenue'])
        total_exp = sum([r[4] for r in rows if r[1] == 'expense'])
        net_profit = total_rev - total_exp
        conn.close()

        for row in self.tree.get_children():
            self.tree.delete(row)

        for r in rows:
            t_type_ar = "إيراد" if r[1] == 'revenue' else "مصروف/شراء"
            self.tree.insert("", tk.END, values=(r[0], t_type_ar, r[2], r[3], f"{r[4]:.2f}", r[5]))

        report_text = f"--- {title} ---\n\nإجمالي الإيرادات (عقود وخدمات): {total_rev:.2f}\nإجمالي المصروفات (مشتريات وتشغيل): {total_exp:.2f}\nصافي الربح: {net_profit:.2f}\nعدد المعاملات المسجلة: {len(rows)}"
        messagebox.showinfo(title, report_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = TicTacApp(root)
    root.mainloop()