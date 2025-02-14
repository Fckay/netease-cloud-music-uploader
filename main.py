import os
import json
import requests
import time

# 导入 login 函数
from login import login  # 直接从 login.py 导入 login 函数
from get_cloud_info import get_cloud_info  # 从 get_cloud_info.py 导入 get_cloud_info 函数

# 获取当前时间戳（秒）
def get_current_timestamp():
    return int(time.time())

# 添加获取当前时间字符串的函数
def get_current_time_str():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# 修改打印相关的函数
def print_with_time(message, style='info'):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    # 定义不同样式的前缀和颜色
    styles = {
        'info': ('INFO', ''),
        'success': ('SUCCESS', '✓ '),
        'warning': ('WARN', '! '),
        'error': ('ERROR', '✗ '),
        'progress': ('PROGRESS', '→ ')
    }
    
    level, prefix = styles.get(style, styles['info'])
    print(f"[{current_time}] [{level}] {prefix}{message}")

def print_divider(char="=", length=60):
    print(char * length)

def print_header(title):
    print_divider()
    print(title.center(56))
    print_divider()

# 读取 cookies.txt 文件
def read_cookie():
    if os.path.exists("cookies.txt"):
        try:
            with open("cookies.txt", "r") as f:
                cookie = f.read().strip()
                if cookie:
                    return cookie
        except Exception as e:
            print(f"读取cookies.txt文件出错: {str(e)}")
    return None

# 手动输入cookie
def input_cookie():
    print("\n请输入cookie（从APP或者客户端获取，否则显示容量不正确）：")
    cookie = input().strip()
    if cookie:
        try:
            # 保存cookie到文件
            with open("cookies.txt", "w") as f:
                f.write(cookie)
            print("Cookie已保存到cookies.txt文件")
            return cookie
        except Exception as e:
            print(f"保存cookie到文件时出错: {str(e)}")
    return None

# 读取歌曲json文件并返回数据
def read_songs_data():
    while True:
        print("\n请输入歌曲json文件的完整路径（直接回车将尝试读取当前目录下的'歌曲.json'）：")
        file_path = input().strip()
        
        # 如果用户直接回车，使用默认路径
        if not file_path:
            file_path = "歌曲.json"
        
        # 检查文件是否存在
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        songs = data.get('data', [])
                        if songs:
                            print(f"成功读取到 {len(songs)} 首歌曲信息")
                            return songs
                        else:
                            print("文件中没有找到歌曲数据")
                            return []
                    except json.JSONDecodeError:
                        print("json文件格式错误，请确保文件内容是正确的JSON格式")
            except Exception as e:
                print(f"读取文件时发生错误: {str(e)}")
        else:
            print(f"找不到文件: {file_path}")
        
        # 询问用户是否重试
        retry = input("\n是否重新输入文件路径？(y/n): ").lower()
        if retry != 'y':
            print("用户取消操作")
            return []

# 提取所有歌曲的 id 和其他信息
def get_all_song_info(songs_data):
    song_info_list = []
    for song in songs_data:
        song_info = {
            'id': song.get("id"),
            'size': song.get("size"),
            'ext': song.get("ext"),
            'bitrate': song.get("bitrate"),
            'md5': song.get("md5")
        }
        song_info_list.append(song_info)
    return song_info_list

# 查询歌曲详情
def get_song_details(song_ids,cookie):
    ids = ",".join(map(str, song_ids))  # 将多个 id 拼接成一个以逗号分隔的字符串
    timestamp = get_current_timestamp()  # 获取当前时间戳
    url = f"http://localhost:3000/song/detail?ids={ids}&time={timestamp}&cookie={cookie}"
    response = requests.get(url)
    try:
        response_data = response.json()
        if response_data.get('code') == 200:
            privileges = response_data.get('privileges', [])
            song_id_list = []
            song_list = []
            songs = response_data.get('songs', [])
            # 去除重复的歌曲
            for privilege in privileges:
                if privilege['cs'] == False:
                    song_id_list.append(privilege['id'])
            for song in songs:
                if song['id'] in song_id_list:
                    song_list.append(song)
            return song_list
        else:
            print("获取歌曲详情失败:", response_data.get("message"))
            return []
    except json.JSONDecodeError:
        print("响应内容无法解析为JSON:", response.text)
        return []

