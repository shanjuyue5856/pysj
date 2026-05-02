import csv
import os

# 创建 data/raw 目录
os.makedirs("data/raw", exist_ok=True)

# 示例数据
rows = [
    ["敦煌壁画A", "朱砂", "辰砂", "红色", "敦煌", "唐代", "拉曼光谱"],
    ["敦煌壁画A", "石青", "蓝铜矿", "蓝色", "敦煌", "唐代", "XRD"],
    ["永乐宫壁画B", "石绿", "孔雀石", "绿色", "山西", "元代", "显微分析"],
    ["麦积山壁画C", "赭石", "赤铁矿", "棕红色", "甘肃", "北魏", "红外光谱"],
    ["克孜尔壁画D", "铅白", "白铅矿", "白色", "新疆", "魏晋", "偏光显微镜"]
]

# 使用 utf-8-sig，Windows / Excel / VS Code 下更稳定
with open("data/raw/pigments.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)

    # 表头
    writer.writerow([
        "mural",
        "pigment",
        "mineral",
        "color",
        "site",
        "dynasty",
        "method"
    ])

    # 数据行
    writer.writerows(rows)

print("CSV 文件已生成：data/raw/pigments.csv")