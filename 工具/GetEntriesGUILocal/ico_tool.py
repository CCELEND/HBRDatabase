
import os
from PIL import Image

# 设置目标尺寸
size = (64, 64)

from PIL import Image

# 打开 256x256 的 ico 文件
input_ico = "entries.ico"
output_ico = "entries1.ico"

# 打开图像
with Image.open(input_ico) as img:
    # 将图像缩小到 64x64
    resized_img = img.resize(size, Image.LANCZOS)
    
    # 保存为新的 ico 文件
    resized_img.save(output_ico, format="ICO")


# # 获取当前目录下的所有文件
# for filename in os.listdir('.'):
#     if filename.endswith('.ico'):
#         # 构建完整的文件路径
#         webppath = os.path.join('.', filename)
#         # 加载图片
#         iconimage = Image.open(webppath).convert("RGBA")
#         # 调整图片大小
#         iconimage = iconimage.resize(size, Image.LANCZOS)
#         # 设置ICO文件路径
#         tempiconpath = os.path.splitext(filename)[0] + '.ico'
#         # 保存为ICO文件
#         iconimage.save(tempiconpath, format='ICO', sizes=[(size[0], size[1])])

