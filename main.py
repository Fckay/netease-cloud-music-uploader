import os
import json
import requests
import time
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    print("\n请输入cookie（登录后请检查网盘容量是否正确，推荐扫码登录）：")
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
    song = song_info['name']
    
    # 构造完整的请求URL和参数
    timestamp = get_current_timestamp()  # 获取当前时间戳
    url = f"http://localhost:3000/cloud/import?id={song_id}&song={song}&cookie={cookie}&artist={artist}&album={album}&fileSize={file_size}&bitrate={bitrate}&md5={md5}&fileType={file_type}&time={timestamp}"
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

# 批量查询歌曲详情
def batch_get_song_details(song_info_list, cookie, batch_size=950, max_workers=0):
    all_unique_songs = []
    total_songs = len(song_info_list)
    
    print_with_time(f"\n开始批量查询歌曲详情，共 {total_songs} 首歌曲")
    
    # 将歌曲列表分成多个批次
    batches = []
    for i in range(0, total_songs, batch_size):
        batch = song_info_list[i:i + batch_size]
        batches.append(batch)
    
    def process_batch(batch):
        song_ids = [song['id'] for song in batch]
        processed_songs = []
        
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
                    processed_songs.append(song_info)
        return processed_songs

    # 根据是否启用多线程选择处理方式
    if max_workers > 0:
        result_lock = threading.Lock()
        # 使用线程池处理所有批次
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_batch = {executor.submit(process_batch, batch): i for i, batch in enumerate(batches)}
            
            # 处理完成的任务
            for future in as_completed(future_to_batch):
                batch_index = future_to_batch[future]
                try:
                    batch_results = future.result()
                    with result_lock:
                        all_unique_songs.extend(batch_results)
                        print_with_time(f"完成第 {batch_index + 1}/{len(batches)} 批处理，当前已获取 {len(all_unique_songs)} 首待上传歌曲")
                except Exception as e:
                    print_with_time(f"处理批次 {batch_index + 1} 时发生错误: {str(e)}", 'error')
    else:
        # 单线程处理
        for i, batch in enumerate(batches):
            try:
                batch_results = process_batch(batch)
                all_unique_songs.extend(batch_results)
                print_with_time(f"完成第 {i + 1}/{len(batches)} 批处理，当前已获取 {len(all_unique_songs)} 首待上传歌曲")
            except Exception as e:
                print_with_time(f"处理批次 {i + 1} 时发生错误: {str(e)}", 'error')
    
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

# 添加新函数：获取多线程设置
def get_thread_settings():
    while True:
        use_threads = input("\n是否启用多线程加速查询？(y/n，默认n): ").strip().lower()
        if not use_threads or use_threads == 'n':
            return 0
        elif use_threads == 'y':
            while True:
                try:
                    thread_count = input("\n请输入线程数量（建议1-5，过多可能导致请求被限制）：").strip()
                    thread_count = int(thread_count)
                    if thread_count <= 0:
                        print_with_time("线程数必须大于0！", 'warning')
                        continue
                    if thread_count > 5:
                        confirm = input("警告：线程数过多可能导致请求频繁被限制！！！，是否继续？(y/n): ").strip().lower()
                        if confirm != 'y':
                            continue
                    return thread_count
                except ValueError:
                    print_with_time("请输入有效的数字！", 'error')
        else:
            print_with_time("无效的输入，请重新选择", 'warning')

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
        
        while True:
            try:
                result = import_song(song_info, cookie)
                if result:
                    code = result.get('code')
                if code == 405:
                    print_with_time(str(result), 'warning')
                    print_with_time(f"操作频繁，暂停{wait_time}秒后重试", 'warning')
                    time.sleep(wait_time)
                    continue
                
                success_songs = result.get('data', {})
                
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
                    save_failed_id(song_id)
                    print_with_time(f"导入失败: {result} 跳过当前歌曲", 'error')
                    print_with_time(f"等待 {upload_interval} 秒...", 'info')
                    time.sleep(upload_interval)
                    break
            except Exception as e:
                time.sleep(upload_interval)
                print_with_time(f"未知错误: {str(e)}", 'error')
                break
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

