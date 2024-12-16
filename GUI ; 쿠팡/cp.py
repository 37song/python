from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QButtonGroup

from cp_ui import Ui_Form
import sys
import requests

import os
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
import pandas as pd
import time
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

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

        # 체크 박스
        self.button_group = QButtonGroup(self)
        self.rocket.stateChanged.connect(self.handle_rocket_checkbox)
        self.free.stateChanged.connect(self.handle_free_checkbox)
        self.button_group.setExclusive(True)

    # 체크 박스
    def handle_rocket_checkbox(self, state):
        if state == Qt.Checked:
            filterType = 'rocket%2Cfree'
            # free 체크박스를 해제
            self.free.setChecked(False)
        elif state == Qt.Unchecked:
            filterType = ''
    def handle_free_checkbox(self, state):
        if state == Qt.Checked:
            filterType = 'free'
            # rocket 체크박스를 해제
            self.rocket.setChecked(False)
        elif state == Qt.Unchecked:
            filterType = ''

    # 스타트 버튼 
    def start(self):
        keyword = self.keyword.text()
        star = self.star.text()
        page = int(self.page.text())
        minPrice = self.minPrice.text()
        maxPrice = self.maxPrice.text()

        # filterType 값 설정
        if self.rocket.isChecked():
            self.filterType = 'rocket'
        elif self.free.isChecked():
            self.filterType = 'free'
        else:
            self.filterType = ''

        #  정렬(sorter) 값 설정
        current_selection_index = self.sort_box.currentIndex()
        if current_selection_index == 0:
            sorter = 'scoreDesc'
        elif current_selection_index == 1:
            sorter = 'salePriceAsc'
        elif current_selection_index == 2:
            sorter = 'salePriceDesc'
        elif current_selection_index == 3:
            sorter = 'saleCountDesc'
        elif current_selection_index == 4:
            sorter = 'latestAsc'
        else:            
            sorter = ''

        # 크롬 실행
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options = chrome_options)
        driver.implicitly_wait(5)
        
        # Selenium 감지 속성 제거
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
                })
                """
            }
        )

        self.result = []

        for p in range(1, page+1) :
            self.url = f'https://www.coupang.com/np/search?rocketAll=false&searchId=&q={keyword}&brand=&offerCondition=&filter=&availableDeliveryFilter=&filterType={self.filterType}&isPriceRange=true&priceRange={minPrice}&minPrice={minPrice}&maxPrice={maxPrice}&page={p}&trcid=&traid=&filterSetByUser=true&channel=user&backgroundColor=&searchProductCount=&component=&rating={star}&sorter={sorter}&listSize=36'
            driver.get(self.url)
            driver.implicitly_wait(5)
            items = driver.find_elements(By.CSS_SELECTOR, ".search-product:not(.search-product__ad-badge):not(.best-seller-carousel-item)")
            best = driver.find_elements(By.CSS_SELECTOR, ".search-product.best-seller-carousel-item")[:5]

        # best 상품 상위 5개 result 에 추가
            if driver.find_elements(By.CSS_SELECTOR, ".search-product.best-seller-carousel-item") == [] :
                pass
            else:
                for b in best :
                    try:
                        name = '★ ' + b.find_element(By.CSS_SELECTOR, 'div.name').text
                    except:
                        name = ''
                    try:
                        link = b.find_element(By.CSS_SELECTOR, '.search-product > a').get_attribute('href')
                    except:
                        link = ''
                    try:
                        price = int(b.find_element(By.CSS_SELECTOR, 'strong.price-value').text.replace(',',''))
                    except:
                        price = ''
                    try:
                        rating = float(b.find_element(By.CSS_SELECTOR, 'span.star > em.rating').text)
                    except:
                        rating = '-'
                    try:
                        review = int(b.find_element(By.CSS_SELECTOR, 'span.rating-total-count').text.strip('(').strip(')'))
                    except:
                        review = '-'
                self.result.append([name, link, price, rating, review])

        # 일반 상품 result 에 추가
            for i in items :
                name = i.find_element(By.CSS_SELECTOR, 'div.name').text
                link = i.find_element(By.CSS_SELECTOR, '.search-product > a').get_attribute('href')
                price = int(i.find_element(By.CSS_SELECTOR, 'strong.price-value').text.replace(',',''))
                try:
                    rating = float(i.find_element(By.CSS_SELECTOR, 'span.star > em.rating').text)
                except:
                    rating = '-'
                try:
                    review = int(i.find_element(By.CSS_SELECTOR, 'span.rating-total-count').text.strip('(').strip(')'))
                except:
                    review = '-'
                self.result.append([name, link, price, rating, review])
            self.textBrowser.append(f' - {p}쪽 크롤링 완료 - \n')
            QApplication.processEvents()


        # textBrowser 출력
        count = len(self.result)
        page = self.page.text()
        self.textBrowser.append(f' ~~ {page}쪽까지, 총 {count}개 제품 크롤링 완료 ~~ ')

    # 저장 버튼 
    def save(self):
        df = pd.DataFrame(self.result, columns=['상품명','링크','가격','별점','리뷰 수'])
        keyword = self.keyword.text()
        df.to_excel(f'{keyword}.xlsx')
        self.textBrowser.append(f'\n {keyword}.xlsx 저장 완료 !! \n')

    # 초기화 버튼 
    def reset(self):
        self.keyword.setText("")
        self.page.setText("")
        self.star.setText("")
        self.minPrice.setText("")
        self.maxPrice.setText("")
        self.rocket.setChecked(False)
        self.free.setChecked(False)
        self.textBrowser.setText("")

    # 종료 버튼 
    def quit(self):
       sys.exit()


app = QApplication()

window = MainWindow()
window.show()

sys.exit(app.exec())
    