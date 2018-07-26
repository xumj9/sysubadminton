import os
import time
from selenium import webdriver
from PIL import Image,ImageFilter
import cv2
from aip import AipOcr

netid = 'xxx'
password = 'xxxxx'
bookdate = '2018-07-27'
playtime = '17:01-18:00'
dir = "/Users/mengjiexu/Documents/badminton/"

width = 280
height = 130
type = 'png'


repadd = dir+"rep.png"
greyadd = dir+"grey.png"
edadd = dir+"edge.png"
resadd =dir+"resize.png"

config = {
    'appId': '11352343',
    'apiKey': 'Nd5Z1NkGoLDvHwBnD2bFLpCE',
    'secretKey': 'A9FsnnPj1Ys2Gof70SNgYo23hKOIK8Os'
}

client = AipOcr(**config)


driver = webdriver.Firefox(executable_path='/Users/mengjiexu/Documents/parser/geckodriver')
driver.get("http://gym.sysu.edu.cn/product/show.html?id=61")
driver.maximize_window()
driver.find_element_by_xpath("//a[contains(text(),'登录')]").click()

screenshotadd = "/Users/mengjiexu/Documents/badminton/screenshot.png"
codeadd = "/Users/mengjiexu/Documents/badminton/code.png"
rebadd = "/Users/mengjiexu/Documents/badminton/rgb.png"

def ResizeImage(filein, fileout, width, height, type):
  img = Image.open(filein)
  out = img.resize((width, height),Image.ANTIALIAS) #resize image with high-quality
  out.save(fileout, type)

def clearimage(originadd):
    img = Image.open(originadd)#读取系统的内照片
    #将黑色干扰线替换为白色
    width = img.size[0]#长度
    height = img.size[1]#宽度
    for i in range(0,width):#遍历所有长度的点
        for j in range(0,height):#遍历所有宽度的点
            data = (img.getpixel((i,j)))#打印该图片的所有点
            if (data[0]<=25 and data[1]<=25 and data[2]<=25):#RGBA的r,g,b均小于30
                img.putpixel((i,j),(255,255,255,255))#则这些像素点的颜色改成白色
    img = img.convert("RGB")#把图片强制转成RGB
    img.save(repadd)#保存修改像素点后的图片
    #灰度化
    Grayimg = cv2.cvtColor(cv2.imread(repadd), cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(Grayimg, 160, 255,cv2.THRESH_BINARY)
    cv2.imwrite(greyadd, thresh)
    #提取边缘
    edimg = Image.open(greyadd)
    conF = edimg.filter(ImageFilter.CONTOUR)
    conF.save(edadd)

def img_to_str(image_path):
    identicode = ""
    image = open(image_path,'rb').read()
    result = client.basicGeneral(image)
    with open("/Users/mengjiexu/Documents/badminton/result.txt","a") as f:
        for line in result["words_result"]:
            identicode =identicode+line["words"]
            f.write(line["words"]+"\n")
    return(identicode)

def getidentify(originadd):
    clearimage(originadd)
    ResizeImage(edadd, resadd, width, height, type)
    identicode = img_to_str(resadd)
    return(identicode)


def Convertimg():
    imglocation = ("//img[@name='captchaImg']")
    driver.save_screenshot(screenshotadd)
    im = Image.open(screenshotadd)
    left = driver.find_element_by_xpath(imglocation).location['x']
    top = driver.find_element_by_xpath(imglocation).location['y']
    right = driver.find_element_by_xpath(imglocation).location['x'] + driver.find_element_by_xpath(imglocation).size['width']
    bottom = driver.find_element_by_xpath(imglocation).location['y'] + driver.find_element_by_xpath(imglocation).size['height']
    im = im.crop((left, top, right, bottom))
    im.save(codeadd)


def Login():
    driver.find_element_by_xpath("//input[@id='username']").send_keys(netid)
    driver.find_element_by_xpath("//input[@id='password']").send_keys(password)
    Convertimg()
    txtcode = getidentify(codeadd)
    print(txtcode)
    driver.find_element_by_xpath("//input[@id='captcha']").send_keys(txtcode)
    time.sleep(2)
    driver.find_element_by_xpath("//input[@type='submit']").click()

def bookfield(bookdate,playtime):
    driver.get("http://gym.sysu.edu.cn/index.html")
    driver.find_element_by_xpath("//a[@href='/product/index.html']").click()
    driver.find_element_by_xpath("//input[@id='txt_name']").send_keys('英东羽毛球场')
    driver.find_element_by_xpath("//button[@type='submit']").click()
    target = driver.find_element_by_xpath("//a[@href='show.html?id=61']")
    driver.execute_script("arguments[0].click();", target)
    time.sleep(2)
    driver.find_element_by_xpath("//li[@data='%s']"%bookdate).click()
    if int(playtime[:2])<15:
        js = "window.scrollTo(0,500)"
    else:
        js = "window.scrollTo(0,950)"
    driver.execute_script(js)
    candidates = driver.find_elements_by_xpath("//span[@data-timer='%s']"%playtime)
    for can in candidates:
        isbooked = can.get_attribute('class')
        if isbooked == "cell football easyui-tooltip tooltip-f":
            can.click()
            driver.execute_script("window.scrollTo(0,500)")
            driver.find_element_by_xpath("//button[@id='reserve']").click()
            break
        else:
            pass


var=0
while var >= 0:
    driver.find_element_by_xpath("//input[@id='username']").clear()
    driver.find_element_by_xpath("//input[@id='password']").clear()
    driver.find_element_by_xpath("//input[@id='captcha']").clear()
    Login()
    var = var+1
    print("这是第%d次登录尝试"%var)
    time.sleep(3)
    try:
        driver.find_element_by_xpath("//strong[contains(text(),'许梦洁')]")
        print("第%d次登录尝试成功，开始订场"%var)
        bookfield(bookdate, playtime)
        print("订场完成")
        print("订场日期为：%s"%bookdate)
        print("订场时段为：%s"%playtime)
        break
    except:
        print("第%d次登录尝试失败，重新尝试"%var)
