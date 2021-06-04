# -*- coding:utf-8 -*-
# -----------------------------------------------------------------------------
# MainWindow.pyw
#
# The main window for an interpreter of while programs.
# 27 May 2021.
#
# Copyright (c) 2021 Shinya Sato
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php#
# -----------------------------------------------------------------------------

import sys
import os

from PySide2.QtCore import Qt, QSize, Signal, QMutex, \
    QMutexLocker, QThread, QCoreApplication, QSettings
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QWidget, QPushButton, QSizePolicy, \
    QTextEdit, QGridLayout, QSplitter, QMainWindow, QStatusBar, \
    QAction, QFontDialog, QMessageBox, QApplication

from QCodeEditor import QCodeEditor

import evaluator

CONFIG_FILE = 'config.ini'


#---------------------------------------------------------------------------
class MyThread(QThread):
    # Create signals 
    stopped_value = Signal(bool)
    message_value = Signal(str)

    
    def __init__(self, parent=None, callback=None):
        super(MyThread, self).__init__(parent)
        self.stopped = False
        self.mutex = QMutex()
        self.evaluator = evaluator.Evaluator(GUI=True,
                                             callback=self.emit_message)
        
    def __del__(self):
        # Threadオブジェクトが削除されたときにThreadを停止する
        print("deleted")
        
        #self.result_value.emit(False)
        #self.stop()
        #self.wait()
        

    def setup(self, sentences):
        self.stopped = True
        self.sentences = sentences
        

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

        self.stopped_value.emit(self.stopped)

            
    def restart(self):
        with QMutexLocker(self.mutex):
            self.stopped = False
            

    def emit_message(self, mes):
        # processEvents は、スレッド内で行い、MainWindows に処理を渡す
        # このようにしないと、バッファが溜まってしまう？、らしい？
        QThread.msleep(1)
        self.message_value.emit(mes)
        QCoreApplication.processEvents()  

        
    def run(self):
        if self.stopped:
            self.restart()
            self.evaluator.evaluator(self.sentences)
            self.stop()
            
        
        


#---------------------------------------------------------------------------
class CentralWidget(QWidget):
    
    def __init__(self, parent=None):
        super(CentralWidget, self).__init__(parent)
        self.setupUi()
        self.setAcceptDrops(True)
        self.setupThread()   

                
    def keyPressEvent(self, event):
        # print('keyPressEvent, key = %s.' % event.key())

        # Ctrl と Enter の同時押し
        if event.modifiers() & Qt.ControlModifier and \
           event.key() == Qt.Key_Return:
            self.pushButton_start.click()
                        
        else:
            # 自分が処理しない場合は、オーバーライド元の処理を実行
            super().keyPressEvent(event)

                
    def setupThread(self):
        self.thread = MyThread(parent=self)
        self.thread.stopped_value.connect(self.enable_start_button)
        self.thread.message_value.connect(self.add_messages)

        
    def setupUi(self):
                
        # 実行ボタン
        self.pushButton_start = QPushButton("実行")
        #self.connect(self.pushButton_start,
        #             SIGNAL("clicked()"), self.run_selection)
        self.pushButton_start.clicked.connect(self.run_selection)
        
        self.pushButton_start.setSizePolicy(QSizePolicy.Preferred,
                                            QSizePolicy.Fixed)

        
        # 強制終了ボタン
        self.pushButton_stop = QPushButton("強制終了")
        self.pushButton_stop.clicked.connect(self.stop)
        self.pushButton_stop.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)
        self.pushButton_stop.setEnabled(False)

        # プログラム入力用
        #self.editor = QTextEdit()
        #self.editor = QPlainTextEdit()

        self.editor = QCodeEditor()        
        self.editor.setUndoRedoEnabled(True)
        
        
        # 実行結果の表示用
        #self.messages = QTextBrowser()
        self.messages = QTextEdit()
        self.messages.setReadOnly(True)
        self.messages.setUndoRedoEnabled(False)
        self.messages.setStyleSheet("background-color: #e0e0e0")

        rowHeight = self.fontMetrics().lineSpacing()
        self.messages.setMinimumHeight(rowHeight * 1)

        
        # メイン画面に部品を配置する
        layout = QGridLayout()
        layout.setSpacing(10)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setObjectName("splitter1")        
        self.splitter.setHandleWidth(1)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.messages)
        self.splitter.setStretchFactor(0,3)
        self.splitter.setStretchFactor(1,1)
        self.splitter.setChildrenCollapsible(False)
        

        layout.addWidget(self.splitter, 0, 0, 10, 1)
        
        layout.addWidget(self.pushButton_start, 0, 2)
        layout.addWidget(self.pushButton_stop,  1, 2)
        
        self.setLayout(layout)

        
        
    def enable_start_button(self):
        self.pushButton_start.setEnabled(True)
        self.pushButton_stop.setEnabled(False)

    def disable_start_button(self):
        self.pushButton_start.setEnabled(False)
        self.pushButton_stop.setEnabled(True)
        
        
    def reset_buttons(self):
        self.pushButton_start.setChecked(False)
        return 0

    def stop(self):
        # sys.exit()
        # QCoreApplication.processEvents()
        
        self.thread.terminate()
        self.thread.wait()
        self.thread.stop()
        self.add_messages("強制終了されました");
                

    def add_messages(self, mes):
        cursor = self.messages.textCursor()
        cursor.insertText(mes + "\n")


        
    def run_selection(self):

        self.messages.clear()
        self.disable_start_button()
        
        textboxValue = self.editor.toPlainText()
        self.thread.setup(textboxValue)
        
        self.thread.start()
    



    

