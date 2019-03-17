import requests
from config import Bj3Mysql, Umeng
from mysql_connect import Connect
import sys, getopt
from datetime import date, timedelta


def obtain_oath_token(email, pwd, umeng_api='http://api.umeng.com'):
    params = {'email': email, 'password': pwd}
    return requests.post(umeng_api + '/authorize', params=params).json()['auth_token']


def obtain_app_key(token, umeng_api='http://api.umeng.com'):
    url = umeng_api + '/apps'
    param = {'auth_token': token}
    apps = requests.get(url, params=param).json()
    app_key = {}
    for app in apps:
        app_key[app['name']] = app['appkey']
    
    return app_key


def obtain_new_users(token, app_name, app_key, start_date, end_date, period_type='daily'):
    umeng_api = Umeng.umeng_api
    url = umeng_api + '/new_users'
    param = {'auth_token': token,
             'appkey': app_key,
             'start_date': start_date,
             'end_date': end_date,
             'period_type': period_type
             }
    new_users = requests.get(url, params=param).json()
    lens = len(new_users['dates'])
    result = list(zip([app_name]*lens, [period_type]*lens, new_users['dates'], new_users['data']['all']))
    return result


def obtain_active_users(token, app_name, app_key, start_date, end_date, period_type='daily'):
    umeng_api = Umeng.umeng_api
    url = umeng_api + '/active_users'
    param = {'auth_token': token,
             'appkey': app_key,
             'start_date': start_date,
             'end_date': end_date,
             'period_type': period_type
             }
    active_users = requests.get(url, params=param).json()
    lens = len(active_users['dates'])
    result = list(zip([period_type] * lens, active_users['dates'], active_users['data']['all']))
    return result
    
def obtain_active_and_new_users(token, app_name, app_key, start_date, end_date, period_type='daily'):
    umeng_api = Umeng.umeng_api
    new_user_url = umeng_api + '/new_users'
    param = {'auth_token': token,
             'appkey': app_key,
             'start_date': start_date,
             'end_date': end_date,
             'period_type': period_type
             }
    new_users = requests.get(new_user_url, params=param).json()

    active_user_url = umeng_api + '/active_users'
    param = {'auth_token': token,
             'appkey': app_key,
             'start_date': start_date,
             'end_date': end_date,
             'period_type': period_type
             }
    active_users = requests.get(active_user_url, params=param).json()

    lens = len(new_users['dates'])
    result = list(zip([period_type] * lens, new_users['dates'],
                      new_users['data']['all'], active_users['data']['all']))
    
    for i in range(len(result)):
        result[i] = app_name + result[i]
    
    print("Umeng获取%s, %s 数据成功" % app_name)
    return result
    

def update_to_stat(conn, insert_list, app_name, type, start_date, end_date):
    delete_sql = "delete from xsl_statistics.umeng_extractor where type = '%s' and app_name = '%s' and OS = '%s'" \
                 "and the_date BETWEEN '%s' and '%s'" %(type, app_name[0], app_name[1], start_date, end_date)
    
    update_sql = "insert into xsl_statistics.umeng_extractor(app_name, OS, type, the_date, new_users, active_users) " \
                 "VALUES (%s, %s, %s, %s, %s, %s)"
    
    try:
        print("开始更新%s, %s, 从%s 到 %s 的数据" %(app_name[0], app_name[1], start_date, end_date))
        conn.cursor.execute(delete_sql)
        conn.cursor.executemany(update_sql, insert_list)
        conn.connection.commit()
        print("%s, %s, 从%s 到 %s 的数据, 更新完成!" % (app_name[0], app_name[1], start_date, end_date))
    except BaseException as e:
        print("异常错误: " + str(e))


def generate_date(type):
    start_date, end_date = None, None
    if type == 'daily':
        start_date = (date.today() - timedelta(days=4)).strftime('%Y-%m-%d')
        end_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    elif type == 'weekly':
        start_date = (date.today() - timedelta(days=date.today().isoweekday()+6)).strftime('%Y-%m-%d')
        end_date = (date.today() - timedelta(days=date.today().isoweekday())).strftime('%Y-%m-%d')
    
    return start_date, end_date


if __name__ == '__main__':
    app_list = {'医口袋android': ('epocket', 'Android'), '医口袋': ('epocket', 'iOS'),
               '病历夹': ('medchart', 'iOS'), '病历夹android': ('medchart', 'Android'),
                '杏树林医学文献for android': ('literature', 'Android'),
                '杏树林医学文献': ('literature', 'iOS')}
    token = obtain_oath_token(Umeng.email, Umeng.pwd, Umeng.umeng_api)
    app_key = Umeng.app_key
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f", ["f="])
    except getopt.GetoptError:
        print('umeng_data_extractor.py -f <frequency>')
        sys.exit(2)
    
    type = args[0]
    print("进入Umeng数据更新,本次更新频率为%s" % type)
    start_date, end_date = generate_date(type)

    conn = Connect(Bj3Mysql)
    for key in app_list:
        insert_list = obtain_active_and_new_users(token, app_list[key], app_key[key], start_date, end_date, type)
        update_to_stat(conn, insert_list, app_list[key], type, start_date, end_date)
    
    conn.close_connect()