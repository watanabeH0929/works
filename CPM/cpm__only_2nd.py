# 現よちよち客がよちよち客になるまでの経過時間（単位: 週）

import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import openpyxl

os.chdir(Path(__file__).parent)

# ここ ----------------------------------------------------
#ecforceから落としたcsvデータの読み込み
df = pd.read_csv('./order_csv/orderCSV_LPEC__samurai.csv', encoding='utf-8')
# ここ ----------------------------------------------------


df['実売上日'] = pd.to_datetime(df['実売上日'], format='%Y/%m/%d')
df['生年月日'] = pd.to_datetime(df['生年月日'], format='%Y/%m/%d')


# =============================
# 条件（iloc 用）
# =============================
mask = df["顧客購入回数"] >= 2

second = (
    df.iloc[mask.values]     # ← 計算対象だけ絞る
      .groupby("顧客ID")["実売上日"]
      .nsmallest(2)
      .groupby(level=0)
      .nth(1)
      .rename("購入2回目")
)

print("\n=== second ===")
print(second)

# =============================
# agg（通常集計）と merge
# =============================
agg = (
    df.groupby('顧客ID')
    .agg(
        購入回数 = ('顧客購入回数', 'max'),
        初回購入日 = ('実売上日', 'min'),
        最終購入日 = ('実売上日', 'max'),
    )
    .merge(second, on='顧客ID', how='right')
    .reset_index()
)

agg['2回目までの日数'] = (agg['購入2回目'] - agg['初回購入日']).dt.days
agg['何週以内に買うか'] = (agg['2回目までの日数'] // 7)

# ===== よちよち客に絞り込み =====
# 初回～直近の期間算出
agg['期間'] = (agg['最終購入日'] - agg['初回購入日']).dt.days
mask_period = agg['期間'] < 90
agg = agg.iloc[mask_period.values]

# 出力時の並び変更
desired_order= ['顧客ID','購入回数','初回購入日','購入2回目','2回目までの日数','何週以内に買うか']
agg = agg[desired_order]

print('==== aggを出力する =====')
print(agg)


# ======== 円グラフ化 start ========
plt.rcParams.update({'font.size':10})
plt.rcParams['font.family'] = 'Yu Gothic'

# 集計
purchase_week = agg['何週以内に買うか'].value_counts()
# print('==== 何週以内に買うかの集計結果 =====')
# print(purchase_week)

label = purchase_week.keys()
point = [0.1,0,0,0,0,0,0,0,0,0,0,0,0] #切り離して強調表示
color_list = ['#589fef','#e9e9e9','#dfdfdf','#d4d4d4','#c9c9c9','#bfbfbf','#b4b4b4','#aaaaaa','#9f9f9f','#949494','#8a8a8a','#7f7f7f','#747474']
pieName__week = './img/pie__week.png'

plt.figure(figsize=(8,5),dpi=100)
plt.title('現よちよち客がよちよち客になるまでの経過時間（単位: 週）')
plt.pie(
    purchase_week,
    autopct=lambda p:'{:.1f}%'.format(p) if p>=11 else '', #グラフ上に表示する%の制御
    startangle=90,        # 始点角度
    labels=None,
    counterclock=False,
    explode=point, #強調用
    colors=color_list,
    textprops={'color': '#fff', 'fontsize': '16', 'fontweight': 'bold'}
)
plt.legend(
    label,
    fancybox=True, #凡例の枠線を角丸に
    loc='center left',
    bbox_to_anchor=(1,0.5),
    facecolor="#fff",
)
plt.savefig(pieName__week)
# plt.show()
# ======== 円グラフ化 end ========

# excelデータの書き出し場所とファイル名指定
file = r'C:\Users\watan\Desktop\pythontest\cpm_ECLP__samurai.xlsx'

with pd.ExcelWriter(file, mode='a') as writer:
    agg.to_excel(writer, sheet_name='week', index=False)


# 出力したexcelにグラフ貼り付け
from openpyxl.drawing.image import Image
workbook = openpyxl.load_workbook(file)

# sheet_week = workbook['summary']
new_sheet = workbook.create_sheet('week__pie') #シート追加

add_img_pie__week = Image(pieName__week)
new_sheet.add_image(add_img_pie__week, 'A1')

workbook.save(file)


# 処理完了メッセージ
print('Done!')
