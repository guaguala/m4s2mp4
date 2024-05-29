import os
import json
import subprocess
import shutil
import time
import sys


# 获取配置信息
def get_settings(settings_file_path):

    if not os.path.exists(settings_file_path):
        with open(settings_file_path, 'w') as f:
            f.write("在cache_path=后输入bilibili应用的缓存路径，在target_path=后输入视频保存路径\ncache_path=\ntarget_path=")
    else:
        settings = {}
        try:
            with open(settings_file_path, 'r',encoding='utf-8') as f:
                settings_lst = f.readlines()
                for item in settings_lst:
                    if item.strip().split('=')[0] == 'cache_path':
                        settings['input_dir'] = item.strip().split('=')[1]
                    if item.strip().split('=')[0] == 'target_path':
                        settings['output_dir'] = item.strip().split('=')[1]
            if not os.path.exists(settings['input_dir']) or not os.path.exists(settings['output_dir']):
                print("\n\033[1;31;40m配置文件路径不存在！\033[0m\n")
                sys.exit(1)
            return settings
        except:
            print("\n\033[1;31;40m配置文件读取错误！\033[0m\n")
            sys.exit(1)
        
        
# 获取文件路径
def get_file_path(path):

    info_path_lst = []      # 视频信息文件列表
    video_path_lst = []     # 音视频文件列表

    for p,dir_lst,file_lst in os.walk(path):
        for item in file_lst:
            if item == '.videoInfo':
                info_path_lst.append(os.path.join(p,item))
            elif  item.split('.')[-1] == 'm4s':
                video_path_lst.append(os.path.join(p,item))

    return info_path_lst,video_path_lst


# 获取视频信息
def get_video_info(video_info_path):

    video_info = {}
    try:
        with open(video_info_path, 'r', encoding='utf8') as file:
            video_dict = json.loads(file.read())
            video_info['itemId'] = video_dict_info('itemId',video_dict)
            video_info['title'] = video_dict_info('title', video_dict)
            video_info['groupTitle'] = video_dict_info('groupTitle', video_dict)
            video_info['groupId'] = video_dict_info('groupId', video_dict)
            video_info['p'] = video_dict_info('p', video_dict)
    except:
        print("\n\033[1;31;40m获取视频信息出错！\033[0m\n")
        sys.exit(1)

    return video_info


# 判断视频信息是否存在group_info文件中
def video_dict_info(key, video_dict):
    if key in video_dict:
        return video_dict[key]
    else:
        return ''


# 创建group文件夹并return
# def create_group_dir(group_info_dict, path):
#     try:
#         if str(group_info_dict['groupTitle']).strip() != '':
#             group_dir_path = path + '/' + str(group_info_dict['groupTitle']).strip()
#             if not os.path.exists(group_dir_path):
#                 os.mkdir(group_dir_path)
#             return group_dir_path
#     except:
#         if str(group_info_dict['groupId']).strip() != '':
#             group_dir_path = path + '/' + str(group_info_dict['groupId']).strip()
#             if not os.path.exists(group_dir_path):
#                 os.mkdir(group_dir_path)
#             return group_dir_path
#     return False

def create_group_dir(dir_path):
    try:
        if str(dir_path).strip() != '':
            if not os.path.exists(dir_path):
                os.mkdir(dir_path)
            return dir_path
    except:
        return ''



# 处理视频文件二进制数据
def video_parse(inpath,outpath):
    try:
        with open(inpath, 'rb') as f1:
            with open(outpath, 'wb+') as f2:
                f2.write(f1.read()[9:])
        return True
    except:
        return 'video_parse'
    

# 合并生成视频
def output_video(path1,path2,path3):
    try:
        cmd = '"ffmpeg.exe" -i "' + path1 + '" -i "' + path2 + '" -codec copy "' + path3 + '"'
        res = subprocess.Popen(cmd,shell=False)
        # os.popen(cmd)
        # ffmpeg结束后退出
        res.communicate()
        res.kill()
        return True
    except:
        return 'output_video'


# 错误信息处理
def output_error_info(output_dir,error_info):
    try:
        with open(output_dir + '/error.log', 'a+') as f:
            f.write(error_info + '\n')
        print("\n\033[1;31;40m视频处理错误信息已写入error.log！\033[0m")
    except:
        print("\033[1;31;40m视频处理错误信息写入失败！\033[0m")


# 清理临时文件
def clean_temp():
    shutil.rmtree('temp')


################################################################


