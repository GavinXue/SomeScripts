import MySQLdb
import config


class Connect:
    def __init__(self, server=config.Bj3Mysql):
        self.connection = MySQLdb.connect(server.host, server.user, server.password, server.db,
                                          server.port, charset='utf8')
        self.cursor = self.connection.cursor()

    def close_connect(self):
        self.connection.close()
        self.cursor.close()

    def sql_query(self, query_sql):
        self.cursor.execute(query_sql)
        return self.cursor.fetchall()


if __name__ == '__main__':
    connect = Connect()
    query_sql_tmp = 'select * from xsl_mada.d_user_basic dub limit 10'
    result = connect.sql_query(query_sql_tmp)
    print(result)
    connect.close_connect()