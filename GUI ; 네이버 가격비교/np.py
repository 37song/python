from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QButtonGroup
from np_ui import Ui_Form
import sys
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import urllib3

os.environ["WDM_SSL_VERIFY"] = "0"

#InsecureRequestWarning 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 크롬 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.110 Safari/537.36")
chrome_options.add_experimental_option("detach", True) 



class MainWindow(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 버튼
        self.start_btn.clicked.connect(self.start)
        self.save_btn.clicked.connect(self.save)
        self.reset_btn.clicked.connect(self.reset)
        self.quit_btn.clicked.connect(self.quit)

        # 체크박스 이벤트 핸들러 연결
        self.fast_check.stateChanged.connect(self.handle_fast_check)
        self.free_check.stateChanged.connect(self.handle_free_check)
        self.over_check.stateChanged.connect(self.handle_overseas_check)


    # 체크 박스
    def handle_fast_check(self, state):
        actual_state = self.fast_check.isChecked()
        if actual_state:
            self.fast_deli = '&fastDelivery=true'
        else:
            self.fast_deli = ''
    def handle_free_check(self, state):
        actual_state = self.free_check.isChecked()
        if actual_state:
            self.free_deli = '&freeDelivery=true'
        else:
            self.free_deli = ''
    def handle_overseas_check(self, state):
        actual_state = self.over_check.isChecked()
        if actual_state:
            self.overseas = '&exagency=true'
        else:
            self.overseas = ''



    # 스타트 버튼 
    def start(self):
        self.result = []
        self.search = self.keyword.text()
        page = int(self.count.text())+1
        min = self.minPrice.text()
        max = self.maxPrice.text()
        
        #  정렬(sorter) 값 설정
        current_selection_index = self.sort_box.currentIndex()
        if current_selection_index == 0:
            self.sort = 'rel'
        elif current_selection_index == 1:
            self.sort = 'price_asc'
        elif current_selection_index == 2:
            self.sort = 'price_dsc'
        elif current_selection_index == 3:
            self.sort = 'review'
        elif current_selection_index == 4:
            self.sort = 'review_rel'
        elif current_selection_index == 5:
            self.sort = 'date'
        else:            
            self.sort = ''

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options = chrome_options)
        wait = WebDriverWait(driver, 10)


        for p in range (1, page) :
            url = f'https://search.shopping.naver.com/search/all?query={self.search}&sort={self.sort}&pagingIndex={p}&minPrice={min}&maxPrice={max}{self.fast_deli}{self.free_deli}{self.overseas}&pagingSize=40&productSet=total&viewType=image'
                    
            driver.get(url)
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            items = driver.find_elements(By.CSS_SELECTOR, 'li.product_list_item__Y4XcD')
            for i in items:
                name = i.find_element(By.CSS_SELECTOR, 'div.product_info_area__KU5QS > div > a').text
                link = i.find_element(By.CSS_SELECTOR, 'div.product_info_area__KU5QS > div > a').get_attribute('href')
                price = int(i.find_element(By.CSS_SELECTOR, 'div.product_info_area__KU5QS > strong > span.price > span > em').text.replace(',',''))
                try:
                    com = i.find_element(By.CSS_SELECTOR, 'em.product_mall_title__a2xpr').textcom = i.find_element(By.CSS_SELECTOR, 'em.product_mall_title__a2xpr').text
                except:
                    pass
                try:
                    rating = float(i.find_element(By.CSS_SELECTOR, 'span.product_grade__ulRGb').text.split('\n')[1])
                except:
                    pass
                try:
                    review = i.find_element(By.CSS_SELECTOR, 'div.product_etc_box___01JR > a:nth-of-type(1) > em').text.split('(')[1].split(')')[0]
                except:
                    pass
                try:
                    purchasecount = i.find_element(By.CSS_SELECTOR, '[data-shp-area-id="purchasecount"]').text.split(' ')[1]
                except:
                    purchasecount = '-'
                try:
                    zzim = i.find_element(By.CSS_SELECTOR, 'div.product_info_area__KU5QS > div.product_etc_box___01JR > span.product_etc__FtVkj > em.product_num__qLoWR').text
                except:
                    zzim = '-'

                self.result.append([com, name, price, rating, review, purchasecount, zzim, link])
            self.textBrowser.append(f'- {p}쪽 크롤링 완료 - \n')
            QApplication.processEvents()
        self.textBrowser.append(f' ~ 크롤링 완료 ~ \n')


    # 저장 버튼 
    def save(self):
        df = pd.DataFrame(self.result, columns=['업체명','이름','가격','별점','리뷰수','구매수','찜','링크'])
        keyword = self.keyword.text()
        df.to_excel(f'네이버 가격비교; {keyword}.xlsx')
        self.textBrowser.append(f" '네이버 가격비교; {keyword}.xlsx' 저장 완료 !! \n")

    # 초기화 버튼 
    def reset(self):
        self.keyword.setText("")
        self.count.setText("")
        self.minPrice.setText("")
        self.maxPrice.setText("")
        self.fast_check.setChecked(False)
        self.free_check.setChecked(False)
        self.over_check.setChecked(False)
        self.textBrowser.setText("")

    # 종료 버튼 
    def quit(self):
       sys.exit()


app = QApplication()

window = MainWindow()
window.show()

sys.exit(app.exec())