# 修改删除未知歌曲的函数
def delete_unknown_songs(cookie, max_workers=0):
    print_header("网易云盘未知歌曲清理")
    
    def fetch_cloud_data(offset):
        url = f'http://localhost:3000/user/cloud?offset={offset}&limit=30&cookie={cookie}'
        response = requests.get(url)
        return response.json()
    
    def delete_song(song_id):
        url = f'http://localhost:3000/user/cloud/del?id={song_id}&cookie={cookie}'
        response = requests.get(url)
        data = response.json()
        if data.get('code') == 200:
            print_with_time(f'歌曲ID: {song_id} 删除成功', 'success')
            return True
        else:
            print_with_time(f'歌曲ID: {song_id} 删除失败', 'error')
            return False

    offset = 0
    has_more = True
    found_count = 0
    deleted_count = 0
    
    print_with_time("正在扫描并删除未知歌曲...", 'info')
    
    while has_more:
        data = fetch_cloud_data(offset)
        songs = data.get('data', [])
        has_more = data.get('hasMore', False)
        
        # 收集当前批次的未知歌曲
        current_batch = []
        for song in songs:
            simple_song = song.get('simpleSong', {})
            name = simple_song.get('name')
            if not name:
                song_id = simple_song.get('id')
                if song_id:
                    found_count += 1
                    current_batch.append(song_id)
        
        # 删除当前批次的未知歌曲
        if current_batch:
            if max_workers > 0:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [executor.submit(delete_song, song_id) for song_id in current_batch]
                    for future in as_completed(futures):
                        if future.result():
                            deleted_count += 1
            else:
                for song_id in current_batch:
                    if delete_song(song_id):
                        deleted_count += 1
        
        # 实时显示进度
        print(f"\r已发现 {found_count} 首未知歌曲，成功删除 {deleted_count} 首...", end='', flush=True)
        offset += 30
    
    # 扫描完成后换行并显示最终结果
    print()
    
    if found_count == 0:
        print_with_time("没有发现未知歌曲", 'success')
        return
    
    print_header("清理完成")
    print_with_time(f"共发现 {found_count} 首未知歌曲", 'info')
    print_with_time(f"成功删除 {deleted_count} 首歌曲", 'success')

# 修改删除全部歌曲的函数
def delete_all_songs(cookie, max_workers=0):
    print_header("删除全部云盘歌曲")
    confirm = input("警告：此操作将删除云盘中的所有歌曲！确定要继续吗？(y/n): ").lower()
    if confirm != 'y':
        print_with_time("操作已取消", 'warning')
        return
    
    def fetch_cloud_data(offset):
        url = f'http://localhost:3000/user/cloud?offset={offset}&limit=30&cookie={cookie}'
        response = requests.get(url)
        return response.json()
    
    def delete_song(song_id):
        url = f'http://localhost:3000/user/cloud/del?id={song_id}&cookie={cookie}'
        response = requests.get(url)
        data = response.json()
        if data.get('code') == 200:
            print_with_time(f'歌曲ID: {song_id} 删除成功', 'success')
            return True
        else:
            print_with_time(f'歌曲ID: {song_id} 删除失败', 'error')
            return False

    # 收集所有歌曲ID
    all_songs = []
    offset = 0
    has_more = True
    
    print_with_time("正在扫描所有歌曲...", 'info')
    
    while has_more:
        data = fetch_cloud_data(offset)
        songs = data.get('data', [])
        has_more = data.get('hasMore', False)
        
        for song in songs:
            simple_song = song.get('simpleSong', {})
            song_id = simple_song.get('id')
            if song_id:
                all_songs.append(song_id)
        
        # 实时显示扫描进度，使用\r来覆盖当前行
        print(f"\r已扫描到 {len(all_songs)} 首歌曲...", end='', flush=True)
        offset += 30
    
    # 扫描完成后换行并显示最终结果
    print()  # 换行
    total_songs = len(all_songs)
    print_with_time(f"共发现 {total_songs} 首歌曲", 'info')
    
    if total_songs == 0:
        print_with_time("云盘中没有歌曲", 'info')
        return
    
    deleted_count = 0
    
    if max_workers > 0:
        print_with_time(f"使用 {max_workers} 个线程进行删除", 'info')
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(delete_song, song_id) for song_id in all_songs]
            for future in as_completed(futures):
                if future.result():
                    deleted_count += 1
    else:
        print_with_time("使用单线程进行删除", 'info')
        for song_id in all_songs:
            if delete_song(song_id):
                deleted_count += 1
    
    print_header("删除操作完成")
    print_with_time(f"共计 {total_songs} 首歌曲", 'info')
    print_with_time(f"成功删除 {deleted_count} 首歌曲", 'success')

