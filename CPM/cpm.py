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


# CPM分析 算出&エクスポート用 python化 start
#売上
sales_volume = df.iloc[:,1].sum()
print(f'売上: {sales_volume}')

#顧客数
all_customers = df.iloc[:,0].nunique()
print(f'顧客数: {all_customers}')

#平均購入単価（小数点以下は四捨五入）
average_order_value = sales_volume/all_customers
average_order_value = round(average_order_value)
print(f'平均購入単価: {average_order_value}')

#分析時の基準とする購入金額
criterion_price = average_order_value * 7
print(f'基準の購入金額: {criterion_price}')

num_dict = {}
num_dict['売上'] = int(sales_volume)
num_dict['顧客数'] = all_customers
num_dict['平均購入単価'] = average_order_value
num_dict['基準の購入金額'] = criterion_price

# print('\n=== 辞書の出力 ===')
# print(num_dict)
# print(type(num_dict))


df__num_dict = pd.DataFrame(list(num_dict.items()), columns=["キー", "値"])

df['実売上日'] = pd.to_datetime(df['実売上日'], format='%Y/%m/%d')
df['生年月日'] = pd.to_datetime(df['生年月日'], format='%Y/%m/%d')

agg = df.groupby('顧客ID').agg(
        生年月日 = ('生年月日', 'min'),
        累計購入金額 = ('小計', 'sum'),
        購入回数 = ('顧客購入回数', 'max'),
        初回購入日 = ('実売上日', 'min'),
        最終購入日 = ('実売上日', 'max'),
    ).reset_index()

today = datetime.datetime.now()
#デバッグ用日付
# today = datetime.datetime(2025, 9, 30, 14, 30)

# 初回～直近の期間算出
agg['期間'] = (agg['最終購入日'] - agg['初回購入日']).dt.days

# 今日から最終購入日までの日数
agg['今日から最終購入日までの日数'] = (today - agg['最終購入日']).dt.days

# 年齢算出
agg['年齢'] = (
    today.year - agg['生年月日'].dt.year
    - ((today.month < agg['生年月日'].dt.month) |
       ((today.month == agg['生年月日'].dt.month) & (today.day < agg['生年月日'].dt.day)))
)
# 年齢を整数に
agg['年齢'] = agg['年齢'].astype('Int64')

# 現役離脱チェック
agg['現役離脱'] = ''
base_date = 240
agg.loc[agg['今日から最終購入日までの日数'] < base_date, '現役離脱'] = '現役'
agg.loc[agg['今日から最終購入日までの日数'] >= base_date, '現役離脱' ] = '離脱'

# 出力時の並び変更
desired_order= ['現役離脱','顧客ID','生年月日','年齢','累計購入金額','購入回数','初回購入日','最終購入日','期間','今日から最終購入日までの日数']
agg = agg[desired_order]

print("\n=== agg ===")
print(agg)
# CPM分析 算出&エクスポート用 python化 end


# 現役・離脱/顧客グループ別顧客数 start
group_baseDate_min = 90 #初回購入から最終購入日までの差 min
group_baseDate_max = 210 #初回購入から最終購入日までの差 max

# 「グループ」追加
conditions = [
    (agg['購入回数'] == 1),
    (agg['購入回数'] >= 2) & (agg['期間']< group_baseDate_min),
    (agg['購入回数'] >= 2) & (agg['期間'] >= group_baseDate_min) & (agg['累計購入金額'] < criterion_price),
    (agg['購入回数'] >= 2) & (agg['期間'] >= group_baseDate_min) & (agg['期間'] < group_baseDate_max) & (agg['累計購入金額'] >= criterion_price),
    (agg['購入回数'] >= 2) & (agg['期間'] >= group_baseDate_max) & (agg['累計購入金額'] >= criterion_price)
]
choices = ['初回客','よちよち客','コツコツ客','流行客','優良客']
agg['グループ'] = np.select(conditions, choices, default='未分類')

print('グループ追加後のagg')
print(agg)


# 並び指定
groups_to_show  = ['初回客','よちよち客','コツコツ客','流行客','優良客','未分類']

# クロス集計
ct = pd.crosstab(agg['現役離脱'],agg['グループ'], margins=True, dropna=False)
ct = ct.reindex(columns=groups_to_show , fill_value=0)

ct['All'] = ct.sum(axis=1)

# 現役離脱を列にして最終表にする（ヘッダ順： 現役離脱, グループA, グループB, グループC）
summary = ct.reset_index()
summary.columns.name = None  # 列名の階層を消す

print('グループ分け')
print(summary)
# 現役・離脱/顧客グループ別顧客数 end


# 円グラフ化 start
plt.rcParams.update({'font.size':11})
plt.rcParams['font.family'] = 'Yu Gothic'

all_customerGroup_num = ct.loc['All'].drop(ct.columns[6])
print(all_customerGroup_num)

print(type(all_customerGroup_num))

label = all_customerGroup_num.keys()
point = [0.1,0,0,0,0,0] #切り離して強調表示
color_list = ['#589fef','0.8','0.7','0.6','0.5','0.4']
pieName__customerGroup = './img/pie__customer_group.png'

plt.figure(figsize=(8,5),dpi=100)
plt.title('顧客グループ比率（全体）')
plt.pie(
    all_customerGroup_num,
    autopct=lambda p:'{:.1f}%'.format(p) if p>=30 else '', #グラフ上に表示する%の制御
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
    bbox_to_anchor=(0.95,0.5),
    facecolor="#fff",
)
plt.savefig(pieName__customerGroup)
# plt.show()
# 円グラフ化 end


# ここ ----------------------------------------------------
# 複数のデータフレームをエクセルファイルに書き込み ※上書き
# excelデータの書き出し場所とファイル名指定
file = r'C:\Users\watan\Desktop\pythontest\cpm_ECLP__samurai.xlsx'
# ここ ----------------------------------------------------


# データフレームをexcelデータとして出力
# 追記にするならmode='a'を追加
with pd.ExcelWriter(file) as writer:
    df__num_dict.to_excel(writer, sheet_name="概要", index=False)
    agg.to_excel(writer, sheet_name='agg', index=False)
    summary.to_excel(writer, sheet_name='summary', index=False)

# 出力したexcelにグラフ貼り付け
from openpyxl.drawing.image import Image
workbook = openpyxl.load_workbook(file)

sheet_summary = workbook['summary']
# new_sheet = workbook.create_sheet('chart') #シート追加

add_img_pie__customerGroup = Image(pieName__customerGroup)
sheet_summary.add_image(add_img_pie__customerGroup, 'A8')

workbook.save(file)

print(type(agg))


# print(agg.loc[:, 'グループ'])
# print(agg.loc[agg['グループ'] == 'よちよち客'])
# mask = agg['グループ'] == 'よちよち客'
# selected_rows = agg.loc[mask]


# 処理完了メッセージ
print('Done!')
