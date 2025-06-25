h = '<div class="skill-it-precent" data-v-ed38c992=""><div class="pro-out" data-v-ed38c992=""><div class="pro-inner" data-v-ed38c992="" style="width:50%;"></div></div><div class="pro-out" data-v-ed38c992=""><div class="pro-inner" data-v-ed38c992="" style="width:50%;"></div></div><div class="pro-out" data-v-ed38c992=""><div class="pro-inner" data-v-ed38c992="" style="width:50%;"></div></div><div class="pro-out" data-v-ed38c992=""><div class="pro-inner" data-v-ed38c992="" style="width:50%;"></div></div><div class="lv lv1" data-v-ed38c992=""><i data-v-ed38c992=""></i><span data-v-ed38c992="">一般</span></div><div class="lv lv2" data-v-ed38c992=""><i data-v-ed38c992=""></i><span data-v-ed38c992="">良好</span></div><div class="lv lv3" data-v-ed38c992=""><i data-v-ed38c992=""></i><span data-v-ed38c992="">熟练</span></div><div class="lv lv4" data-v-ed38c992=""><i data-v-ed38c992=""></i><span data-v-ed38c992="">精通</span></div></div>'

from bs4 import BeautifulSoup

soup = BeautifulSoup(h, "html.parser")

# 查找所有的 div 元素，class 为 "pro-out"
pro_outs = soup.find_all("div", class_="pro-out")

# 遍历每个 "pro-out" 元素
for pro_out in pro_outs:
    # 查找其中的 "pro-inner" 元素
    pro_inner = pro_out.find("div", class_="pro-inner")
    # 获取 "pro-inner" 元素的 style 属性
    style = pro_inner.get("style")
    # 提取宽度值（假设宽度值在 "width:" 后面）
    width = style.split("width:")[1].split(";")[0]
    print(width)  # 输出宽度值
