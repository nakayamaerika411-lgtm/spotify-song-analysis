# ファイル名: mysql_uploader.py

import os
import csv
import mysql.connector
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# MySQL接続設定 (この情報は .env ファイルから取得されます)
DB_CONFIG = {
    # .envにDB_HOSTがなければ'localhost'を使用
    'host': os.getenv("DB_HOST", "localhost"),     
    # .envにDB_USERがなければ'root'を使用
    'user': os.getenv("DB_USER", "root"),         
    # .envにDB_PASSWORDがなければ空文字を使用
    'password': os.getenv("DB_PASSWORD", ""),     
    'database': "spotify_project_db",             
    'charset': 'utf8mb4'
}

# 歌詞のURLが統合されたCSVファイル名
CSV_FILE = 'integrated_song_lyrics_data.csv'

def create_database_and_table(db_config):
    """データベースとテーブルが存在しない場合に自動で作成する"""
    
    # データベース名を除いた接続情報
    db_name = db_config['database']
    temp_config = db_config.copy()
    
    # データベースの作成には、データベース名を指定せずに接続する必要がある
    if 'database' in temp_config:
        del temp_config['database'] 
    
    try:
        # データベース接続
        db = mysql.connector.connect(**temp_config)
        cursor = db.cursor()
        
        # データベースの作成
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"データベース '{db_name}' を確認/作成しました。")
        
        # 新しいデータベースを使用するように設定
        cursor.execute(f"USE {db_name}") 
        
        # --- 💡 修正箇所: 既存テーブルの削除（強制リセット） ---
        cursor.execute("DROP TABLE IF EXISTS hit_songs")
        print("既存の 'hit_songs' テーブルをリセットしました。")
        # --- 修正箇所 終わり ---
        
        # テーブル作成SQL (存在しなければ作成)
        table_creation_sql = """
        CREATE TABLE hit_songs (
            song_id VARCHAR(50) PRIMARY KEY,
            track_name VARCHAR(255) NOT NULL,
            artist_name VARCHAR(255) NOT NULL,
            popularity INT,
            danceability FLOAT,
            energy FLOAT,
            valence FLOAT,
            acousticness FLOAT,
            speechiness FLOAT,
            instrumentalness FLOAT,
            tempo FLOAT,
            lyrics_url VARCHAR(500)
        );
        """
        cursor.execute(table_creation_sql)
        print(f"テーブル 'hit_songs' を確認/作成しました。")# データベースの作成 (存在しなければ作成)
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"データベース '{db_name}' を確認/作成しました。")
        
        # 新しいデータベースを使用するように設定
        cursor.execute(f"USE {db_name}") 
        
        # テーブル作成SQL (存在しなければ作成)
        table_creation_sql = """
        CREATE TABLE IF NOT EXISTS hit_songs (
            song_id VARCHAR(50) PRIMARY KEY,
            track_name VARCHAR(255) NOT NULL,
            artist_name VARCHAR(255) NOT NULL,
            popularity INT,
            danceability FLOAT,
            energy FLOAT,
            valence FLOAT,
            acousticness FLOAT,
            speechiness FLOAT,
            instrumentalness FLOAT,
            tempo FLOAT,
            lyrics_url VARCHAR(500)
        );
        """
        cursor.execute(table_creation_sql)
        print(f"テーブル 'hit_songs' を確認/作成しました。")
        
        cursor.close()
        db.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"データベース/テーブル作成エラー: {err}")
        return False

def upload_data_to_mysql():
    """CSVファイルを読み込み、MySQLテーブルにデータを挿入する"""
    
    # 接続テスト
    try:
        # テーブル作成後に、データベース名を指定して再接続
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()
        print("MySQLデータベースへの接続に成功しました。データ投入を開始します。")
    except mysql.connector.Error as err:
        print(f"致命的なエラー: MySQL接続エラー: {err}")
        return

    # CSVファイルからのデータ読み込み
    try:
        with open(CSV_FILE, mode='r', newline='', encoding='latin-1') as f:
            reader = csv.DictReader(f)
            data_to_insert = list(reader)
    except FileNotFoundError:
        print(f"エラー: {CSV_FILE} が見つかりません。Genius APIを使ったデータ収集を完了させてください。")
        cursor.close()
        db.close()
        return
        
    # SQL INSERT文の準備 (カラムはCSVヘッダーと一致していることを想定)
    insert_sql = """
    INSERT INTO hit_songs (
        song_id, track_name, artist_name, popularity, danceability, energy, 
        valence, acousticness, speechiness, instrumentalness, tempo, lyrics_url
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    ) ON DUPLICATE KEY UPDATE 
        popularity=VALUES(popularity), lyrics_url=VALUES(lyrics_url);
    """
    
    # 挿入処理
    inserted_count = 0
    total_count = len(data_to_insert)
    print(f"合計 {total_count} 件のデータをデータベースに挿入します...")

    for i, row in enumerate(data_to_insert):
        # データ型をSQLに合わせて整形
        values = (
            row.get('id'), # song_idにCSVの'id'列を使用
            row.get('track_name'),
            row.get('artist_name'),
            row.get('popularity'),
            row.get('danceability'),
            row.get('energy'),
            row.get('valence'),
            row.get('acousticness'),
            row.get('speechiness'),
            row.get('instrumentalness'),
            row.get('tempo'),
            row.get('lyrics_url')
        )
        
        try:
            cursor.execute(insert_sql, values)
            inserted_count += 1
            if inserted_count % 50 == 0:
                # 50件ごとに進捗を報告
                print(f"進捗: {inserted_count}/{total_count} 件処理完了。", end='\r')
        except mysql.connector.Error as err:
            print(f"\nデータ挿入エラー (ID: {row.get('id')}): {err}")

    # 変更をコミットして確定
    db.commit()
    
    print(f"\n--- データ格納完了 ---")
    print(f"成功裏に挿入/更新されたレコード: {inserted_count} 件")

    cursor.close()
    db.close()


if __name__ == "__main__":
    
    # 1. データベースとテーブルを自動作成
    if create_database_and_table(DB_CONFIG):
        # 2. データのアップロード
        upload_data_to_mysql()
    
    print("\n次のステップはステップ5：データ分析と可視化です。")