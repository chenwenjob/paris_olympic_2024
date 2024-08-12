import json
import requests
from lxml import etree
import datetime
import hashlib
import pymysql

def get_current_medalList():
    # 接口URL
    url = 'https://tiyu.baidu.com/al/major/home?page=home&match=2024%E5%B9%B4%E5%B7%B4%E9%BB%8E%E5%A5%A5%E8%BF%90%E4%BC%9A&tab=%E5%A5%96%E7%89%8C%E6%A6%9C'

    # 调用GET接口
    response = requests.get(url)

    # 调用POST接口
    # response = requests.post(url, data=data)

    html = etree.HTML(response.text)
    script_json = html.xpath('//script[@type="application/json"]')

    # 金牌数
    format_medalList = []

    for per in script_json[0:1]:
        json_str = json.loads(per.text)
        medalList = json_str['data']['data']['tabsList'][1]['data']['medalList'][0]
        # 获取时间
        current_time = json_str['data']['common']['requestStart']
        dt = datetime.datetime.fromtimestamp(current_time / 1000)
        new_dt = dt.strftime('%Y-%m-%d %H:%M:%S')

        # 当前获取奖牌数
        for list in medalList:
            format_list = {
                'get_time': new_dt,
                'countryAbbr': list['countryAbbr'],
                'countryName': list['countryName'],
                'delegationId': list['delegationId'],
                'gold': list['gold'],
                'silver': list['silver'],
                'total': list['total'],
                'rank': list['rank']
            }
            print(format_list)
            format_medalList.append(format_list)
            # medalList-seasonList
            # "本届奖牌榜",
            # "2020东京",
            # "2016里约热内卢",
            # "2012伦敦",
            # "2008北京",
            # "2004雅典",
            # "2000悉尼",
            # "1996亚特兰大",
            # "1992巴塞罗那"

    return format_medalList


def get_history_medalList(delegationId):
    # 接口URL
    url = 'https://tiyu.baidu.com/al/major/delegation?page=delegation&match=2024%E5%B9%B4%E5%B7%B4%E9%BB%8E%E5%A5%A5%E8%BF%90%E4%BC%9A&tab=%E8%8E%B7%E5%A5%96%E5%90%8D%E5%8D%95&id=' + delegationId

    # 调用GET接口
    response = requests.get(url)

    # 调用POST接口
    # response = requests.post(url, data=data)

    html = etree.HTML(response.text)
    script_json = html.xpath('//script[@type="application/json"]')

    output_data = []

    for per in script_json[0:1]:
        json_str = json.loads(per.text)
        # 0 赛程 1 获奖名单 2 运动员
        tabData = json_str['data']['data']['tabsList'][1]['data'][0]['tabData']

        # print(tabData)

        # 当前获取奖牌数
        for perdata in tabData:
            date_str = perdata['date']
            for data in perdata['dateList']:
                format_data = {
                    "id": hashlib.md5(str(date_str + data["country"] + data["playerName"]).encode('utf-8')).hexdigest(),
                    "get_time": date_str,
                    "country": data["country"],
                    "medal": data["medal"],
                    "medalType": data["medalType"],
                    "playerName": data["playerName"],
                    "smallMatch": data["smallMatch"],
                    "time": data["time"],
                    "bigMatch": data["bigMatch"]
                }
                print(format_data)
                output_data.append(format_data)

        return output_data

def import_mysql(data_list):

    host = 'your ip addr'
    port = 3306
    dbName = 'databasesName'
    user = 'user'
    password = 'yourPassword'
    db = pymysql.connect(host=host, port=port, user=user, passwd=password, db=dbName, charset='utf8')
    # 创建一个游标对象，通过游标对象来进行数据的增删改查。
    cursor = db.cursor()
    num = 0

    for data in data_list:
        id = data['id']
        get_time = data['get_time']
        country = data['country']
        medal = data['medal']
        medalType = data['medalType']
        playerName = data['playerName']
        smallMatch = data['smallMatch']
        time_data = data['time']
        bigMatch = data['bigMatch']

        # 构造insert into 语句，使用到了format 占位符
        sql = "replace INTO colin.paris_2024(id, get_time, country, medal, medalType, playerName, smallMatch, `time`, bigMatch)VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(id, get_time, country, medal, medalType, playerName, smallMatch, time_data, bigMatch)
        # print("当前时间戳===", sql)
        cursor.execute(sql)
        num=num+1
        #提交事务
    db.commit()
    cursor.close()
    db.close()
    print("输入条数",num)


if __name__ == '__main__':
    # 获取当天数据，包含delegationId
    format_medalList = get_current_medalList()
    all_data=[]

    # 遍历获取历史数据
    for medalList in format_medalList:
        delegationId = medalList['delegationId']

        # print(delegationId)
        # 遍历国家 获奖信息

        output_data = get_history_medalList(delegationId)
        all_data.extend(output_data)

    # 写入数据库
    import_mysql(all_data)

    print("写入完成")

