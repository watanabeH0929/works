import os
import glob
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

class Aggregate:
    def __init__(self, empty_filename, conditional, target_count, renamed_name):
        self.empty_filename = empty_filename
        self.conditional = conditional
        self.target_count = target_count
        self.renamed_name = renamed_name
    def run_process(self):
        # 入力情報の取得
        input_dir = entry_input.get()
        output_dir = entry_output.get()
        filename = entry_filename.get() or self.empty_filename

        if not input_dir or not output_dir:
            messagebox.showerror("エラー", "フォルダを両方選択してください")
            return

        if not filename.endswith(".csv"):
            filename += ".csv"

        try:
            # 1. 読み込むCSVファイルの一覧を取得
            search_pattern = os.path.join(input_dir, "*.csv")
            files = glob.glob(search_pattern)

            if not files:
                messagebox.showwarning("警告", "CSVファイルが見つかりません")
                return

            # 2. 全CSVの読み込みと結合 (顧客IDを文字列固定)
            df_list = []
            for file in files:
                temp_df = pd.read_csv(file, encoding='utf-8-sig', dtype=str, usecols=['顧客ID', '顧客番号', '配信ステータス', '開封有無'])
                df_list.append(temp_df)
        
            df = pd.concat(df_list, ignore_index=True)

            # 3. 絞り込み
            filtered_df = df.query(self.conditional)

            # 4. 顧客IDごとに開封有無をカウントして1行にまとめる
            summary_df = filtered_df.groupby('顧客番号')[self.target_count].count().reset_index()
            summary_df = summary_df.rename(columns={self.target_count: self.renamed_name})

            # 5. 保存
            save_path = os.path.join(output_dir, filename)
            # Excelでの文字化けを考慮し utf-8-sig で出力
            summary_df.to_csv(save_path, index=False, encoding="utf-8-sig")

            messagebox.showinfo("成功", f"集計が完了しました！\n保存先: {save_path}")

        except Exception as e:
            messagebox.showerror("エラー", f"予期せぬエラーが発生しました:\n{e}")

mail_unopened = Aggregate('result_mailUnopened', '配信ステータス == "完了" & 開封有無 == "無"', '開封有無', '開封無の件数')
mail_undeliverable = Aggregate('result_mailUndeliverable', '配信ステータス == "配信不可"', '配信ステータス', '「配信不可」回数')

# --- GUIデザイン ---
root = tk.Tk()
root.title("メルマガ「配信不可」回数集計ツール")
root.geometry("600x350")

# 入力フォルダ
tk.Label(root, text="集計元CSVフォルダを選択:", font=("MS Gothic", 10)).pack(pady=(20, 0))
frame_in = tk.Frame(root)
frame_in.pack(pady=5)
entry_input = tk.Entry(frame_in, width=60)
entry_input.pack(side=tk.LEFT, padx=5)
tk.Button(frame_in, text="選択", command=lambda: entry_input.insert(0, filedialog.askdirectory())).pack(side=tk.LEFT)

# 出力フォルダ
tk.Label(root, text="出力先の保存場所を選択:", font=("MS Gothic", 10)).pack(pady=(15, 0))
frame_out = tk.Frame(root)
frame_out.pack(pady=5)
entry_output = tk.Entry(frame_out, width=60)
entry_output.pack(side=tk.LEFT, padx=5)
tk.Button(frame_out, text="選択", command=lambda: entry_output.insert(0, filedialog.askdirectory())).pack(side=tk.LEFT)

# ファイル名
tk.Label(root, text="出力ファイル名 (.csv):", font=("MS Gothic", 10)).pack(pady=(15, 0))
entry_filename = tk.Entry(root, width=68)
entry_filename.insert(0, "mail_aggregate.csv")
entry_filename.pack(pady=5)

# 実行
frame_btn = tk.Frame(root)
frame_btn.pack(pady=30)
tk.Button(frame_btn, text="未開封件数を集計", command=lambda: mail_unopened.run_process(), bg="#3ea8ff", fg="white", font=("MS Gothic", 11, "bold"), width=20, height=2).pack(side="left", padx=10)
tk.Button(frame_btn, text="配信不可回数を集計", command=lambda: mail_undeliverable.run_process(), bg="#4CAF50", fg="white", font=("MS Gothic", 11, "bold"), width=20, height=2).pack(side="left", padx=10)

root.mainloop()
