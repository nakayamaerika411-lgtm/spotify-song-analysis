# ファイル名: genius_collector.py

import os
import csv
import requests
import time
from dotenv import load_dotenv

# Genius APIとrequestsのためのライブラリ
# 💡 注: python-lyricsgeniusesなどのライブラリもありますが、今回はシンプルなrequestsで実装します。

load_dotenv()

# Genius Access Tokenを取得
GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
BASE_URL = "https://api.genius.com/"

if not GENIUS_ACCESS_TOKEN:
    print("エラー: .envファイルからGENIUS_ACCESS_TOKENが読み込めませんでした。")
    exit()

HEADERS = {
    'Authorization': f'Bearer {GENIUS_ACCESS_TOKEN}'
}

# レートリミット対策のための待機時間（秒）
# Genius APIはMusixmatchより制限が緩い可能性がありますが、念のため設定します。
WAIT_TIME = 0.5 

def search_genius_song(track_name, artist_name):
    """
    曲名とアーティスト名からGeniusの楽曲情報を取得する
    """
    search_url = BASE_URL + 'search'
    # 検索クエリを整形 (例: "Levitating Dua Lipa")
    search_query = f"{track_name} {artist_name}" 
    
    params = {'q': search_query}
    
    try:
        response = requests.get(search_url, params=params, headers=HEADERS)
        data = response.json()
        
        # 結果リスト
        hits = data.get('response', {}).get('hits', [])
        if hits:
            # 最初のヒット曲のURLを返す
            return hits[0]['result']['url'] 
            
    except Exception as e:
        print(f"Genius検索中にエラー: {e}")
    return None

def get_lyrics(song_url):
    """
    Geniusの曲のURLから歌詞を取得する（スクレイピングの簡易版）
    Genius API自体は歌詞のテキストを提供しないため、Webページから取得する必要があります。
    この機能は複雑なので、一旦、APIから提供されるURLを保存するだけにします。
    """
    return song_url if song_url else "LYRICS_URL_NOT_FOUND"


def integrate_lyrics(input_file, output_file):
    """
    Spotifyデータに歌詞URLを統合し、新しいCSVとして保存する
    """
    data_with_lyrics = []
    
    try:
        with open(input_file, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            songs = list(reader)
    except FileNotFoundError:
        print(f"エラー: {input_file} が見つかりません。Spotifyデータ収集を完了させてください。")
        return

    total_songs = len(songs)
    print(f"CSVから {total_songs} 曲のデータを読み込みました。Genius URLの収集を開始します...")

    for i, song in enumerate(songs):
        track_name = song['track_name']
        artist_name = song['artist_name']
        
        print(f"({i+1}/{total_songs}) 処理中: {artist_name} - {track_name}", end='\r')
        
        # Genius URLの取得
        song_url = search_genius_song(track_name, artist_name)
        
        # 新しい辞書を作成し、lyrics_urlキーを追加
        new_song = song.copy()
        new_song['lyrics_url'] = get_lyrics(song_url)
        data_with_lyrics.append(new_song)
        
        time.sleep(WAIT_TIME) # レートリミット対策
        
    print("\n--- Genius URL収集完了 ---")

    # 新しいCSVファイルに保存
    # フィールド名を更新（lyrics_urlを追加）
    fieldnames = list(songs[0].keys()) + ['lyrics_url']
    with open(output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_with_lyrics)

    print(f"統合されたデータを '{output_file}' に保存しました。")
    print(f"収集された曲数: {len(data_with_lyrics)} 件")


if __name__ == "__main__":
    input_csv = 'spotify_hit_songs_data.csv'
    output_csv = 'integrated_song_lyrics_data.csv' 
    
    integrate_lyrics(input_csv, output_csv)
    
    print("\n次のステップはステップ4：MySQLへのデータ格納です。")