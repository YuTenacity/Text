import tkinter as tk
import random


# ── 人物表情绘制 ──
def draw_character(canvas, expression="normal"):
    """在 canvas 上画一个可爱人物，支持 normal / angry / happy 三种表情"""
    canvas.delete("char")

    w, h = 400, 260
    cx, cy = w // 2, 80

    # ── 头发 ──
    canvas.create_oval(cx - 55, cy - 80, cx + 55, cy + 30, fill="#3e2723", outline="", tags="char")
    # 刘海
    canvas.create_arc(cx - 58, cy - 82, cx + 58, cy - 10, start=180, extent=180,
                       fill="#4e342e", outline="", tags="char")

    # ── 脸 ──
    canvas.create_oval(cx - 50, cy - 45, cx + 50, cy + 50, fill="#ffccbc", outline="#e0a080", width=2, tags="char")

    # ── 腮红 ──
    canvas.create_oval(cx - 48, cy + 8, cx - 30, cy + 22, fill="#ffab91", outline="", tags="char")
    canvas.create_oval(cx + 30, cy + 8, cx + 48, cy + 22, fill="#ffab91", outline="", tags="char")

    # ── 眼睛 ──
    if expression == "angry":
        # 生气：倒八字眉 + 瞪眼
        # 左眉
        canvas.create_line(cx - 28, cy - 16, cx - 12, cy - 26, fill="#3e2723", width=4, tags="char")
        # 右眉
        canvas.create_line(cx + 28, cy - 16, cx + 12, cy - 26, fill="#3e2723", width=4, tags="char")
        # 左眼
        canvas.create_oval(cx - 24, cy - 14, cx - 10, cy, fill="white", outline="#3e2723", width=2, tags="char")
        canvas.create_oval(cx - 19, cy - 11, cx - 15, cy - 5, fill="#3e2723", outline="", tags="char")
        # 右眼
        canvas.create_oval(cx + 10, cy - 14, cx + 24, cy, fill="white", outline="#3e2723", width=2, tags="char")
        canvas.create_oval(cx + 15, cy - 11, cx + 19, cy - 5, fill="#3e2723", outline="", tags="char")
    elif expression == "happy":
        # 开心：弯弯笑眼
        canvas.create_arc(cx - 26, cy - 16, cx - 8, cy + 2, start=180, extent=180,
                           fill="#3e2723", outline="", style="chord", tags="char")
        canvas.create_arc(cx + 8, cy - 16, cx + 26, cy + 2, start=180, extent=180,
                           fill="#3e2723", outline="", style="chord", tags="char")
    else:
        # normal：圆圆大眼
        canvas.create_oval(cx - 24, cy - 14, cx - 10, cy + 2, fill="white", outline="#3e2723", width=2, tags="char")
        canvas.create_oval(cx - 20, cy - 11, cx - 14, cy - 1, fill="#3e2723", outline="", tags="char")
        # 高光
        canvas.create_oval(cx - 19, cy - 10, cx - 16, cy - 7, fill="white", outline="", tags="char")

        canvas.create_oval(cx + 10, cy - 14, cx + 24, cy + 2, fill="white", outline="#3e2723", width=2, tags="char")
        canvas.create_oval(cx + 14, cy - 11, cx + 20, cy - 1, fill="#3e2723", outline="", tags="char")
        canvas.create_oval(cx + 16, cy - 10, cx + 19, cy - 7, fill="white", outline="", tags="char")

    # ── 嘴 ──
    if expression == "angry":
        # 生气嘟嘴
        canvas.create_arc(cx - 10, cy + 12, cx + 10, cy + 32, start=0, extent=-180,
                           fill="#e57373", outline="#c62828", width=2, style="chord", tags="char")
    elif expression == "happy":
        # 开心咧嘴
        canvas.create_arc(cx - 12, cy + 6, cx + 12, cy + 28, start=0, extent=-180,
                           fill="#f06292", outline="#c62828", width=2, style="chord", tags="char")
        # 牙齿
        canvas.create_arc(cx - 7, cy + 4, cx + 7, cy + 18, start=0, extent=-180,
                           fill="white", outline="", style="chord", tags="char")
    else:
        # normal：微笑
        canvas.create_arc(cx - 8, cy + 8, cx + 8, cy + 24, start=0, extent=-180,
                           fill="#f48fb1", outline="#d81b60", width=2, style="chord", tags="char")

    # ── 身体 ──
    canvas.create_oval(cx - 35, cy + 52, cx + 35, cy + 120, fill="#e91e63", outline="#c2185b", width=2, tags="char")
    # 领口
    canvas.create_polygon(cx - 12, cy + 50, cx, cy + 70, cx + 12, cy + 50,
                           fill="#ffccbc", outline="#e0a080", width=1, tags="char")

    # ── 手臂 ──
    canvas.create_oval(cx - 50, cy + 60, cx - 30, cy + 95, fill="#ffccbc", outline="#e0a080", width=1, tags="char")
    canvas.create_oval(cx + 30, cy + 60, cx + 50, cy + 95, fill="#ffccbc", outline="#e0a080", width=1, tags="char")


