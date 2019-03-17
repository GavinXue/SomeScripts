from selenium import webdriver
from urllib.parse import urlencode
from datetime import datetime, timedelta
from time import sleep
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
import pytesseract


# 打开浏览器
def openbrowser():
    global browser

    # https://passport.baidu.com/v2/?login
    url = "https://passport.baidu.com/v2/"
    # 打开谷歌浏览器
    browser = webdriver.Chrome(executable_path="/usr/local/bin/chromedriver")
    # 输入网址
    browser.get(url)
    # 打开浏览器时间
    # print("等待10秒打开浏览器...")
    # time.sleep(10)

    # 找到id="TANGRAM__PSP_3__userName"的对话框
    # 清空输入框
    browser.find_element_by_id("TANGRAM__PSP_3__userName").clear()
    browser.find_element_by_id("TANGRAM__PSP_3__password").clear()

    # 输入账号密码
    account = []
    try:
        fileaccount = open("./baidu/account.txt")
        accounts = fileaccount.readlines()
        for acc in accounts:
            account.append(acc.strip())
        fileaccount.close()
    except Exception as err:
        print(err)
        input("请正确在account.txt里面写入账号密码")
        exit()
    browser.find_element_by_id("TANGRAM__PSP_3__userName").send_keys(account[0])
    browser.find_element_by_id("TANGRAM__PSP_3__password").send_keys(account[1])

    # 点击登陆登陆
    # id="TANGRAM__PSP_3__submit"
    browser.find_element_by_id("TANGRAM__PSP_3__submit").click()

    # 等待登陆10秒
    # print('等待登陆10秒...')
    # time.sleep(10)
    print("等待网址加载完毕...")

    select = input("请观察浏览器网站是否已经登陆(y/n)：")
    while 1:
        if select == "y" or select == "Y":
            print("登陆成功！")
            print("准备打开新的窗口...")
            # time.sleep(1)
            # browser.quit()
            break

        elif select == "n" or select == "N":
            selectno = input("账号密码错误请按0，验证码出现请按1...")
            # 账号密码错误则重新输入
            if selectno == "0":

                # 找到id="TANGRAM__PSP_3__userName"的对话框
                # 清空输入框
                browser.find_element_by_id("TANGRAM__PSP_3__userName").clear()
                browser.find_element_by_id("TANGRAM__PSP_3__password").clear()

                # 输入账号密码
                account = []
                try:
                    fileaccount = open("./baidu/account.txt")
                    accounts = fileaccount.readlines()
                    for acc in accounts:
                        account.append(acc.strip())
                    fileaccount.close()
                except Exception as err:
                    print(err)
                    input("请正确在account.txt里面写入账号密码")
                    exit()

                browser.find_element_by_id("TANGRAM__PSP_3__userName").send_keys(account[0])
                browser.find_element_by_id("TANGRAM__PSP_3__password").send_keys(account[1])
                # 点击登陆sign in
                # id="TANGRAM__PSP_3__submit"
                browser.find_element_by_id("TANGRAM__PSP_3__submit").click()

            elif selectno == "1":
                # 验证码的id为id="ap_captcha_guess"的对话框
                input("请在浏览器中输入验证码并登陆...")
                select = input("请观察浏览器网站是否已经登陆(y/n)：")

        else:
            print("请输入“y”或者“n”！")
            select = input("请观察浏览器网站是否已经登陆(y/n)：")

def generate_url(date, key_word):
    # from_date = datetime.strptime(date, '%Y-%m-%d')
    from_date = (pd.to_datetime(date) - timedelta(days=30)).strftime('%Y%m%d')
    to_date = (pd.to_datetime(date) - timedelta(days=7)).strftime('%Y%m%d')
    payload = {"word": key_word}
    url = 'http://index.baidu.com/?tpl=trend&type=0&area=0&time={}%7C{}&'.format(from_date, to_date) \
          + urlencode(payload, encoding='gbk')
    print(url)
    return url

def generate_index(key_word, date):
    # key_word, date = key.split(',')
    try:
        url = generate_url(date, key_word)
        browser.get(url)
    except BaseException as e:
        print(e)
        return 'url解析失败'
    # 寻找点击平均值
    sleep(1.5)
    try:
        browser.find_element_by_id("trend-meanline").click()
    except BaseException as e:
        print(e)
        return '未找到关键词'
    
    sleep(1)
    ele = browser.find_elements_by_css_selector("#trend rect")
    
    for i in ele:
        ActionChains(browser).move_to_element_with_offset(i, 5, 5).perform()
        sleep(0.01)
    sleep(1.5)

    # 截取数据的截图
    img_ele = browser.find_element_by_class_name('contentWord')
    locations = img_ele.location
    sizes = img_ele.size
    
    # 像素乘以2是在retina屏使用HiDpi的情况下要使用的
    rectangle = (int(locations['x'] + 5) * 2, int(locations['y'] + 5) * 2, int(locations['x'] + sizes['width'] - 5) * 2,
                          int(locations['y'] + sizes['height'] - 5) * 2)
    
    path = "./baidu/img/" + key_word + date
    browser.save_screenshot(str(path) + ".png")
    
    img = Image.open(str(path) + ".png")
    jpg = img.crop(rectangle)
    
    # 对图片进行放大操作
    (x, y) = jpg.size
    out = jpg.resize((x*4, y*4), Image.ANTIALIAS)
    # out.save(path + 'zoom.jpg', 'png', quality=100)

    try:
        # image = Image.open(str(path) + "zoom.jpg")
        code = pytesseract.image_to_string(out)
        return code.replace(' ', '').replace('.', '').replace(',', '')
    except BaseException as e:
        print(e)


if __name__ =='__main__':
    # 此处传入需要获取百度指数的关键词文件
    df = pd.read_csv('./baidu/20170303_actor_for_obtain_index_norMovie.csv')
    df['baidu_index'] = '0'
    
    print(df.index.size)
    
    # 打开浏览器登录
    openbrowser()
    browser.maximize_window()
    try:
        for index, row in df.iterrows():
            baidu_index = generate_index(row['actor'], row['pub_date'])
            df.at[index, 'baidu_index'] = baidu_index
            print('Get {} baidu index before {}, value is: {}'.format(row['actor'], row['pub_date'], baidu_index))
        df.to_csv('./baidu/20170303_actor_for_obtain_index_norMovie_result5.csv')
    except BaseException as e:
        print(e)
        df.to_csv('./baidu/20170303_actor_for_obtain_index_norMovie_result5.csv')

