#!/usr/bin/env python3
import os
import re
import requests
import zipfile
import subprocess
import fnmatch
import io
from sys import exit

# List of Connect links
videos = {
    '1.1': 'https://c.deic.dk/ps8nkv4de7yr/',
    '1.2': 'https://c.deic.dk/p1s78u4ekl8q/',
    '2.1': 'https://c.deic.dk/p60sxp0kviaf/',
    '2.2': 'https://c.deic.dk/p5osvtmqrbtz/',
}


class Clip():
    def __init__(self, path, session, link):
        self.session = session
        self.link = link

        self.parse_day()

        self.local_dir = path + '/' + str(self.day)

        # Directory containing video clips
        self.clips_dir = (self.local_dir + '/' +
                          self.session.replace('.', '_'))

    def parse_day(self):
        # Extract the day of the session
        day_search = re.search(r'^\d{1,2}', self.session)

        if not day_search:
            raise NameError('Invalid key')
        else:
            day = day_search.group(0)

        self.day = day
        pass


class ConnectGrabber():
    def __init__(self, videos):
        self.setup_dir()

        # Clips list
        self.clips = []

        # Instantiate the clips
        for session, link in videos.items():
            self.clips.append(Clip(self.path, session, link))

        print('Found ' + str(len(self.clips)) + ' clips')

    def setup_dir(self):
        if os.path.exists(os.getcwd() + '/' + 'grabs'):
            print('lol')
            exit(0)
        else:
            os.mkdir(os.getcwd() + '/' + 'grabs')
            os.chdir('./grabs')

        self.path = os.getcwd()

    def files_to_render(self, clips_dir):
        file_1 = None
        file_2 = None

        for file in os.listdir(clips_dir):
            if fnmatch.fnmatch(file, 'cameraVoip*.flv'):
                file_1 = clips_dir + '/' + file
            elif fnmatch.fnmatch(file, 'screenshare*.flv'):
                file_2 = clips_dir + '/' + file

        if (file_1 or file_2) is None:
            print('Error')
            exit(1)

        return (file_1, file_2)

    def download(self):
        for i in range(len(self.clips)):

            clip = self.clips[i]

            # Create directory to store assets
            if os.path.exists(clip.local_dir):
                pass
            else:
                os.mkdir(clip.local_dir)

            print('Downloading session ' + str(clip.session))

            # Append Adobe Connect API call
            clip.link += 'output/filename.zip?download=zip'

            r = requests.get(clip.link)

            if r.status_code == 200:
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(clip.local_dir + '/' +
                             clip.session.replace('.', '_'))
            else:
                print('File did not download')
                pass

    def transcode(self):
        for i in range(len(self.clips)):

            file_1, file_2 = self.files_to_render(self.clips[i].clips_dir)

            output_file = (self.clips[i].local_dir + '/' +
                           self.clips[i].session.replace('.', '_') + '.mp4')

            p = subprocess.call(['ffmpeg', '-i', file_1, '-i', file_2,
                                 '-filter_complex',
                                 '[0:v]pad=1024+320:720[int];' +
                                 '[int][1:v]overlay=320:0[v]',
                                 '-map', '[v]', '-map', '0:a',
                                 '-c:v', 'libx264', '-crf', '24', '-r', '24',
                                 '-preset', 'veryfast', output_file])


prog = ConnectGrabber(videos)

prog.download()
prog.transcode()