# 执行 import 请求
def import_song(song_info, cookie):
    song_id = song_info['id']
    artist = song_info['artist']
    album = song_info['album']
    file_size = song_info['size']
    bitrate = song_info['bitrate']
    md5 = song_info['md5']
    file_type = song_info['ext']
    
    # 构造完整的请求URL和参数
    timestamp = get_current_timestamp()  # 获取当前时间戳
    url = f"http://localhost:3000/cloud/import?id={song_id}&cookie={cookie}&artist={artist}&album={album}&fileSize={file_size}&bitrate={bitrate}&md5={md5}&fileType={file_type}&time={timestamp}"
    #print(f"执行导入请求 URL: {url}")
    
    response = requests.get(url)
    try:
        response_data = response.json()
        return response_data
    except json.JSONDecodeError:
        print("响应内容无法解析为JSON:", response.text)
        return None

# 保存失败的 id 到文件
def save_failed_id(song_id):
    with open("failed_ids.txt", "a") as f:
        f.write(f"{song_id}\n")

# 批量查询歌曲详情并去重
def batch_get_song_details(song_info_list, cookie, batch_size=900):
    all_unique_songs = []
    total_songs = len(song_info_list)
    
    print_with_time(f"\n开始批量查询歌曲详情，共 {total_songs} 首歌曲")
    
    # 按批次处理歌曲
    for i in range(0, total_songs, batch_size):
        batch = song_info_list[i:i + batch_size]
        song_ids = [song['id'] for song in batch]
        print_with_time(f"\n处理第 {i+1} 到 {min(i+batch_size, total_songs)} 首歌曲")
        
        # 查询这一批歌曲的详情
        song_details = get_song_details(song_ids, cookie)
        if song_details:
            # 将歌曲详情与原始信息合并
            for song in song_details:
                song_id = song['id']
                # 找到对应的原始信息
                original_info = next((s for s in batch if s['id'] == song_id), None)
                if original_info:
                    song_info = {
                        'id': song_id,
                        'name': song['name'],
                        'artist': song['ar'][0]['name'],
                        'album': song['al']['name'],
                        'size': original_info['size'],
                        'ext': original_info['ext'],
                        'bitrate': original_info['bitrate'],
                        'md5': original_info['md5']
                    }
                    all_unique_songs.append(song_info)
        
        print_with_time(f"本次重复处理完成，当前已获取 {len(all_unique_songs)} 首待上传歌曲")
    
    print_with_time(f"\n去重后共有 {len(all_unique_songs)} 首歌曲待上传")
    return all_unique_songs

# 添加新函数：保存已上传的歌曲ID
def save_uploaded_id(song_id):
    with open("uploaded_ids.txt", "a") as f:
        f.write(f"{song_id}\n")

# 添加新函数：读取已上传的歌曲ID
def read_uploaded_ids():
    uploaded_ids = set()
    if os.path.exists("uploaded_ids.txt"):
        try:
            with open("uploaded_ids.txt", "r") as f:
                uploaded_ids = set(line.strip() for line in f if line.strip())
            print(f"找到 {len(uploaded_ids)} 首已上传的歌曲记录")
        except Exception as e:
            print(f"读取已上传记录时出错: {str(e)}")
    return uploaded_ids

# 添加新的导入统计函数
def calculate_upload_rate(start_time, uploaded_count):
    elapsed_time = time.time() - start_time
    minutes = elapsed_time / 60
    rate = uploaded_count / minutes if minutes > 0 else 0
    return rate

# 添加新函数：获取用户设置的等待时间
def get_wait_time():
    while True:
        wait_time = input("\n请设置遇到频繁限制时的等待时间（秒），直接回车默认40秒：").strip()
        try:
            return int(wait_time) if wait_time else 40
        except ValueError:
            print("请输入有效的数字！")

# 添加新函数：获取上传间隔时间
def get_upload_interval():
    while True:
        interval = input("\n请设置每次上传的间隔时间（秒），支持小数点，直接回车默认不限制：").strip()
        if not interval:  # 如果直接回车，返回0表示不限制
            return 0
        try:
            interval = float(interval)
            if interval < 0:
                print_with_time("间隔时间不能小于0！")
                continue
            return interval
        except ValueError:
            print_with_time("请输入有效的数字！")

