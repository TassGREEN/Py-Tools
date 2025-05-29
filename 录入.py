
import time
import keyboard

# 切换到英文输入法（假设快捷键是 Ctrl + Space）
keyboard.press_and_release('ctrl+space')
time.sleep(1)  # 等待输入法切换完成

# 读取 txt 文件内容
with open("input.txt", "r", encoding="utf-8") as f:
    content = f.read()
print("请在 5 秒内点击目标文本框...")
time.sleep(5)
print("开始逐字输入内容...")
# 开始模拟打字
for char in content:
    keyboard.write(char)
    time.sleep(0.01)  # 控制打字速度

print("✅ 输入完成！")
