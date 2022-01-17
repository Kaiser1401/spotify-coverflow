import time
import requests
import spotipy
import spotipy.util as util
from io import BytesIO
from PIL import Image, ImageTk
from tkinter import Tk, Frame, Label

from my_secrets import *
from pprint import pprint

MONITOR_WIDTH = 1024
MONITOR_HEIGHT = 768

# in my_secrets.py:

# USERNAME = ""
# SECRET = ""
# SCOPE = "user-read-playback-state"
# URI = "http://localhost:8888/callback"
# ID = ""

GRAYSCALE = True
contrast_border_percent = 5

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
    img = Image.open(BytesIO(res.content)).resize((640, 640), Image.ANTIALIAS)
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


def main(sp):
    '''
    Main event loop, draw the image and text to tkinter window
    '''

    root = Tk()
    root.configure(bg="black", cursor="none")
    root.attributes('-fullscreen', True)

    f = Frame(root, bg="black", width=MONITOR_WIDTH, height=MONITOR_HEIGHT)
    f.grid(row=0, column=0, sticky="NW")
    f.grid_propagate(0)
    f.update()

    most_recent_song = ""
    while True:
        redraw = True

        time.sleep(5)
        current_song = get_current_playing(sp)

        if current_song["name"] != most_recent_song:
            redraw = True
        else:
            redraw = False

        if redraw:
            artist = current_song["artist"]
            name = current_song["name"]
            most_recent_song = name

            pi = convert_image(current_song["img_src"])

            img_x = MONITOR_WIDTH / 3
            img_y = MONITOR_HEIGHT / 2

            label = Label(f, image=pi, highlightthickness=0, bd=0)
            label.place(x=img_x, y=img_y, anchor="center")

            artist_label = Label(
                f,
                text=artist,
                bg="black",
                fg="white",
                font=("Courier New", 30)
            )

            artist_x = MONITOR_WIDTH - (MONITOR_WIDTH / 5)
            artist_y = (MONITOR_HEIGHT / 2) - 50
            artist_label.place(x=artist_x, y=artist_y, anchor="center")

            song_label = Label(
                f,
                text=name,
                bg="black",
                fg="white",
                font=("Courier New", 20),
            )

            song_x = MONITOR_WIDTH - (MONITOR_WIDTH / 5)
            song_y = (MONITOR_HEIGHT / 2) + 20
            song_label.place(x=song_x, y=song_y, anchor="center")

            root.update()

            label.destroy()
            artist_label.destroy()
            song_label.destroy()


if __name__ == "__main__":
    sp = get_spotify()
    main(sp)
