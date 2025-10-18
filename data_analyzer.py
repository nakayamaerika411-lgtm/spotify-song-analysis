# ファイル名: data_analyzer.py (最終修正版)

import os
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv

load_dotenv()

# MySQL接続設定 (前ステップと同じ情報)
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'user': os.getenv("DB_USER", "root"),
    'password': os.getenv("DB_PASSWORD", ""),
    'database': "spotify_project_db"
}

def load_data_from_mysql():
    """MySQLから全データを取得し、Pandas DataFrameとして返す"""
    try:
        db = mysql.connector.connect(**DB_CONFIG)
        sql_query = "SELECT * FROM hit_songs;"
        
        # SQLの結果をPandas DataFrameとして読み込む
        df = pd.read_sql(sql_query, db)
        db.close()
        print(f"データ取得成功。合計 {len(df)} レコードをロードしました。")
        return df
    
    except mysql.connector.Error as err:
        print(f"MySQLからのデータロード中にエラーが発生しました: {err}")
        return pd.DataFrame()

def analyze_and_visualize(df):
    """データ分析と可視化を行う"""
    if df.empty:
        print("データフレームが空のため分析をスキップします。")
        return

    # --- 🛠️ 最終修正箇所: 欠損値（None/NULL）のクリーニングと型変換 ---
    
    # 数値計算を行う特徴量カラムのリスト (popularityを含む)
    features_and_popularity = ['popularity', 'danceability', 'energy', 'valence', 
                               'acousticness', 'speechiness', 'instrumentalness', 'tempo']
    
    # 1. 欠損値（None/NULL）を0に置換
    df[features_and_popularity] = df[features_and_popularity].fillna(0)
    
    # 2. **強力な型変換**: 全てを数値型に変換し、変換できない場合は強制的にNaNにする
    #    その後、NaNを再度0で埋める
    for col in features_and_popularity:
        if col == 'popularity':
            # popularityは整数INT型に
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        else:
            # 他の特徴量は浮動小数点数FLOAT型に
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)
    
    # --- 🛠️ 修正箇所 終わり ---

    # -----------------------------------------------------
    # 1. 人気度（Popularity）と楽曲特徴量の相関分析
    # -----------------------------------------------------
    print("\n--- 1. 人気度と特徴量の相関分析 ---")
    
    features = ['danceability', 'energy', 'valence', 'acousticness', 
                'speechiness', 'instrumentalness', 'tempo']
    
    # 相関行列を計算
    correlation = df[['popularity'] + features].corr()
    print("人気度との相関:\n", correlation['popularity'].sort_values(ascending=False))

    # 可視化: 人気度と最も相関の高い特徴量 (例: danceability)
    plt.figure(figsize=(10, 6))
    sns.regplot(x='danceability', y='popularity', data=df)
    plt.title('Relationship between Danceability and Song Popularity')
    plt.xlabel('Danceability')
    plt.ylabel('Popularity')
    plt.savefig('viz_popularity_vs_danceability.png')
    plt.show(block=False) 

    # -----------------------------------------------------
    # 2. 感情（Valence）とエネルギー（Energy）の分布
    # -----------------------------------------------------
    print("\n--- 2. 感情(Valence)とエネルギー(Energy)の分布 ---")
    
    # 散布図で分布を可視化
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x='valence', y='energy', hue='popularity', data=df, 
                    size='popularity', sizes=(20, 200), alpha=0.6)
    plt.title('Valence vs. Energy of Hit Songs (Size indicates Popularity)')
    plt.xlabel('Valence (Positivity)')
    plt.ylabel('Energy')
    plt.legend(title='Popularity') 
    plt.savefig('viz_valence_vs_energy.png')
    plt.show(block=False)
    
    # -----------------------------------------------------
    # 3. 楽器中心の曲（Instrumentalness）の傾向
    # -----------------------------------------------------
    # 楽器中心度が高い曲（> 0.5）の割合を計算
    instrumental_songs = df[df['instrumentalness'] > 0.5]
    print(f"\n楽器中心の曲（Instrumentalness > 0.5）の割合: {len(instrumental_songs)/len(df)*100:.2f}%")
    
    # 楽器中心度とボーカル曲の人気度の比較 (ボックスプロット)
    df['type'] = df['instrumentalness'].apply(lambda x: 'Instrumental' if x > 0.5 else 'Vocal')
    plt.figure(figsize=(8, 6))
    sns.boxplot(x='type', y='popularity', data=df)
    plt.title('Popularity comparison: Instrumental vs. Vocal Tracks')
    plt.savefig('viz_instrumental_vs_vocal_popularity.png')
    plt.show() 

if __name__ == "__main__":
    
    # 1. データのロード
    all_data = load_data_from_mysql()
    
    # 2. 分析と可視化の実行
    analyze_and_visualize(all_data)
    
    print("\n--- ステップ5 分析・可視化完了 ---")
    print("次のステップはステップ6：結果の英語での論理的記述と発表です。")