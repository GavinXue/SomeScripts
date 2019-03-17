import requests
from mysql_connect import Connect
from config import Bj3Mysql

def obtain_insert_data():
    # 输入 jira.test.com 修成对应 Jira 环境地址
    project_url = 'http://jira.test.com/rest/api/2/project'
    search_url = 'http://jira.test.com/rest/api/2/search'
    
    s = requests.Session()  # save the login cookie
    # 数据账号和密码
    s.auth = ('xxx', 'password')  # 这里使用的用户如果被删除账户，是需要重新更换的
    
    total = s.post(search_url, json={"startAt": 0, "maxResults": 1}).json()['total']
    insert_list = []
    
    for startAt in range(0, total, 1000):
        search_params = {
            "startAt": startAt,
            "maxResults": 1000
        }
        print("Begin to get the issues from {} to {}".format(startAt, startAt+1000))
        
        issues = s.post(search_url, json=search_params).json()['issues']
        
        for issue in issues:
            fields = issue['fields']
            components_str = list_to_str(fields, 'components')
            version_str = list_to_str(fields, 'versions')
            fix_version_str = list_to_str(fields, 'fixVersions')
            resolution_str = fields['resolution']['name'] if fields['resolution'] else None
            assignee = fields['assignee']['displayName'] if fields['assignee'] else None
            environment = fields['environment'].replace('"', '') if fields['environment'] else None
            
            tmp_value = (issue['id'], fields['creator']['displayName'], fields['created'],
                         fields['issuetype']['name'], fields['summary'].replace('"', ' '),
                         fields['priority']['name'], components_str, environment,
                         fields['status']['name'], resolution_str, version_str,
                         fix_version_str, fields['updated'], fields['resolutiondate'],
                         fields['project']['name'], assignee)
            insert_list.append(tmp_value)

    print("The script get %s issues info in total." %len(insert_list))
    return insert_list


def list_to_str(fields, key):
    if not fields[key]:
        return None
    func = lambda x: " ".join(x)
    result_list = [x['name'] for x in fields[key]]
    result = func(result_list)
    return result


def update_info_to_statistics(insert_list):
    insert_update_sql = 'insert into xsl_statistics.jira_bug_info(bug_id, creator, created_time, bug_type, summary, priority, ' \
                        'components, environment, status, resolution, affect_version, fix_version, updated_time, ' \
                        'resolution_time, project, assignee) ' \
                        'values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}","{12}","{13}","{14}", "{15}") ' \
                        'on duplicate key update creator = "{1}", created_time = "{2}", bug_type = "{3}", summary = "{4}", ' \
                        'priority = "{5}", components = "{6}", environment = "{7}", status = "{8}", resolution = "{9}", ' \
                        'affect_version = "{10}", fix_version = "{10}", updated_time = "{12}", ' \
                        'resolution_time = "{13}", project = "{14}", assignee = "{15}"'
    
    # 需要事先建立数据库配置
    conn = Connect(Bj3Mysql)
    try:
        for i in insert_list:
            update_sql = insert_update_sql.format(i[0],i[1],i[2],i[3],i[4],i[5],i[6],i[7],
                                                  i[8],i[9],i[10],i[11],i[12],i[13],i[14], i[15])
            print(update_sql)
            conn.cursor.execute(update_sql)
        conn.connection.commit()
    except BaseException as e:
        print("updating failed", e)
    finally:
        conn.close_connect()


if __name__ == "__main__":
    insert_list = obtain_insert_data()
    update_info_to_statistics(insert_list)