import os
import json
import subprocess
import shutil
import time
import configparser
import sys


config = configparser.ConfigParser()

config["ALL"] = {
    "windows_cache_path":"",
    "andorid_cache_path":"",
    "windows_output_path":"windows_output", 
    "android_output_path":"android_output",
    "windows_parse_offset":9,
    "android_parse_offset":0
}

config_note =[
    "# 在windows_cache_path=后输入windows版应用的缓存路径",
    "# 在andorid_cache_path=后输入android版应用的缓存路径",
    "# 在windows_output_path=后输入windows版提取视频的输出路径",
    "# 在android_output_path=后输入android版提取视频的输出路径",
    "# 在windows_parse_offset=后输入windows版视频解析时应删除的十六进制位数，默认9",
    "# 在android_parse_offset=后输入android版视频解析时应删除的十六进制位数，默认0"
]


def check_ffmpeg():
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            return True
        else:
            return False
    except FileNotFoundError:
        return False

def get_ffmpeg_path():
    """获取 ffmpeg.exe 的路径，兼容打包和未打包情况"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的 exe，数据文件在临时目录 sys._MEIPASS 下
        base_dir = sys._MEIPASS
    else:
        # 如果是直接运行脚本，数据文件在当前目录下
        base_dir = os.path.dirname(os.path.abspath(__file__))

    ffmpeg_path = os.path.join(base_dir, "ffmpeg.exe")
    return ffmpeg_path

# 配置读取
def get_config():
    config.read('config.ini')
    option = config["ALL"]
    return option


# 配置生成
def set_config():
    with open('config.ini', 'w') as cf:
        for i in config_note:
            cf.write(i +"\n")
        config.write(cf)


# 错误信息处理
def error_info(output_path,path,content):
    with open(output_path + '/error.log', 'a+') as f:
        log = content + f":{path}\n"
        f.write(log)

# windows文件夹非法字符串替换  
def replace_windows_path(path):
    return path.replace("\\", "-").replace(":", "").replace("*", "").replace("?", "").replace("\"", "").replace("<", "").replace(">", "").replace("|", "").replace("/", "")



# 清除临时文件
def clean_temp():
    if os.path.exists('temp'):
        shutil.rmtree('temp')
    if not os.path.exists("temp"):
        os.mkdir("temp")


# 处理视频文件二进制数据
def video_parse_android(inpath,outpath):
    # 处理非加密数据
    try:
        shutil.copy(inpath, outpath)
        return True
    except:
        return 'video_parse error'


def video_parse_windows(inpath,outpath):
    option = get_config()
    #处理加密数据
    try:
        with open(inpath, 'rb') as f1:
            with open(outpath, 'wb+') as f2:
                f2.write(f1.read()[int(option["windows_parse_offset"]):])
        return True
    except:
        return 'video_parse error'


# 合并音视频
def output_video(ffmpeg_path,path1,path2,path3):
    try:
        cmd = f"\"{ffmpeg_path}\" -i \"{path1}\" -i \"{path2}\" -codec copy \"{path3}\""
        # cmd = '"ffmpeg.exe" -i "' + path1 + '" -i "' + path2 + '" -codec copy "' + path3 + '"'
        res = subprocess.Popen(cmd,shell=False)
        # os.popen(cmd)
        # ffmpeg结束后退出
        res.communicate()
        res.kill()
        return True
    except:
        return "video output error"


# 批量提取Windows客户端缓存视频
def get_windows_cache_video(ffmpeg_path):
    option = get_config()
    windows_cache_path = option["windows_cache_path"]
    videoinfo_json_files = get_videoinfo_path(windows_cache_path)

    n = len(videoinfo_json_files)

    if not os.path.exists(option["windows_output_path"]):
        os.mkdir(option["windows_output_path"])
    
    i = 0
    e = 0
    while i < n:
        try:
            videoinfo_json = get_windows_cache_file_info(videoinfo_json_files[i])

            print(f"第{i+1}个视频：{videoinfo_json["groupTitle"]}-{videoinfo_json["p"]}")

            target_path = option["windows_output_path"] + "/" + replace_windows_path(videoinfo_json["groupTitle"]) + str(videoinfo_json["groupId"])

            if not os.path.exists(target_path):
                os.mkdir(target_path)
            
            m4s_files = get_windows_cache_file_path(videoinfo_json_files[i])
            
            video_parse_result_1 = video_parse_windows( m4s_files[0], 'temp/' + os.path.basename(m4s_files[0]))
            video_parse_result_2 = video_parse_windows( m4s_files[1], 'temp/' + os.path.basename(m4s_files[1]))
            if video_parse_result_1 != True or video_parse_result_2 != True:
                error_info(option["windows_output_path"],videoinfo_json_files[i],video_parse_result_1)
                e += 1
            output_result = output_video(ffmpeg_path,'temp/' + os.path.basename(m4s_files[0]),'temp/' + os.path.basename(m4s_files[1]), target_path + "/video-" + str(videoinfo_json["p"]) +".mp4")
            if output_result != True:
                error_info(option["windows_output_path"],videoinfo_json_files[i],output_result)
                e += 1 
        except:
            error_info(option["windows_output_path"],videoinfo_json_files[i],"")
            e += 1

        if os.path.exists('temp/' + os.path.basename(m4s_files[0])):
            os.remove('temp/' + os.path.basename(m4s_files[0]))
        if os.path.exists('temp/' + os.path.basename(m4s_files[1])):
            os.remove('temp/' + os.path.basename(m4s_files[1])) 

        i += 1
    
    print(f"{n}个视频处理完成,失败{e}个，失败信息已写入{option["windows_output_path"]}\\error.log日志")


def get_videoinfo_path(windows_cache_path):
    videoinfo_json_files = []
    for root, dirs, files in os.walk(windows_cache_path):
        # 检查当前目录中是否存在videoInfo.json文件
        if 'videoInfo.json' in files:
            # 构建完整文件路径并添加到结果列表
            file_path = os.path.join(root, 'videoInfo.json')
            videoinfo_json_files.append(file_path)

    return videoinfo_json_files

def get_windows_cache_file_info(videoinfo_json_file):
    try:
        with open(videoinfo_json_file, 'r', encoding='utf-8') as f:
            videoinfo_json = json.loads(f.read())
        return videoinfo_json
    except :
        print(f"错误：解析JSON文件时出错")
        return "get file info error"

def get_windows_cache_file_path(videoinfo_json_file):

    m4s_files = []
    for root, dirs, files in os.walk(os.path.dirname(videoinfo_json_file)):
        for file in files:
            if file.endswith(".m4s"):
                m4s_files.append(os.path.join(root, file))
    return m4s_files


# 批量提取Android客户端缓存视频
def get_android_cache_video(ffmpeg_path):
    option = get_config()
    android_cache_path = option["andorid_cache_path"]
    entry_json_files = get_entry_path(android_cache_path)
    
    n = len(entry_json_files)
    
    if not os.path.exists(option["android_output_path"]):
        os.mkdir(option["android_output_path"])

    i = 0
    e = 0
    while i < n:
        try:
            cache_file_info = get_android_cache_file_info(entry_json_files[i])
            cache_file_path = get_cache_file_path(cache_file_info)

            print(f"第{i+1}个视频：{cache_file_info[0]["title"]}-{cache_file_info[0]["page_data"]["cid"]}")
            
            video_parse_result_1 = video_parse_android( cache_file_path[0], 'temp/' + os.path.basename(cache_file_path[0]))
            video_parse_result_2 = video_parse_android( cache_file_path[1], 'temp/' + os.path.basename(cache_file_path[1]))
            if video_parse_result_1 != True or video_parse_result_2 != True:
                error_info(option["android_output_path"],entry_json_files[i],video_parse_result_1)
                e += 1
            
            # target_path = option["android_output_path"] + "/" + replace_windows_path(cache_file_info[0]["title"]) + "_" + str(cache_file_info[0]["page_data"]["cid"])
            target_path = option["android_output_path"] + "/" + replace_windows_path(cache_file_info[0]["title"])
            if not os.path.exists(target_path):
                os.mkdir(target_path)

            shutil.copy(entry_json_files[i], target_path + "/entry-"+ str(cache_file_info[0]["page_data"]["cid"]) +".json")

            output_result = output_video(ffmpeg_path,'temp/audio.m4s','temp/video.m4s',target_path + "/video-" + str(cache_file_info[0]["page_data"]["cid"]) +".mp4")
            if output_result != True:
                error_info(option["android_output_path"],entry_json_files[i],output_result)
                e += 1
        except:
            error_info(option["android_output_path"],entry_json_files[i],"")
            e += 1
            
        if os.path.exists('temp/audio.m4s'):
            os.remove('temp/audio.m4s')
        if os.path.exists('temp/video.m4s'):
            os.remove('temp/video.m4s') 
        
        i += 1

    print(f"{n}个视频处理完成,失败{e}个,失败信息已写入{option["android_output_path"]}\\error.log日志")
        

def get_entry_path(android_cache_path):
    entry_json_files = []
    for root, dirs, files in os.walk(android_cache_path):
        # 检查当前目录中是否存在entry.json文件
        if 'entry.json' in files:
            # 构建完整文件路径并添加到结果列表
            file_path = os.path.join(root, 'entry.json')
            entry_json_files.append(file_path)

    return entry_json_files


def get_android_cache_file_info(entry_json_file):
    try:
        # 获取prefered_video_quality字段的值[5](@ref)
        with open(entry_json_file, 'r', encoding='utf-8') as f:
            entry_json = json.loads(f.read())
        cache_folder_name = str(entry_json['prefered_video_quality'])
        if not cache_folder_name:
            print(f"警告：文件 '{entry_json}' 中未找到 'prefered_video_quality' 字段或该字段为空")
            return None
        
        # 获取entry.json文件所在的目录路径
        entry_dir = os.path.dirname(entry_json_file)

        # 构建目标文件夹的完整路径
        cache_path = os.path.join(entry_dir, cache_folder_name)
        
        
        # 检查路径是否存在（可选）
        if not os.path.exists(cache_path):
            print(f"警告：路径 '{cache_path}' 不存在")
        
        # video_name = str(entry_json['title'])
        # print(f"视频名称：{video_name}")
        
        return entry_json,cache_path

    except :
        print(f"错误：解析JSON文件 '{entry_json}' 时出错")
        return None


def get_cache_file_path(cache_file_info):

    cache_path = cache_file_info[1]
    if cache_file_info != None:
        cache_video_path = cache_path + '/video.m4s'
        cache_audio_path = cache_path + '/audio.m4s'
        return cache_video_path,cache_audio_path


# 菜单
def menu():
    ffmpeg_path = get_ffmpeg_path()
    if check_ffmpeg:
        ffmpeg_path = "ffmpeg.exe"
    else:
        if not os.path.exists(ffmpeg_path):
            print("ffmpeg not found！")
            tstr = input("\n按回车键退出...")
            return
    if not os.path.exists("config.ini"):
        set_config()
        res = subprocess.Popen(["notepad", "config.ini"])
    while True:
        os.system('cls')
        print(
            "\n\033[1;35;40mBilibli缓存视频提取MP4\033[0m\n\n" +
            "功能选择：\n" +
            "1. 批量提取Windows客户端缓存视频\n" +
            "2. 批量提取Android客户端缓存视频\n" +
            "3. 修改配置文件\n" +
            "4. 重置配置文件\n" +
            "5. 说明\n" +
            "0. 清除临时文件\n\n" +
            
            "-"*50+"\n"
        )
        choice = input("输入序号选择对应功能：")
        match choice:
            case '1':
                clean_temp()
                get_windows_cache_video(ffmpeg_path)
                tstr = input("\n按回车键返回主菜单...")
                continue
            case '2':
                clean_temp()
                get_android_cache_video(ffmpeg_path)
                tstr = input("\n按回车键返回主菜单...")
                continue
            case '3':
                res = subprocess.Popen(["notepad", "config.ini"])
                continue
            case '4':
                set_config()
                res = subprocess.Popen(["notepad", "config.ini"])
                continue
            case '5':
                os.system('cls')
                print(
                    "- 若运行Pyhon脚本需下载ffmpeg，配置环境变量或将脚本放入ffmpeg.exe同文件夹运行\n" +
                    "- 先在config.ini中进行路径配置\n" +
                    "- 手动转换方法：找到音频和视频的m4s放同一文件夹，在该文件打开命令提示符输入如下命令\n" +
                    "- 示例：ffmpeg.exe -i \"audio.m4s\" -i \"video.m4s\" -codec copy \"output.mp4\"\n" 
                )
                tstr = input("\n按回车键返回主菜单...")
                continue
            case '0':
                clean_temp()
                print("\n临时文件已删除！")
                time.sleep(1)
                continue


# Main function
if __name__ == '__main__':
    menu()