import os
from pathlib import Path
import pandas as pd
import glob

os.chdir(Path(__file__).parent)

# 読み込むCSVファイルの一覧を取得（例：mail_dataフォルダ内の全てのcsv）
files = glob.glob("./mail_data/*.csv")
df = pd.concat([pd.read_csv(file, encoding='932', dtype=str, usecols=['顧客ID','顧客番号','配信ステータス','開封有無']) for file in files], ignore_index=True)

# # print(df)

# 絞り込み
filtered_df = df.query('配信ステータス == "完了" & 開封有無 == "無"')

print('filtered_dfの出力')
print(filtered_df)

# 開封有無の件数をカウントして列に代入
summary_df = filtered_df.groupby('顧客番号')['開封有無'].count().reset_index()

# summary_df = filtered_df.groupby('顧客番号').agg(
#     顧客ID = ('顧客ID', 'first'),
#     開封無の件数 = ('開封有無', 'count')
# ).reset_index()

print(summary_df)

print(type(summary_df))

# summary_df.columns = ['顧客ID', '顧客番号', '開封無の件数']

# 結果をCSVに保存
summary_df.to_csv("output__debug.csv", index=False, encoding="932")


print('集計完了')