# 修改 process_songs 函数
def process_songs(song_info_list, cookie, wait_time=40, upload_interval=0):
    failed_attempts = {}  # 记录每个 ID 失败的次数
    total_songs = len(song_info_list)
    uploaded_count = 0
    start_time = time.time()
    
    print_header("开始上传歌曲")
    print_with_time(f"总计待上传: {total_songs} 首歌曲", 'info')
    print_divider("-")
    
    for song_info in song_info_list:
        song_id = song_info['id']
        song_name = song_info['name']
        artist_name = song_info['artist']
        print_with_time(f"正在导入: {song_name} - {artist_name}", 'progress')
        print_with_time(f"进度: {uploaded_count}/{total_songs} | ID: {song_id}", 'info')
        
        attempts = 0
        while attempts < 3:
            try:
                result = import_song(song_info, cookie)
                if result:
                    code = result.get('code')
                if code == 405:
                    print_with_time(str(result), 'warning')
                    print_with_time(f"操作频繁，暂停{wait_time}秒后重试", 'warning')
                    time.sleep(wait_time)
                    continue
                
                success_songs = result.get('data', {}).get('successSongs', [])
                failed = result.get('data', {}).get('failed', [])
                
                if success_songs:
                    uploaded_count += 1
                    rate = calculate_upload_rate(start_time, uploaded_count)
                    print_with_time(f"导入成功: {song_name}", 'success')
                    print_with_time(f"当前进度: {uploaded_count}/{total_songs} | 平均速率: {rate:.1f}首/分钟", 'info')
                    save_uploaded_id(song_id)
                    
                    if upload_interval > 0:
                        print_with_time(f"等待 {upload_interval} 秒...", 'info')
                        time.sleep(upload_interval)
                    print_divider("-")
                    break
                else:
                    if all(f['code'] == -100 for f in failed):
                        print_with_time(f"歌曲已存在: {song_name}", 'warning')
                        save_failed_id(song_id)
                        break
                    else:
                        print_with_time(f"导入失败: {result}", 'error')
                attempts += 1
            except Exception as e:
                print_with_time(f"未知错误: {str(e)}", 'error')
                break
        
        if attempts == 3:
            print_with_time(f"跳过歌曲: {song_name} (已重试3次)", 'error')
            save_failed_id(song_id)
        print_divider("-")
    
    # 上传完成后的统计信息
    print_header("上传任务完成")
    elapsed_time = time.time() - start_time
    minutes = elapsed_time / 60
    final_rate = calculate_upload_rate(start_time, uploaded_count)
    print_with_time(f"成功上传: {uploaded_count}/{total_songs} 首歌曲", 'success')
    print_with_time(f"总耗时: {minutes:.1f}分钟", 'info')
    print_with_time(f"平均速率: {final_rate:.1f}首/分钟", 'info')
    print_divider()

# 修改 main 函数
def main():
    print_header("网易云音乐云盘导入工具")
    print("正在启动服务...")
    print("请确保已启动 NeteaseCloudMusicApi 服务")
    print_divider()
    
    # 尝试读取已保存的 cookie
    cookie = read_cookie()
    
    if cookie:
        print("已从cookies.txt文件读取到cookie")
        # 获取并显示云盘信息
        get_cloud_info(cookie)
    else:
        print("没有找到有效的cookie，请选择登录方式：")
        print("1. 扫码登录")
        print("2. 手动输入cookie")
        
        while True:
            choice = input("请输入选择（1或2）：").strip()
            if choice == "1":
                # 执行扫码登录
                cookie = login()
                if cookie:
                    print_with_time("扫码登录成功")
                    get_cloud_info(cookie)
                else:
                    print_with_time("扫码登录失败")
                    return
                break
            elif choice == "2":
                # 手动输入cookie
                cookie = input_cookie()
                if cookie:
                    print_with_time("登录成功")
                    get_cloud_info(cookie)
                else:
                    print_with_time("登录失败")
                    return
                break
            else:
                print("无效的选择，请重新输入")
    
    # 修改设置提示的输出
    print_divider()
    print("用户设置")
    wait_time = get_wait_time()
    print(f"频繁限制等待时间: {wait_time}秒")
    
    upload_interval = get_upload_interval()
    if upload_interval > 0:
        print(f"上传间隔时间: {upload_interval}秒")
    else:
        print("上传间隔: 不限制")
    print_divider()

    # 读取歌曲数据
    songs_data = read_songs_data()
    
    if songs_data:
        song_info_list = get_all_song_info(songs_data)
        
        # 读取已上传的歌曲ID
        uploaded_ids = read_uploaded_ids()
        if uploaded_ids:
            choice = input("\n检测到上次上传的记录，是否继续上次的上传？(y/n): ").lower().strip()
            if choice == 'y':
                # 过滤掉已上传的歌曲
                song_info_list = [song for song in song_info_list if str(song['id']) not in uploaded_ids]
                print(f"过滤后还有 {len(song_info_list)} 首歌曲待上传")
        
        # 先批量查询歌曲详情并去重
        unique_songs = batch_get_song_details(song_info_list, cookie)
        if unique_songs:
            # 执行歌曲导入请求，传入用户设置的等待时间和上传间隔
            process_songs(unique_songs, cookie, wait_time, upload_interval)
        else:
            print("没有找到有效的歌曲信息")
    else:
        print("没有找到任何歌曲数据")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"程序发生错误: {str(e)}")
    finally:
        input("\n按回车键退出程序...")  # 添加这行确保用户能看到输出
