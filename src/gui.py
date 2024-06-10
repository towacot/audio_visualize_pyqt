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

    def __init__(self,params,Playstate,spectrogram_queue,paramsqueue):
        #app建てる
        app = pg.mkQApp("test")
        #uiファイル読み込み
        win=uic.loadUi("gui.ui")
        #ウィンドウの設定
        win.resize(1200,700)
        win.setWindowTitle('リアルタイムスペクトログラム')
    
        
        #グラフに必要な設定
        pg.setConfigOptions(antialias=True)
        #--------------------------------------------------------------------------------
        # UIの設定
        win.playButton.clicked.connect(self.playClicked)
        win.pauseButton.clicked.connect(self.pauseClicked)
        win.resetButton.clicked.connect(self.resetClicked)

        chunkselecter = win.chunkbox
        stepselecter = win.stepbox
        chunkselecter.addItems(["1024","2048","4096","8192"])
        stepselecter.addItems(["1/4","1/2","3/4","1"])
        chunkselecter.setCurrentIndex(1)
        stepselecter.setCurrentIndex(2)
        win.show()
        #--------------------------------------------------------------------------------
        #スペクトログラム格納用配列
        self.SPECTROGRM=np.full((1,1025),-80,dtype=np.float64)
        ##スペクトログラム用パラメタ
        self.step_width=params["step"]
        self.chunk=params["chunk"]
        self.sample_rate=params["sample_rate"]
        self.fleqs=self.chunk//2+1
        #グラフ描画領域の処理
        ##imageItemの初期化
        imageitem = pg.ImageItem(self.SPECTROGRM)
        # カラーマップの設定
        colormap = cm.get_cmap("inferno")  
        colormap._init()
        lut = (colormap._lut * 255).view(np.ndarray)
        imageitem.setLookupTable(lut)
        imageitem.setLevels([-80, 0])

        ##viewboxの初期化
        viewbox=win.graphicsView.addViewBox()
        viewbox.addItem(imageitem)
        ##axisitem の初期化　仮
        self.time_axis = np.arange(self.SPECTROGRM.shape[0]) * params["step"] / params["sample_rate"]
        axis_left = pg.AxisItem(orientation="left")
        axis_bottom = pg.AxisItem(orientation="bottom")
        axis_bottom.setLabel('Time ')
        #縦軸の設定
        n_ygrid = 10
        yticks = {}
        for i in range(n_ygrid):
            index=int(self.fleqs*i/n_ygrid)
            yticks[index] = str(int(index*params["sample_rate"]/self.fleqs)) + "Hz"
        axis_left.setTicks([yticks.items()])
        plotitem = pg.PlotItem(viewBox=viewbox, axisItems={"left": axis_left, "bottom": axis_bottom})
        
        
        ##plotitemの初期化
        # plotitem = pg.PlotItem(viewBox=viewbox, axisItems={"left":axis_left},)
        
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
        self.volume=np.zeros(256)
        self.volumebar = win.findChild(QProgressBar, 'volumeBar')
        
        ##パラメタ共有用のキュー
        self.paramsqueue=paramsqueue
        ##その他データ
        self.t = [0]
        self.sample_rate = params["sample_rate"]

        #入力フォーマット確認
        self.positive_threshold = (1 << 15) - 1
        self.negative_threshold = 1 << 15

        #スタイルシート適用
        self.setCustomStyle()

        # スペクトログラムチャンクを保存するキュー
        self.spectrogram_queue = spectrogram_queue

    def setaxis(self):
       ##axisitem の初期化　仮
        axis_left = pg.AxisItem(orientation="left")
        axis_bottom = pg.AxisItem(orientation="bottom")
        axis_bottom.setLabel('Time (s)')
        #縦軸の設定
        n_ygrid = 10
        yticks = {}
        for i in range(n_ygrid):
            index=int(self.fleqs*i/n_ygrid)
            yticks[index] = str(int(index*self.sample_rate/(2*self.fleqs))) + "Hz"
        axis_left.setTicks([yticks.items()])
        self.plotitem = pg.PlotItem(viewBox=self.viewbox, axisItems={"left": axis_left, "bottom": axis_bottom})
        self.plotitem.setYRange(min=0,max=index,padding=0)
        self.win.graphicsView.setCentralItem(self.plotitem)

    def setparams(self):
        #現在のパラメタをクリア
        self.spectrogram_queue.clear()
        #コンボボックスからパラメータを取得
        self.chunk = int(self.win.chunkbox.currentText())
        stepindex = int(self.win.stepbox.currentIndex())+1
        self.step_width = (self.chunk*stepindex)//4
        self.fleqs=self.chunk//2+1
        #グラフの軸を調整
        self.setaxis()
        #スペクトログラムの初期化
        self.SPECTROGRM=np.full((1,int(self.fleqs)),-80,dtype=np.float64)
        
        #パラメータをキューに追加
        self.paramsqueue.put({"chunk":self.chunk,"step":self.step_width})

    def playClicked(self):
        if self.playstate.full():
            return
        #選択中のパラメータを適用
        self.setparams()
        #playstateを更新
        self.playstate.put(1)
    def pauseClicked(self):
        if self.playstate.empty():
            return
        #キューを空にする
        self.playstate.get()
    def resetClicked(self):
       # print("reset")
        #print("reset")
        pass
       

    def indicater(self,data):
        if not self.volume_write:
            self.volume_write=True
            data=np.array(data,dtype=np.float64)
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
        # self.indicater_ui(self.volume)
        #play中の処理
        if not self.playstate.empty():
            #今あるすべての計算結果について描画を行う
            while not len(self.spectrogram_queue) == 0:
                #1窓幅分のスペクトルデータを取り出す
                ary = self.spectrogram_queue.popleft()
                ary =np.array(ary, dtype=np.float64)
                #メインのスペクトログラムデータに追加
                self.SPECTROGRM = np.vstack((self.SPECTROGRM, ary))
                #表示数の処理
                max_rows = 300
                if self.SPECTROGRM.shape[0] > max_rows:
                    self.SPECTROGRM = self.SPECTROGRM[-max_rows:]
            #スペクトログラムの描画
            self.imageitem.setImage(self.SPECTROGRM, autoLevels=False)


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
