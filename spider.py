'''
v0.2
1. 把 main 改为 reply 请求, 以处理需要展开的子评论
2. 增加数据域: 时间, rpid, root
3. 修改 headers 和 csv_writer 为全局变量, 且 Cookie 从文件读取
4. aid 输入方式改为命令行参数

@Description:
    通过 https://api.bilibili.com/x/v2/reply/wbi/main? 请求获取B站某视频评论区的所有评论 (包括子评论)
    获取的评论信息包括: rpid (评论的唯一标识符); root (父级评论的 rpid, 如果没有则为 0); 时间; 用户的昵称, 性别, IP; 评论内容; 点赞数
    需要 Cookie.txt 文件
    输入视频 aid (oid)
    输出到 csv 文件 (默认以 aid 命名), 编码为带 BOM 的 UTF-8
@Author: July
@Time: 2024/3/2
@File: spider-bilibili_singleVideo_reply.py
'''
from urllib.parse import quote
import csv
import hashlib
import re
import requests
import sys
import time


'''
全局变量
'''
# get 请求的头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'Cookie': "",  #需要从文件读取
    'Referer':'https://www.bilibili.com/'
}
# csv 写入文件
csv_writer = None


def hash(oid, pagination_str, date, is_first):
    '''计算 w_rid
    :param oid:            oid
    :param pagination_str: 形如 {"offset":"..."}, "..." 中的双引号要转义
    :param date:           十位时间戳
    :param is_first:       是否是第一次请求, 用于判断是否包含 "seek_rpid="
    :return:               计算得到的 w_rid

    w_rid 需要 JS 逆向 md5(Jt + Wt), 其中 Jt = en.join("&"), Wt = "ea1db124af3c7062474693fa704f4ff8" 固定值
    '''
    if is_first == True:
        en=[
            "mode=2",
            "oid=%s" % oid,
            f"pagination_str={quote(pagination_str)}",
            "plat=1",
            "seek_rpid=",
            "type=1",
            "web_location=1315875",
            f"wts={date}",
        ]
    else:
        en=[
            "mode=2",
            "oid=%s" % oid,
            f"pagination_str={quote(pagination_str)}",
            "plat=1",
            "type=1",
            "web_location=1315875",
            f"wts={date}",
        ]
    Wt = "ea1db124af3c7062474693fa704f4ff8"
    Jt = '&'.join(en)
    string = Jt + Wt
    MD5 = hashlib.md5()
    MD5.update(string.encode('utf-8'))
    w_rid = MD5.hexdigest()
    return w_rid


def write_reply(reply):
    '''向 csv 文件中写入一条评论信息
    :param reply: replies 数组中的单个对象, 对应一条评论的信息

    不在本函数中处理子评论
    '''
    # 提取评论内容
    rpid = reply['rpid_str']  #评论标识符
    root = reply['root_str']  #对应主评论的 ripd, 主评论本身的 root 为 0
    rtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reply['ctime']))  #时间戳转格式化时间
    name = reply['member']['uname']  #昵称
    sex = reply['member']['sex']  #性别
    # location 可能不存在, 需要判空
    if 'location' in reply['reply_control']:
        location = reply['reply_control']['location'].replace('IP属地：', '')  #IP属地
    else:
        location = ''
    message = reply['content']['message'].replace('\n', '<br>')  #评论信息 (replace 替换换行符为<br>)
    like = reply['like']  #点赞数
    dit = {
            'rpid': rpid,
            'root': root,
            '时间': rtime,
            '昵称': name,
            '性别': sex,
            'IP': location,
            '评论': message,
            '点赞': like,
    }
    csv_writer.writerow(dit)

    return


def get_main(oid, next_offset, is_first):
    '''请求一次评论信息, 获取评论列表
    :param oid:         视频的 aid, 在请求中为 oid 参数
    :param next_offset: 下个 pagination_str 中的 offset 参数
    :param is_first:    是否是第一次请求, 用于判断是否包含 "seek_rpid="
    :return:            (replies, next_offset, is_end)
    '''
    date = str(int(time.time()))  #十位时间戳
    next_offset = next_offset.replace('"', '\\"')  #将双引号转义
    pagination_str = '{"offset":"%s"}' % (next_offset)  #生成 pagination_str
    w_rid = hash(oid, pagination_str, date, is_first)  #获取 w_rid
    # 准备 requests.get 请求的参数
    url = 'https://api.bilibili.com/x/v2/reply/wbi/main?'
    if is_first == True:
        data = {
            'oid': oid,
            'type': '1',
            'mode': '2',
            'pagination_str': pagination_str,
            'plat': '1',
            'seek_rpid': '',
            'web_location': '1315875',
            'w_rid': w_rid,
            'wts': date,
        }
        # 调试, 生成请求 URL, 可以直接在浏览器访问
        # print('[DEBUG] URL = ' + url + '&'.join([
        #     'oid=%s' % oid,
        #     'type=1',
        #     'mode=2',
        #     f"pagination_str={quote(pagination_str)}",
        #     'plat=1',
        #     'seek_rpid=',
        #     'web_location=1315875',
        #     f'w_rid={w_rid}',
        #     f'wts={date}',
        #     ])
        # )
    else:
        data = {
            'oid': oid,
            'type': '1',
            'mode': '2',
            'pagination_str': pagination_str,
            'plat': '1',
            'web_location': '1315875',
            'w_rid': w_rid,
            'wts': date,
        }
        # print('[DEBUG] URL = ' + url + '&'.join([
        #     'oid=%s' % oid,
        #     'type=1',
        #     'mode=2',
        #     f"pagination_str={quote(pagination_str)}",
        #     'plat=1',
        #     'web_location=1315875',
        #     f'w_rid={w_rid}',
        #     f'wts={date}',
        #     ])
        # )
    # 调用 main 接口, 获取 response
    response = requests.get(url=url, params=data, headers=headers)
    json_data = response.json()
    # 提取 replies
    replies = json_data['data']['replies']
    # 提取下一页的参数 next_offset (用于 pagination_reply)
    if 'next_offset' in json_data['data']['cursor']['pagination_reply']:
        next_offset = json_data['data']['cursor']['pagination_reply']['next_offset']
    else:
        next_offset = ''
    # 提取 is_end
    is_end = json_data['data']['cursor']['is_end']

    return replies, next_offset, is_end


