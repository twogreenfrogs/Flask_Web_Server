"""
- get camera basic info def. BeautifulSoup
"""
import sys
import os
import cv2
import time
import requests
import shutil
import urllib 
import urllib2
import base64
import subprocess
from threading import Thread, Event, ThreadError
import numpy as np
import logging
from bs4 import BeautifulSoup

DEBUG = True
if DEBUG:
    logging_level=logging.DEBUG
else:
    logging_level=logging.INFO

logging.basicConfig(level=logging_level, format='%(asctime)s - %(levelname)s - %(message)s')
#logging.basicConfig(filename='ipcam.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
dprint=logging.debug

class ExceptionCam(Exception):
    def __init__(self, msg):
        self.msg = msg

class SercommCam(object):
    """
    Sercomm Cam Base class
    Sercomm Cam APIs:
      url_video="http://IPADDR/adm/set_group.cgi?group=JPEG&resolution=3"
      url_videostream = "http://IPADDR/img/video.mjpeg"
      url_snapshot="http://IPADDR/img/snapshot.cgi?size=4"
      url_ptctrl="http://IPADDR/pt/ptctrl.cgi?mv=D,10"
    """

    def __init__(self, ipaddr, username="administrator", password=""):
        self.ipaddr = ipaddr
        self.username = username
        self.password = password
        self.url_videostream = "http://" + self.ipaddr + "/img/video.mjpeg"
        self.url_snapshot = "http://" + self.ipaddr + "/img/snapshot.cgi?size="
        self.url_ptctrl = "http://" + self.ipaddr + "/pt/ptctrl.cgi?mv="
        self.url_resolution = "http://" + self.ipaddr + "/adm/set_group.cgi?group=JPEG&resolution="
        self.url_status = "http://" + self.ipaddr + "/adm/file.cgi?next_file=status.htm"

    def getinfo(self):
        """
        get basic ipcam information
        """
        res = requests.get(self.url_status, auth=(self.username, self.password))
        soup = BeautifulSoup(res.content, "lxml")
        #soup = BeautifulSoup(res.text)
        tds=soup.find_all('td')

        for td in tds:
            if 'IP Address:' in td:
                ipaddr = td.find_next().string
            if 'MAC Address:' in td:
                macaddr = td.find_next().string
            if 'Device Name:' in td:
                dname = td.find_next().string
            if 'F/W version:' in td:
                fwver = td.find_next().string
            if 'SSID:' in td:
                ssid = td.find_next().string

        print 'IP Address:', ipaddr
        print 'MAC Address:', macaddr
        print 'Device Name:', dname
        print 'F/W version:', fwver
        print 'Wireless SSID:', ssid
	
    def start(self):
        """
        start live video stream in thread
        """
        self._stream_thread = Thread(target=self._stream)
	self._stream_flag = True
        self._stream_thread.start()

    def _stream(self):
        """
        #below doesnt work in some cams...
        camera = cv2.VideoCapture(self.url_videostream)
        if not camera.isOpened:
            dprint('failed to open camera')
            raise ExceptionCam('failed to open camera')

        dprint("streaming camera started. press 'q' to stop...")
        while self._stream_flag:
            ret, frame = camera.read()
            if frame is not None: 
		#gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                cv2.imshow('frame', frame)
                if cv2.waitKey(10) == ord("q"):
                    dprint("q pressed. Exiting...")
                    break
        dprint("releasing camera and closing window")
        camera.release()
        cv2.destroyAllWindows()
        """
        #stackoverflow.com - how to download image using requests
        request = urllib2.Request(self.url_videostream)

        base64string = base64.encodestring("{0}:{1}".format(self.username, self.password)).replace('\n', '')
        request.add_header("Authorization", "Basic {0}".format(base64string))

        stream = urllib2.urlopen(request)

        bytes=''
        while self._stream_flag:
            bytes+=stream.read(1024)
            a = bytes.find('\xff\xd8')
            b = bytes.find('\xff\xd9')
            if a!=-1 and b!=-1:
                jpg = bytes[a:b+2]
                bytes= bytes[b+2:]
                img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
                cv2.imshow('Live Video Streaming',img)
                if cv2.waitKey(10) == ord('q'):
                    break
        dprint("releasing camera and closing window")
        #camera.release()
        #cv2.destroyAllWindows()

    def stop(self):
        """
	stop live video stream
        """

        self._stream_flag = False
        
	#while self.stream_thread.isAlive():
        #    time.sleep(1)
	
	self._stream_thread.join()
        dprint("camera streaming stopped...")
        return True

    def videoclip(self, outfile="video.avi", duration=30):
        """
        save video clip for given duration as file name outfile_timestamp
        default duration: 30 sec, default file name video.avi
        """ 
        dprint("saving {0} sec videoclip...".format(duration))
        self._videoclip_thread = Thread(target=self._videoclip, args=(outfile, duration))
        self._videoclip_thread.start()

    def _videoclip(self, clipfile, duration):
        #stackoverflow.com - how to download image using requests
        request = urllib2.Request(self.url_videostream)
        base64string = base64.encodestring("{0}:{1}".format(self.username, self.password)).replace('\n', '') 
	request.add_header("Authorization", "Basic {0}".format(base64string))

        stream = urllib2.urlopen(request)
        fourcc = cv2.cv.CV_FOURCC('m', 'p', '4', 'v')
        video  = cv2.VideoWriter()
        if not video.open(clipfile, fourcc, 25, (640, 480), True):
            dprint('failed to open videowriter')
            raise ExceptionCam('failed to open videowriter')

        start_time = int(time.time())
        elapsed_time = 0

        bytes=''
        while duration > elapsed_time:
            bytes+=stream.read(1024)
            a = bytes.find('\xff\xd8')
            b = bytes.find('\xff\xd9')
            if a!=-1 and b!=-1:
                jpg = bytes[a:b+2]
                bytes= bytes[b+2:]
                img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
                video.write(img)
                cv2.imshow('Live Video Streaming',img)
                if cv2.waitKey(10) == ord('q'):
                    break
            elapsed_time = int(time.time()) - start_time

        video.release()

        videofile = clipfile + "_" + time.strftime('%Y:%m:%d-%H:%M:%S')
	subprocess.check_call(["mv", clipfile, videofile])
        dprint("video clip: {0} saved.".format(videofile))
	
	""" 
	bytes=''
        while True:
            bytes+=stream.read(1024)
            a = bytes.find('\xff\xd8')
            b = bytes.find('\xff\xd9')
            if a!=-1 and b!=-1:
                jpg = bytes[a:b+2]
                bytes= bytes[b+2:]
                img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
                video.write(img)

                cv2.imshow('image',img)
                if cv2.waitKey(10) == ord('q'):
                    break  
	"""
        """
        #camera = cv2.VideoCapture(-1) # for local built-in camera
        fourcc = cv2.cv.CV_FOURCC('m', 'p', '4', 'v')
	camera = cv2.VideoCapture(self.url_videostream)
        if not camera.isOpened:
            dprint('failed to open camera')
            raise ExceptionCam('failed to open camera')
        video  = cv2.VideoWriter()
        if not video.open(outfile, fourcc, 25, (640, 480), True):
            dprint('failed to open videowriter')
            raise ExceptionCam('failed to open camera')

        #capture videoclip for given duration
        start_time = int(time.time())
        elapsed_time = 0
        while duration > elapsed_time:
            ret, img = camera.read()
            if ret: 
                video.write(img)
                cv2.imshow("Live Video Streaming",img)
            if cv2.waitKey(10) == ord('q'):
                break

            elapsed_time = int(time.time()) - start_time

        video.release()
        camera.release()
	cv2.destroyAllWindows()
	videofile = outfile + "_" + time.strftime('%Y:%m:%d-%H:%M:%S')
	try:
            subprocess.check_call(["mv", outfile, videofile])
	    dprint("saved video clip as {0}".format(videofile))
        except Exception as err:
            dprint(err)
        """

    def timelapse(self, rate=1, duration=60):
        # http://askubuntu.com/questions/50339/how-to-make-a-stop-motion-or-time-lapse-video-with-webcam
        #ffmpeg -r 30 -i %04d.jpeg -s hd480 -vcodec libx264 time-lapse.mp4
        dprint("generating timelapse video for {0} sec at rate {1}".format(duration, rate))
        self._timelapse_thread = Thread(target=self._timelapse, args=(rate, duration))
        self._timelapse_thread.start()

    def _timelapse(self, rate=1, duration=60):
        """
        get timelapsed video with given gap and duration
        """
        #img1 = cv2.imread("snapshot0.jpg")
        #height, width, layers = img1.shape

        fourcc = cv2.cv.CV_FOURCC('m', 'p', '4', 'v')
        video  = cv2.VideoWriter()
        #if not video.open("timelapsed.avi", fourcc, rate, (640, 480), True):
        if not video.open("timelapsed.avi", fourcc, 1, (640, 480), True):
            dprint('failed to open videowriter')
            raise ExceptionCam('failed to open videowriter')

        for i in range(10):
            res=requests.get(self.url_snapshot+str(3), auth=(self.username, self.password), stream=True)
            if res.status_code == 200:
                #_img="snapshot.jpeg_" + time.strftime('%Y:%m:%d_%H:%M:%S')
                _img="snapshot{0}.jpg".format(i)
                with open(_img, "wb") as outfile:
                    res.raw.decode_content = True
                    shutil.copyfileobj(res.raw, outfile)

                img = cv2.imread(_img)
                video.write(img) 
	        subprocess.call(["rm", "-rf",  _img])

        video.release()
        cv2.destroyAllWindows()

    def play(self, videofile="video.avi"):
        if not os.path.exists(videofile):
            raise ExceptionCam('Cannot find ' + videofile +' file')

        dprint("playing video {0}".format(videofile))
        video=cv2.VideoCapture(videofile)
        #while(video.isOpened()):
        while video.isOpened():
            ret, frame = video.read()
            if ret: 
                cv2.imshow('Video Clip', frame)
            else:
                break
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

        video.release()
        cv2.destroyAllWindows() 

    def snapshot(self, size=4, name=None):
        #take snapshot
        #url_snapshot="http://192.168.1.80/img/snapshot.cgi?size=4"
	"""
	capture = cv2.VideoCapture(self.url_snapshot + str(size))
        ret, img = capture.read()
	dprint('got image. displaying and saving...')
        cv2.imshow("Snapshot", img)
        cv2.imwrite("snapshot.jpg", img)
	"""

	res=requests.get(self.url_snapshot, auth=(self.username, self.password), stream=True)
	if res.status_code == 200:
            if name:
                _img=name
            else:
                _img="snapshot_" + time.strftime('%Y:%m:%d-%H:%M:%S')
	    
            with open(_img, "wb") as outfile:
                res.raw.decode_content = True
                shutil.copyfileobj(res.raw, outfile)
        dprint("snapshot: {0} saved.".format(_img))

        """
        img = cv2.imread(_img)
        cv2.imshow('Snapshot', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        """

    def speak(self, message):
	#send audio message
	pass

