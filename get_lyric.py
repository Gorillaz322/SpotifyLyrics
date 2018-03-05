import urllib2
import json
import subprocess
import os
import re

location = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

if not os.path.exists('lyrics'):
    os.makedirs('lyrics')

base_path = location + '/lyrics'


class NoDataFoundException(Exception):
    pass


class Lyric(object):
    def __init__(self, artist, title):
        self.artist = artist
        self.title = title
        self.filename = os.path.join(
            base_path,
            "{artist}-{song}.txt"
            .format(artist="_".join(self.artist.split()),
                    song="_".join(self.title.split())))

    @staticmethod
    def _urlify_artist(artist):
        return artist \
            .replace(' ', '%20') \
            .replace('/', '%2F')

    @staticmethod
    def _urlify_song(title):
        # remove regular brackets
        title = re.sub(r'\([^)]*\)', '', title)

        # remove square brackets
        title = re.sub(r'\[.*?\]', '', title)

        # remove everything after a dash
        if ' - ' in title:
            title = re.sub(r'\ - .*$', '', title)

        return title \
            .strip() \
            .replace(' ', '%20') \
            .replace('/', '%2F')

    def get(self):
        # if lyric was already saved to file - getting from it
        if os.path.isfile(self.filename):
            with open(self.filename, 'r') as lyrics:
                lyric = lyrics.read()
        else:
            response = json.load(urllib2.urlopen(
                'http://lyric-api.herokuapp.com/api/find/{artist}/{song_title}'
                    .format(artist=self._urlify_artist(artist),
                            song_title=self._urlify_song(title))
            ))

            if response['err'] != 'none':
                raise NoDataFoundException()

            lyric = response['lyric']

            f = open(self.filename, 'w')
            f.write(lyric)

        return lyric

    def show(self):
        lyric_text = self.get()
        lines = lyric_text.split('\n')

        # length of terminal window as number of lines in a text
        y_size = len(lines) + 1

        # width of terminal as longest line in a text
        x_size = max([len(line) for line in lines])

        subprocess.call(
            [
                'gnome-terminal',
                '--geometry',
                '{x}x{y}+4096+0'.format(x=str(x_size), y=str(y_size)),
                '-e',
                'vim "{file}"'.format(file=self.filename)
            ]
        )

artist = subprocess.check_output(['playerctl', 'metadata', 'artist'])
title = subprocess.check_output(['playerctl', 'metadata', 'title'])
lyric = Lyric(artist, title)

try:
    lyric.show()
except NoDataFoundException:
    subprocess.call([
        "notify-send",
        "-i",
        "dialog-error",
        "Cannot find lyric for",
        "{} - {}".format(artist, title)
    ])

