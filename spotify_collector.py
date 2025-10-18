# ファイル名: spotify_collector.py

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
import csv
import string 

# .envファイルを読み込み、環境変数に設定する
# .envファイルが'D:\spotify_analysis'にあることを確認してください。
load_dotenv()

# 環境変数からClient IDとSecretを取得（**直書きを避けます**）
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# Client IDとSecretが取得できているかチェック
if not CLIENT_ID or not CLIENT_SECRET:
    print("エラー: .envファイルからClient IDまたはClient Secretが読み込めませんでした。")
    print(".envファイルの内容を確認してください（引用符や改行がないか）。")
    exit()

# 1. API接続のための認証情報を設定 (変数を参照するように修正)
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID,
                                                           client_secret=CLIENT_SECRET))

def collect_hit_songs(start_year, end_year, min_popularity=70, limit=50):
    """
    指定された年範囲のヒット曲データを収集する関数。
    ページネーションとアルファベットによるクエリ分割を実装する。
    """
    all_tracks = []
    
    # 2019年から2024年まで年ごとにループ
    for year in range(start_year, end_year + 1):
        print(f"\n--- {year}年の楽曲を収集中 ---")
        
        # アルファベット a-z および数字 ('0-9') で検索を分割。'other'は削除
        search_terms = list(string.ascii_lowercase) + ['0-9']
        
        for term in search_terms:
            offset = 0  # 取得開始位置
            
            # 2. 'other'の複雑な検索を削除し、アルファベットと数字に集中
            if term == '0-9':
                query = f'year:{year} track:0-9*'
            else:
                query = f'year:{year} track:{term}*' # 例: year:2019 track:a*
            
            # --- ページネーションのループ ---
            while True:
                # 検索の進捗を表示
                print(f"  [クエリ: {term.upper()}] 取得済件数: {len(all_tracks)}", end='\r')
                
                # APIにリクエストを送信
                try:
                    results = sp.search(q=query, type='track', limit=limit, offset=offset)
                except Exception as e:
                    # 1000件制限のエラーを処理
                    if 'Limit + Offset exceeds maximum of 1000' in str(e):
                        print(f"\n  ⚠️ 1000件制限に到達しました。クエリ '{term.upper()}' の収集をスキップします。")
                    else:
                        print(f"\n  APIエラーが発生しました: {e}")
                    break

                tracks = results['tracks']['items']
                if not tracks:
                    break

                # データを処理し、ヒット曲をフィルタリング
                for track in tracks:
                    if track['popularity'] >= min_popularity:
                        track_data = {
                            'spotify_id': track['id'],
                            'track_name': track['name'],
                            'artist_name': track['artists'][0]['name'], 
                            'release_date': track['album']['release_date'],
                            'popularity': track['popularity'],
                            'year': year
                        }
                        # 重複防止: 既にリストに含まれているIDは追加しない
                        if not any(t['spotify_id'] == track_data['spotify_id'] for t in all_tracks):
                            all_tracks.append(track_data)
                
                # 次のページの開始位置を設定
                offset += limit
                
                # 検索結果の総数、または1000件制限に達したらループを終了
                if offset >= results['tracks']['total'] or offset >= 1000:
                    break
        
        print(f"\n{year}年の収集完了。現在、ヒット曲 {len(all_tracks)} 件を収集。")

    return all_tracks

if __name__ == "__main__":
    
    # データ収集を実行する
    # 収集は時間がかかるため、焦らず待ちましょう！
    hit_songs = collect_hit_songs(start_year=2019, end_year=2024)
    
    print("\n\n--- 全データ収集完了 ---")
    print(f"合計ヒット曲数（Popularity >= 70）: {len(hit_songs)} 件")
    
    # データをCSVとして一時保存
    if hit_songs:
        csv_file = 'spotify_hit_songs_data.csv'
        keys = hit_songs[0].keys()
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(hit_songs)
        
        print(f"データを '{csv_file}' に保存しました。")
    
    print("\n次のステップはMusixmatchの歌詞データとの統合です。")