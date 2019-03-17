import requests
import numpy as np
from config import Sensors
from mysql_connect import Connect
from datetime import date, timedelta
import json
from sd_send_email import send_mail
import sys, getopt


def obtain_monitor_event(id=None):
    if id:
        query_sql = "select id, event_name, where_condition, expectation, " \
                "standard_deviation, event_product, description, aggregator from xsl_sensors_data.track_event_monitor " \
                "where id in(%s) order by event_product" %id
    else:
        query_sql = "select id, event_name, where_condition, expectation, " \
                "standard_deviation, event_product, description, aggregator from xsl_sensors_data.track_event_monitor " \
                "where status = 1 order by event_product"
    conn = Connect()
    events = conn.sql_query(query_sql)
    conn.close_connect()
    return events


def update_E_and_SD(E_and_SD):
    update_sql = "update xsl_sensors_data.track_event_monitor " \
                 "set expectation = %s, standard_deviation = %s " \
                 "where id = %s "
    conn = Connect()
    try:
        conn.cursor.executemany(update_sql, E_and_SD)
        conn.connection.commit()
        conn.close_connect()
    except BaseException as e:
        print(e)
        conn.close_connect()
    

def calculate_E_and_SD(update=True, monitor_id=None):
    # 当传update值,进行均值和标准差更新
    print("进入更新均值和标准差更新过程")
    if update:
        from_date = (date.today() - timedelta(days=date.today().isoweekday()+7)).strftime('%Y-%m-%d')
        to_date = (date.today() - timedelta(days=date.today().isoweekday())).strftime('%Y-%m-%d')
        events = obtain_monitor_event(monitor_id)
        # 使用配置表中的event_name和conditions,注意event的index随obtain_monitor_event中的sql字段变化
        # 之后几行使用较多List下标, 注意变动影响
        results = [(id, obtain_event_from_sensors(event_name, aggregator, condition, from_date, to_date))
                   for (id, event_name, condition, e, sd, e_prod, desc, aggregator) in events]
        E_and_SD = []
        for result in results:
            if result[1]['rows']:
                result_values = [value[0] for value in result[1]['rows'][0]['values']]
            else:
                result_values = [0]
            E_and_SD.append((round(np.average(result_values),2), round(np.std(result_values),2), result[0]))
        update_E_and_SD(E_and_SD)
        print("全部事件每日期望值和标准差已更新!")
    else:
        pass


def obtain_event_from_sensors(event_name, aggregator, condition, from_date, to_date):
    url = Sensors.url + '/api/events/report?token=' + Sensors.token
    data = {
        "measures": [
            {
                "event_name": event_name,
                "aggregator": aggregator
            }
        ],
        "unit": "day",
        "from_date": from_date,
        "to_date": to_date
    }
    if condition:
        condition = json.loads(condition)
        data["filter"] = condition
       
    event_result = requests.post(url, json=data).json()
    return event_result


def generate_event_url(event_name, aggregator, condition):
    # 由于不懂SD的url拼接规则,只好按常规访问的url模仿
    from_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    to_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    url = Sensors.url + "/segmentation/#"
    tmp = "measures[0][event_name]={event_name}&measures[0][aggregator]={aggregator}&" \
          "unit=day&from_date={from_date}&to_date={to_date}"\
            .format(event_name=event_name, aggregator=aggregator,from_date=from_date,to_date=to_date)
    condition_str = ""
    if condition:
        condition = json.loads(condition)
        if 'relation' in condition:
            condition_str += "&filter[relation]={}".format(condition['relation'])
        for i in range(len(condition['conditions'])):
            # 这里当param同时出现几个时未做处理
            condition_str += "&filter[conditions][{}][field]={}" \
                             "&filter[conditions][{}][function]={}" \
                             .format(i, condition['conditions'][i]['field'],
                                     i, condition['conditions'][i]['function'])
            if 'params' in condition['conditions'][i]:
                for param in condition['conditions'][i]['params']:
                    condition_str += "&filter[conditions][{}][params][]={}".format(i,param)
    url = url + tmp + condition_str
    return url


def obtain_event_monitor_data(monitor_id=None):
    print("开始从SensorsData所需监控的数据;")
    events = obtain_monitor_event(monitor_id)
    from_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    to_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    # 注意从MySQL配置中取回的event顺序
    results = [(id, obtain_event_from_sensors(event_name, aggregator, condition, from_date, to_date))
               for (id, event_name, condition, e, sd, e_prod, desc, aggregator) in events]
    event_result_list= []
    for result in results:
        for event in events:
            if event[0] == result[0] and result[1]['num_rows'] == 1:
                # 拼接跳转的链接url
                link_url = generate_event_url(event[1],event[7], event[2])
                tmp_list = list(event)
                tmp_list[2] = result[1]['rows'][0]['values'][0][0]
                tmp_list.append(link_url)
                event_result_list.append(tuple(tmp_list))
            elif event[0] == result[0]:
                link_url = generate_event_url(event[1], event[7], event[2])
                tmp_list = list(event)
                tmp_list[2] = 0
                tmp_list.append(link_url)
                event_result_list.append(tuple(tmp_list))
    print("SensorsData所需监控的数据完成;")
    return event_result_list


if __name__ == '__main__':
    # 通过输入监控id来进行测试,同时传入测试的邮箱,发送给测试人数据, 如果测试则直接调用calculate_E_and_SD
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:e:", ["monitor_id=", "email="])
    except getopt.GetoptError:
        print('sd_track_monitor.py -i <monitor_id list> -e <email address>')
        sys.exit(2)
    
    if opts:
        args = []
        for opt, arg in opts:
            args.append(arg)
    if args:
        if len(args) != 2:
            print("请输入测试监控id和发送测试监控的邮箱。格式sd_track_monitor.py -i <monitor_id list> -e <email address>")
            sys.exit(2)
        print("进入埋点监控测试,测试id为{args[0]},发送测试邮箱为{args[1]}".format(args=args))
        calculate_E_and_SD(update=True, monitor_id=args[0])
        event_list = obtain_event_monitor_data(monitor_id=args[0])
        send_mail(event_list=event_list, email_list=args[1])
    
    else:
        event_list = obtain_event_monitor_data()
        if date.today().isoweekday() == 1:
            calculate_E_and_SD()
        send_mail(event_list=event_list, email_list="xx@xxx.com,xxx@xxx.com")
    