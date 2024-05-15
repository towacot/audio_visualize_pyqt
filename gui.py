from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QProgressBar


class MainWindow():
    def __init__(self,chunk,):
        #app建てる
        app = pg.mkQApp("test")
        #uiファイル読み込み
        win=uic.loadUi("test.ui")
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
        self.testsp=np.full((1,5000),200)

        #グラフ描画領域の処理
        ##imageItemの初期化
        imageitem = pg.ImageItem(self.testsp)

        ##viewboxの初期化
        viewbox=win.graphicsView.addViewBox()
        viewbox.addItem(imageitem)
        ##axisitem の初期化　仮
        axis_left = pg.AxisItem(orientation="left")
        n_ygrid = 5
        yticks = {}
        for i in range(n_ygrid):
            yticks[i * (1 / (n_ygrid - 1))] = str(i)
        axis_left.setTicks([yticks.items()])
        
        ##plotitemの初期化
        plotitem = pg.PlotItem(viewBox=viewbox, axisItems={"left":axis_left})

        ##graphicsViewにplotItemをセット
        win.graphicsView.setCentralItem(plotitem)
        #--------------------------------------------------------------------------------
        #状態管理
        self.playstate=False
        self.volume_write=True
        
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
        self.dt=chunk
        ##その他データ
        self.data = 0
        self.ptr = 0
        self.t = [0]

        #入力フォーマット確認
        self.positive_threshold = (1 << 15) - 1
        self.negative_threshold = 1 << 15

        #スタイルシート適用
        self.setCustomStyle()

    def playClicked(self):
        print("play")
        self.playstate=True
    def pauseClicked(self):
        print("pause")
        self.playstate=False
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
        if self.volume_write:
            self.volume[:]=data
            self.volume_write=False
        else:
            pass
       
    def indicater_ui(self, volume):
      # ルート平均二乗 (RMS) を計算する
        if self.volume_write:
            return
        volume /= np.where(volume > 0, self.positive_threshold, self.negative_threshold)
        rms = np.sqrt(np.mean(volume**2))
        result = int(rms*100)
        self.volumebar.setValue(result)
        self.volume_write=True
    def get_sp_data(self,ary):
        pass
    def update(self):
        self.indicater_ui(self.volume)
        if self.playstate:
            self.testsp=np.block([[self.testsp],[np.full((1,5000),self.data)]])
            self.imageitem.setImage(self.testsp) 
            self.data=(self.data + 1) % 250  # データを増加させ、10で割った余りを取ることで0〜9の範囲にする
            
            #     sp_graph.enableAutoRange('xy', False)  # 初めのデータセットをプロットした後に自動スケーリングを停止
            self.ptr += 1
        else:
            pass

    def run(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(50)
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
