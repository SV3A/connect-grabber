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
        """ Constructed function """
        self.session = session
        self.link = link

        # Get list number, i.e. the digits preceding the '.'
        self.parse_number()

        # Directory
        self.local_dir = path + '/' + str(self.number)

        # Directory containing downloaded video clips
        self.clips_dir = (self.local_dir + '/' +
                          self.session.replace('.', '_'))

    def parse_number(self):
        """ Get list/session number"""
        num_search = re.search(r'^\d{1,2}', self.session)

        if not num_search:
            raise NameError('Invalid key')
        else:
            self.number = num_search.group(0)


class ConnectGrabber():
    def __init__(self, videos):
        """ Constructor function """
        # Setup working dir / output folder
        self.setup_dir()

        # Instantiate the clips
        self.clips = []

        for session, link in videos.items():
            self.clips.append(Clip(self.path, session, link))

        # Feedback
        print('Found ' + str(len(self.clips)) + ' clips')

    def setup_dir(self):
        """ Makes a working folder and changes directory to it """

        # Check if default dir exists
        if os.path.exists(os.getcwd() + '/' + 'grabs'):
            found_dir = False
            user_dir = 'grabs'
            while found_dir is not True:
                user_dir = input('\'' + user_dir + '\' dir exists.\n' +
                                 'Choose another folder name: ')
                if not os.path.exists(os.getcwd() + '/' + user_dir):
                    found_dir = True

            os.mkdir(os.getcwd() + '/' + user_dir)
            os.chdir('./' + user_dir)
        else:
            os.mkdir(os.getcwd() + '/' + 'grabs')
            os.chdir('./grabs')

        # Store working path
        self.path = os.getcwd()

    def files_to_render(self, clips_dir):
        """ Collect the files to be merged together """
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
        """ Convert Adobe link and download and extract assets """
        for i in range(len(self.clips)):

            clip = self.clips[i]

            # Create directory to store assets
            if not os.path.exists(clip.local_dir):
                os.mkdir(clip.local_dir)

            # Feedback
            print('Downloading session ' + str(clip.session))

            # Append Adobe Connect API call
            clip.link += 'output/filename.zip?download=zip'

            # Download and extract
            r = requests.get(clip.link)

            if r.status_code == 200:
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(clip.local_dir + '/' +
                             clip.session.replace('.', '_'))
            else:
                print('File did not download')
                pass

    def transcode(self):
        """ Takes the two video tracks and merges them """
        for i in range(len(self.clips)):

            file_1, file_2 = self.files_to_render(self.clips[i].clips_dir)

            output_file = (self.clips[i].local_dir + '/' +
                           self.clips[i].session.replace('.', '_') + '.mp4')

            subprocess.call(['ffmpeg', '-i', file_1, '-i', file_2,
                             '-filter_complex',
                             '[0:v]pad=1024+320:720[int];' +
                             '[int][1:v]overlay=320:0[v]',
                             '-map', '[v]', '-map', '0:a',
                             '-c:v', 'libx264', '-crf', '24', '-r', '24',
                             '-preset', 'veryfast', output_file])


# Init
prog = ConnectGrabber(videos)

prog.download()
prog.transcode()