def get_reply(oid, rpid):
    '''获取某 rpid 对应的评论及其所有子评论
    :param oid:  视频 oid
    :param rpid: 主评论的 rpid
    :return:     获取的所有评论数, 用于提示信息
    '''
    # 进行第一次请求, 获取主评论和第一页子评论
    url = 'https://api.bilibili.com/x/v2/reply/reply?'
    data = {
        'oid': oid,
        'type': '1',
        'root': rpid,
        'ps': 10,
        'pn': 1,
        'web_location': '333.788',
    }
    response = requests.get(url=url, params=data, headers=headers)
    json_data = response.json()
    if not json_data['data']:
        print("[Error] NoneType json_data['data']. json_data:")
        print(json_data)
        return 0
    # 写入主评论信息
    write_reply(json_data['data']['root'])
    # 获取初始 page 信息
    reply_total = json_data['data']['page']['count']
    page_num = json_data['data']['page']['num']
    page_size = json_data['data']['page']['size']
    # 遍历所有页, 获取并写入所有子评论
    reply_count = 0
    while reply_count < reply_total:
        for sub_reply in json_data['data']['replies']:
            write_reply(sub_reply)
            reply_count += 1
        if reply_count >= reply_total:
            break;
        data['pn'] += 1  #增加到下一页
        # 获取新的请求
        response = requests.get(url=url, params=data, headers=headers)
        json_data = response.json()

    return reply_count + 1  # reply_count 只记录了子评论数量, 要加上主评论


def print_getcontent_hint(time_delta, reply_cnt, reply_total_cnt, is_end):
    hint_str = '[%.3fs] get %d replies (total %d), is_end = %s' % (time_delta, reply_cnt, reply_total_cnt, is_end)
    print((len(hint_str) + 4) * '-')
    print('| ' + hint_str + ' |')
    print((len(hint_str) + 4) * '-')


if __name__ == '__main__':

    # 用户输入 aid
    # aid = input('请输入视频 aid (Please input aid of video): ')
    aid = sys.argv[1]

    # 读入 Cookie 到 headers
    with open('Cookie.txt', 'r', encoding='utf-8') as f:
        headers['Cookie'] = f.read().replace('\n', '')
    # print('[DEBUG] Cookie = %s' % headers['Cookie'])

    # 创建 csv 文件对象
    f = open('data/%s.csv' % aid, mode='w', encoding='utf_8_sig', newline='')  
    csv_writer = csv.DictWriter(f, fieldnames=[
        'rpid',
        'root',
        '时间',
        '昵称',
        '性别',
        'IP',
        '评论',
        '点赞',
    ])
    csv_writer.writeheader()

    # 获取评论信息, 写入 csv 文件
    next_offset = ''  #初始为空
    is_first = True  #用于判断 seek_rpid 的写入
    is_end = False  #用于判断评论是否翻完了
    reply_total_count = 0  #共计获取了多少评论, 用于提示信息输出
    while is_end == False:
        time_pre = time.time()  #记录当前时间, 用于输出提示信息
        # 获取新一页的主评论 rpid
        replies, next_offset, is_end = get_main(aid, next_offset, is_first)
        # 修改 is_first
        if is_first == True:
            is_first = False
        # 处理每个请求
        reply_count = 0
        for reply in replies:
            if reply['replies']:
                # 子评论不为空, 用 reply 请求
                reply_count += get_reply(aid, reply['rpid'])
            else:
                # 子评论为空, 直接处理
                write_reply(reply)
                reply_count += 1
        # 输出提示信息
        reply_total_count += reply_count
        print_getcontent_hint(time.time() - time_pre, reply_count, reply_total_count, is_end)
