# paris_olympic_2024
爬虫获取巴黎奥运会2024获奖明细数据

## 1 获取的数据展示
![奖牌明细数据](https://img-blog.csdnimg.cn/img_convert/75bb1266cf1af2962b552085f62f749e.webp?x-oss-process=image/format,png)

![基于明细数据统计过滤中国金牌数据](https://img-blog.csdnimg.cn/img_convert/484e6188be1bf4c04f26345713cae2d7.webp?x-oss-process=image/format,png)

![统计金牌榜](https://img-blog.csdnimg.cn/img_convert/7c91f4817e36682863cd8e6e9d640f90.webp?x-oss-process=image/format,png)

## 2 实现原理
网上查询了一圈，要么是付费接口，要么是残缺文章，一气之下自己开发实现，现将核心原理和代码发出来，方便需要的朋友。
> 原理
通过python爬取遍历爬取百度奖牌榜，xpath解析网页数据，并将获取的数据清洗入库到mysql。后面就可以随心统计展示了。

![数据网页截图](https://img-blog.csdnimg.cn/img_convert/ed67ef4be43fde53a04425847f9fc047.webp?x-oss-process=image/format,png)

## 3核心代码实现
#### 3.1获取金牌榜与获取国家ID数据列表
> 数据示例：
{'get_time': '2024-08-09 09:28:04', 'countryAbbr': 'ZAM', 'countryName': '赞比亚', 'delegationId': '151', 'gold': 0, 'silver': 0, 'total': 1, 'rank': 80}
> 数据说明：其中delegationId 为国家id号，gold 金牌数，silver 银牌，total 奖牌总数，rank 奖牌排名。

代码实现
```
def get_current_medalList():
    # 爬取的百度接口URL
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
```
#### 3.2 获取单个国家（例如：中国 id 为 29）奖牌数据明细列表
> 数据示例：
> {'id': '1a9a2bfdb9a015662622c4e674ca3d65', 'get_time': '08月08日', 'country': '中国', 'medal': '第28金', 'medalType': 'gold', 'playerName': '罗诗芳', 'smallMatch': '女子59公斤级', 'time': '23:05', 'bigMatch': '举重'}
> 数据说明: get_time 获奖日期，time 获奖时间，country 国家名字，playerName 运动员名称


代码实现
```
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
```
放回的html数据相对比较复杂，结构嵌套层数较多。程序代码中已经实现了解析过程，可忽略解析过程，直接摘取果实享用。

#### 3.3 奖牌数据明细写入关系型数据库，mysql
> 基于明细数据创建mysql表单
> 明细数据示例：{'id': '1a9a2bfdb9a015662622c4e674ca3d65', 'get_time': '08月08日', 'country': '中国', 'medal': '第28金', 'medalType': 'gold', 'playerName': '罗诗芳', 'smallMatch': '女子59公斤级', 'time': '23:05', 'bigMatch': '举重'}

mysql DDL参考：
```
-- colin.paris_2024 definition

CREATE TABLE `paris_2024` (
  `id` varchar(100) NOT NULL,
  `get_time` varchar(100) DEFAULT NULL,
  `country` varchar(100) DEFAULT NULL,
  `medal` varchar(100) DEFAULT NULL,
  `medalType` varchar(100) DEFAULT NULL,
  `playerName` varchar(100) DEFAULT NULL,
  `smallMatch` varchar(100) DEFAULT NULL,
  `time` varchar(100) DEFAULT NULL,
  `bigMatch` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```
代码实现
```
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
```


## 4 各个代码块调用main
需要python包
>import json
import requests
from lxml import etree
import datetime
import hashlib
import pymysql

main 函数
```
import json
import requests
from lxml import etree
import datetime
import hashlib
import pymysql

def  3.1 核心函数（copy到此）
def  3.2 核心函数（copy到此）
def  3.3 核心函数（copy到此）

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
```

## 5 数据展现
动态图实现，后续文章详细说明
![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/e7d1e0a88cc84c68a1119a6aae4419c1.png)

以上是整个巴黎奥运会奖牌数据获取实现原理和明细代码。
感谢给个关注，点个赞！


