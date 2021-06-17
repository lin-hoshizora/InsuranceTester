from pathlib import Path
import pickle
import unicodedata
import xml.etree.ElementTree as ET


class InfoCheck:
  def __init__(self, path, check_xml):
    self.checks = {str(p): {'info_checkbox':{},'skip':{},'HknjaNum':{},'syukbn':{}} for p in Path(path).glob('*.jpg')}
    for p in Path(path).glob('*.png'):
      self.checks[str(p)] = {'info_checkbox':{},'skip':{},'HknjaNum':{},'syukbn':{}}
    self.keys = list(self.checks.keys())
    self.idx = 0
    self.check_xml = check_xml
    self.findex_folder = Path('/home/label/mnt_findex/')
    self.gt_folder = self.findex_folder / 'Almex/01_Patient/Output/done/'
    self.invalid_only = False
    




  def get_gt(self, img_path):
    if not self.findex_folder.is_mount():
      print('XML folder not mounted!')
      return
    img_path = Path(img_path)
    xml_paths = list(self.gt_folder.glob(f'{img_path.stem[:-2]}*'))
    if not xml_paths:
      return
    root = ET.parse(str(xml_paths[0])).getroot()
    bdate = root.find('Patient').find('Birthday').text
    insurances = {}
    kbns = ['主保険', '公費', '高齢受給者', '限度額認証']
    for child in root.find('Insurances').findall('Insurance'):
      syukbn = kbns[int(child.find('SyuKbn').text) - 1]
      insurances[syukbn] = {}
      for item in child:
        if item.tag in ['SyuKbn', 'DspSeq', 'KakuninYmd']:
          continue
        insurances[syukbn][item.tag] = unicodedata.normalize('NFKC', item.text) if item.text is not None else item.text
      insurances[syukbn]['HknjaName'] = root.find('Patient').find('Name').text.replace('\u3000', '').replace(' ', '')
    # print(insurances)
    return bdate, insurances

  def get_item(self):
    img_path = self.keys[self.idx]
    records = self.checks[img_path]
    if self.check_xml:
      bdate, insurances = self.get_gt(img_path)
    else:
      bdate = insurances = None
    return img_path, records, bdate, insurances

  def next(self):
    if self.invalid_only:
      while True:
        if self.idx < len(self.keys) - 1:
          self.idx += 1
          ck = self.checks[self.keys[self.idx]]
          if 'mark' in ck:
            if ck['mark'] == 'fail':
              break
        else:
          break
    else:
      if self.idx < len(self.keys) - 1:
        self.idx += 1
    return self.get_item()

  def prev(self):
    if self.invalid_only:
      while True:
        if self.idx > 0:
          self.idx -= 1
          ck = self.checks[self.keys[self.idx]]
          if 'mark' in ck:
            if ck['mark'] == 'fail':
              break
        else:
          break
    else:
      if self.idx > 0:
        self.idx -= 1
    return self.get_item()

  def jump(self, idx):
    if 0 <= self.idx < len(self.keys):
      self.idx = idx
    return self.get_item()

  def mark_pass(self):
    self.checks[self.keys[self.idx]]['mark'] = 'pass'

  def mark_fail(self):
    self.checks[self.keys[self.idx]]['mark'] = 'fail'

  def mark_att(self):
    self.checks[self.keys[self.idx]]['mark'] = 'attention'

  def get_stats(self):
    total = len(self.keys)
    n_pass = sum([r['mark'] == 'pass' for k, r in self.checks.items() if 'mark' in r])
    n_fail = sum([r['mark'] == 'fail' for k, r in self.checks.items() if 'mark' in r])
    n_att = sum([r['mark'] == 'attention' for k, r in self.checks.items() if 'mark' in r])
    n_other = total - n_fail - n_pass - n_att 
    return n_pass, n_fail, n_other, n_att, total

  def save_to_file(self, path):
    with open(path+'.pkl', 'wb') as f:
      pickle.dump(self.checks, f)

  def load_from_file(self, path):
    with open(path, 'rb') as f:
      self.checks = pickle.load(f)
    self.keys = list(self.checks.keys())
    self.idx = 0
  

  def set_info_checkbox(self,checkboxs_staus):
    self.checks[list(self.checks.keys())[self.idx]]['info_checkbox'] = checkboxs_staus
    
  def get_info_checkbox(self):
    if self.checks[list(self.checks.keys())[self.idx]] == {}:
      return False
    else:
      return self.checks[list(self.checks.keys())[self.idx]]['info_checkbox']


  def set_info_skip(self,info_skip):
    self.checks[list(self.checks.keys())[self.idx]]['skip'] = info_skip
    for i in list(self.checks.keys()):
      print(F"{self.checks[i]}")


  def set_hkNum(self,hkNum):
    self.checks[list(self.checks.keys())[self.idx]]['HknjaNum'] = hkNum

  def set_syukbn(self,syukbn):
    self.checks[list(self.checks.keys())[self.idx]]['syukbn'] = syukbn