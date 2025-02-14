import requests
from PIL import Image
from io import BytesIO
import base64
import time

# 获取当前时间戳
def get_current_timestamp():
    return int(time.time())

# 获取unikey
def get_unikey():
    url = f"http://localhost:3000/login/qr/key?time={get_current_timestamp()}"
    response = requests.get(url)
    data = response.json()
    if data['code'] == 200:
        return data['data']['unikey']
    return None

# 创建二维码
def create_qr(unikey):
    url = f"http://localhost:3000/login/qr/create?key={unikey}&qrimg=1&time={get_current_timestamp()}"
    response = requests.get(url)
    data = response.json()
    if data['code'] == 200:
        qrimg_base64 = data['data']['qrimg']
        return qrimg_base64
    return None

# 显示二维码图像
def display_qr_image(qrimg_base64):
    img_data = base64.b64decode(qrimg_base64.split(",")[1])
    img = Image.open(BytesIO(img_data))
    img.show()

# 监控扫码状态
def check_scan_status(unikey):
    url = f"http://localhost:3000/login/qr/check?key={unikey}&time={get_current_timestamp()}"
    response = requests.get(url)
    #print(f"响应内容: {response.text}")  # 打印每次请求的响应内容
    return response.json()

# 登录函数
def login():
    unikey = get_unikey()
    if not unikey:
        print("无法获取unikey")
        return None

    qrimg_base64 = create_qr(unikey)
    if not qrimg_base64:
        print("无法创建二维码")
        return None
    
    # 显示二维码图像
    display_qr_image(qrimg_base64)

    print("请扫描二维码，等待扫码成功...")

    # 监控扫码状态
    while True:
        status = check_scan_status(unikey)
        
        if status['code'] == 803:
            print("授权登录成功")
            cookie = status['cookie']
            print(f"保存的 Cookie: {cookie}")
            # 保存 cookie 到文件
            with open("cookies.txt", "w") as f:
                f.write(cookie)
            return cookie  # 返回 cookie
        elif status['code'] == 801:
            print("等待扫码，继续请求中...")
        elif status['code'] == 802:
            print("授权中，继续请求中...")
        else:
            print(f"扫码失败: {status['message']}")
            return None  # 返回 None，表示扫码失败
        
        time.sleep(2)  # 每隔2秒检查一次扫码状态

