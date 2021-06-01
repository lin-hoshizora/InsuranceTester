ITEMS = {
  '主保険': {
    "Patient": {
      "Birthday": {} 
    },
    "Insurance": {
      "SyuKbn": "主保険",
      "HknjaNum": {},
      "Kigo": {},
      "Num": {},
      "HonKzkKbn": {},
      "YukoEdYmd": {},
      "RouFtnKbn": {},
      "SkkGetYmd": {},
      "HknjaName": {},
      "KofuYmd": {},
    }
  },
  '公費': {
    "Patient": {
      "Birthday": {} 
    },
    "Insurance": {
      "SyuKbn": "公費",
      "HknjaNum": {},
      "Num": {},
      "YukoStYmd": {},
      "YukoEdYmd": {},
      "RouFtnKbn": {},
      "JgnGak": {},
      "HknjaName": {},
      "KofuYmd": {},
    }
  },
  '高齢受給者': {
    "Patient": {
      "Birthday": {} 
    },
    "Insurance": {
      "SyuKbn": "高齢受給者",
      "YukoStYmd": {},
      "YukoEdYmd": {},
      "RouFtnKbn": {},
      "KofuYmd": {},
    }
  },
  '限度額認証': {
    "Patient": {
      "Birthday": {} 
    },
    "Insurance": {
      "SyuKbn": "限度額認証",
      "YukoStYmd": {},
      "YukoEdYmd": {},
      "RouFtnKbn": {},
      "KofuYmd": {},
    }
  },
}

ITEM_NAME = {
  "SyuKbn": "主区分",
  "Birthday": "生年月日",
  "HknjaNum": "保険者名",
  "Kigo": "記号",
  "Num": "番号",
  "HonKzkKbn": "本人家族区分",
  "YukoStYmd": "有効開始日",
  "YukoEdYmd": "有効終了日",
  "RouFtnKbn": "高齢負担区分",
  "JgnGak": "限度額",
  "SkkGetYmd": "資格取得日",
  "HknjaName": "受給者名",
  "KofuYmd": "交付年月日",
}

ITEM_CODE = {ITEM_NAME[code]: code for code in ITEM_NAME}