''' 
一、批量提取视频并按照视频集合归类：
1. 文件处理
2. 视频处理
3. 视频整理
'''
def get_groups_videos():

    settings_file_path = 'settings.ini'

    # 读取配置文件
    settings = get_settings(settings_file_path)
    # 创建临时文件夹
    if not os.path.exists('temp'):
        os.mkdir('temp')

    # 生成groups_info文件
    info_path_lst,video_path_lst = get_file_path(settings['input_dir'])  # 获取视频信息文件路径、音视频文件路径
    groups_info_path = settings['output_dir'] + "/groups_info.txt"  # 获取groups_info.txt的地址
    groups_info_file = open(groups_info_path,'a+',encoding='utf-8')
    for item in info_path_lst:  # 读取每个视频的.videoInfo文件
        groups_info_file.write(json.dumps(get_video_info(item))+'\n')
    groups_info_file.close()
    print('\033[1;35;40m视频信息已写入groups_info.txt\033[0m')

    # 根据groups_info生成文件夹和group_info文件
    group_dir_path_lst = [] # 组文件夹地址列表
    if os.path.exists(groups_info_path):
        groups_info_file = open(groups_info_path,'r',encoding='utf-8')
        m = 1
        while True:
            line = groups_info_file.readline()
            if line == '':
                break
            elif line.strip()[0:7] == 'missing':
                continue
            group_dir_path = settings['output_dir'] + '/' + json.loads(line.strip())['groupTitle']
            if create_group_dir(group_dir_path) == '':
                group_dir_path = settings['output_dir'] + '/' + json.loads(line.strip())['groupId']     
            if group_dir_path != '':
                group_dir_path_lst.append(group_dir_path)
                try:
                    with open(group_dir_path+'/group_info.txt', 'a+',encoding='utf-8') as f:
                        f.write(str(json.loads(line))+'\n')

                    print("\r", end="")
                    print("\033[1;35;40m已处理信息文件: {}\033[0m".format(m), end="")
                    sys.stdout.flush()

                except:
                    print('\033[1;31;40m处理第'+ str(m) +'个group_info.txt出错！\033[0m')
                m += 1
        groups_info_file.close()

    # 复制处理m4s文件到目标文件夹
    if os.path.exists(groups_info_path):
        groups_info_file = open(groups_info_path,'r',encoding='utf-8')
        m = 1
        while True:
            line = groups_info_file.readline()
            if line == '':
                break
            elif line.strip()[0:7] == 'missing':
                continue
            video_part_lst = []
            for video_path in video_path_lst:
                if os.path.basename(os.path.dirname(video_path)) == str(json.loads(line)['itemId']).strip():
                    video_part_lst.append(video_path)
            if len(video_part_lst) == 2:
                # 复制原始视频到临时文件夹
                output_video_dir_path = ''
                if os.path.exists(settings['output_dir'] + '/' + str(json.loads(line)['groupTitle']).strip()):
                    output_video_dir_path = settings['output_dir'] + '/' + str(json.loads(line)['groupTitle']).strip()
                elif os.path.exists(settings['output_dir'] + '/' + str(json.loads(line)['groupId']).strip()):
                    output_video_dir_path = settings['output_dir'] + '/' + str(json.loads(line)['groupId']).strip()
                if output_video_dir_path != '':
                    output_video_path_1 = output_video_dir_path + '/' + str(json.loads(line)['p']).strip() + '-' + str(json.loads(line)['title']).strip() + '.mp4'
                    output_video_path_2 = output_video_dir_path + '/' + str(json.loads(line)['p']).strip() + '-' + str(json.loads(line)['itemId']).strip() + '.mp4'
                    video_parse_result_1 = video_parse( video_part_lst[0], 'temp/' + os.path.basename(video_part_lst[0]))
                    video_parse_result_2 = video_parse( video_part_lst[0], 'temp/' + os.path.basename(video_part_lst[1]))
                    if not (video_parse_result_1 and video_parse_result_2):
                        output_error_info(settings['output_dir'], str(json.loads(line)))
                        continue
                    # 视频合成
                    output_result = output_video('temp/' + os.path.basename(video_part_lst[0]),'temp/' + os.path.basename(video_part_lst[1]),output_video_path_1)
                    if not output_result:
                        output_result = output_video('temp/' + os.path.basename(video_part_lst[0]),'temp/' + os.path.basename(video_part_lst[1]),output_video_path_2)
                    else:
                        output_error_info(settings['output+_dir'], str(json.loads(line)))
                        continue
                    # 清理临时文件
                    if os.path.exists('temp/' + os.path.basename(video_part_lst[0])) and os.path.exists('temp/' + os.path.basename(video_part_lst[1])):
                        os.remove('temp/' + os.path.basename(video_part_lst[0]))
                        os.remove('temp/' + os.path.basename(video_part_lst[1])) 
                else:
                    print('\033[1;31;40m获取output_video_dir_path失败:'+ str(json.loads(line)['groupId']).strip() +'\033[0m')
                m += 1
            else:
                output_error_info(settings['output_dir'], str(json.loads(line)))
                continue
        # 清理临时文件
        shutil.rmtree('temp')

