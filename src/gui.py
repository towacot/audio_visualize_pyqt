from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
import sys
import queue
import time
from PyQt5 import uic
from PyQt5.QtWidgets import QProgressBar
from colour import Color
from matplotlib import cm
class MainWindow():

    def __init__(self,params,Playstate,spectrogram_queue):
        #app建てる
        app = pg.mkQApp("test")
        #uiファイル読み込み
        win=uic.loadUi("gui.ui")
        #ウィンドウの設定
        win.resize(1200,700)
        win.setWindowTitle('pyqtgraph example: Plotting')
    
        
        #グラフに必要な設定
        pg.setConfigOptions(antialias=True)
        #--------------------------------------------------------------------------------
        # UIの設定
        win.playButton.clicked.connect(self.playClicked)
        win.pauseButton.clicked.connect(self.pauseClicked)
        win.resetButton.clicked.connect(self.resetClicked)
        win.show()
        #--------------------------------------------------------------------------------
        #テスト用配列データ
        self.testsp=np.full((1,1025),-80,dtype=np.float64)

        #グラフ描画領域の処理
        ##imageItemの初期化
        imageitem = pg.ImageItem(self.testsp)
        # カラーマップの設定
        colormap = cm.get_cmap("inferno")  # cm.get_cmap("CMRmap")
        colormap._init()
        lut = (colormap._lut * 255).view(np.ndarray)
        imageitem.setLookupTable(lut)
        imageitem.setLevels([-60, 0])

        ##viewboxの初期化
        viewbox=win.graphicsView.addViewBox()
        viewbox.addItem(imageitem)
        ##axisitem の初期化　仮
        self.time_axis = np.arange(self.testsp.shape[0]) * params["step"] / params["sample_rate"]
        axis_left = pg.AxisItem(orientation="left")
        axis_bottom = pg.AxisItem(orientation="bottom")
        axis_bottom.setLabel('Time (s)')
        n_ygrid = 6000
        yticks = {}
        for i in range(n_ygrid):
            yticks[i] = str(i)
        axis_left.setTicks([yticks.items()])
        plotitem = pg.PlotItem(viewBox=viewbox, axisItems={"left": axis_left, "bottom": axis_bottom})
       
        
        ##plotitemの初期化
        plotitem = pg.PlotItem(viewBox=viewbox, axisItems={"left":axis_left},)
        
        ##graphicsViewにplotItemをセット
        win.graphicsView.setCentralItem(plotitem)
        #--------------------------------------------------------------------------------
        #状態管理
        self.playstate=Playstate
        self.volume_write=False
        
        #ui構成要素
        self.app=app
        self.win=win
        self.imageitem=imageitem
        self.viewbox=viewbox
        self.plotitem=plotitem

        #入力データ管理
        self.volume=np.zeros(1024)
        self.volumebar = win.findChild(QProgressBar, 'volumeBar')
        ##スペクトログラム用データ 仮
        self.sp_ary = np.zeros((1, 5000))
        self.dt=params["step"]/params["sample_rate"]
        self.step_width=params["step"]
        ##その他データ
        self.data = 0
        self.ptr = 0
        self.t = [0]
        self.sample_rate = params["sample_rate"]

        #入力フォーマット確認
        self.positive_threshold = (1 << 15) - 1
        self.negative_threshold = 1 << 15

        #スタイルシート適用
        self.setCustomStyle()

        # スペクトログラムチャンクを保存するキュー
        self.spectrogram_queue = spectrogram_queue
        self.blank_positions = []  # 空白部分の位置を記憶するリスト

        self.current_time_line = pg.InfiniteLine(angle=90, movable=False, pen='r')
        plotitem.addItem(self.current_time_line)
        self.plotitem = plotitem
        self.start_time = time.time()


    def playClicked(self):
        print("play")
        self.playstate.put(1)
    def pauseClicked(self):
        print("pause")
        #キューを空にする
        self.playstate.get()
    def resetClicked(self):
        print("reset")
        print("reset")
        self.playstate = False
        self.ptr = 0
        self.data = 0
        self.t = [0]
        self.testsp=np.full((1,5000),200)
        self.imageitem.setImage(self.testsp)

    def indicater(self,data):
        if not self.volume_write:
            self.volume_write=True
            self.volume[:]=data
            self.volume_write=False
        else:
            pass
       
    def indicater_ui(self, volume):
      # ルート平均二乗 (RMS) を計算する
        if self.volume_write:
            return
        self.volume_write=True
        volume /= np.where(volume > 0, self.positive_threshold, self.negative_threshold)
        rms = np.sqrt(np.mean(volume**2))
        result = int(rms*100)
        self.volumebar.setValue(result)
        self.volume_write=False

    def update(self):
        if not self.playstate.empty():
            while not len(self.spectrogram_queue) == 0:
                ary = self.spectrogram_queue.popleft()
                ary =np.array(ary, dtype=np.float64)
                self.testsp = np.vstack((self.testsp, ary))
                max_rows = 250
                if self.testsp.shape[0] > max_rows:
                    self.testsp = self.testsp[-max_rows:]
            self.imageitem.setImage(self.testsp, autoLevels=False)


    def run(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(1)
        self.start_time = time.time()
        self.app.exec_()

    def setCustomStyle(self):
        style = """
            QPushButton#PlayButton,
            QPushButton#PauseButton,
            QPushButton#ResetButton{
            background-color: rgb(248, 248, 248);
            border-bottom-color: rgb(145, 145, 145);
            border-right-color: rgb(145, 145, 145);
            border-radius: 5px;
            border-width: 2px;
            border-style: none ridge ridge none;
            }

            QProgressBar {
            border: 2px solid #7F939B;
            border-radius: 5px;
            height:4px;
            background-color: #E0E0E0; 
            text-align: center;           
            }
            QProgressBar::chunk {
            background-color: #7F939B;
            width: 10px; 
            margin: 0.5px;
            }
            QComboBox {
            background-color: #E0E0E0;
            border: 2px solid #2196F3;
            border-radius: 5px;
            }
            QComboBox::drop-down {
            
            }
            
            
        """
        self.win.setStyleSheet(style)
  
if __name__ == '__main__':
    main = MainWindow(1)
    main.run()
