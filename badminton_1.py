# encoding:utf-8

import os
import time
import cv2 as cv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageFilter
from aip import AipOcr


class Badminton():
    def __init__(self, dir):
        # file_location
        self.dir = dir

        # baidu-aip
        # TODO: 填入自己的baidu-aip信息
        config = {
            'appId': '—**********-',
            'apiKey': '—**********-',
            'secretKey': '—**********-'
        }
        self.init_baidu_client(config)

        # chrome
        # TODO: 填入自己chromedriver的路径
        driver_path = r'C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe'
        target_link = r'http://gym.sysu.edu.cn/product/show.html?id=61'
        self.init_chrome(driver_path, target_link)

    def init_baidu_client(self, config):
        self.client = AipOcr(**config)

    def init_chrome(self, driver_path, target_link):
        self.driver = webdriver.Chrome(driver_path)
        self.driver.get(target_link)
        self.driver.maximize_window()
        self.driver.find_element_by_xpath("//a[contains(text(),'登录')]").click()

    def resize_image(self, filein):
        width = 280
        height = 130
        type = 'png'

        resize_path = os.path.join(self.dir, 'resize.png')
        img = Image.open(filein)
        out = img.resize((width, height), Image.ANTIALIAS)  # resize image with high-quality
        out.save(resize_path, type)

        return resize_path

    def extract_image(self, original_img):
        thre_path = os.path.join(self.dir, 'rep.png')
        gray_path = os.path.join(self.dir, 'gray.png')
        edge_path = os.path.join(self.dir, 'edge.png')

        img = Image.open(original_img)
        # 将黑色干扰线替换为白色
        width = img.size[0]  # 长度
        height = img.size[1]  # 宽度
        for i in range(0, width):  # 遍历所有长度的点
            for j in range(0, height):  # 遍历所有宽度的点
                data = (img.getpixel((i, j)))  # 打印该图片的所有点
                if (data[0] <= 25 and data[1] <= 25 and data[2] <= 25):  # RGBA的r,g,b均小于25
                    img.putpixel((i, j), (255, 255, 255, 255))  # 则这些像素点的颜色改成白色
        img = img.convert("RGB")  # 把图片强制转成RGB
        img.save(thre_path)  # 保存修改像素点后的图片
        # 灰度化
        gray = cv.cvtColor(cv.imread(thre_path), cv.COLOR_BGR2GRAY)
        _, thresh = cv.threshold(gray, 160, 255, cv.THRESH_BINARY)
        cv.imwrite(gray_path, thresh)
        # 提取边缘
        edimg = Image.open(gray_path)
        conF = edimg.filter(ImageFilter.CONTOUR)
        conF.save(edge_path)

        return edge_path

    def img_to_str(self, image_path):
        result_path = os.path.join(self.dir, 'result.txt')

        identicode = ""
        image = open(image_path, 'rb').read()
        result = self.client.basicGeneral(image)
        with open(result_path, 'a') as f:
            for line in result["words_result"]:
                identicode = identicode + line["words"]
                f.write(line["words"] + "\n")
        return (identicode)

    def get_identify(self, original_img):
        edge_path = self.extract_image(original_img)
        resize_path = self.resize_image(edge_path)
        identified_code = self.img_to_str(resize_path)
        return (identified_code)

    def catch_capcha(self):
        src_path = os.path.join(self.dir, 'screenshot.png')
        dst_path = os.path.join(self.dir, 'code.png')

        img_loc = ("//img[@name='captchaImg']")
        self.driver.save_screenshot(src_path)
        img = Image.open(os.path.join(src_path))
        left = self.driver.find_element_by_xpath(img_loc).location['x']
        top = self.driver.find_element_by_xpath(img_loc).location['y']
        right = self.driver.find_element_by_xpath(img_loc).location['x'] + \
                self.driver.find_element_by_xpath(img_loc).size[
                    'width']
        bottom = self.driver.find_element_by_xpath(img_loc).location['y'] + \
                 self.driver.find_element_by_xpath(img_loc).size[
                     'height']
        img = img.crop((left, top, right, bottom))
        img.save(dst_path)

        return dst_path

    def login(self, netid, password):
        self.driver.find_element_by_xpath("//input[@id='username']").send_keys(netid)
        self.driver.find_element_by_xpath("//input[@id='password']").send_keys(password)
        txtcode = self.get_identify(self.catch_capcha())
        self.driver.find_element_by_xpath("//input[@id='captcha']").send_keys(txtcode)
        time.sleep(2)
        self.driver.find_element_by_xpath("//input[@type='submit']").click()

    def book_field(self, bookdate, playtime):
        self.driver.get("http://gym.sysu.edu.cn/index.html")
        self.driver.find_element_by_xpath("//a[@href='/product/index.html']").click()
        self.driver.find_element_by_xpath("//input[@id='txt_name']").send_keys('英东羽毛球场')
        self.driver.find_element_by_xpath("//button[@type='submit']").click()
        target = self.driver.find_element_by_xpath("//a[@href='show.html?id=61']")
        self.driver.execute_script("arguments[0].click();", target)
        time.sleep(2)
        # TODO: 可以判断bookdate是否出现
        self.driver.find_element_by_xpath("//li[@data='%s']" % bookdate).click()
        if int(playtime[:2]) < 15:
            js = "window.scrollTo(0,500)"
        else:
            js = "window.scrollTo(0,950)"
        self.driver.execute_script(js)
        candidates = self.driver.find_elements_by_xpath("//span[@data-timer='%s']" % playtime)
        for can in candidates:
            is_booked = can.get_attribute('class')
            if is_booked == "cell football easyui-tooltip tooltip-f":
                can.click()
                self.driver.execute_script("window.scrollTo(0,500)")
                self.driver.find_element_by_xpath("//button[@id='reserve']").click()
                break
            else:
                pass

        # 新增
        time.sleep(1)
        self.driver.find_element_by_xpath("//button[@id='reserve']").click()

        locator = (By.CLASS_NAME, "confirm")
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(locator))
        self.driver.find_element_by_class_name("confirm").click()

        locator = (By.CLASS_NAME, "bankitem")
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(locator))
        self.driver.find_element_by_xpath("//li[@data-payid='2']").click()
        self.driver.find_element_by_css_selector("[class='button-large button-info']").click()

    def run(self, netid, password, date, period):
        count = 1
        login_url = self.driver.current_url

        while True:
            self.driver.find_element_by_xpath("//input[@id='username']").clear()
            self.driver.find_element_by_xpath("//input[@id='password']").clear()
            self.driver.find_element_by_xpath("//input[@id='captcha']").clear()
            self.login(netid, password)
            print("第%s次登录尝试" % count)
            time.sleep(5)

            if self.driver.current_url != login_url:
                print('成功！')
                break
            else:
                print('失败！')
                count += 1

        count = 1
        while True:
            try:
                print("第%d次尝试订场" % count)
                self.book_field(date, period)
                print("订场完成")
                print("订场日期为：%s" % date)
                print("订场时段为：%s" % period)
                break
            except:
                print("失败！")
                count += 1


if __name__ == '__main__':
    # TODO: 填入自己的netid信息

    netid = '—**********-'
    password = '—**********-'

    bookdate = '2019-04-04'
    playtime = '15:01-16:00'

    # TODO: 填入暂时存放图片的路径，默认为本文件下的temp文件夹。
    dir = r'./temp'
    if not os.path.exists(dir):
        os.mkdir(dir)

    pincha = Badminton(dir)
    pincha.run(netid, password, bookdate, playtime)
