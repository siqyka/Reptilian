from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import time
import requests
import jobdb
from threading import Thread,Lock
from concurrent.futures import ThreadPoolExecutor

lock=Lock()

class Lagou():
    def __init__(self,timeout):
        self.timeout=timeout
        self.joburls=[]
        self.headers={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': 'GA1.2.1667356220.1534744913; user_trace_token=20180820140128-7a53df3d-a43e-11e8-aa7e-5254005c3644; LGUID=20180820140128-7a53e264-a43e-11e8-aa7e-5254005c3644; showExpriedIndex=1; showExpriedCompanyHome=1; showExpriedMyPublish=1; index_location_city=%E6%9D%AD%E5%B7%9E; _gid=GA1.2.899023627.1535330620; SEARCH_ID=d3516a148b5f49968e65dc909afec4ad; hasDeliver=177; JSESSIONID=ABAAABAAAIAACBIE1425982A89C0349B1533E55C2C1F33E; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1535331307,1535356850,1535357717,1535419465; X_HTTP_TOKEN=4786867dd90f34a2fd0a40327ef7c993; LG_LOGIN_USER_ID=157fd6ceb4cd29a553d69538873124685043dfcdf6eb5dc0; _putrc=BE3CE0C96DF640E3; login=true; unick=%E6%88%9A%E7%9B%88%E5%87%AF; TG-TRACK-CODE=index_deliver; gate_login_token=d50e14cedb88dfb124a282102e80eaffe5f87194692e0b14; LGSID=20180828112105-65f1629f-aa71-11e8-ba95-525400f775ce; PRE_UTM=; PRE_HOST=; PRE_SITE=; PRE_LAND=https%3A%2F%2Fwww.lagou.com%2F; _gat=1; Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1535427570; LGRID=20180828113903-e89599f3-aa73-11e8-b24b-5254005c3644',
            'Referer': 'https://www.lagou.com/jobs/list_python?labelWords=&fromSearch=true&suginput=',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
            }

        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--disable-gpu')
        # chrome_options.add_argument('blink-settings=imagesEnabled=false')#不加载图片
        # self.browser=webdriver.Chrome(chrome_options=chrome_options)

        self.browser=webdriver.Chrome()#可视浏览器

        self.browser.set_page_load_timeout(self.timeout)
        self.wait=WebDriverWait(self.browser,self.timeout)

        self.db=jobdb.SaveToDatabase()

    #获取第一级页面，爬取工作源链接
    def get_first_page(self,url,page):
        try:
            self.browser.get(url)
            if page>1:
                ypage=self.browser.find_element_by_class_name("pager_is_current").text  #获取当前是第几页

                submit=self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.next_disabled'))) #获取'下一页'按钮

                #点击 要去的页码减当前页码 次数
                for i in range(page-int(ypage)):
                    submit.click()
                    time.sleep(0.5)
                self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'.pager_is_current'),str(page)))  #判断是否是要的页面
        except Exception as e:
            print('erorr',e)

        #等待信息页面加载完成
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.s_position_list ')))

        #获取链接放入数组，等待调用
        res=pq(self.browser.page_source)
        items=res('.p_top .position_link').items()
        for item in items:
            url=item.attr('href')
            self.joburls.append(url)
        
        return self.joburls
    
    #获取具体某个工作信息
    def get_jobmsg(self,url):
        try:
            res=requests.get(url,headers=self.headers)  #请求页面
            re=pq(res.text)
            sadd=re('.work_addr').text().split(' ')[-2]     #公司地址
            position=re('.job-name .name').text()           ##职位
            company=re('#job_company .fl').text().split(' ')[0]     #公司
            salary=re('.job_request span').text().split(' ')[0]     #工资
            claim=",".join(re('.job_request span').text().split(' ')[3::2])     #基本要求
            
            #形成字典
            dic={
                'sadd':sadd,
                'position':position,
                'company':company,
                'salary':salary,
                'claim':claim,
                'joburl':url
            }
            # yield dic

            lock.acquire()
            self.db.set(dic)
            lock.release()

        except Exception as e:
            print('msgerorr:',e)

#单线程
# def main():
#     url='https://www.lagou.com/jobs/list_python?px=default&city=%E6%9D%AD%E5%B7%9E#filterBox'
#     lagou=Lagou(30)
#     db=jobdb.SaveToDatabase()
#     for i in range(1,2):
#         lagou.get_first_page(url,i)

#     for x in lagou.joburls:
#         datas=lagou.get_jobmsg(x)
#         for data in datas:
#             db.set(data)

#多线程
# def main():
#     Threadl=[]

#     url='https://www.lagou.com/jobs/list_python?px=default&city=%E6%9D%AD%E5%B7%9E#filterBox'
#     lagou=Lagou(30)

#     for i in range(2,6):
#         lagou.get_first_page(url,i)

#     for x in lagou.joburls:
#         t=Thread(target=lagou.get_jobmsg,args=(x,))
#         Threadl.append(t)
#         t.start()

#     for t1 in Threadl:
#         t1.join()


#线程池
def main():
    url='https://www.lagou.com/jobs/list_python?px=default&city=%E6%9D%AD%E5%B7%9E#filterBox'
    lagou=Lagou(30)

    for i in range(1,2):
        lagou.get_first_page(url,i)

    with ThreadPoolExecutor(3) as executor:
        executor.map(lagou.get_jobmsg,lagou.joburls)



if __name__ == '__main__':
    main()