class RC8230(SercommCam):
    def __init__(self, ipaddr, username="administrator", password=""):
        super(RC8230, self).__init__(ipaddr, username, password)

    def ptctrl(self, direction, step=10):
        """
        move pan-tilt to direction by amount of given step
        url_ptctrl="http://IPADDR/pt/ptctrl.cgi?mv=D,10"
        """
        direction=str(direction.upper())
        step=str(step)
        dprint("moving ip cam pantilt to {0} by {1}".format(direction, step))
        res = requests.get(self.url_ptctrl + direction + "," + step, auth=(self.username, self.password))

        time.sleep(5) # give motor time to react
        if res.status_code == 200:
            return True
        else:
            dprint("failed to control ip camera. error_code: {0}".format(res.status_code))
            return False

    def resolution(self, size=4):
        """
        set video resolution
        url_video="http://IPADDR/adm/set_group.cgi?group=JPEG&resolution=4"
        """
        if size > 4 or size < 1:
            dprint("invalid resolution. Setting to max resolution(=4)")
            size = 4

        res = requests.get(self.url_resolution + str(size), auth=(self.username, self.password))
        time.sleep(10) # give time to reset 
        if res.status_code == 200:
            dprint("IP cam mpeg resolution set to {0}".format(size))
            return True
        else:
            dprint("Failed to set IP cam mpeg resolution to {0}".format(size))
            return False