# 添加关注作者的函数
def follow_user(cookie):
    follow_url = f'http://localhost:3000/follow?id=1833949577&t=1&cookie={cookie}'
    try:
        response = requests.get(follow_url)
        data = response.json()
        if data.get('code') == 200:
            print_with_time("关注作者账号成功，cookie有效", 'success')
            return True
        elif data.get('code') == 201:
            print_with_time("已关注作者账号，cookie有效", 'success')
            return True
        else:
            print_with_time("关注作者失败："+response.text, 'warning')
            return False
    except Exception as e:
        print_with_time(f"关注请求出错: {str(e)}", 'error')
        return False

# 修改 main 函数
def main():
    print_header("网易云音乐云盘工具1.1.0")
    print("正在启动服务...")
    print("请确保已启动 NeteaseCloudMusicApi 服务")
    print_divider()
    print("【需要代挂进群联系】")
    print("【最新版Windows打包版见群文件】GitHub：https://github.com/Fckay/netease-cloud-music-uploader")
    print_divider()
    
    # 尝试读取已保存的 cookie
    cookie = read_cookie()
    
    if not cookie:
        print("没有找到有效的cookie，请选择登录方式：")
        print("1. 扫码登录（推荐）")
        print("2. 手动输入cookie")
        
        while True:
            choice = input("请输入选择（1或2）：").strip()
            if choice == "1":
                cookie = login()
                if cookie:
                    print_with_time("扫码登录成功")
                    follow_user(cookie)  # 添加关注作者
                    get_cloud_info(cookie)
                else:
                    print_with_time("扫码登录失败")
                    return
                break
            elif choice == "2":
                cookie = input_cookie()
                if "os=" in cookie:
                    cookie = cookie + "; " + 'os=pc;appver=3.4;'
                if cookie:
                    print_with_time("登录成功")
                    follow_user(cookie)  # 添加关注作者
                    get_cloud_info(cookie)
                else:
                    print_with_time("登录失败")
                    return
                break
            else:
                print("无效的选择，请重新输入")
    else:
        print("已从cookies.txt文件读取到cookie")
        follow_user(cookie)  # 添加关注作者
        get_cloud_info(cookie)

    while True:
        print_divider()
        print("请选择功能：")
        print("1. 网易音乐网盘导入")
        print("2. 网易音乐网盘删除")
        print("0. 退出程序")
        
        choice = input("请输入选择：").strip()
        
        if choice == "1":
            # 原有的导入功能代码
            wait_time = get_wait_time()
            upload_interval = get_upload_interval()
            max_workers = get_thread_settings()
            songs_data = read_songs_data()
            
            if songs_data:
                song_info_list = get_all_song_info(songs_data)
                uploaded_ids = read_uploaded_ids()
                if uploaded_ids:
                    if input("\n检测到上次上传的记录，是否继续上次的上传？(y/n): ").lower().strip() == 'y':
                        song_info_list = [song for song in song_info_list if str(song['id']) not in uploaded_ids]
                        print(f"过滤后还有 {len(song_info_list)} 首歌曲待上传")
                
                unique_songs = batch_get_song_details(song_info_list, cookie, max_workers=max_workers)
                if unique_songs:
                    process_songs(unique_songs, cookie, wait_time, upload_interval)
                else:
                    print("没有找到有效的歌曲信息")
            
        elif choice == "2":
            while True:
                print_divider()
                print("删除功能：")
                print("1. 删除未知歌曲")
                print("2. 删除全部歌曲")
                print("0. 返回上级菜单")
                
                sub_choice = input("请输入选择：").strip()
                
                if sub_choice in ["1", "2"]:
                    max_workers = get_thread_settings()  # 复用之前的线程设置函数
                    if sub_choice == "1":
                        delete_unknown_songs(cookie, max_workers)
                    else:
                        delete_all_songs(cookie, max_workers)
                    break
                elif sub_choice == "0":
                    break
                else:
                    print_with_time("无效的选择，请重新输入", 'warning')
        
        elif choice == "0":
            print_with_time("程序已退出", 'info')
            break
        
        else:
            print_with_time("无效的选择，请重新输入", 'warning')

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"程序发生错误: {str(e)}")
    finally:
        input("\n按回车键退出程序...")  # 添加这行确保用户能看到输出
