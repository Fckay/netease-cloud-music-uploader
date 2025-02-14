import requests

# 获取云盘信息
def get_cloud_info(cookie):
    url = "http://localhost:3000/user/cloud"
    params = {"cookie": cookie, "limit": 1}
    
    response = requests.get(url, params=params)
    try:
        response_data = response.json()
        if response_data.get('code') == 200:
            total_size = response_data['size']
            max_size = response_data['maxSize']
            file_count = response_data['count']
            # 输出云盘信息
            print("云盘信息:")
            print(f"总大小: {convert_bytes(total_size)}")
            print(f"最大容量: {convert_bytes(max_size)}")
            print(f"文件数量: {file_count}")
        else:
            print(f"获取云盘信息失败: {response_data.get('message')}")
    except json.JSONDecodeError:
        print("响应内容无法解析为JSON:", response.text)

# 字节数转换为可读格式（GB, MB, TB等）
def convert_bytes(size_in_bytes):
    try:
        size_in_bytes = float(size_in_bytes)  # 确保传入的值是一个数字
    except ValueError:
        return "无效的字节数"  # 如果无法转换为数字，则返回错误信息

    units = ['B', 'KB', 'MB', 'GB', 'TB']
    for unit in units:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} {unit}"
