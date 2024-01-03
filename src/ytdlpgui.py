import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QDialog
from PyQt5.QtCore import QProcess
#from PyQt5 import uic
from design import Ui_Dialog
from configparser import ConfigParser

class Ui(QDialog, Ui_Dialog):
    def __init__(self, parent=None, cfg=None, cfg_name=""):
        super(Ui, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.setupUi(self)

        self.cfg = cfg
        self.cfg_name = cfg_name
        self.cfg.read(self.cfg_name)

        #self.setWindowIcon(QtGui.QIcon('C:/Users/ryand/Documents/python_stuff/ytdlpgui/weirdlookingpepe.png'))
        #uic.loadUi('C:/Users/ryand/Documents/python_stuff/ytdlpgui/design.ui', self) # Load the .ui file

        self.ytdlp_path = ""
        self.ffmpeg_path = ""
        self.download_path = os.path.dirname(os.path.abspath(sys.argv[0])) # default download path is current directory

        # check if any are in the config file already
        if (self.cfg.has_option("", "ytdlp_path")):
            self.ytdlp_path = cfg['DEFAULT']['ytdlp_path']

        if (self.cfg.has_option("", "ffmpeg_path")):
            self.ffmpeg_path = cfg['DEFAULT']['ffmpeg_path']

        if (self.cfg.has_option("", "download_path")):
            self.download_path = cfg['DEFAULT']['download_path']

        self.message("yt-dlp location: "+ ("None" if self.ytdlp_path == "" else self.ytdlp_path))
        self.message("ffmpeg location: "+ ("Default (will only work if ffmpeg is in your path/same folder as yt-dlp)" if self.ffmpeg_path == "" else self.ffmpeg_path))
        self.message("location to download to: " + self.download_path + "\n")

        self.currProcess = None
        self.video = None
        self.audio = None

        self.dlpathButton.clicked.connect(self.dlpathButtonPressed)
        self.ffmpegButton.clicked.connect(self.ffmpegButtonPressed)
        self.pathButton.clicked.connect(self.pathButtonPressed)
        self.updateButton.clicked.connect(self.updateButtonPressed)

        self.listButton.clicked.connect(self.listButtonPressed)
        self.downloadButton.clicked.connect(self.downloadButtonPressed)

        self.show()

    def pathButtonPressed(self):
        fs = FileSelector('select yt-dlp location', filetypes = "Executable Files (*.exe)")
        ytdlp_path = fs.initUI()
        if ytdlp_path == None:
            self.message("yt-dlp location unchanged: " + ("None" if self.ytdlp_path == "" else self.ytdlp_path) + "\n")
            return
        self.ytdlp_path = ytdlp_path
        self.message("yt-dlp location updated: " + self.ytdlp_path + "\n")

        self.cfg['DEFAULT']['ytdlp_path'] = self.ytdlp_path
        with open(self.cfg_name, 'w') as configfile:    # save
            self.cfg.write(configfile)

    def ffmpegButtonPressed(self):
        fs = FileSelector('select ffmpeg location', filetypes = "Executable Files (*.exe)")
        ffmpeg_path = fs.initUI()
        if ffmpeg_path == None:
            self.message("ffmpeg location unchanged: " + ("Default (will only work if ffmpeg is in your path/same folder as yt-dlp)" if self.ffmpeg_path == "" else self.ffmpeg_path) + "\n")
            return
        self.ffmpeg_path = ffmpeg_path
        self.message("ffmpeg location updated: " + self.ffmpeg_path + "\n")

        self.cfg['DEFAULT']['ffmpeg_path'] = self.ffmpeg_path
        with open(self.cfg_name, 'w') as configfile:    # save
            self.cfg.write(configfile)

    def dlpathButtonPressed(self):
        fs = FileSelector('select location to download to', directory=True)
        download_path = fs.initUI()
        if download_path == None:
            self.message("location to download to unchanged: " + ("None" if self.download_path == "" else self.download_path) + "\n")
            return

        self.download_path = download_path
        self.message("location to download to updated: " + self.download_path + "\n") # TODO: save to external file

        self.cfg['DEFAULT']['download_path'] = self.download_path
        with open(self.cfg_name, 'w') as configfile:    # save
            self.cfg.write(configfile)

    def updateButtonPressed(self):
        err = False
        if self.ytdlp_path == "":
            self.message("yt-dlp path not chosen!")
            err = True
        if (not err) and (self.currProcess is None):
            self.setUpProcess()
            self.currProcess.start(self.ytdlp_path, ['-U'])

        if err:
            self.message("")

    def listButtonPressed(self):
        err = False
        if self.ytdlp_path == "": # check for path
            self.message("yt-dlp path not chosen!")
            err = True

        videoLink = self.linkBox.toPlainText()
        if videoLink == "": # check for video link
            self.message("video link is empty!")
            err = True

        if (not err) and (self.currProcess is None):
            self.setUpProcess()
            self.currProcess.start(self.ytdlp_path, ['-F', videoLink])

        if err:
            self.message("")

    def downloadButtonPressed(self):
        err = False
        if self.ytdlp_path == "": # check for path
            self.message("yt-dlp path not chosen!")
            err = True

        videoLink = self.linkBox.toPlainText()
        if videoLink == "": # check for video link
            self.message("video link is empty!")
            err = True

        video = self.videoBox.toPlainText()
        audio = self.audioBox.toPlainText()
        if (video == "") and (audio == ""): # check video and audio quality
            self.message("video quality and audio quality are both empty!")
            err = True
        
        if not err:
            self.setUpProcess()
            argArr = []

            if self.ffmpeg_path != "":
                argArr.extend(["--ffmpeg-location", self.ffmpeg_path])

            if self.download_path != "":
                argArr.extend(['--output', self.download_path + "/%(title)s.%(ext)s"])

            argArr.append("-f")

            if video == "":
                argArr.append(audio)
            elif audio == "":
                argArr.append(video)
            else: # both video and audio are not none
                argArr.append(video + "+" + audio)
            
            argArr.append(videoLink)

            cmd = "Running command: " + self.ytdlp_path
            for i in argArr:
                cmd += " " + i
            self.message(cmd)
            self.currProcess.start(self.ytdlp_path, argArr)
        
        if err:
            self.message("")

    def setUpProcess(self):
        self.currProcess = QProcess()
        self.currProcess.readyReadStandardOutput.connect(self.handle_stdout)
        self.currProcess.readyReadStandardError.connect(self.handle_stderr)
        self.currProcess.stateChanged.connect(self.handle_state)
        self.currProcess.finished.connect(self.process_finished)

    def handle_stderr(self):
        data = self.currProcess.readAllStandardError() # data is a QString
        stderr = bytes(data).decode("utf8")
        self.message(stderr)

    def handle_stdout(self):
        data = self.currProcess.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.message(stdout)

    def handle_state(self, state):
        if state == QProcess.Starting:
            return
        states = {
            QProcess.NotRunning: 'Complete',
            # QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        self.message(f"Command: {state_name} --------------------------------------------------------------")

    def process_finished(self):
        self.currProcess = None

    def message(self, s):
        self.consoleBox.append(s)


class FileSelector(QWidget):
    def __init__(self, title, filetypes="", directory=False):
        super().__init__()
        self.title = title
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.filetypes = filetypes
        self.directory=directory
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        return self.openFileNameDialog()     
    
    def openFileNameDialog(self):
        #options = QFileDialog.Options()
        #options |= QFileDialog.DontUseNativeDialog
        if not self.directory:
            fileName, _ = QFileDialog.getOpenFileName(self, self.title, "", self.filetypes)
        else:
            fileName = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if fileName:
            return fileName

if __name__ == '__main__':
    config = ConfigParser()
    app = QApplication(sys.argv)
    ex = Ui(cfg=config, cfg_name = 'ytdlpgui.ini')
    
    sys.exit(app.exec_())