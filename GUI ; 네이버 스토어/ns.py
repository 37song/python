from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QButtonGroup
from ns_ui import Ui_Form
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

        # 기본 값으로 속성 초기화
        self.official = ''
        self.free = ''
        self.include = ''
        self.star48 = ''

        # 체크박스 이벤트 핸들러 연결
        self.off_check.stateChanged.connect(self.handle_off_check)
        self.free_check.stateChanged.connect(self.handle_free_check)
        self.include_check.stateChanged.connect(self.handle_include_check)
        self.star48_check.stateChanged.connect(self.handle_star48_check)


    # 체크 박스
    def handle_off_check(self, state):
        actual_state = self.off_check.isChecked()
        if actual_state:
            self.official = '&mallTypes=OFFICIAL_CERTIFIED'
        else:
            self.official = ''
    def handle_free_check(self, state):
        actual_state = self.free_check.isChecked()
        if actual_state:
            self.free = '&recommendedDeliveries=FREE_DELIVERY'
        else:
            self.free = ''
    def handle_include_check(self, state):
        actual_state = self.include_check.isChecked()
        if actual_state:
            self.include = '&includedDeliveryFee=true'
        else:
            self.include = ''
    def handle_star48_check(self, state):
        actual_state = self.star48_check.isChecked()
        if actual_state:
            self.star48 = '&score=4.8%7C5'
        else:
            self.star48 = ''


    # 스타트 버튼 
    def start(self):
        self.search = self.keyword.text()
        self.number = int(self.count.text())
        minPrice = self.minPrice.text()
        maxPrice = self.maxPrice.text()
        if minPrice == '':
            self.priceRange = ''
        else:
            self.priceRange = f'&priceRange={minPrice}%7C{maxPrice}'

        #  정렬(sorter) 값 설정
        current_selection_index = self.sort_box.currentIndex()
        if current_selection_index == 0:
            self.sort = 'RECOMMEND'
        elif current_selection_index == 1:
            self.sort = 'LOW_PRICE'
        elif current_selection_index == 2:
            self.sort = 'HIGH_PRICE'
        elif current_selection_index == 3:
            self.sort = 'PURCHASE'
        elif current_selection_index == 4:
            self.sort = 'REVIEW'
        elif current_selection_index == 5:
            self.sort = 'RECENT'
        else:            
            self.sort = ''

        url = f'https://search.shopping.naver.com/ns/search?query={self.search}{self.official}{self.free}{self.include}{self.star48}{self.priceRange}&sort={self.sort}&related=ON'

        # 크롬 실행
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options = chrome_options)
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        self.result = []

        while len(self.result) < self.number:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # 페이지 로드를 기다림
            divs = driver.find_elements(By.CSS_SELECTOR, 'div.basicProductCardInformation_basic_product_card_information__7v_uc.basicProductCardInformation_view_type_grid2__mlh6E')
            
            for div in divs:
                if not div.find_elements(By.CSS_SELECTOR, '.basicProductCardInformation_advertisement_area__HzaQ_'):
                    name = div.find_element(By.CSS_SELECTOR, 'strong.basicProductCardInformation_title__Bc_Ng').text
                    # 데이터 중복 체크
                    if name not in [x[1] for x in self.result]:
                        com = div.find_element(By.CSS_SELECTOR, 'span.basicProductCardInformation_mall_name__8IS3Q').text
                        price = int(div.find_element(By.CSS_SELECTOR, 'span.priceTag_inner_price__TctbK').text.split('\n')[0].replace(',', ''))
                        link = div.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
                        try:
                            star = float(div.find_element(By.CSS_SELECTOR, 'span.productCardReview_star__7iHNO').text.split('\n')[1])
                        except:
                            star = ''
                        try:
                            review = div.find_element(By.CSS_SELECTOR, 'span.productCardReview_text__A9N9N:not(.productCardReview_star__7iHNO)').text.split(' ')[1]
                        except:
                            review = ''
                        self.result.append([com, name, price, link, star, review])
                self.lenth = len(self.result)
                self.textBrowser.append(f'- {self.lenth}개 상품 크롤링 완료 - \n')
                QApplication.processEvents()
        self.textBrowser.append(f' ~ 크롤링 완료 ~ \n')


    # 저장 버튼 
    def save(self):
        df = pd.DataFrame(self.result, columns=['업체명','상품명','가격','링크','별점','리뷰 수'])
        keyword = self.keyword.text()
        df.to_excel(f'네이버 스토어; {keyword}.xlsx')
        self.textBrowser.append(f" '네이버 스토어; {keyword}.xlsx' 저장 완료 !! \n")


    # 초기화 버튼 
    def reset(self):
        self.keyword.setText("")
        self.count.setText("")
        self.minPrice.setText("")
        self.maxPrice.setText("")
        self.off_check.setChecked(False)
        self.free_check.setChecked(False)
        self.include_check.setChecked(False)
        self.star48_check.setChecked(False)
        self.textBrowser.setText("")

    # 종료 버튼 
    def quit(self):
       sys.exit()


app = QApplication()

window = MainWindow()
window.show()

sys.exit(app.exec())