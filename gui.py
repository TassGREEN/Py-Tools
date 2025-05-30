import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, simpledialog
import time
import keyboard
import threading
import os
import pyperclip
import win32gui
import win32process
import psutil
import winsound


# ================== 工具函数 ==================

def is_app_in_foreground():
    """检查当前焦点是否在本程序"""
    try:
        foreground_window = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(foreground_window)
        process = psutil.Process(pid)
        return process.pid == os.getpid()
    except Exception as e:
        print("⚠️ 焦点检测失败:", e)
        return True  # 出错时默认继续执行


# ================== 自定义圆角按钮类 ==================

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, radius=20, *args, **kwargs):
        super().__init__(parent, bg=parent.cget('bg'), bd=0, highlightthickness=0, *args, **kwargs)
        self.command = command
        self.radius = radius
        self.text = text

        # 固定使用米白色风格
        self.colors = {
            "bg": "#dddddd",
            "hover": "#cccccc",
            "text": "black"
        }

        width = kwargs.get("width", 100)
        height = kwargs.get("height", 40)

        self.rect = self.create_rounded_rectangle(0, 0, width, height, radius, fill=self.colors["bg"])
        self.text_id = self.create_text(width / 2, height / 2, text=text, fill=self.colors["text"], font=("Segoe UI", 10))

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

    def create_rounded_rectangle(self, x1, y1, x2, y2, r, **kwargs):
        return self.create_polygon(
            x1 + r, y1,
            x2 - r, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2 - r,
            x1, y1 + r,
            fill=kwargs.get("fill"),
            outline=""
        )

    def on_enter(self, event):
        self.itemconfig(self.rect, fill=self.colors["hover"])

    def on_leave(self, event):
        self.itemconfig(self.rect, fill=self.colors["bg"])

    def on_click(self, event):
        if self.command:
            self.command()


# ================== 主程序类 ==================

class SoftAutoTypingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoTypingTool")
        self.root.geometry("800x700")
        self.root.configure(bg="#f0f0f0")  # 米白色背景
        self.root.overrideredirect(True)  # 去掉默认边框

        # 控件变量
        self.switch_input = tk.BooleanVar(value=True)
        self.typing_speed = tk.DoubleVar(value=0.01)
        self.running = False
        self.last_interrupt_index = 0
        self.focus_lost = False  # 新增：标记焦点是否丢失

        # 字体颜色变量
        self.font_size = tk.IntVar(value=12)
        self.text_color = tk.StringVar(value="black")
        self.bg_color = tk.StringVar(value="white")

        self.create_title_bar()
        self.create_widgets()
        self.create_shortcuts()
        self.setup_draggable()

        # 初始化提示日志
        self.log("✨ 欢迎使用 AutoTypingTool")
        self.log("📌 请在下方文本框中输入内容，点击【开始自动输入】即可模拟键盘输入")
        self.log("📎 可通过【读取剪贴板】快速粘贴内容")
        self.log("🛑 若您切换到其他窗口，输入将自动暂停\n")

    def create_title_bar(self):
        self.title_bar = tk.Frame(self.root, bg="#dcdcdc", height=30)
        self.title_bar.pack(fill="x")

        self.title_label = tk.Label(self.title_bar, text="AutoTypingTool", bg="#dcdcdc", fg="black", font=("Segoe UI", 10))
        self.title_label.pack(side="left", padx=10)

        self.close_button = tk.Label(self.title_bar, text="✕", bg="#dcdcdc", fg="black", font=("Segoe UI", 10), width=2)
        self.close_button.pack(side="right", padx=5)
        self.close_button.bind("<Button-1>", lambda e: self.root.destroy())
        self.close_button.bind("<Enter>", lambda e: self.close_button.config(bg="#e74c3c", fg="white"))
        self.close_button.bind("<Leave>", lambda e: self.close_button.config(bg="#dcdcdc", fg="black"))

        self.minimize_button = tk.Label(self.title_bar, text="—", bg="#dcdcdc", fg="black", font=("Segoe UI", 10), width=2)
        self.minimize_button.pack(side="right", padx=5)
        self.minimize_button.bind("<Button-1>", lambda e: self.root.iconify())
        self.minimize_button.bind("<Enter>", lambda e: self.minimize_button.config(bg="#bbbbbb"))
        self.minimize_button.bind("<Leave>", lambda e: self.minimize_button.config(bg="#dcdcdc"))

    def create_widgets(self):
        # ===== 第五步：美化主窗口边缘（新增外层 Frame）=====
        main_frame = tk.Frame(self.root, bg="#f0f0f0", bd=0, relief="flat")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        content_frame = tk.Frame(main_frame, bg="#f0f0f0")  # 所有内容放在这里面
        content_frame.pack(fill="both", expand=True)
        # ==================================================

        # 主文本框（减小一半高度）
        self.text_area = tk.Text(content_frame, height=9, width=90, wrap="word", undo=True,
                               bg="white", fg="black",
                               insertbackground="black", font=("微软雅黑", self.font_size.get()))
        self.text_area.pack(pady=10)

        # 工具按钮区
        tool_frame = tk.Frame(content_frame, bg="#f0f0f0")
        tool_frame.pack(pady=5)

        RoundedButton(tool_frame, text="保存草稿", command=self.save_draft, width=80, height=30).pack(side="left", padx=5)
        RoundedButton(tool_frame, text="加载模板", command=self.load_template, width=80, height=30).pack(side="left", padx=5)
        RoundedButton(tool_frame, text="读取剪贴板", command=self.load_clipboard_content, width=90, height=30).pack(side="left", padx=5)
        RoundedButton(tool_frame, text="清空文本框", command=self.clear_text_area, width=90, height=30).pack(side="left", padx=5)
        RoundedButton(tool_frame, text="字体大小", command=self.change_font_size, width=80, height=30).pack(side="left", padx=5)
        RoundedButton(tool_frame, text="文字颜色", command=self.choose_text_color, width=90, height=30).pack(side="left", padx=5)
        RoundedButton(tool_frame, text="背景颜色", command=self.choose_bg_color, width=90, height=30).pack(side="left", padx=5)

        # 切换输入法
        tk.Checkbutton(content_frame, text="切换英文输入法 (Ctrl+Space)", variable=self.switch_input,
                       bg="#f0f0f0", fg="black", selectcolor="#dddddd").pack(anchor="w", padx=10)

        # 打字速度
        speed_frame = tk.Frame(content_frame, bg="#f0f0f0")
        speed_frame.pack(pady=10)
        tk.Label(speed_frame, text="打字速度（秒/字）:", bg="#f0f0f0", fg="black").pack(side="left", padx=10)
        self.speed_slider = tk.Scale(speed_frame, from_=0.001, to=0.2, resolution=0.005, orient="horizontal",
                                   variable=self.typing_speed, length=300, bg="#f0f0f0", fg="black",
                                   troughcolor="#aaaaaa")
        self.speed_slider.pack(side="left")

        # 操作按钮
        btn_frame = tk.Frame(content_frame, bg="#f0f0f0")
        btn_frame.pack(pady=10)
        RoundedButton(btn_frame, text="开始自动输入", command=self.start_typing, width=120, height=35).pack(side="left", padx=5)
        RoundedButton(btn_frame, text="继续输入", command=self.resume_typing, width=90, height=35).pack(side="left", padx=5)
        RoundedButton(btn_frame, text="取消", command=self.stop_typing, width=80, height=35).pack(side="left", padx=5)

        # 日志输出（增大高度）
        log_label = tk.Label(content_frame, text="【日志输出】", bg="#f0f0f0", fg="black", font=("Segoe UI", 10))
        log_label.pack(anchor="w", padx=10)

        log_frame = tk.Frame(content_frame, bg="white", highlightbackground="#cccccc", highlightthickness=1)
        log_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.log_text = tk.Text(log_frame, height=24, width=90, state='disabled',
                              bg="white", fg="black", font=("Consolas", 10),
                              relief="flat", wrap="word")
        self.log_text.pack(fill="both", expand=True)

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)

    def play_alert_sound(self):
        winsound.Beep(800, 300)

    def simulate_typing(self, content, speed):
        total_chars = len(content)
        if total_chars == 0:
            self.log("❌ 内容为空，无法开始输入。")
            return

        self.log(f"\n⌨️ 开始输入内容，共 {total_chars} 个字符...\n")

        for i, char in enumerate(content):
            if not self.running:
                self.log("🛑 已取消输入。")
                break

            # 改进焦点检测逻辑
            if self.focus_lost and not is_app_in_foreground():
                self.log("⚠️ 检测到焦点已离开当前窗口，自动停止输入。")
                self.last_interrupt_index = i + 1
                self.play_alert_sound()
                messagebox.showwarning("警告", "检测到您切换了窗口，输入已暂停")
                self.running = False
                break

            keyboard.write(char)
            time.sleep(speed)

            if (i + 1) % 100 == 0 or i == total_chars - 1:
                percent = min((i + 1) / total_chars * 100, 100)
                self.log(f"\r✅ 已输入: {i + 1}/{total_chars} 字符 | 进度: {percent:.1f}%")
        if self.running:
            self.log("\n\n🎉 输入完成！")
        self.running = False

    def start_typing(self):
        if self.running:
            messagebox.showwarning("提示", "已有任务正在运行！")
            return

        content = self.text_area.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "请输入要输入的内容！")
            return

        self.running = True
        self.focus_lost = False  # 启动输入时重置焦点状态
        threading.Thread(target=self._run_typing_task, args=(content,)).start()

    def _run_typing_task(self, content):
        try:
            if self.switch_input.get():
                self.switch_to_english_input()

            self.log("📌 请在 5 秒内点击目标文本框...")
            time.sleep(5)
            self.simulate_typing(content, self.typing_speed.get())
        except Exception as e:
            self.log(f"\n❌ 发生错误: {e}")
        finally:
            self.running = False

    def stop_typing(self):
        self.running = False
        self.log("🛑 用户手动取消输入。")

    def save_draft(self):
        draft_path = "draft.txt"
        content = self.text_area.get("1.0", tk.END)
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("保存成功", f"草稿已保存至：{os.path.abspath(draft_path)}")
        self.log(f"💾 草稿已保存至：{os.path.abspath(draft_path)}")

    def load_template(self):
        path = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert(tk.END, content)
                self.log(f"📎 已加载模板：{path}")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败：{e}")

    def change_font_size(self):
        size = simpledialog.askinteger("字体大小", "请输入字体大小（如 12）", initialvalue=self.font_size.get(), minvalue=6, maxvalue=72)
        if size:
            self.font_size.set(size)
            self.update_text_style()

    def choose_text_color(self):
        color = colorchooser.askcolor(title="选择文字颜色")[1]
        if color:
            self.text_color.set(color)
            self.update_text_style()

    def choose_bg_color(self):
        color = colorchooser.askcolor(title="选择背景颜色")[1]
        if color:
            self.bg_color.set(color)
            self.update_text_style()

    def update_text_style(self):
        self.text_area.config(
            font=("微软雅黑", self.font_size.get()),
            fg=self.text_color.get(),
            bg=self.bg_color.get(),
            insertbackground="black"
        )

    def clear_text_area(self):
        self.text_area.delete("1.0", tk.END)
        self.log("🧹 文本框已清空")

    def resume_typing(self):
        content = self.text_area.get("1.0", tk.END)
        if not content or self.last_interrupt_index >= len(content):
            messagebox.showinfo("提示", "没有可恢复的内容")
            return

        resumed_content = content[self.last_interrupt_index:]
        self.log(f"▶️ 从中断位置继续输入，剩余 {len(resumed_content)} 字符...")
        threading.Thread(target=self._run_typing_task, args=(resumed_content,), daemon=True).start()

    def load_clipboard_content(self):
        try:
            content = pyperclip.paste()
            if not content:
                messagebox.showinfo("提示", "剪贴板为空")
                return
            self.text_area.insert(tk.END, content)
            self.log("📎 已加载剪贴板内容")
        except Exception as e:
            messagebox.showerror("错误", f"无法读取剪贴板：{e}")

    def switch_to_english_input(self):
        self.log("🔄 正在尝试切换输入法（英文）...")
        try:
            keyboard.press_and_release('ctrl+space')
            time.sleep(1)
        except Exception as e:
            self.log(f"⚠️ 输入法切换失败: {e}")

    def create_shortcuts(self):
        self.root.bind("<Control-Return>", lambda e: self.start_typing())

    def setup_draggable(self):
        def on_press(event):
            self.offset_x = event.x
            self.offset_y = event.y

        def on_drag(event):
            x = self.root.winfo_pointerx() - self.offset_x
            y = self.root.winfo_pointery() - self.offset_y
            self.root.geometry(f"+{x}+{y}")

        self.title_bar.bind("<Button-1>", on_press)
        self.title_bar.bind("<B1-Motion>", on_drag)


# ================== 启动主程序 ==================
if __name__ == "__main__":
    root = tk.Tk()
    app = SoftAutoTypingApp(root)
    root.mainloop()