# ── 弹出表白弹框 ──
class ConfessionPopup:
    def __init__(self, parent):
        self.parent = parent
        self.angry_count = 0
        self.yes_font_size = 14
        self.no_font_size = 14

        self.popup = tk.Toplevel(parent)
        self.popup.title("💌")
        self.popup.geometry("420x520")
        self.popup.configure(bg="#fff0f5")
        self.popup.resizable(False, False)
        # 置顶
        self.popup.attributes("-topmost", True)
        self.popup.protocol("WM_DELETE_WINDOW", self.on_close)

        self.build_ui()

    def build_ui(self):
        # ── 人物画布 ──
        self.char_canvas = tk.Canvas(
            self.popup, width=400, height=260, bg="#fff0f5", highlightthickness=0
        )
        self.char_canvas.pack(pady=(20, 0))
        draw_character(self.char_canvas, "normal")
        self.expression = "normal"

        # ── 问题文字 ──
        self.question = tk.Label(
            self.popup,
            text="你 愿 意 做 我 女 朋 友 吗 ？",
            font=("微软雅黑", 16, "bold"),
            fg="#d81b60",
            bg="#fff0f5",
        )
        self.question.pack(pady=15)

        # ── 生气文字（隐藏） ──
        self.angry_label = tk.Label(
            self.popup,
            text="",
            font=("微软雅黑", 11, "bold"),
            fg="#ff1744",
            bg="#fff0f5",
        )
        self.angry_label.pack()

        # ── 按钮区 ──
        self.btn_frame = tk.Frame(self.popup, bg="#fff0f5")
        self.btn_frame.pack(pady=20)

        self.yes_btn = tk.Button(
            self.btn_frame,
            text="我愿意 💖",
            font=("微软雅黑", self.yes_font_size, "bold"),
            fg="white",
            bg="#e91e63",
            activebackground="#c2185b",
            activeforeground="white",
            relief="flat",
            padx=25,
            pady=10,
            command=self.on_yes,
        )
        self.yes_btn.pack(side=tk.LEFT, padx=15)

        self.no_btn = tk.Button(
            self.btn_frame,
            text="我才不要 😤",
            font=("微软雅黑", self.no_font_size),
            fg="#999",
            bg="#fce4ec",
            activebackground="#f8bbd0",
            activeforeground="#999",
            relief="flat",
            padx=20,
            pady=10,
            command=self.on_no,
        )
        self.no_btn.pack(side=tk.LEFT, padx=15)

    # ── 点"我才不要" ──
    def on_no(self):
        self.angry_count += 1

        # 1. "我才不要" 字体变小
        self.no_font_size = max(6, self.no_font_size - 2)
        # 2. "我愿意" 字体变大
        self.yes_font_size = min(36, self.yes_font_size + 3)

        self.no_btn.config(font=("微软雅黑", self.no_font_size))
        self.yes_btn.config(font=("微软雅黑", self.yes_font_size, "bold"))

        # 3. 人物变生气
        self.expression = "angry"
        draw_character(self.char_canvas, "angry")

        # 4. 显示生气文字
        angry_msgs = [
            "哼！😠",
            "你再想想！😡",
            "快点按我愿意！！🤬",
            "我真的生气了！！👿",
            "不要挑战我的耐心！💢",
            "呜呜呜...你欺负我 😭",
            "求求你按我愿意吧 🥺",
        ]
        msg = angry_msgs[min(self.angry_count - 1, len(angry_msgs) - 1)]
        self.angry_label.config(text=msg)

        # 5. 按钮随机微移（防止机械连点）
        if self.angry_count >= 3:
            x_shift = random.randint(-30, 30)
            y_shift = random.randint(-5, 5)
            self.no_btn.place(x=130 + x_shift, y=310 + y_shift)

    # ── 点"我愿意" ──
    def on_yes(self):
        # 清空弹框 → 显示结局
        for w in self.popup.winfo_children():
            w.destroy()
        self.popup.configure(bg="#ffe0ec")

        # 最终人物：开心
        final_char = tk.Canvas(
            self.popup, width=400, height=260, bg="#ffe0ec", highlightthickness=0
        )
        final_char.pack(pady=20)
        draw_character(final_char, "happy")

        self._spawn_final_hearts(final_char)
        self._animate_final_hearts(final_char)

        tk.Label(
            self.popup,
            text="💖 爱 你 哟 💖",
            font=("微软雅黑", 24, "bold"),
            fg="#d81b60",
            bg="#ffe0ec",
        ).pack(pady=10)

        tk.Label(
            self.popup,
            text="从今天起，你是我的全世界 🌍\n我会一直一直陪着你 ✨",
            font=("微软雅黑", 13),
            fg="#ad1457",
            bg="#ffe0ec",
        ).pack(pady=5)

        # 关闭按钮
        tk.Button(
            self.popup,
            text="💕 好哒！💕",
            font=("微软雅黑", 14, "bold"),
            fg="white",
            bg="#e91e63",
            activebackground="#c2185b",
            relief="flat",
            padx=40,
            pady=8,
            command=self.popup.destroy,
        ).pack(pady=20)

    # ── 结局爱心特效 ──
    def _spawn_final_hearts(self, canvas):
        import math as _math

        def _animate():
            try:
                canvas.delete("fheart")
                t = _animate.frame
                _animate.frame += 0.08
                for i in range(12):
                    angle = (i / 12) * 2 * _math.pi + t * 0.3
                    x = 200 + _math.cos(angle * 2.3) * 60
                    y = 130 + _math.sin(angle * 1.7) * 40 - 30
                    size = int(14 + _math.sin(t + i) * 6)
                    canvas.create_text(x, y, text="♥",
                                        font=("Arial", size), fill="#ff4081", tags="fheart")
                canvas.after(40, _animate)
            except Exception:
                pass

        _animate.frame = 0.0
        _animate()

    def on_close(self):
        self.popup.destroy()


# ── 主窗口（隐藏） ──
def main():
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    ConfessionPopup(root)
    root.mainloop()


if __name__ == "__main__":
    main()
