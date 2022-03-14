import time
import requests
import spotipy
import spotipy.util as util
from io import BytesIO
from PIL import Image, ImageTk
from tkinter import Tk, Frame, Label

from my_secrets import *
from pprint import pprint


GRAYSCALE = True
contrast_border_percent = 5

MONITOR_WIDTH = 1024
MONITOR_HEIGHT = 768

IMG_SIZE = 640
IMG_BORDER = 50

time_spotify_poll_seconds = 5
_time_next_spotify_poll = 0
time_redraw_seconds = 0.1
_time_next_redraw = 0

# in my_secrets.py:

# USERNAME = ""
# SECRET = ""
# SCOPE = "user-read-playback-state"
# URI = "http://localhost:8888/callback"
# ID = ""


def get_spotify():
    '''
    This will open a new browser window if the developer account information
    above is correct. Follow the instructions that appear in the console dialog.
    After doing this once the token will auto refresh as long as the .cache file exists
    in the root directory.
    '''

    #open_browser=False,
    spotify = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(client_id=ID, client_secret=SECRET, username=USERNAME, redirect_uri=URI, scope=SCOPE))
    spotify.me()

    #token = util.prompt_for_user_token(USERNAME, SCOPE, ID, SECRET, URI)
    return spotify


def get_current_playing(sp):
    '''
    Returns information about the current playing song. If no song is currently
    playing the most recent song will be returned.
    '''

    spotify = sp
    results = spotify.current_user_playing_track()

    if not results:
        return None

    img_src = results["item"]["album"]["images"][0]["url"]
    artist = results["item"]["artists"][0]["name"]
    album = results["item"]["album"]["name"]
    name = results["item"]["name"]
    isrc = results["item"]["external_ids"]["isrc"]

    return {
        "img_src": img_src,
        "artist": artist,
        "album": album,
        "name": name,
        "id": isrc
    }


# def itunes_search(song, artist):
#     '''
#     Check if iTunes has a higher definition album cover and
#     return the url if found
#     '''
#
#     try:
#         matches = itunespy.search_track(song)
#     except LookupError:
#         return None
#
#     for match in matches:
#         if match.artist_name == artist:
#             return match.artwork_url_100.replace('100x100b', '5000x5000b')


def convert_image(src):
    '''
    Convert the image url to Tkinter compatible PhotoImage
    '''

    res = requests.get(src)
    img = Image.open(BytesIO(res.content)).resize((IMG_SIZE, IMG_SIZE), Image.ANTIALIAS)
    if GRAYSCALE:
        # use V channel of HSV
        _, _, img = img.convert('HSV').split()

        # contrast / stretching of values (lowest and highest percentage of range is black and white, rest i scaled)
        if contrast_border_percent > 0:
            pixels = list(img.getdata())
            pixels.sort()
            count = len(pixels)
            idx = int(contrast_border_percent*count/100)
            val_low = pixels[idx]
            val_high = pixels[-idx]
            while (val_high-val_low) < 32:
                idx = idx // 2
                val_low = pixels[idx]
                val_high = pixels[-idx]
                if idx < 10:
                    break

            scale = 255/(val_high-val_low)
            def chg_value(v):
                o = int((v-val_low)*scale)
                o = max(0, min(o, 255))
                return o
            img = img.point(chg_value)


    pi = ImageTk.PhotoImage(img, size=())
    return pi



def get_spotify_info(sp):
    pass



def main(sp):
    '''
    Main event loop, draw the image and text to tkinter window
    '''

    current_song = None

    root = Tk()
    root.configure(bg="black", cursor="none")
    root.attributes('-fullscreen', True)

    f = Frame(root, bg="black", width=MONITOR_WIDTH, height=MONITOR_HEIGHT)
    f.grid(row=0, column=0, sticky="NW")
    f.grid_propagate(0)
    f.update()

    label = None
    artist_label = None
    song_label = None
    most_recent_song = ""
    while True:
        global _time_next_spotify_poll
        global _time_next_redraw

        redraw = False

        if _time_next_spotify_poll < time.time():
            current_song = get_current_playing(sp)
            _time_next_spotify_poll = time.time()+time_spotify_poll_seconds
        if current_song:
            if current_song["id"] != most_recent_song:
                redraw = True
            # TODO update early when song shorter than 5 seconds

        if _time_next_redraw < time.time():
            redraw = True

        if redraw:
            _time_next_redraw = time.time()+time_redraw_seconds

            if current_song:
                artist = current_song["artist"]
                name = current_song["name"]
                most_recent_song = current_song["id"]
                pi = convert_image(current_song["img_src"])
            else:
                artist = "Nothing playing"
                name = ""
                most_recent_song = ""
                pi = None



            img_x = IMG_BORDER
            img_y = MONITOR_HEIGHT / 2

            if pi:
                if not label:
                    label = Label(f, image=pi, highlightthickness=0, bd=0)
                    label.place(x=img_x, y=img_y, anchor="w")
                else:
                    label.configure(image=pi)

            if not artist_label:
                artist_label = Label(
                    f,
                    text=artist,
                    bg="black",
                    fg="white",
                    font=("Courier New", 30)
                )
                artist_x = MONITOR_WIDTH - IMG_BORDER
                artist_y = 0
                artist_label.place(x=artist_x, y=artist_y, anchor="ne")
            else:
                artist_label.configure(text=artist)



            if not song_label:
                song_label = Label(
                    f,
                    text=name,
                    bg="black",
                    fg="white",
                    font=("Courier New", 20),
                )
                song_x = MONITOR_WIDTH - IMG_BORDER
                song_y = MONITOR_HEIGHT
                song_label.place(x=song_x, y=song_y, anchor="se")
            else:
                song_label.configure(text=name)

            root.update()

#            label.destroy()
#            artist_label.destroy()
#            song_label.destroy()

        delay = max(0, min(_time_next_redraw, _time_next_redraw)-time.time())
        time.sleep(delay)

if __name__ == "__main__":
    sp = get_spotify()
    main(sp)

