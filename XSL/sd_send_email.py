import email, smtplib
from config import EmailAccounts
from email.mime.text import MIMEText
from functools import reduce


def send_mail(event_list, email_list="bigdata@xingshulin.com", subject=None):
    print("开始进入邮件发送流程!")
    server = smtplib.SMTP(EmailAccounts.server)
    to_addrs = email_list.split(',')
    
    body_content = build_content(event_list)
    msg = MIMEText(body_content, "html")
    msg['From'] = "statistics@xingshulin.com"
    msg['To'] = email_list
    msg['Cc'] = ""
    msg['Subject'] = "[监控中心] SD埋点数据每日异常监控%s" % subject
    
    server.login(EmailAccounts.internal['address'], EmailAccounts.internal['password'])
    server.sendmail(EmailAccounts.internal['address'],
                    to_addrs, msg.as_string())
    server.quit()
    print("监控邮件已发送完成!")

def build_content(event_list):
    body = "<div><p>本邮件针对sensors data中的事件埋点，监控配置表xsl_sensors_data.track_event_monitor中的设置事件。" \
           "预警分析以下五种情况(注：期望E和标准差SD基于预测当周的上一周数据核算)：</p><ol>" \
           "<li>红色预警：所监控事件数据为0时，在事件未发生列数据为0</li>" \
           "<li>红色预警：当监控事件发生次数小于 E - 2*SD时，预示数据产生不正常波动，需密切关注</li>" \
           "<li>橙色预警：当监控事件发生次数小于 E - SD时，预示数据可能产生不正常波动</li>" \
           "<li>蓝色预警：当监控事件发生次数小于 E + SD时，预示数据可能产生不正常波动</li>" \
           "<li>绿色预警：当监控事件发生次数小于 E + 2*SD时，预示数据产生不正常波动，需密切关注</li></ol></div><br>"
    table_lines = [build_table_line(id , event_name, value, expectation, sigma, event_product, description, link_url)
                   for (id , event_name, value, expectation, sigma, event_product, description, aggregator, link_url) in event_list]
    
    headers = ["监控id", "事件名", "监控产品", "事件描述", "数据为0", "红色预警", "橙色预警", "蓝色预警", "绿色预警"]
    header_str = "<tr bgColor=#8080FF style=\"color:white\"><th style=\"padding:10px\"> " + \
                 reduce(lambda x, y: x + ' </th><th style=\"padding:10px\"> ' + y, headers) + \
                 " </th></tr>"
    table_str = ""
    for line in table_lines:
        if line:
            table_str = table_str + line
    table_str = '<table borderColor=#C0C0C0 border="1" style="border-collapse:collapse">' \
                + header_str + table_str + '</table>'
    content = body + table_str
    return content

def build_table_line(id, event_name, value, expectation, sigma, event_product, description, link_url):
    line_str = '<td>{}</td><td><a href={}>{}</a></td><td>{}</td><td>{}</td>'\
                .format(id, link_url, event_name, event_product, description)
    tmp = ""
    if value == 0:
        tmp = '<td style="background: #EF5350; text-align: center">{}</td><td></td><td></td><td></td><td></td>'.format(value)
    elif value <= expectation - 2*sigma:
        tmp = '<td></td><td style="background: #EF5350; text-align:center">{}</td><td></td><td></td><td></td>'.format(value)
    elif expectation - 2 * sigma < value < expectation-sigma:
        tmp = '<td></td><td></td><td style="background: #FFA726; text-align:center">{}</td><td></td><td></td>'.format(value)
    elif expectation + sigma < value < expectation + 2*sigma:
        tmp = '<td></td><td></td><td></td><td style="background: #64B5F6; text-align:center">{}</td><td></td>'.format(value)
    elif value >= expectation + 2*sigma:
        tmp = '<td></td><td></td><td></td><td></td><td style="background: #4DB6AC; text-align: center">{}</td>'.format(value)
    if tmp:
        line_str = '<tr>'+ line_str + tmp + '</tr>'
        return line_str
    else:
        return None
    
    
if __name__ == '__main__':
    event_list =  [(1, "event", 0, 20, 10), (2, "event2", 40, 20, 10)]
    send_mail(event_list)