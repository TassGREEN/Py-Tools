import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, simpledialog
import time
import keyboard
import threading
import os
class SoftAutoTypingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SoftAutoTypingTool")
        self.root.geometry("800x700")
        self.root.configure(bg="#2e2e2e")
        self.root.overrideredirect(True)

        # 控件变量
        self.switch_input = tk.BooleanVar(value=True)
        self.typing_speed = tk.DoubleVar(value=0.01)
        self.running = False

        # 字体颜色变量
        self.font_size = tk.IntVar(value=12)
        self.text_color = tk.StringVar(value="white")
        self.bg_color = tk.StringVar(value="#2e2e2e")

        self.create_title_bar()
        self.create_widgets()
        self.create_shortcuts()
        self.setup_draggable()

    def create_title_bar(self):
        # 自定义标题栏
        self.title_bar = tk.Frame(self.root, bg="#1e1e1e", height=30)
        self.title_bar.pack(fill="x")

        title_label = tk.Label(self.title_bar, text="AutoTypingTool", bg="#1e1e1e", fg="white", font=("Segoe UI", 10))
        title_label.pack(side="left", padx=10)

        close_button = tk.Label(self.title_bar, text="✕", bg="#1e1e1e", fg="white", font=("Segoe UI", 10), width=2)
        close_button.pack(side="right", padx=5)
        close_button.bind("<Button-1>", lambda e: self.root.destroy())

        minimize_button = tk.Label(self.title_bar, text="—", bg="#1e1e1e", fg="white", font=("Segoe UI", 10), width=2)
        minimize_button.pack(side="right", padx=5)
        minimize_button.bind("<Button-1>", lambda e: self.root.iconify())

    def create_widgets(self):
        content_frame = tk.Frame(self.root, bg="#2e2e2e")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 输入文本框
        self.text_area = tk.Text(content_frame, height=18, width=90, wrap="word", undo=True,
                                 bg=self.bg_color.get(), fg=self.text_color.get(),
                                 insertbackground="white", font=("微软雅黑", self.font_size.get()))
        self.text_area.pack(pady=10)

        # 工具按钮
        tool_frame = tk.Frame(content_frame, bg="#2e2e2e")
        tool_frame.pack(pady=5)

        self.add_button(tool_frame, "保存草稿", self.save_draft).pack(side="left", padx=5)
        self.add_button(tool_frame, "打开……", self.load_template).pack(side="left", padx=5)
        self.add_button(tool_frame, "字体大小", self.change_font_size).pack(side="left", padx=5)
        self.add_button(tool_frame, "文字颜色", self.choose_text_color).pack(side="left", padx=5)
        self.add_button(tool_frame, "背景颜色", self.choose_bg_color).pack(side="left", padx=5)

        # 切换输入法
        tk.Checkbutton(content_frame, text="切换英文输入法 (Ctrl+Space)", variable=self.switch_input,
                       bg="#2e2e2e", fg="white", selectcolor="#3e3e3e").pack(anchor="w", padx=10)

        # 打字速度
        speed_frame = tk.Frame(content_frame, bg="#2e2e2e")
        speed_frame.pack(pady=10)
        tk.Label(speed_frame, text="打字速度（秒/字）:", bg="#2e2e2e", fg="white").pack(side="left", padx=10)
        tk.Scale(speed_frame, from_=0.005, to=0.2, resolution=0.005, orient="horizontal",
                 variable=self.typing_speed, length=300, bg="#2e2e2e", fg="white",
                 troughcolor="#444444").pack(side="left")

        # 操作按钮
        btn_frame = tk.Frame(content_frame, bg="#2e2e2e")
        btn_frame.pack(pady=10)
        self.add_button(btn_frame, "开始自动输入", self.start_typing, width=15).pack(side="left", padx=5)
        self.add_button(btn_frame, "取消", self.stop_typing, width=10).pack(side="left", padx=5)

        # 日志输出
        log_label = tk.Label(content_frame, text="【日志输出】", bg="#2e2e2e", fg="white", font=("Segoe UI", 10))
        log_label.pack(anchor="w", padx=10)
        self.log_text = tk.Text(content_frame, height=10, width=90, state='disabled',
                                bg="#1c1c1c", fg="lightgray", font=("Consolas", 10))
        self.log_text.pack(padx=10, pady=10)

    def add_button(self, parent, text, command, width=10):
        return tk.Button(parent, text=text, command=command, width=width,
                         bg="#3e3e3e", fg="white", relief="flat", padx=10, pady=5,
                         activebackground="#555555", activeforeground="white")

    def create_shortcuts(self):
        self.root.bind("<Control-Return>", lambda e: self.start_typing())

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)

    def switch_to_english_input(self):
        self.log("🔄 正在尝试切换输入法（英文）...")
        try:
            keyboard.press_and_release('ctrl+space')
            time.sleep(1)
        except Exception as e:
            self.log(f"⚠️ 输入法切换失败: {e}")

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

    def load_template(self):
        path = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert(tk.END, content)
                messagebox.showinfo("加载成功", f"已加载模板：{path}")
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
            insertbackground="white"
        )

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

if __name__ == "__main__":
    root = tk.Tk()
    app = SoftAutoTypingApp(root)
    root.mainloop()