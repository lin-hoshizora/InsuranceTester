from pathlib import Path
import pickle
import cv2

class TextLineLabel:
  def __init__(self, path):
    with open(path, 'rb') as f:
      self.check_list = pickle.load(f)
    self.idx = 0
    self.next()

  def get_item(self):
    item = self.check_list[self.idx]
    return item

  def next(self):
    while ('y_confirm' in self.get_item()):
      self.idx += 1
      if self.idx == len(self.check_list):
        self.idx -= 1
        break
      print(self.idx)
    return self.get_item()

  def prev(self):
    if self.idx > 0:
      self.idx -= 1
    return self.get_item()

  def jump(self, idx):
    if 0 <= idx < len(self.check_list):
      self.idx = idx
    return self.get_item()

  def save_item(self, item):
    self.check_list[self.idx] = item

  def save_to_file(self, path):
    with open(path, 'wb') as f:
      pickle.dump(self.check_list, f)
