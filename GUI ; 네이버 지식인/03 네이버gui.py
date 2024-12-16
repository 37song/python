from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget
from naver_kin_ui import Ui_Form
import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd


class MainWindow(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # self.객체이름.clicked.connect(self.실행할메서드이름)
        self.start_btn.clicked.connect(self.start)
        self.reset_btn.clicked.connect(self.reset)
        self.save_btn.clicked.connect(self.save)
        self.quit_btn.clicked.connect(self.quit)

    def start(self):
        input_keyword = self.keyword.text()
        input_page = int(self.page.text())

        self.result =[]
        for i in range(1, input_page + 1):
            self.textBrowser.append(f'-----{i} 페이지-----')
            response = requests.get(f'https://kin.naver.com/search/list.naver?query={input_keyword}&page={input_page}')
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            posts = soup.select('.basic1 > li')
            for post in posts:
                title = post.select_one('._searchListTitleAnchor').text
                link = post.select_one('._searchListTitleAnchor').attrs['href']
                date = post.select_one('.txt_inline').text
                cate = post.select_one('.txt_block > a:nth-of-type(2)').text
                resp = int(post.select_one('.txt_block > span:nth-of-type(2)').text.split(' ')[1])
                self.textBrowser.append(title)
                QApplication.processEvents()
                self.result.append([title, link, date, cate, resp])

        self.textBrowser.append('~~~ 크롤링 끝 ~~~')

    def reset(self):
        self.keyword.setText('')
        self.page.setText('')
        self.textBrowser.setText('')

    def save(self):
        input_keyword = self.keyword.text()

        df = pd.DataFrame(self.result, columns=['제목','링크','날짜','카테고리','답변수'])
        df.to_excel(f'{input_keyword}.xlsx')

    def quit(self):
        sys.exit()

app = QApplication()

window = MainWindow()
window.show()

sys.exit(app.exec())



        
