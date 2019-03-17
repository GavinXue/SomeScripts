import dateutil.parser
from mysql_connect import Connect
from config import Bj3Mysql
import requests
from datetime import datetime, timedelta
import time
from pytz import timezone


def convert_timezone(time_arg):
    if time_arg:
        time_arg = dateutil.parser.parse(time_arg)
        au_tz = timezone('Asia/Shanghai')
        tmp_time = time_arg.astimezone(au_tz)
        time_arg = datetime.strftime(tmp_time, '%Y-%m-%d %H:%M:%S ')
    else:
        time_arg = None

    return time_arg


def obtain_project_list(token):
    headers = {
        "Content-Type": "application/json",
        "access_token": token
    }
    result = requests.get("https://api.worktile.com/v1/projects", headers=headers).json()
    team_project = list(map(lambda x: (x["team_id"], x["pid"]), result))
    # if someone wanna filter project is not private, add if x['visibility'] != 1 else None to above lambda
    # team_project = list(filter(lambda x: x, tmp))
    return team_project


def obtain_token(connect):
    content = connect.sql_query('select code, access_token, token_time, refresh_token,'
                          'client_id, app_secret from xsl_mada.worktile_token where id=1')[0]

    t = datetime.now() - content[2]
    is_expire = timedelta(days=t.days, seconds=t.seconds).total_seconds()

    if is_expire < 7770000:
        return content[1], content[4]

    else:
        headers = {
            "Content-Type": "application/json",
            "refresh_token": content[3],
            "client_id": content[4]
        }
        results = requests.get('https://api.worktile.com/oauth2/refresh_token', headers=headers)

        token_data = results.json()
        update_sql = "update xsl_mada.worktile_token set access_token = '%s', refresh_token = '%s'," \
                     "token_time = '%s' where id = 1" % (token_data["access_token"], token_data["refresh_token"],
                                                         time.strftime('%Y-%m-%d %H:%M:%S'))
        connect.cursor.execute(update_sql)
        connect.connection.commit()
        connect.cursor.nextset()
        return token_data["access_token"], content[4]


def obtain_insert_list(token, team_id, project_id):
    headers = {
        "content_type": "application/json",
        "access_token": token
    }

    team_result = requests.get("https://api.worktile.com/v1/teams/" + team_id, headers=headers).json()

    if team_id == '-1':
        team_result['team_id'] = '-1'
        team_result['name'] = '未建立团队'

    pid_header = {
        "content_type": "application/json",
        "access_token": token
    }
    task_result = requests.get("https://api.worktile.com/v1/tasks?pid=" + project_id, headers=pid_header).json()

    insert_list = []
    relation_insert_list = []
    tid_list = []

    count = 0
    for task in task_result:
        task_insert_value = team_result['team_id'], team_result['name'], task['pid'], task['project']['name'], \
                            task['tid'], task['name'], task['desc'], \
                            convert_timezone(task['created_at']), convert_timezone(task['expire_date']), \
                            task['completed'], convert_timezone(task['completed_date']), task['archived']

        insert_list.append(task_insert_value)
        tid_list.append(str(task['tid']))
        count += 1

        for label in task['labels']:
            label_insert_value = task['tid'], 'label', label['desc']
            relation_insert_list.append(label_insert_value)

        for watcher in task['watchers']:
            watcher_insert_value = task['tid'], 'watcher', watcher['display_name']
            relation_insert_list.append(watcher_insert_value)

        for member in task['members']:
            executor_insert_value = task['tid'], 'executor', member['display_name']
            relation_insert_list.append(executor_insert_value)

    print('团队:%s--项目:%s--共取得%d个任务' % (team_result['name'], project_id, count))

    return insert_list, tuple(tid_list), relation_insert_list


def insert_func(connect, insert_list, table_name, tid_tuple):
    print("开始进行插入数据表%s" % table_name)
    if table_name == 'worktile_task_list':
        delete_sql = 'delete from xsl_mada.worktile_task_list where task_id in %s' % str(tid_tuple)
        connect.cursor.execute(delete_sql)
        # Enforce UTF-8 for the connection.
        connect.cursor.execute('SET NAMES utf8mb4')
        connect.cursor.execute("SET CHARACTER SET utf8mb4")
        connect.cursor.execute("SET character_set_connection=utf8mb4")
        insert_sql = "insert into xsl_mada.worktile_task_list(team_id, team_name, " \
                     "project_id,project_name,task_id,task_name,task_desc,task_create_time," \
                     "task_expire_time,task_completed,task_complete_time,task_achived)" \
                     "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        connect.cursor.executemany(insert_sql, insert_list)
        connect.connection.commit()
        print("%s 最近90天数据已更新" % table_name)

    if table_name == 'worktile_task_relation':
        delete_sql = 'delete from xsl_mada.worktile_task_relation where task_id in %s' % str(tid_tuple)
        connect.cursor.execute(delete_sql)
        # Enforce UTF-8 for the connection.
        connect.cursor.execute('SET NAMES utf8mb4')
        connect.cursor.execute("SET CHARACTER SET utf8mb4")
        connect.cursor.execute("SET character_set_connection=utf8mb4")
        insert_sql = "insert into xsl_mada.worktile_task_relation(task_id, type, value) VALUES (%s,%s,%s)"
        connect.cursor.executemany(insert_sql, insert_list)
        connect.connection.commit()
        print("%s 最近90天数据已更新" % table_name)
    print("%s已插入完成" % table_name)

if __name__ == '__main__':
    conn = Connect(Bj3Mysql)
    try:
        access_token, client_id = obtain_token(conn)
        team_projects = obtain_project_list(access_token)
        task_insert_list, tid_tuple, task_relation_insert_list = [], (), []
        for t_p in team_projects:
            x, y, z = obtain_insert_list(access_token, team_id=t_p[0], project_id=t_p[1])
            task_insert_list += x
            tid_tuple += y
            task_relation_insert_list += z
        insert_func(conn, task_insert_list, 'worktile_task_list', tid_tuple)
        insert_func(conn, task_relation_insert_list, 'worktile_task_relation', tid_tuple)
        conn.close_connect()
        print("最近90天worktile数据导出已完成")
    except BaseException as e:
        conn.close_connect()
        print(e)

