from pathlib import Path
import json
import unicodedata
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QMenuBar, QToolBar, QMenu, QAction, QMessageBox, QWidget
from PyQt5.QtWidgets import QLabel, QPushButton, QPlainTextEdit, QLineEdit, QToolButton, QFileDialog, QSpinBox, QCheckBox, QStackedWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap
from PyQt5.QtCore import Qt, QUrl
from PyQt5 import  QtWebSockets
from label import TextLineLabel
from info_check import InfoCheck
from config import INFO_ITEMS

import csv

def jp_date(date):
  try:
    year = int(date[:4])
    month = int(date[4:6])
    day = int(date[6:])
    appendix = f'年{month}月{day}日'
    if 1867 < year <= 1911:
      date = f'明治{year - 1867}'
    if 1911 < year <= 1925:
      date = f'大正{year - 1911}'
    if 1925 < year <= 1988:
      date = f'昭和{year - 1925}'
    if 1988 < year <= 2018:
      date = f'平成{year - 1988}'
    if 2018 < year:
      date = f'令和{year - 2018}'
    return date + appendix
  except Exception as e:
    print(e)
    return date

class Mainwindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.init_ws()
    self.syukbn2idx = {}
    self.info_contents = {k: {} for k in INFO_ITEMS}
    self.info_titles = {k: {} for k in INFO_ITEMS}
    self.info_checkboxs = {k: {} for k in INFO_ITEMS}
    self.send_key = True
    self.info_layout = None

    self.init_gui()
    self.label = None
    
    info_check = None
    self.syukbn = None

  def init_ws(self):
    self.ws_client = QtWebSockets.QWebSocket()
    self.ws_client.textMessageReceived.connect(self.on_ws_msg)
    self.ws_client.error.connect(self.on_ws_err)
    self.ws_client.open(QUrl('ws://localhost:8766'))
    self.ws_client.connected.connect(self.show_ws_connect)

  def show_ws_connect(self):
    self.status_text.setText('バックエンドへ接続しました')

  def on_ws_msg(self, message):
    res = json.loads(message)
    if 'ImagePath' in res and 'SyuKbn' in res:
      if res['SyuKbn'] != 'Unknown':
        self.syukbn = res['SyuKbn']
        self.info_view.setCurrentIndex(self.syukbn2idx[self.syukbn])
        self.info_view.setVisible(True)
        item_req = {'Patient': {'Birthday': {}}, 'Insurance': {}}
        for k in INFO_ITEMS[res['SyuKbn']]:
          if k == 'Birthday':
            continue
          item_req['Insurance'][k] = {}
        self.ws_client.sendTextMessage(json.dumps(item_req))
      else:
        # self.syukbn = res['SyuKbn']
        self.status_text.setText('認識できませんでした。')
        self.status_text.setStyleSheet("QLabel { color : red; font-size: 22px; background: chartreuse;}")
        if self.syukbn in INFO_ITEMS:
          # print('80  ',res['SyuKbn'])
          # print(self.syukbn)
          # .setText('認識できませんでした。')
          # print('82  ',self.info_contents)
          for k in self.info_contents[self.syukbn]:
            # print('85  ',k)
            self.info_contents[self.syukbn][k].setText('認識できませんでした。')
          # self.info_view.setVisible(False)
          
        
    elif 'Patient' in res and 'Insurance' in res:
      required = INFO_ITEMS[self.syukbn]
      # print(self.gt_insurances[self.syukbn])
      for k in required:
        if k == 'Birthday':
          if k in res['Patient']:
            txt = res['Patient'][k]['text']
            if txt == self.gt_bdate:
              txt = 'PASS'
          else:
            txt = 'None'
        else:
          if k in res['Insurance']:
            txt = res['Insurance'][k]['text']
            if txt == '被保険者':
              txt = '本人'
            if txt == '被扶養者':
              txt = '家族'
            if self.gt_insurances is not None:
              if self.syukbn in self.gt_insurances:
                if k in self.gt_insurances[self.syukbn]:
                  if txt == self.gt_insurances[self.syukbn][k]:
                    txt = 'PASS'
          else:
            txt = 'None'
        is_visible = not txt == 'PASS'
        self.info_titles[self.syukbn][k].setVisible(is_visible)
        self.info_contents[self.syukbn][k].setVisible(is_visible)
        if ('Ymd' in k or 'Birthday' in k) and txt is not None:
          txt = jp_date(txt)
        if not isinstance(txt, str):
          txt = str(txt)
        self.info_contents[self.syukbn][k].setText(txt)
    self.send_key = True

  def on_ws_err(self, error_code):
    self.status_text.setText(f'WS Error Code: {error_code}, {self.ws_client.errorString()}')

  def init_gui(self):
    self.setWindowTitle('OCR Tester')
    self.setFont(self.get_font(15))
    # self.print_fonts()
   
    # menu
    self.setup_menu()
    self.setup_toolbar()
    self.setup_center()
    self.setup_status_bar()
    self.setMinimumSize(1080, 720)
    self.showMaximized()

  def setup_menu(self):
    self.menu_bar = QMenuBar(self)
    self.file = QMenu('フアイル', self)
    open_action = QAction('開く', self)
    open_action.setShortcut('Ctrl+O')
    save_action = QAction('保存', self)
    save_action.setShortcut('Ctrl+S')
    load_action = QAction('テスト記録を導入', self)
    load_action.triggered.connect(self.load_test_record)
    self.file.addAction(open_action)
    self.file.addAction(save_action)
    self.file.addAction(load_action)
    self.file.setFont(self.get_font(12))
    self.file.triggered[QAction].connect(self.file_menu_handler)
    self.menu_bar.addMenu(self.file)
    self.setMenuBar(self.menu_bar)

  def file_menu_handler(self, q):
    """
    Handle actions in the file menu
    """
    if q.text() == '開く':
      if self.tabs.currentIndex() == 0:
        self.open_insurance()
      if self.tabs.currentIndex() == 1:
        self.open_chip_label()

    if q.text() == '保存':
      if self.tabs.currentIndex() == 0:
        self.save_insurance()
      if self.tabs.currentIndex() == 1:
        self.save_chip_label()

  def save_insurance(self, path=None):
    path = QFileDialog.getSaveFileName(self, '保存パスを選ぶ', '/home/label/デスクトップ/')[0]
    if path is None or path == '':
      return
    if self.info_check is None:
      return
    self.info_check.save_to_file(path)
    self.save_insurance_csv(path)
    self.status_text2.setText(f'{path}に保存しました')

  def save_chip_label(self):
    path = QFileDialog.getSaveFileName(self, '保存パスを選ぶ')[0]
    if path is None:
      return
    self.save_choice()
    self.label.save_to_file(path)
    self.status_text.setText(f'{path}に保存しました')

  def open_insurance(self):
    # path = QFileDialog.getExistingDirectory(self, '画像フォールダーを選ぶ', '/home/label/file-remote/insurance_backup')
    path = QFileDialog.getExistingDirectory(self, '画像フォールダーを選ぶ', '/ori_img')
    if path is None or path == '':
      return
    if not Path(path).exists():
      return
    self.info_check = InfoCheck(path, self.xml_enable.isChecked())
    self.show_insurance(self.info_check.get_item())
    self.status_text.setText(f'テスト画像:　{len(self.info_check.checks)}枚')
    self.btn_goto_idx_insurance.setMaximum(len(self.info_check.checks))

  def open_chip_label(self): 
    path = QFileDialog.getOpenFileName(self, '再確認用データを選ぶ')[0]
    if path is None or path == '':
      return
    if not Path(path).exists():
      return
    self.label = TextLineLabel(path)
    self.status_text2.setText(f'再確認データ{len(self.label.check_list)}件を読込完了')
    self.show_chip(self.label.get_item())
    self.btn_goto_idx.setMaximum(len(self.label.check_list) - 1)

  def setup_toolbar(self):
    self.toolbar = QToolBar('toolbar', self)
    adv_vis = QAction('Adv Mode', self)
    self.toolbar.addAction(adv_vis)
    self.xml_enable = QCheckBox('XML比較', self)
    self.xml_enable.setChecked(False)
    self.xml_enable.stateChanged.connect(self.set_xml)
    self.toolbar.addWidget(self.xml_enable)
    self.reconnect_btn = QPushButton('バックエンド再接続', self)
    self.toolbar.addWidget(self.reconnect_btn)
    self.reconnect_btn.clicked.connect(self.ws_reconnect)
    self.invalid_ck = QCheckBox('不合格のみ表示', self)
    self.invalid_ck.setChecked(False)
    self.invalid_ck.stateChanged.connect(self.set_invalid)
    self.toolbar.addWidget(self.invalid_ck)
    self.addToolBar(self.toolbar)

  def ws_reconnect(self):
    self.ws_client.open(QUrl('ws://localhost:8766'))

  def set_xml(self):
    if self.info_check is None:
      return
    self.info_check.check_xml = self.xml_enable.isChecked()
    self.show_insurance(self.info_check.get_item())

  def set_invalid(self):
    if self.info_check is None:
      return
    self.info_check.invalid_only = self.invalid_ck.isChecked()

  def setup_status_bar(self):
    self.status_bar = QStatusBar()
    self.status_text = QLabel(self)
    self.status_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
    self.status_bar.addWidget(self.status_text)
    self.status_text2 = QLabel(self)
    self.status_text2.setTextInteractionFlags(Qt.TextSelectableByMouse)
    self.status_bar.addWidget(self.status_text2)
    self.setStatusBar(self.status_bar)

  def get_font(self, size, family='Noto Sans CJK JP Medium'):
    font = QFont(family, size)
    return font

  def setup_center(self):
    self.tabs = QTabWidget(self)
    self.setup_insurance_viwer()
    self.setup_label_checker()
    self.setCentralWidget(self.tabs)

  def setup_insurance_viwer(self):
    self.insurance_viewer = QWidget(self)
    
    img_row = QWidget(self)
    img_area = QWidget(self)
    self.img_view = QLabel(self)
    self.img_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    btn_row = QWidget(self)
    self.pass_btn = QPushButton('合格')
    self.pass_btn.clicked.connect(self.let_pass)
    self.fail_btn = QPushButton('不合格')
    self.fail_btn.clicked.connect(self.let_fail)
    self.att_btn = QPushButton('放置')
    self.att_btn.clicked.connect(self.let_att)
    self.fp_status = QLabel(self)
    self.fp_status.setFont(self.get_font(25))
    self.fp_status.setAlignment(Qt.AlignCenter)
    btn_layout = QHBoxLayout()
    btn_layout.addWidget(self.fp_status)
    btn_layout.addWidget(self.pass_btn)
    btn_layout.addWidget(self.fail_btn)
    btn_layout.addWidget(self.att_btn)
    btn_row.setLayout(btn_layout)
    ## 合格ボタンを隠す
    btn_row.setVisible(False)
    img_area_layout = QVBoxLayout()
    img_area_layout.addWidget(self.img_view)
    img_area_layout.addWidget(btn_row)
    img_area_layout.setContentsMargins(0, 0, 0, 0)
    img_area_layout.setSpacing(0)
    img_area.setLayout(img_area_layout)
    img_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.info_view = self.get_infos()
    self.info_view.setMinimumWidth(400)
    img_layout = QHBoxLayout()
    img_layout.addWidget(img_area)
    img_layout.addWidget(self.info_view)
    img_layout.setContentsMargins(0, 0, 0, 0)
    img_layout.setSpacing(0)
    img_row.setLayout(img_layout)
    
    # row for ctrl buttons
    btn_row = QWidget(self)
    self.btn_next_insurance = QPushButton('次へ', self)
    self.btn_next_insurance.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.btn_next_insurance.clicked.connect(self.show_next_insurance)
    self.btn_prev_insurance = QPushButton('前へ', self)
    self.btn_prev_insurance.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.btn_prev_insurance.clicked.connect(self.show_prev_insurance)
    self.btn_goto_idx_insurance = QSpinBox(self)
    self.btn_goto_idx_insurance.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
    self.btn_goto_idx_insurance.setMinimum(0)
    self.btn_goto_idx_insurance.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
    self.btn_goto_insurance = QPushButton('枚目へ', self)
    self.btn_goto_insurance.clicked.connect(self.show_certain_insurance)
    btn_layout = QHBoxLayout()
    btn_layout.addWidget(self.btn_prev_insurance)
    btn_layout.addWidget(self.btn_next_insurance)
    btn_layout.addWidget(self.btn_goto_idx_insurance)
    btn_layout.addWidget(self.btn_goto_insurance)
    btn_row.setLayout(btn_layout)

    insurance_layout = QVBoxLayout()
    insurance_layout.addWidget(img_row)
    insurance_layout.addWidget(btn_row)
    insurance_layout.setContentsMargins(0, 0, 0, 0)
    insurance_layout.setSpacing(0)
    self.insurance_viewer.setLayout(insurance_layout)
    self.tabs.addTab(self.insurance_viewer, '保険証確認')

  def get_infos(self):
    info_view = QStackedWidget(self)
    
    for syukbn_idx, syukbn in enumerate(INFO_ITEMS.keys()):
      info = QWidget(self)
      info.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
      layout = QGridLayout()
      title = QLabel('主区分', self)
      title.setFont(self.get_font(25))
      
      layout.addWidget(title, 0, 1)
      content = QLabel(syukbn, self)
      content.setFont(self.get_font(25))

      layout.addWidget(content, 0, 2)
      print(INFO_ITEMS[syukbn])
      for idx, k in enumerate(INFO_ITEMS[syukbn]):
        title = QLabel(INFO_ITEMS[syukbn][k], self)
        title.setFont(self.get_font(25))
        title.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        content = QLabel(self)
        content.setFont(self.get_font(25))
        content.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        content.setAlignment(Qt.AlignLeft)
        content.setAlignment(Qt.AlignVCenter)
        checkbox = QCheckBox(k)
        # print('357  ',checkbox.text())

        checkbox.setFont(self.get_font(25))
        layout.addWidget(title, idx + 1, 1)
        layout.addWidget(content, idx + 1, 2)
        layout.addWidget(checkbox, idx + 1, 3)
        self.info_contents[syukbn][k] = content
        self.info_titles[syukbn][k] = title

        self.info_checkboxs[syukbn][k] = checkbox
        # self.info_checkboxs[syukbn][k].stateChanged.connect(lambda:self.btnstate(self.info_checkboxs[syukbn][k]))
        self.info_checkboxs[syukbn][k].toggled.connect(
                lambda state, checkbox=checkbox: self.checkBoxState(checkbox)  # +++
            )


        
      info.setLayout(layout)
      self.syukbn2idx[syukbn] = syukbn_idx
      info_view.addWidget(info)
    return info_view

  def get_info(self, title, content):
    info_row = QWidget(self)
    info_title = QLabel(title, self)
    info_content = QLabel(content, self)
    info_layout = QHBoxLayout()
    info_layout.addWidget(info_title)
    info_layout.addWidget(info_content)
    info_layout.setContentsMargins(0, 0, 0, 0)
    info_row.setLayout(info_layout)
    return info_row

  def setup_label_checker(self):
    """
    View training data and compare with predictions from the current model
    """
    self.label_checker = QWidget(self)
    self.chip_view = QLabel(self)
    self.chip_view.setAlignment(Qt.AlignCenter)
    self.chip_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    self.eq_txt = QLabel(self)
    self.eq_txt.setFont(self.get_font(25))
    self.eq_txt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    # row showing training data    
    self.label_txt = QLabel(self)
    self.label_txt.setFont(self.get_font(25))
    self.label_txt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.label_txt.setTextInteractionFlags(Qt.TextSelectableByMouse)

    label_title = QLabel('既存データ', self)
    label_title.setAlignment(Qt.AlignVCenter)
    label_title.setMinimumWidth(150)
    label_btn = QPushButton('採用', self)
    label_btn.clicked.connect(self.choose_label)
    label_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    # row showing pred data
    pred_title = QLabel('OCR出力', self)
    pred_title.setAlignment(Qt.AlignVCenter)
    pred_title.setMinimumWidth(150)
    self.pred_txt = QLabel(self)
    self.pred_txt.setFont(self.get_font(25))
    self.pred_txt.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.pred_txt.setTextInteractionFlags(Qt.TextSelectableByMouse)
    pred_btn = QPushButton('採用', self)
    pred_btn.clicked.connect(self.choose_pred)
    pred_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    cmp_grid = QWidget()
    cmp_layout = QGridLayout()
    cmp_layout.addWidget(self.eq_txt, 1, 1)
    cmp_layout.addWidget(label_title, 2, 1)
    cmp_layout.addWidget(self.label_txt, 2, 2)
    cmp_layout.addWidget(label_btn, 2, 3)
    cmp_layout.addWidget(pred_title, 3, 1)
    cmp_layout.addWidget(self.pred_txt, 3, 2)
    cmp_layout.addWidget(pred_btn, 3, 3)
    cmp_grid.setLayout(cmp_layout)

    # row for confirmation
    confirm_row = QWidget(self)
    confirm_title = QLabel('正しい文字列', self)
    confirm_title.setMinimumWidth(150)
    self.confirm_txt = QLineEdit(self)
    confirm_layout = QHBoxLayout()
    confirm_layout.addWidget(confirm_title)
    confirm_layout.addWidget(self.confirm_txt)
    confirm_row.setLayout(confirm_layout)

    # row for ctrl buttons
    btn_row = QWidget(self)
    self.btn_next_chip = QPushButton('次へ', self)
    self.btn_next_chip.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.btn_next_chip.clicked.connect(self.show_next_chip)
    self.btn_prev_chip = QPushButton('前へ', self)
    self.btn_prev_chip.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.btn_prev_chip.clicked.connect(self.show_prev_chip)
    self.btn_goto_idx = QSpinBox(self)
    self.btn_goto_idx.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
    self.btn_goto_idx.setMinimum(0)
    self.btn_goto_idx.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
    self.btn_goto_chip = QPushButton('枚目へ', self)
    self.btn_goto_chip.clicked.connect(self.show_certain_chip)
    btn_layout = QHBoxLayout()
    btn_layout.addWidget(self.btn_prev_chip)
    btn_layout.addWidget(self.btn_next_chip)
    btn_layout.addWidget(self.btn_goto_idx)
    btn_layout.addWidget(self.btn_goto_chip)
    btn_row.setLayout(btn_layout)

    layout = QVBoxLayout()
    layout.addWidget(self.chip_view)
    layout.addWidget(cmp_grid)
    layout.addWidget(confirm_row)
    layout.addWidget(btn_row)
    layout.setAlignment(Qt.AlignBottom)
    
    self.label_checker.setLayout(layout)
    self.tabs.addTab(self.label_checker, '学習データ確認')

  def save_choice(self):
    item = self.label.get_item()
    item['y_confirm'] = self.confirm_txt.text()
    self.label.save_item(item)
    self.label.save_to_file('./check_list_tmp.pkl')
    n_confirmed = sum(['y_confirm' in r for r in self.label.check_list])
    total = len(self.label.check_list)
    n_unconfirmed = total - n_confirmed
    self.status_text.setText(f'確認済：　{n_confirmed}件　　未確認:　{n_unconfirmed}件    合計: {total} 件')

  def show_next_chip(self):
    if self.label is None:
      return
    self.save_choice()
    item = self.label.next()
    self.show_chip(item)

  def show_prev_chip(self): 
    if self.label is None:
      return
    self.save_choice()
    item = self.label.prev()
    self.show_chip(item)

  def show_certain_chip(self):
    if self.label is None:
      return
    self.save_choice()
    idx = self.btn_goto_idx.value()
    if isinstance(idx, int):
      item = self.label.jump(idx)
      self.show_chip(item)

  def show_chip(self, item):
    img_path = item['path']
    img_path = img_path.replace('/datasets/', '/home/wangg/datasets_remote/')
    self.chip_view.setPixmap(QPixmap(img_path).scaled(self.chip_view.size(), Qt.KeepAspectRatio))
    #self.eq_txt.setText(eq)
    self.label_txt.setText(item['y_true'])
    self.pred_txt.setText(item['y_pred'])
    if 'y_confirm' in item:
      self.confirm_txt.setText(item['y_confirm'])
    else:
      self.confirm_txt.setText('')

  def show_next_insurance(self):
    if self.info_check is None:
      return
    if self.syukbn in INFO_ITEMS:
      for k in self.info_contents[self.syukbn]:
        self.info_contents[self.syukbn][k].setText('')
    
    insurance = self.info_check.next()
    print('next')
    info_checks = self.info_check.get_info_checkbox()
    self.set_checkbox_status(info_checks)

    if self.send_key:
      self.show_insurance(insurance)
      self.send_key = False

  def show_prev_insurance(self):
    if self.info_check is None:
      return
    if self.syukbn in INFO_ITEMS:
      for k in self.info_contents[self.syukbn]:
        self.info_contents[self.syukbn][k].setText('')
    insurance = self.info_check.prev()

    print('prev')
    info_checks = self.info_check.get_info_checkbox()
    self.set_checkbox_status(info_checks)



    if self.send_key:
      self.show_insurance(insurance)
      self.send_key = False

  def show_certain_insurance(self):
    if self.info_check is None:
      return
    insurance = self.info_check.jump(self.btn_goto_idx_insurance.value())
    self.show_insurance(insurance)
    

  def show_insurance(self, insurance):
    img_path, self.infos, self.gt_bdate, self.gt_insurances = insurance
    self.img_view.setPixmap(QPixmap(img_path).scaled(self.img_view.size(), Qt.KeepAspectRatio))
    #self.ws_client.sendTextMessage(json.dumps({"Scan": img_path.replace('/label/', '/smapa/').replace('/wangg/', '/smapa/')}))
    print(json.dumps({"Scan": img_path.replace('/label/', '/smapa/')}))
    self.ws_client.sendTextMessage(json.dumps({"Scan": img_path.replace('/label/', '/smapa/')}))
    self.status_text2.setText(f'{self.info_check.idx + 1}/{len(self.info_check.keys)} 枚　　{Path(img_path).name}')
    if 'mark' in self.infos:
      if self.infos['mark'] == 'pass':
        self.fp_status.setText('合格')
      elif self.infos['mark'] == 'fail':
        self.fp_status.setText('不合格')
      else:
        self.fp_status.setText('一時放置')
    else:
      self.fp_status.setText('未確認')
    self.update_insurance_stats()
    if self.info_check.idx != 0:
      self.info_check.save_to_file('./insurance_check.tmp')

  def let_pass(self):
    if self.info_check is None:
      return
    self.info_check.mark_pass()
    self.fp_status.setText('合格')
    self.update_insurance_stats()

  def let_fail(self):
    if self.info_check is None:
      return
    self.info_check.mark_fail()
    self.fp_status.setText('不合格')
    self.update_insurance_stats()

  def let_att(self):
    if self.info_check is None:
      return
    self.info_check.mark_att()
    self.fp_status.setText('一時放置')
    self.update_insurance_stats()

  def update_insurance_stats(self):
    n_pass, n_fail, n_other, n_att, total = self.info_check.get_stats()
    msg = f'合格: {n_pass}  不合格: {n_fail}  一時放置: {n_att}　未確認: {n_other}     '
    self.status_text.setStyleSheet("QLabel { color : black; font-size: 22px; }")
    self.status_text.setText(msg)

  def print_fonts(self):
    print(QFontDatabase().families())

  def choose_pred(self):
    self.confirm_txt.setText(self.pred_txt.text())

  def choose_label(self):
    self.confirm_txt.setText(self.label_txt.text())

  def load_test_record(self):
    path = QFileDialog.getOpenFileName(self, 'テスト記録を選ぶ', '/home/label/デスクトップ/')[0]
    if path is None or path == '':
      return
    if not Path(path).exists():
      return
    self.info_check = InfoCheck('./', self.xml_enable.isChecked())
    self.info_check.load_from_file(path)
    self.show_insurance(self.info_check.get_item())

  def closeEvent(self, e):
    answer = QMessageBox.question(
      self, None,
      'quit',
      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
    )
    if answer & QMessageBox.Save:
      if self.tabs.currentIndex() == 0:
        self.save_insurance()
      if self.tabs.currentIndex() == 1:
        self.save_chip_label()
    elif answer & QMessageBox.Cancel:
      e.ignore()

  def checkBoxState(self,b):
    info_check = {}
    for k,v in self.info_checkboxs['主保険'].items():
      # print('646  ',k)
      info_check[str(v.text())]=v.isChecked()
      # print('654 ',f"{v.text()}:  {v.isChecked()}")
    if self.info_check:
      self.info_check.set_info_checkbox(info_check)

  def set_checkbox_status(self,info_checks):
    # print(info_checks)
    if info_checks:
      for k,v in self.info_checkboxs['主保険'].items():
        # print('659 ',v,info_checks[k])
        v.setChecked(info_checks[k])
    else:
      for k,v in self.info_checkboxs['主保険'].items():
        v.setChecked(False)
        
  def save_insurance_csv(self,path):
    category = INFO_ITEMS['主保険']
    with open(path+'.csv', 'w', newline='') as csvfile:
      fieldnames = ['img_path', 'error']
      writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
      writer.writeheader()
      for key in list(self.info_check.checks.keys()):
        data_value = self.info_check.checks[key]
        errors_status = []
        if data_value == {}:
          pass
        else:   
          info_checkbox = data_value['info_checkbox']
          for i in list(info_checkbox.keys()):
            if info_checkbox[i]:
              errors_status.append(category[i])
        print(errors_status)
        writer.writerow({'img_path': key, 'error': errors_status})