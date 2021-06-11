# -*- coding:utf-8 -*-
# -----------------------------------------------------------------------------
# MainWindow.pyw
#
# The main window for an interpreter of while programs.
# 11 June 2021.
#
# Copyright (c) 2021 Shinya Sato
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php#
# -----------------------------------------------------------------------------

import sys
import os
import copy

from PySide2.QtCore import (Qt, QSize, 
                            QSettings, QEvent, QDir, QFile, QFileInfo,
                            QTextStream)
from PySide2.QtGui import QFont, QIcon
from PySide2.QtWidgets import (QWidget, QPushButton, 
                               QTextEdit, QGridLayout, QVBoxLayout, QSplitter,
                               QMainWindow, QStatusBar,
                               QAction, QFontDialog, QMessageBox,
                               QApplication, QToolBar, QToolButton,
                               QDockWidget, QStyle, QFrame, QFileDialog)

from QCodeEditor import QCodeEditor
from TableView import TableView
from MyThread import MyThread

CONFIG_FILE = 'config.ini'


import PySide2
dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path



class History:
    def __init__(self):

        self.generation = 0
        self.history = []

        

    def set_firstGeneration(self, elem):
        self.generation = 1
        self.history = []
        self.history.append(elem)

        
    def set_elem(self, elem):
        self.history.append(elem)
        self.generation += 1


        
    def get_elem(self, generation=None):
        if generation == None:
            generation = self.generation

                   
        return self.history[generation-1]

    def get_elem_previous(self, generation=None):
        if generation == None:
            generation = self.generation

        return self.history[generation-2]

            
    def is_theFirstGeneration(self):
        if self.generation > 1:
            return False
        else:
            return True
        
    def is_theLatestGeneration(self):
        if self.generation == len(self.history):
            return True
        else:
            return False
        
    def change_generation_next(self):
        self.generation += 1

        
    def change_generation_previous(self):
        self.generation -= 1
        
    def init_generation(self):
        # 0世代
        self.generation = 0
        
#---------------------------------------------------------------------------
class CentralWidget(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_Ui()
        self.setAcceptDrops(False)
                
        
    def setup_Ui(self):
                        
        # プログラム入力用
        #self.editor = QTextEdit()
        #self.editor = QPlainTextEdit()

        self.editor = QCodeEditor()        
        self.editor.setUndoRedoEnabled(True)
        
        
        # 実行結果の表示用
        #self.messageArea = QTextBrowser()
        self.messageArea = QTextEdit()
        self.messageArea.setReadOnly(True)
        self.messageArea.setUndoRedoEnabled(False)
        self.messageArea.setStyleSheet("background-color: #e0e0e0")

        rowHeight = self.fontMetrics().lineSpacing()
        self.messageArea.setMinimumHeight(rowHeight * 1)


        
        
        # メイン画面に部品を配置する
        layout = QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(5,0,5,5 )

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.splitter.setObjectName("splitter")        
        self.splitter.setHandleWidth(1)

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.messageArea)
        self.splitter.setStretchFactor(0,3)
        self.splitter.setStretchFactor(1,1)
        self.splitter.setChildrenCollapsible(False)
        
        layout.addWidget(self.splitter)
        
        self.setLayout(layout)
        
       
    # public methods
    def add_messages(self, mes):
        cursor = self.messageArea.textCursor()
        cursor.insertText(mes + "\n")


    def clear_messages(self):
        self.messageArea.clear()


    def get_program(self):
        return self.editor.toPlainText()

    
    def set_HighlightLine(self, lineno):
        self.editor.setHighlightLineno(lineno)
        self.editor.highlightLine()
        
    def clear_HighlightLine(self):
        self.editor.clearHighlightLine()

    def set_ReadOnly(self, flag):
        self.editor.setReadOnly(flag)
        if flag:
            self.editor.setExtraSelections([])
            


    