#---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent=parent)

        # Window Title
        self.setWindowTitle('whileプログラムのインタプリタ')

        # Status Bar
        #self.statusBar = QStatusBar(self)
        #self.setStatusBar(self.statusBar)
        #self.statusBar.showMessage('')

        # Menu Bar
        self.exit_menu = self.menuBar().addMenu('ファイル')

        self.exitAct = QAction('フォントの選択', self,
                                         statusTip='フォントの選択',
                                         triggered=self.select_font)        
        self.exit_menu.addAction(self.exitAct)

        self.exitAct = QAction('終了する', self,
                                         shortcut="Ctrl+Q",
                                         statusTip='終了する',
                                         triggered=self.close)        
        self.exit_menu.addAction(self.exitAct)
        
        self.help_menu = self.menuBar().addMenu('このソフトウェアの使い方')
        self.aboutAct = QAction('使い方', self, statusTip='使い方', triggered=self.about)
        self.help_menu.addAction(self.aboutAct)

        # Central Widget
        self.central_widget = CentralWidget(parent=parent)
        self.setCentralWidget(self.central_widget)
        widget_layout = QGridLayout()
        widget_layout.addWidget(self)
        self.setLayout(widget_layout)

        self.loadSettings()


    def closeEvent(self, e):
        self.saveSettings()


    def initSettings(self):
        # Window Size
        # self.setFixedSize(750, 700)
        self.resize(600, 400)

        # font
        c = self.central_widget.editor.textCursor()
        current_font = c.charFormat().font()
        current_font.setPointSize(12)
        self.update_font(current_font)
        
        
    def loadSettings(self):
        # https://fereria.github.io/reincarnation_tech/11_PySide/01_PySide_Basic/00_Tutorial/09_qsettings/
        
        if not os.path.exists(CONFIG_FILE): # ファイル存在判定
            self.initSettings()
            return
            
        setting = QSettings(CONFIG_FILE, QSettings.IniFormat)

        # splitter の位置を復帰        
        self.central_widget.splitter.restoreState(setting.value(self.central_widget.splitter.objectName()))

        # GUIの位置を復帰
        self.restoreGeometry(setting.value("geometry"))

        # Font
        try:
            font_family = setting.value("font_family")
            font_size = int(setting.value("font_size"))
            font_weight = int(setting.value("font_weight"))
                        
            font = QFont(font_family, font_size, font_weight)
            self.update_font(font)
        except:
            pass
        
        
        
    def saveSettings(self):
        setting = QSettings(CONFIG_FILE, QSettings.IniFormat)

        # Splitterの位置保存
        setting.setValue(self.central_widget.splitter.objectName(),
                         self.central_widget.splitter.saveState())
        # UIの位置保存
        setting.setValue("geometry", self.saveGeometry())

        # font 情報（QTextEdit からの取得はうまくできない）
        c = self.central_widget.editor.textCursor()
        current_font = c.charFormat().font()

        font_family = current_font.family()
        font_size = current_font.pointSize()
        font_weight = current_font.weight()
        setting.setValue("font_family", font_family)
        setting.setValue("font_size", font_size)
        setting.setValue("font_weight", font_weight)

        
        
    def update_font(self, font):
        self.central_widget.editor.setFont(font)
        self.central_widget.messages.setFont(font)
        #self.central_widget.pushButton_start.setFont(font)
        #self.central_widget.pushButton_stop.setFont(font)
        #self.central_widget.pushButton_reset.setFont(font)
        #self.central_widget.pushButton_clear.setFont(font)

        

    def select_font(self):
        # QPlainTextEdit から取得する場合
        c = self.central_widget.editor.textCursor()
        current_font = c.charFormat().font()
        
        # QTextEdit から取得する場合（うまく行かない）
        #font_family = self.central_widget.messages.fontFamily()
        #font_size = self.central_widget.messages.fontPointSize()
        #font_weight = self.central_widget.messages.fontWeight()
        #current_font = QFont(family=font_family,
        #                           pointSize = font_size,
        #                           weight = font_weight)
        
        (ok, font) = QFontDialog.getFont(current_font, self, "Select font")
        if ok:
            #fontInfo = font.toString()
            #QMessageBox.information(self, "Font", fontInfo)
            self.update_font(font)
            
            
    def about(self):
        QMessageBox.about(self, "このソフトウェアについて",
            "ソフトウェアの使い方については、同梱されている「README」などを参照してください。"
)
#-- --------------------------------------------------------- --#
#-- --------------------------------------------------------- --#
#-- --------------------------------------------------------- --#
#-- --------------------------------------------------------- --#
#-- --------------------------------------------------------- --#
#-- --------------------------------------------------------- --#
#-- --------------------------------------------------------- --#




#---------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    mainwindow = MainWindow()
    mainwindow.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()




