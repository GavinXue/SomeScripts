class MySQL226:
    host = "xxx"
    user = "xxx"
    password = "xxx"
    database = "xxx"
    db = 'xxx'
    port = 3306


class MySQL226Root:
    host = "xxx"
    user = "xxx"
    password = "xxx"
    database = "xxx"
    db = 'xxx'
    port = 3306


class Bj3Mysql:
    host = "xxx"
    user = "xxx"
    password = "xxx"
    database = "xxx"
    db = 'xxx'
    port = 3306


class Sensors:
    token = 'xxx'
    url = 'xxx'
    qa_url = 'qa_projects_SA_url'
    default_url = 'default_project_url'
    query_url = 'http://xxxxx.com:8007/api/sql/query'


class KuaiDiNiao:
    app_key = "xxxx"
    business_id = xxx
    url = "http://api.kdniao.cc/Ebusiness/EbusinessOrderHandle.aspx"


class EmailAccounts:
    internal = {
        "address": "xxx@xxx.com",
        "password": "xxx"
    }
    external = {
        "address": "xxx@xxx.com",
        "password": "xxx"
    }
    server = "smtp.exmail.qq.com"
    error_monitor_email = "xxx@xxx.com"


class Umeng:
    email = 'xxx@xxx.com'
    pwd = 'xxx@*'
    umeng_api = 'http://api.umeng.com'
    token = 'xxx'
    app_key = {'病历夹HD': 'xxx', '杏树林医学文献for android': 'xxx',
               '大话医学android': 'xxx', '杏树林医学文献': 'xxx'}


if __name__ == "__main__":
    test = PlatformConfig('production')
    print(test.login_name)