#---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent=parent)

        # Status Bar
        #self.statusBar = QStatusBar(self)
        #self.setStatusBar(self.statusBar)
        #self.statusBar.showMessage('')

        self.setAcceptDrops(True)

        # タイトル        
        self.title = 'WHILE Program Interpreter'
        
        # Menu Bar
        self.setup_MenuBar()

        # ツールバー
        self.setup_ToolBar()

        # ドック
        self.setup_Dock()

        # Central Widget
        self.centralWidget = CentralWidget(parent=parent)
        self.setCentralWidget(self.centralWidget)
        self.centralWidget.editor.document().modificationChanged.connect(self.modified_event)
        

        # main 関数で focus をもらうため（すべて表示し終わった main 内で実行させる）
        self.focusWidget = self.centralWidget.editor
        
        # MainWindow を配置
        layout = QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        
        layout.addWidget(self)
        self.setLayout(layout)
       
        
        # スレッド
        self.thread = MyThread(parent=self)
        self.thread.stopped_value.connect(self.eval_finished)
        self.thread.message_value.connect(self.centralWidget.add_messages)

        
        # Settings 処理
        self.loadSettings()


        # public ---------------------------
        # メンバ変数

        # 閉じるときに設定を保存する
        self.resetConfigFlag = True

        # Env の History
        self.history = History()
        

        # ファイル名
        self.fname = "無題"
        self.fname_with_path = ""
        
        self.set_window_title(self.fname_with_path)
        

    def set_window_title(self, fname):
        # Window Title
        self.setWindowIcon(QIcon.fromTheme("application-text"))
        if fname != "":
            self.setWindowTitle(fname + '[*] - ' + self.title)
        else:
            self.setWindowTitle('[*]' + self.title)
            


    # -----------------------------------------------------------------
    # ドラッグ%ドロップ関連
    # -----------------------------------------------------------------
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            file_name = url.toLocalFile()
            #print("Dropped file: " + file_name)
            
        self.open_file(file_name)

            
    # -----------------------------------------------------------------
    # ドック関連
    # -----------------------------------------------------------------
    def setup_Dock(self):
        # 環境表示用
        self.tableView = TableView()


        # ボタン群レイアウト
        layout = QGridLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        
        self.startDebugButton = QPushButton()
        self.startDebugButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.startDebugButton.clicked.connect(self.set_program)
        self.startDebugButton.setCheckable(False)  
        
        self.stopDebugButton = QPushButton()
        self.stopDebugButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopDebugButton.setEnabled(False)
        self.stopDebugButton.setCheckable(False)  
        self.stopDebugButton.clicked.connect(self.stop_debug)

        self.rewindDebugButton = QPushButton()
        self.rewindDebugButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.rewindDebugButton.clicked.connect(self.rewind_program)
        self.rewindDebugButton.setEnabled(False)
        self.rewindDebugButton.setCheckable(False)  
        
        self.onestepDebugButton = QPushButton()
        self.onestepDebugButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.onestepDebugButton.clicked.connect(self.run_program_onestep)
        self.onestepDebugButton.setEnabled(False)
        self.onestepDebugButton.setCheckable(False)  


        line = QFrame(self)
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Plain)
 
        
        layout.addWidget(self.startDebugButton,0,0)
        layout.addWidget(self.stopDebugButton,0,1)
        layout.addWidget(line,0,2)        
        layout.addWidget(self.rewindDebugButton,0,3)
        layout.addWidget(self.onestepDebugButton,0,4)

        # ボタン群レイアウト layout を widget として扱えるようにする
        buttonsWidget = QWidget()
        buttonsWidget.setLayout(layout)
        buttonsWidget.setContentsMargins(0,0,0,0)


        # layoutV に、ボタン群 widget と self.tableView を縦方向に追加
        layoutV = QVBoxLayout()
        layoutV.setSpacing(0)
        layoutV.setContentsMargins(0,0,0,0)
        layoutV.addWidget(buttonsWidget)        
        layoutV.addWidget(self.tableView)
        
        debugWidget = QWidget()
        debugWidget.setLayout(layoutV)
        debugWidget.setContentsMargins(0,0,0,0)
        

        # Dock の作成
        self.addDock = QDockWidget('デバッグ', self)        
        self.addDock.setObjectName("dock")        
        self.addDock.setWidget(debugWidget)
        self.addDock.setContentsMargins(0,0,0,0)
                
        self.addDock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.RightDockWidgetArea, self.addDock)
        self.addDock.installEventFilter(self)        


    def show_Dock(self):
        self.addDock.show()
        self.debug_act.setEnabled(False)

        
    def eventFilter(self, source, event):
        if (event.type() == QEvent.Close and \
            isinstance(source, QDockWidget)):
            #print(source.windowTitle())
            #print(source.objectName())
            self.debugAct.setEnabled(True)
            
            
        return super().eventFilter(source, event)

    
        
        
    # -----------------------------------------------------------------
    # メニュー関連
    # -----------------------------------------------------------------
    def setup_MenuBar(self):

        # ファイルメニュー
        self.fileMenu = self.menuBar().addMenu('ファイル')

        self.newFileAct = QAction('新規作成', self,
                                         #shortcut="Ctrl+Q",
                                         statusTip='新規作成',
                                         triggered=self.new_file)        
        self.newFileAct.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        self.fileMenu.addAction(self.newFileAct)

        self.openFileAct = QAction('開く...', self,
                                         #shortcut="Ctrl+Q",
                                         statusTip='開く...',
                                         triggered=self.open_file)
        self.openFileAct.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))

        self.fileMenu.addAction(self.openFileAct)

        self.saveFileAct = QAction('上書き保存', self,
                                         #shortcut="Ctrl+Q",
                                         statusTip='上書き保存',
                                         triggered=self.save_file)        
        self.saveFileAct.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.saveFileAct.setEnabled(False)
        self.fileMenu.addAction(self.saveFileAct)

        self.saveasFileAct = QAction('名前をつけて保存...', self,
                                         #shortcut="Ctrl+Q",
                                         statusTip='名前をつけて保存...',
                                         triggered=self.saveas_file)        
        self.fileMenu.addAction(self.saveasFileAct)
        
        

        self.fileMenu.addSeparator()
        
        self.exitAct = QAction('終了する', self,
                                         #shortcut="Ctrl+Q",
                                         statusTip='終了する',
                                         triggered=self.close)        
        self.exitAct.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        self.fileMenu.addAction(self.exitAct)

        
        # ツールメニュー
        self.toolMenu = self.menuBar().addMenu('ツール')

        self.startProgramAct = QAction('プログラムの実行', self,
                                         statusTip='プログラムの実行',
                                         triggered=self.run_program)        
        self.startProgramAct.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.toolMenu.addAction(self.startProgramAct)


        self.stopProgramAct = QAction('プログラムの強制停止', self,
                                         statusTip='プログラムの強制停止',
                                         triggered=self.stop_program)        
        self.stopProgramAct.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.toolMenu.addAction(self.stopProgramAct)
        self.stopProgramAct.setEnabled(False)
        

        self.selectFontAct = QAction('フォントの選択', self,
                                         statusTip='フォントの選択',
                                         triggered=self.select_font)        
        self.toolMenu.addAction(self.selectFontAct)
        
        self.debugAct = QAction('デバッグの表示', self,
                                         statusTip='デバッグ',
                                         triggered=self.show_Dock)        
        self.toolMenu.addAction(self.debugAct)
        self.debugAct.setEnabled(False)
        
        
        # ヘルプメニュー
        self.helpMenu = self.menuBar().addMenu('ヘルプ')

        self.reset_config_act = QAction('配置設定の初期化', self,
                                      statusTip='配置設定の初期化',
                                      triggered=self.reset_config)
        self.helpMenu.addAction(self.reset_config_act)

        
        self.aboutAct = QAction('使い方', self, statusTip='使い方',
                                triggered=self.about)
        self.helpMenu.addAction(self.aboutAct)
        


    def maybeSave(self):
        if not self.centralWidget.editor.document().isModified():
            return True

        #if self.fname.startswith(':/'):
        #    return True

        ret = QMessageBox.warning(self, "Message",
                "プログラムは編集中です。\n" \
                + "保存しますか？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        
        if ret == QMessageBox.Yes:
            if self.fname_with_path == "":
                self.saveas_file()
                return False
            else:
                self.save_file()
                return True
        
        if ret == QMessageBox.Cancel:
            return False
        
        return True   



    def new_file(self):
        if self.maybeSave():
            self.centralWidget.editor.clear()
            self.centralWidget.editor.setPlainText("")
            
            self.fname = ""
            self.fname_with_path = ""
            
            self.centralWidget.editor.document().setModified(False)
            
            self.setWindowModified(False)
            self.saveFileButton.setEnabled(False)
            self.saveFileAct.setEnabled(False)
            
            self.stopDebugButton.click()
            #self.centralWidget.editor.moveCursor(self.cursor.End)
        

    
    def open_file(self, path=None):
        if self.maybeSave():
            if not path:
                current_dir = QDir.currentPath()
                path, _ = QFileDialog.getOpenFileName(self,
                                                  "Open File",
                                                  current_dir,
                    "Text Files (*.while *.txt);;All Files (*.*)")

            if path:
                inFile = QFile(path)
                if inFile.open(QFile.ReadWrite | QFile.Text):
                    text = inFile.readAll()
                    try:
                        text = str(text, encoding = 'utf8')
                    except:
                        return
                    
                    self.centralWidget.editor.setPlainText(text)
                    
                    self.centralWidget.editor.document().setModified(False)
                    self.setWindowModified(False)
                    self.saveFileButton.setEnabled(False)
                    self.saveFileAct.setEnabled(False)
                    
                    self.fname_with_path = path
                    self.fname = QFileInfo(path).fileName()                
                    self.set_window_title(self.fname_with_path)

                    # デバッグモードは終了しておく
                    self.stop_debug()
                    

                    
    def save_file(self):
        if self.fname_with_path != "":
            file = QFile(self.fname_with_path)
            
            if not file.open( QFile.WriteOnly | QFile.Text):
                QMessageBox.warning(self, "Error",
                        "ファイル %s に書き込めませんでした:\n%s." \
                        % (self.fname_with_path, file.errorString()))
                return

            # ファイル保存
            outstr = QTextStream(file)
            QApplication.setOverrideCursor(Qt.WaitCursor)
            outstr << self.centralWidget.editor.toPlainText()
            QApplication.restoreOverrideCursor()
            
            self.centralWidget.editor.document().setModified(False)
            self.setWindowModified(False)
            self.saveFileButton.setEnabled(False)
            self.saveFileAct.setEnabled(False)
            
            self.fname = QFileInfo(self.fname).fileName() 
            self.set_window_title(self.fname_with_path)

        else:
            self.saveas_file()


    def saveas_file(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save as...",
                                            self.fname,
                                            "WHILE program files (*.while)")

        if not fname:
            print("エラー：保存できませんでした。")
            return False

        lfname = fname.lower()
        if not lfname.endswith('.while'):
            fname += '.while'

            
        self.fname_with_path = fname
        _, self.fname = os.path.split(str(fname))


        return self.save_file()

    
        
    def about(self):
        QMessageBox.about(self, "このソフトウェアについて",
            "ソフトウェアの使い方については、同梱されている「README」などを参照してください。")

    def reset_config(self):
        reply = QMessageBox.question(self, 'UI 配置の初期化', 
                                     'UI 配置情報の設定ファイルを削除しますか？',
                                     QMessageBox.Yes, QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            self.resetConfigFlag = False
            os.remove(CONFIG_FILE)
            QMessageBox.about(self, "設定ファイルの削除",
            "UI 配置情報の設定ファイルを削除しました。アプリを再起動すると、UI の配置が初期化されます")
            
            
            

    # -----------------------------------------------------------------
    # ツールバー関連
    # -----------------------------------------------------------------
    def setup_ToolBar(self):
        toolBar = QToolBar()
        toolBar.setStyleSheet("QToolBar{spacing:10px; padding: 5px; border:0px}")
        toolBar.setObjectName("toolbar")        
        
        
        self.addToolBar(toolBar)
        
        # newfile
        self.newFileButton = QToolButton()
        self.newFileButton.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        self.newFileButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.newFileButton.clicked.connect(self.new_file)
        toolBar.addWidget(self.newFileButton)        

        
        # openfile
        self.openFileButton = QToolButton()
        self.openFileButton.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.openFileButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.openFileButton.clicked.connect(self.open_file)
        toolBar.addWidget(self.openFileButton)        

        
        # savefile
        self.saveFileButton = QToolButton()
        self.saveFileButton.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.saveFileButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.saveFileButton.clicked.connect(self.save_file)
        self.saveFileButton.setEnabled(False)
        toolBar.addWidget(self.saveFileButton)        
        


        toolBar2 = QToolBar()
        toolBar2.setStyleSheet("QToolBar{spacing:10px; padding: 5px; border:0px}")
        toolBar2.setObjectName("toolbar2")        
        self.addToolBar(toolBar2)
        
        # run program
        self.startButton = QToolButton()
        self.startButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.startButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.startButton.clicked.connect(self.run_program)
        toolBar2.addWidget(self.startButton)        

        # stop program
        self.stopButton = QToolButton()
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopButton.clicked.connect(self.stop_program)
        self.stopButton.setEnabled(False)
        self.stopProgramAct.setEnabled(False)
        toolBar2.addWidget(self.stopButton)        


        

    # -----------------------------------------------------------------
    # スロット
    # -----------------------------------------------------------------
    def stop_debug(self):
        self.stopDebugButton.setEnabled(False)
        self.startDebugButton.setEnabled(True)
        self.onestepDebugButton.setEnabled(False)

        self.enable_startButton()
        
        self.centralWidget.set_ReadOnly(False)
        self.centralWidget.clear_HighlightLine()
        self.tableView.set_data({})

        
        if self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()
            self.thread.stop()
            
        
        
    def set_program(self):
        textboxValue = self.centralWidget.get_program()        
        first_executable_lineno = self.thread.setup(textboxValue)
        
        if self.thread.evaluatorInfo['noerror']:
            self.tableView.set_data({})
            self.centralWidget.clear_messages()
            
            self.startDebugButton.setEnabled(False)
            self.stopDebugButton.setEnabled(True)
            self.onestepDebugButton.setEnabled(True)

            self.startButton.setEnabled(False)
            self.startProgramAct.setEnabled(True)
            
            self.centralWidget.set_HighlightLine(first_executable_lineno)
            self.centralWidget.set_ReadOnly(True)

            self.history.set_firstGeneration({'env':{},
                                              'lineno':first_executable_lineno})
            
            # oneStep 実行を有効化
            self.thread.oneStep = True


    def rewind_program(self):

        self.onestepDebugButton.setEnabled(True)
                
        self.history.change_generation_previous()
        
        current = self.history.get_elem()
        self.centralWidget.set_HighlightLine(current['lineno'])
        
        if self.history.is_theFirstGeneration():

            # self.history.init_generation()
            self.tableView.set_data({})
            self.rewindDebugButton.setEnabled(False)
            
            
        else:
            previous = self.history.get_elem_previous()
            self.tableView.set_data(current['env'], previous['env'])

    

    def run_program_onestep(self):
        
        if self.history.is_theLatestGeneration():
            self.startDebugButton.setEnabled(False)
            self.rewindDebugButton.setEnabled(True)
            self.thread.start()

        else:
            self.history.change_generation_next()
            current = self.history.get_elem()
            self.tableView.set_data(current['env'])
            
            self.centralWidget.set_HighlightLine(current['lineno'])
            
            if self.history.is_theLatestGeneration():
                if current['lineno'] == 0:
                
                    # 最終世代だったら 
                    self.onestepDebugButton.setEnabled(False)
                    self.rewindDebugButton.setEnabled(True)
            
                else:                    
                    self.onestepDebugButton.setEnabled(True)
                    self.rewindDebugButton.setEnabled(True)
        
            


        
    def run_program(self):
        self.centralWidget.clear_messages()
        
        program = self.centralWidget.get_program()
        self.thread.setup(program)
        
        if self.thread.evaluatorInfo['noerror']:
            self.stop_debug()

            self.centralWidget.set_ReadOnly(False)

            self.disable_startButton()
            self.onestepDebugButton.setEnabled(False)

            self.centralWidget.clear_HighlightLine()

            self.thread.oneStep = False
            self.thread.start()




        
    def stop_program(self):
        # sys.exit()
        # QCoreApplication.processEvents()
        
        self.thread.terminate()
        self.thread.wait()
        self.thread.stop()
        self.centralWidget.add_messages("強制終了されました");
                


    def eval_finished(self):

        evaluatorInfo = self.thread.evaluatorInfo
        try:
            self.tableView.set_data(evaluatorInfo['env'])
            
        except:
            self.tableView.set_data({})

            
        if self.thread.oneStep == False:
            # 通常実行
            self.enable_startButton()

        else:
            # oneStep 実行

            # history に追加
            self.history.set_elem({'env':copy.deepcopy(evaluatorInfo['env']),
                                   'lineno':evaluatorInfo['lineno']})


            
            if evaluatorInfo['empty']:
                # もう実行するものがない場合

                #self.startDebugButton.setEnabled(True)
                self.onestepDebugButton.setEnabled(False)
                #self.stopDebugButton.setEnabled(False)

                #self.centralWidget.set_ReadOnly(False)
                self.centralWidget.clear_HighlightLine()
                QMessageBox.information(self,
                                        "プログラム実行の終了",
                                        "すべてのプログラムが実行されました。",
                                        QMessageBox.Ok)

            else:
                # self.startDebugButton.setEnabled(True)
                self.centralWidget.set_HighlightLine(evaluatorInfo['lineno'])
            
            
        
        
    # -----------------------------------------------------------------
    # スタートボタンの依存関連
    # -----------------------------------------------------------------
    def enable_startButton(self):
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)

        self.startProgramAct.setEnabled(True)
        self.stopProgramAct.setEnabled(False)
                
        self.centralWidget.set_ReadOnly(False)
        self.centralWidget.editor.highlightCurrentLine()
        

    def disable_startButton(self):
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)

        self.startProgramAct.setEnabled(False)
        self.stopProgramAct.setEnabled(True)
        
        self.centralWidget.set_ReadOnly(True)



    # -----------------------------------------------------------------
    # キー入力時のショートカット
    # -----------------------------------------------------------------        
    def keyPressEvent(self, event):
        # print('keyPressEvent, key = %s.' % event.key())

        # Ctrl と Enter の同時押し
        if event.modifiers() & Qt.ControlModifier and \
           event.key() == Qt.Key_Return:
            self.startButton.click()
                        
        else:
            # 自分が処理しない場合は、オーバーライド元の処理を実行
            super().keyPressEvent(event)


    # -----------------------------------------------------------------
    # modified が変更されたときの処理
    # -----------------------------------------------------------------        
    def modified_event(self, flag):
        self.setWindowModified(flag)
        self.saveFileButton.setEnabled(True)
        self.saveFileAct.setEnabled(True)


            

    # -----------------------------------------------------------------
    # Setting 処理
    # -----------------------------------------------------------------        
    def closeEvent(self, e):
        if self.maybeSave():
            e.accept()
            self.saveSettings()
            
        else:
            e.ignore()
        


    def initSettings(self):
        # Window Size
        # self.setFixedSize(750, 700)
        self.resize(800, 600)

        # font
        c = self.centralWidget.editor.textCursor()
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
        self.centralWidget.splitter.restoreState(setting.value(self.centralWidget.splitter.objectName()))

        # GUIの位置を復帰
        self.restoreGeometry(setting.value("geometry"))
        self.restoreState(setting.value("windowState"))
        
        # Font
        try:
            font_family = setting.value("font_family")
            font_size = int(setting.value("font_size"))
            font_weight = int(setting.value("font_weight"))
                        
            font = QFont(font_family, font_size, font_weight)
            self.update_font(font)
        except:
            pass
        
        # tableview の第1列の幅
        width = setting.value("tableview_column_width")
        self.tableView.set_HeaddaColumnWidth(int(width))
        
                
    def saveSettings(self):
        if self.resetConfigFlag == False:
            return

        
        setting = QSettings(CONFIG_FILE, QSettings.IniFormat)

        # Splitterの位置
        setting.setValue(self.centralWidget.splitter.objectName(),
                         self.centralWidget.splitter.saveState())
        
        # UIの位置
        setting.setValue("geometry", self.saveGeometry())
        setting.setValue("windowState", self.saveState())

        # font 情報（QTextEdit からの取得はうまくできなかった）
        c = self.centralWidget.editor.textCursor()
        current_font = c.charFormat().font()

        font_family = current_font.family()
        font_size = current_font.pointSize()
        font_weight = current_font.weight()
        setting.setValue("font_family", font_family)
        setting.setValue("font_size", font_size)
        setting.setValue("font_weight", font_weight)

        # tableview の第1列の幅
        width = self.tableView.get_HeaddaColumnWidth()
        setting.setValue("tableview_column_width", width)

        
        #program = self.centralWidget.get_program()
        #setting.setValue("program", program)

        
        
    def update_font(self, font):
        self.centralWidget.editor.setFont(font)
        self.centralWidget.messageArea.setFont(font)
        self.tableView.set_font(font)

        

    def select_font(self):
        # QPlainTextEdit から取得する場合
        c = self.centralWidget.editor.textCursor()
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

    mainwindow.focusWidget.setFocus()
 
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()




