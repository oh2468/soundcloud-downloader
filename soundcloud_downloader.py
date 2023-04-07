import sys
import urllib.request as request
import json
import time

troubleshoot = False
stream_interval = 0.5

headers = {
    "User-Agent":  "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11",
}


def requst_builder(url):
    return request.Request(url, None, headers) 


def request_text(url, is_json=False):
    req = requst_builder(url)
    with request.urlopen(req) as resp:
        content = resp.read().decode("UTF-8")
        return json.loads(content) if is_json else content


def request_data(url):
    req = requst_builder(url)
    with request.urlopen(req) as resp:
        return resp.read()


def get_song_doc(song_url):
    song_doc = request_text(song_url)

    if troubleshoot:
        with open("song.html", "w", encoding="UTF-8") as file:
            file.write(song_doc)

    return song_doc


def get_song_artist_and_title(song_doc):
    artist = song_doc.split('username":"')[1].split('"')[0]
    title = song_doc.split('og:title" content="')[1].split('"')[0]
    return (artist, title)


def get_client_id(song_doc):
    id_script_url = song_doc.split('<script crossorigin src="')[-1].split('"')[0]
    id_script = request_text(id_script_url)

    if troubleshoot:
        with open("script.js", "w", encoding="UTF-8") as file:
            file.write(id_script)
    
    client_id = id_script.split('client_id:"')[1].split('"')[0]
    return client_id


def get_track_authorization(song_doc):
    return song_doc.split('track_authorization":"')[1].split('"')[0]


def save_song_img(song_doc, artist, title):
    img_url = song_doc.split('<img src="')[1].split('"')[0]
    jpg_file = "{} - {}.jpg".format(artist, title)

    with open(jpg_file, "wb") as file:
        file.write(request_data(img_url))


def get_hls_stream(song_doc):
    return song_doc.split('"transcodings":[{"url":"')[1].split('"')[0]


def download_stream(hls_steam_url, artist, title):
    stream = request_text(hls_steam_url)
    part_identifier = "https://"
    song_file = "{} - {}.mp3".format(artist, title)

    if troubleshoot:
        with open("stream.m3u8", "w", encoding="UTF-8") as file:
            file.write(stream)
        
    stream_parts = stream.count(part_identifier)
    est_download_time = int(stream_parts * stream_interval)
    counter = 0

    print("The estimated download time is: {} s".format(est_download_time))
    with open(song_file, "wb") as file:
        for line in stream.split("\n"):
            if line.startswith(part_identifier):
                time.sleep(stream_interval)
                file.write(request_data(line))
                counter += 1
                prog = int((counter / stream_parts) * 100)
                print("download progress: {} %".format(prog), end="\n" if counter == stream_parts else "\r")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("MISSING SOUNDCLOUD SONG LINK.... ABORTING DOWNLOAD")
        sys.exit(1)

    song_doc = get_song_doc(sys.argv[1])
    artist, title = get_song_artist_and_title(song_doc)
    
    track_auth = get_track_authorization(song_doc)
    client_id = get_client_id(song_doc)
    hls_stream = get_hls_stream(song_doc)
    
    hls_url = "{}?client_id={}&track_authorization={}".format(hls_stream, client_id, track_auth)
    hls_playlist_url = request_text(hls_url, True)["url"]

    print("Starting download on: {} - {}".format(artist, title))

    download_stream(hls_playlist_url, artist, title)
    save_song_img(song_doc, artist, title)

    print("Download now completed. Bye!")