'''
二、提取单个视频
'''
def get_one_video(inpath,outpath):
    
    # 创建临时文件夹
    if not os.path.exists('temp'):
        os.mkdir('temp')

    video_part_lst = []
    video_info_path = ''
    
    for p,dir_lst,file_lst in os.walk(inpath):
        for item in file_lst:
            if item == '.videoInfo':
                video_info_path = os.path.join(p,item)
            elif  item.split('.')[-1] == 'm4s':
                video_part_lst.append(os.path.join(p,item))
    
    video_info = get_video_info(video_info_path)
    # 复制视频信息文件
    shutil.copy(video_info_path,outpath + '/video_info.txt')
    print("\033[1;35;40m已处理信息文件: " + video_info_path,outpath + "/video_info.txt\033[0m")

    if len(video_part_lst) == 2:
        video_parse( video_part_lst[0], 'temp/' + os.path.basename(video_part_lst[0]))
        video_parse( video_part_lst[1], 'temp/' + os.path.basename(video_part_lst[1]))

        output_video_path_1 = outpath + '/' + str(video_info['title']) + '.mp4'
        output_video_path_2 = outpath + '/' + str(video_info['itemId']) + '.mp4'

        try:
            if os.path.exists('temp/' + os.path.basename(video_part_lst[0])) and os.path.exists('temp/' + os.path.basename(video_part_lst[1])):
                output_result = output_video(
                    'temp/' + os.path.basename(video_part_lst[0]),
                    'temp/' + os.path.basename(video_part_lst[1]),
                    output_video_path_1
                    )
                if output_result == True:
                    print("\033[1;35;40m已处理视频: " + output_video_path_1 + "\033[0m")
        except:
            if os.path.exists('temp/' + os.path.basename(video_part_lst[0])) and os.path.exists('temp/' + os.path.basename(video_part_lst[1])):
                # 视频输出
                output_result = output_video(
                    'temp/' + os.path.basename(video_part_lst[0]),
                    'temp/' + os.path.basename(video_part_lst[1]),
                    output_video_path_2
                    )
                if output_result == True:
                    print("\033[1;35;40m已处理视频: " + output_video_path_2 + "\033[0m")
            # 清理临时文件
        if os.path.exists('temp/' + os.path.basename(video_part_lst[0])) and os.path.exists('temp/' + os.path.basename(video_part_lst[1])):
            os.remove('temp/' + os.path.basename(video_part_lst[0]))
            os.remove('temp/' + os.path.basename(video_part_lst[1]))    


'''
菜单
'''
def menu():
    while True:
        os.system('cls')
        print(
            # "\n"+"-"*50+"\n" +
            "\n\033[1;35;40mBilibli缓存视频提取MP4\033[0m\n\n" +
            "功能选择：\n" +
            "1. 批量提取视频并按照视频集合归类\n" +
            "2. 提取单个视频\n" +
            "3. 说明和注意事项\n" +
            "0. 清除临时文件\n" +
            "-"*50+"\n"
        )
        choice = input("输入序号选择对应功能：")
        if choice == '1':
            os.system('cls')
            get_groups_videos()
            print("\n\033[1;35;40m已处理完成！回车键返回菜单\033[0m\n\n")
            tmp = input()
            continue
        elif choice == '2':
            os.system('cls')
            inpath = input("请输入视频所在目录路径：")
            outpath = input("请输入要提取到的目录路径：")
            if os.path.exists(inpath) and os.path.exists(outpath):
                get_one_video(inpath,outpath)
                print("\n\033[1;35;40m已处理完成！回车键返回菜单\033[0m\n\n")
                tmp = input()
            else:
                print("\n\033[1;35;40m请输入正确路径！\033[0m")
                time.sleep(1)
            continue
        elif choice == '3':
            os.system('cls')
            print(
                "\n- 确保已下载ffmpeg\n" + 
                "- 将ffmpeg配置环境变量或将本程序放在ffmpeg的bin目录下\n" +
                "- 批量处理需先在settings.ini文件中填写文件夹路径\n" +
                "- 路径含有中文可能会带来问题\n" +
                "- 建议创建一个单独的空文件夹作为存放视频的路径\n" +
                "- 按住ctrl+c终止程序运行\n"
                "\n\033[1;35;40m回车键返回菜单\033[0m\n"
            )
            tmp = input()
            continue
        elif choice == '0':
            shutil.rmtree('temp')
            continue
        else:
            print("\n\033[1;35;40m请输入正确的序号！\033[0m")
            time.sleep(1)
            continue


# Main function
if __name__ == '__main__':
    menu()