class RC8221(SercommCam):
    def __init__(self, ipaddr, username="administrator", password=""):
        super(RC8221, self).__init__(ipaddr, username, password)

    def resolution(self, size=4):
        """
        set video resolution
        url_video="http://IPADDR/adm/set_group.cgi?group=JPEG&resolution=4"
        """
        if size > 4 or size < 1:
            dprint("invalid resolution. Setting to max resolution(=4)")
            size = 4
        res = requests.get(self.url_resolution + str(size), auth=(self.username, self.password))
        time.sleep(10) # give time to reset
        if res.status_code == 200:
            dprint("IP cam mpeg resolution set to {0}".format(size))
            return True
        else:
            dprint("Failed to set IP cam mpeg resolution to {0}".format(size))
            return False

if __name__ == "__main__":
    cam_ipaddr = "192.168.1.81"
    cam = RC8221(cam_ipaddr)
    type(cam)

    dprint('getting cam info...')
    cam.getinfo()
    dprint('setting resolution...')
    cam.resolution(3)
    dprint('getting snapshot...')
    cam.snapshot(size=3)

    dprint('testing live video streaming...')
    cam.start()
    time.sleep(30)
    cam.stop()

    dprint('getting 30 sec video clip...')
    cam.videoclip(duration=30)
    time.sleep(30)
    if isinstance(cam, RC8230):
        dprint('testing pan tilt...')
        cam.ptctrl("R", "50") 
        cam.ptctrl("L", "50") 
        cam.ptctrl("U", "50") 
        cam.ptctrl("D", "50") 

    dprint('getting timelapse video...')
    cam.timelapse(rate=1, duration=30)
    time.sleep(35)
    cam.play("timelapsed.avi")


