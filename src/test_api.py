import requests

url = "http://127.0.0.1:5000/api/qa"

questions = [
    "石绿通过哪些方法识别",
    "辰砂（α-HgS）有哪些元素",
    "莫高窟220窟壁画位于哪里",
    "Fe相关壁画有哪些"
]

for q in questions:
    print("=" * 60)
    print("问题：", q)

    resp = requests.post(
        url,
        json={"question": q},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )

    print("状态码：", resp.status_code)
    try:
        print("返回结果：", resp.json())
    except Exception:
        print("原始返回：", resp.text)