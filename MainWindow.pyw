# -*- coding:utf-8 -*-
# -----------------------------------------------------------------------------
# MainWindow.pyw
#
# The main window for an interpreter of while programs.
# 16 June 2021.
#
# Copyright (c) 2021 Shinya Sato
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php
# -----------------------------------------------------------------------------

import sys
import os
import copy
import re

from PySide2.QtCore import (Qt, QSize, 
                            QSettings, QEvent, QDir, QFile, QFileInfo,
                            QTextStream)
from PySide2.QtGui import QFont, QIcon, QColor, QTextCursor
from PySide2.QtWidgets import (QWidget, QPushButton, 
                               QTextEdit, QGridLayout, QVBoxLayout, QHBoxLayout,
                               QSplitter,
                               QMainWindow, QStatusBar,
                               QAction, QFontDialog, QMessageBox,
                               QApplication, QToolBar, QToolButton,
                               QDockWidget, QStyle, QFrame, QFileDialog,
                               QLineEdit, QLabel, QSpacerItem, QSizePolicy)

from src.QCodeEditor import QCodeEditor
from src.EnvViewer import EnvViewer
from src.PresetEnv import PresetEnv
from src.MyThread import MyThread
from src.FindWidget import FindWidget

CONFIG_FILE = 'config.ini'


import PySide2
dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path



class History:
    def __init__(self):

        self.history = []

        
    def set_elem(self, elem):
        self.history.append(elem)
        

    def set_elem_as_the1st(self, elem):
        self.history = []
        self.set_elem(copy.deepcopy(elem))

        
    def get_elem(self, relative=0):
        length = len(self.history)
        try:
            retval = self.history[length - 1 + relative]
        except:
            retval = {}
            
        return retval

    def get_at(self, num):
        try:
            return self.history[num]
        except:
            return {}

            
    
            
    def can_rewind(self):
        if len(self.history) > 1:
            return True
        else:
            return False
                
    def discard_thelatest(self):
        self.history.pop()
        
        
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

        self.scrollbar_style = '''
        QScrollBar:vertical{
         background: white;
         width: 15px;
         height: 50px;
         }
        QScrollBar::handle:vertical{
         background: lightgray;
         min-height: 100;
        }
        QScrollBar::handle:vertical:hover{
         background: gray;
        }
        '''
        
        self.editor = QCodeEditor()        
        self.editor.setUndoRedoEnabled(True)
        self.editor.setStyleSheet('border:0px')
        self.editor.verticalScrollBar().setStyleSheet(self.scrollbar_style)
        
        
        # 実行結果の表示用
        #self.messageArea = QTextBrowser()
        self.messageArea = QTextEdit()
        self.messageArea.setReadOnly(True)
        self.messageArea.setUndoRedoEnabled(False)
        self.messageArea.setStyleSheet("background-color: #e0e0e0;border:0px")
        self.messageArea.verticalScrollBar().setStyleSheet(self.scrollbar_style)

        rowHeight = self.fontMetrics().lineSpacing()
        self.messageArea.setMinimumHeight(rowHeight * 1)

        self.messageArea.setObjectName("messageArea")
        

        # 検索用
        self.findField = FindWidget(self.editor,
                                    self.editor.set_find_word,
                                    self.editor.replace_word)
        self.editor.myclicked.connect(self.findField.suspend)
        self.findField.setVisible(False)
        
        
        # メイン画面に部品を配置する
        layout = QGridLayout()
        layout.setSpacing(0)
        #layout.setContentsMargins(5,0,5,5 )
        layout.setContentsMargins(0,0,0,0)

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.splitter.setObjectName("splitter")        
        self.splitter.setHandleWidth(1)

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.messageArea)
        self.splitter.setStretchFactor(0,3)
        self.splitter.setStretchFactor(1,1)
        self.splitter.setChildrenCollapsible(False)

        layout.addWidget(self.findField)
        layout.addWidget(self.splitter)
        
        self.setLayout(layout)
        
       
    # public methods
    def add_messages(self, mes, error=False):
        cursor = self.messageArea.textCursor()

        escaped = mes.replace("&","&amp;").replace(">","&gt;").replace("<","&lt;")
        
        if error:
            cursor.insertHtml('<font color="#cc3333">%s</font>' % escaped)
            
        else:
            cursor.insertHtml('<font color="black">%s</font>' % escaped)

        cursor.insertText("\n")


    def clear_messages(self):
        self.messageArea.clear()
        

    def get_program(self):
        return self.editor.toPlainText()

    
    def set_HighlightLine(self, lineno, trail=True):
        self.editor.setHighlightLineno(lineno, trail)
        #self.editor.highlightLine()
        
        
    def clear_HighlightLine(self):
        self.editor.clearHighlightLine()

    def set_ReadOnly(self, flag):
        self.editor.setReadOnly(flag)
        #if flag:
        #    self.editor.setExtraSelections([])
            
    def set_tabStop(self, tabStop):
        self.editor.tabStop = tabStop



#---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent=parent)

        # Status Bar
        #self.statusBar = QStatusBar(self)
        #self.setStatusBar(self.statusBar)
        #self.statusBar.showMessage('')

        self.setAcceptDrops(True)

        # ファイル名
        self.fname = "無題"
        self.fname_with_path = ""
        
        # タイトル        
        self.title = 'WHILE Program Interpreter'
        self.set_window_title(self.fname_with_path)

        # Central Widget
        self.centralWidget = CentralWidget(parent=parent)
        self.setCentralWidget(self.centralWidget)
        self.centralWidget.editor.document().modificationChanged.connect(self.modified_event)


        self.centralWidget.messageArea.viewport().installEventFilter(self)
        self.centralWidget.messageArea.installEventFilter(self)

        
        self.scrollbar_style = '''
        QScrollBar:vertical{
         background: white;
         width: 12px;
         height: 50px;
         }
        QScrollBar::handle:vertical{
         background: lightgray;
         min-height: 100;
        }
        QScrollBar::handle:vertical:hover{
         background: gray;
        }
        '''


        
        # Menu Bar
        self.setup_MenuBar()

        # ツールバー
        self.setup_ToolBar()

        # ドック
        self.setup_Dock()
        self.setup_Dock_preset()

        #self.presetDock.sizeHint()
        #self.presetDock.adjustSize()
        #self.presetDock.resize(self.presetDock.minimumSizeHint())

        
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


        # 閉じるときに設定を保存する
        self.resetConfigFlag = True

        # Env の History
        self.history = History()

        

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
    def setup_Dock_preset(self):
        self.presetEnv = PresetEnv()
        self.presetEnv.selectionModel.selectionChanged.connect(self.enable_removeItemButton)

        # ボタン群レイアウト
        #layout = QGridLayout()
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)

        font = self.font()
        font.setPointSize(12)
        font.setBold(True)
        
        self.addItemButton = QPushButton("+")
        self.addItemButton.clicked.connect(self.presetEnv.newItem)
        self.addItemButton.setCheckable(False)  
        self.addItemButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.addItemButton.setStyleSheet("QPushButton {margin:0; padding: 3px 10px 3px 10px;}")
        self.addItemButton.setFont(font)
        
        self.removeItemButton = QPushButton("-")
        self.removeItemButton.clicked.connect(self.presetEnv.removeItems)
        self.removeItemButton.setCheckable(False)  
        self.removeItemButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.removeItemButton.setStyleSheet("QPushButton {margin:0; padding: 3px 10px 3px 10px;}")
        self.removeItemButton.setFont(font)
        self.removeItemButton.setEnabled(False)

        
        layout.addWidget(self.addItemButton)
        layout.addWidget(self.removeItemButton)
        layout.addStretch()

        buttonsWidget = QWidget()
        buttonsWidget.setLayout(layout)
        buttonsWidget.setContentsMargins(0,0,0,0)
        
        # layoutV に、ボタン群 widget と self.tableView を縦方向に追加
        layoutV = QVBoxLayout()
        layoutV.setSpacing(0)
        layoutV.setContentsMargins(0,0,0,0)
        layoutV.addWidget(buttonsWidget)        
        layoutV.addWidget(self.presetEnv)
        
        presetWidget = QWidget()
        presetWidget.setLayout(layoutV)
        presetWidget.setContentsMargins(0,0,0,0)

        # Dock の作成
        self.presetDock = QDockWidget('変数の初期値', self)        
        self.presetDock.setObjectName("preset-dock")        
        self.presetDock.setWidget(presetWidget)        
        self.presetDock.setContentsMargins(0,0,0,0)

        rowHeight = self.fontMetrics().lineSpacing()
        #self.presetDock.setMaximumHeight(rowHeight * 15)
        self.presetDock.setMinimumHeight(rowHeight * 10)
        
        
        self.presetDock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.RightDockWidgetArea, self.presetDock)

        # https://forum.qt.io/topic/94473/qdockwidget-resize-issue/16
        # なぜかこれで最小サイズになる（最後のメッセージ欄を参照）
        self.resizeDocks([self.presetDock], [1], Qt.Vertical)

        self.presetDock.installEventFilter(self)        

        

    def enable_removeItemButton(self, selected, deselected):
        if len(selected) > 0:
            self.removeItemButton.setEnabled(True)
        else:
            self.removeItemButton.setEnabled(False)
        
        
    def setup_Dock(self):
        # 環境表示用
        self.envViewer = EnvViewer()
        #self.envViewer.tableWidget.verticalScrollBar().setStyleSheet(self.scrollbar_style)
        self.envViewer.vertical_scrollbar_setStyleSheet(self.scrollbar_style)

        # ボタン群レイアウト
        #layout = QGridLayout()
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        
        self.startDebugButton = QPushButton()
        self.startDebugButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.startDebugButton.clicked.connect(self.prepare_debug_mode)
        self.startDebugButton.setCheckable(False)  
        self.startDebugButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.startDebugButton.setStyleSheet("QPushButton {margin:0; padding: 3px 15px 3px 15px;}")

        
        self.stopDebugButton = QPushButton()
        self.stopDebugButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopDebugButton.setEnabled(False)
        self.stopDebugButton.setCheckable(False)  
        self.stopDebugButton.clicked.connect(self.stop_debug)
        self.stopDebugButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.stopDebugButton.setStyleSheet("QPushButton {margin:0; padding: 3px 15px 3px 15px;}")

        
        self.rewindDebugButton = QPushButton()
        self.rewindDebugButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.rewindDebugButton.clicked.connect(self.rewind_program)
        self.rewindDebugButton.setEnabled(False)
        self.rewindDebugButton.setCheckable(False)  
        self.rewindDebugButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.rewindDebugButton.setStyleSheet("QPushButton {margin:0; padding: 3px 15px 3px 15px;}")
        
        self.onestepDebugButton = QPushButton()
        self.onestepDebugButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.onestepDebugButton.clicked.connect(self.run_program_onestep)
        self.onestepDebugButton.setEnabled(False)
        self.onestepDebugButton.setCheckable(False)  
        self.onestepDebugButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.onestepDebugButton.setStyleSheet("QPushButton {margin:0; padding: 3px 15px 3px 15px;}")


        line = QFrame(self)
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Plain)
 
        """
        layout.addWidget(self.startDebugButton,0,0)
        layout.addWidget(self.stopDebugButton,0,1)
        layout.addWidget(line,0,2)        
        layout.addWidget(self.rewindDebugButton,0,3)
        layout.addWidget(self.onestepDebugButton,0,4)
        """
        layout.addWidget(self.startDebugButton)
        layout.addWidget(self.stopDebugButton)
        layout.addWidget(line)
        layout.addWidget(self.rewindDebugButton)
        layout.addWidget(self.onestepDebugButton)
        layout.addStretch()
        
        # ボタン群レイアウト layout を widget として扱えるようにする
        buttonsWidget = QWidget()
        buttonsWidget.setLayout(layout)
        buttonsWidget.setContentsMargins(0,0,0,0)


        # layoutV に、ボタン群 widget と self.envViewer を縦方向に追加
        layoutV = QVBoxLayout()
        layoutV.setSpacing(0)
        layoutV.setContentsMargins(0,0,0,0)
        layoutV.addWidget(buttonsWidget)        
        layoutV.addWidget(self.envViewer)
        
        debugWidget = QWidget()
        debugWidget.setLayout(layoutV)
        debugWidget.setContentsMargins(0,0,0,0)
        

        # Dock の作成
        self.debugDock = QDockWidget('デバッグ', self)        
        self.debugDock.setObjectName("dock")        
        self.debugDock.setWidget(debugWidget)
        self.debugDock.setContentsMargins(0,0,0,0)
                
        self.debugDock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.RightDockWidgetArea, self.debugDock)

        # Dock が閉じた時の処理用に eventFilter 関数を使う
        self.debugDock.installEventFilter(self)        



    def show_Dock(self):
        """
        if self.debugDockAct.isChecked():
            self.debugDock.show()
        else:
            self.debugDock.hide()
        """
        self.debugDock.setVisible(self.debugDockAct.isChecked())

    def show_presetDock(self):
        self.presetDock.setVisible(self.presetDockAct.isChecked())
        
        
    def eventFilter(self, source, event):
        if (event.type() == QEvent.Close and \
            isinstance(source, QDockWidget)):
            # Dock が閉じた時の処理
            
            #print(source.windowTitle())
            #print(source.objectName())
            if source.objectName() == self.debugDock.objectName():
                self.debugDockAct.setChecked(False)
            elif source.objectName() == self.presetDock.objectName():
                self.presetDockAct.setChecked(False)

        elif event.type() == QEvent.MouseButtonRelease and \
             source == self.centralWidget.messageArea.viewport():

            cursor = self.centralWidget.messageArea.textCursor()
            cursor.clearSelection()
            block_text = cursor.block().text()
            line_match = re.search('^(\d+)行目', block_text)
            if line_match:
                lineno = int(line_match.group(1))
                #cursor = self.editor.textCursor()
                #cursor.movePosition(QTextCursor.Start)
                cursor = QTextCursor(self.centralWidget.editor.document().findBlockByNumber(lineno - 1))
                self.centralWidget.editor.setTextCursor(cursor)
                self.centralWidget.editor.setFocus()
                

                
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

        
        self.fileMenu.addSeparator()

        
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
        
        subFileMenu = self.fileMenu.addMenu('設定')

        self.reset_config_act = QAction('配置設定の初期化...', self,
                                      statusTip='配置設定の初期化',
                                      triggered=self.reset_config)
        subFileMenu.addAction(self.reset_config_act)


        
        self.fileMenu.addSeparator()
        
        self.exitAct = QAction('終了する', self,
                                         #shortcut="Ctrl+Q",
                                         statusTip='終了する',
                                         triggered=self.close)        
        self.exitAct.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        self.fileMenu.addAction(self.exitAct)


        # 編集メニュー
        self.editMenu = self.menuBar().addMenu('編集')



        self.undoAction = QAction("元に戻す",self,
                                 shortcut="Ctrl+Z",
                                 statusTip="編集作業を一つ戻します",
                                 triggered=self.centralWidget.editor.undo)
        self.undoAction.setEnabled(False)
        self.centralWidget.editor.undoAvailable.connect(self.undoAction.setEnabled)
        self.editMenu.addAction(self.undoAction)


        self.redoAction = QAction("やり直し",self,
                                 shortcut="Ctrl+Y",
                                 statusTip="Undo された編集作業を一つ戻します",
                                 triggered=self.centralWidget.editor.redo)
        self.redoAction.setEnabled(False)
        self.centralWidget.editor.redoAvailable.connect(self.redoAction.setEnabled)
        self.editMenu.addAction(self.redoAction)

        # ---
        self.editMenu.addSeparator()
        # ---

        self.cutAction = QAction("切り取り",self,
                                 shortcut="Ctrl+X",
                                 statusTip="選択領域を削除してクリップボードへ貼り付けます",
                                 triggered=self.centralWidget.editor.cut)
        self.editMenu.addAction(self.cutAction)

        self.copyAction = QAction("コピー",self,
                                  shortcut="Ctrl+C",
                                  statusTip="選択領域をクリップボードへ貼り付けます",
                                  triggered=self.centralWidget.editor.copy)
        self.editMenu.addAction(self.copyAction)

        self.pasteAction = QAction("貼り付け",self,
                                   shortcut="Ctrl+V",
                                   statusTip="クリップボードから貼り付けます",
                                   triggered=self.centralWidget.editor.paste)
        self.editMenu.addAction(self.pasteAction)
        
        # ---
        self.editMenu.addSeparator()
        # ---

        self.selectAllAction = QAction("すべて選択",self,
                                       shortcut="Ctrl+A",
                                       statusTip="すべての行を選択します",
                                       triggered=self.centralWidget.editor.selectAll)
        self.editMenu.addAction(self.selectAllAction)

        
        # ---
        self.editMenu.addSeparator()
        # ---

        self.findAction = QAction("検索",self,
                                  shortcut="Ctrl+F",
                                  statusTip="検索",
                                  triggered=lambda :self.centralWidget.findField.open(mode="find"))
        self.editMenu.addAction(self.findAction)

        self.replaceAction = QAction("置換",self,
                                  shortcut="Ctrl+H",
                                  statusTip="置換",
                                  triggered=lambda :self.centralWidget.findField.open(mode="replace"))
        self.editMenu.addAction(self.replaceAction)

        
        
        """
    self.copyAction = QtGui.QAction(QtGui.QIcon("icons/copy.png"),"Copy to clipboard",self)
    self.copyAction.setStatusTip("Copy text to clipboard")
    self.copyAction.setShortcut("Ctrl+C")
    self.copyAction.triggered.connect(self.text.copy)
     
    self.pasteAction = QtGui.QAction(QtGui.QIcon("icons/paste.png"),"Paste from clipboard",self)
    self.pasteAction.setStatusTip("Paste text from clipboard")
    self.pasteAction.setShortcut("Ctrl+V")
    self.pasteAction.triggered.connect(self.text.paste)
     
    self.undoAction = QtGui.QAction(QtGui.QIcon("icons/undo.png"),"Undo last action",self)
    self.undoAction.setStatusTip("Undo last action")
    self.undoAction.setShortcut("Ctrl+Z")
    self.undoAction.triggered.connect(self.text.undo)
     
    self.redoAction = QtGui.QAction(QtGui.QIcon("icons/redo.png"),"Redo last undone thing",self)
    self.redoAction.setStatusTip("Redo last undone thing")
    self.redoAction.setShortcut("Ctrl+Y")
    self.redoAction.triggered.connect(self.text.redo)
        """





        


        
        # 表示メニュー
        self.visualMenu = self.menuBar().addMenu('表示')

        self.toolBarVisibleAct = QAction('ツールバー', self,
                                         statusTip='ツールバーの表示',
                                         triggered=self.toggle_toolBar)        
        self.toolBarVisibleAct.setObjectName("toolbar_enabled")        
        self.toolBarVisibleAct.setCheckable(True)
        self.toolBarVisibleAct.setChecked(True)
        self.visualMenu.addAction(self.toolBarVisibleAct)

        self.visualMenu.addSeparator()

        subDebugMenu = self.visualMenu.addMenu('デバッグ')
        
        self.debugDockAct = QAction('ドッグの表示', self,
                                         statusTip='ドッグの表示',
                                         triggered=self.show_Dock)        
        self.debugDockAct.setObjectName("debugDock_enabled")        
        self.debugDockAct.setCheckable(True)
        self.debugDockAct.setChecked(True)
        subDebugMenu.addAction(self.debugDockAct)
        

        self.debugTrailAct = QAction('軌跡', self,
                                         statusTip='軌跡',
                                         triggered=self.set_debug_trail)
        self.debugTrailAct.setObjectName("debugTrail_enabled")        
        self.debugTrailAct.setCheckable(True)
        self.debugTrailAct.setChecked(True)
        subDebugMenu.addAction(self.debugTrailAct)
        self.debug_tail = True         # animation 用フラグ

        
        self.visualMenu.addSeparator()
        subPresetMenu = self.visualMenu.addMenu('変数の初期値')
        self.presetDockAct = QAction('ドッグの表示', self,
                                         statusTip='ドッグの表示',
                                         triggered=self.show_presetDock)        
        self.presetDockAct.setObjectName("presetDock_enabled")        
        self.presetDockAct.setCheckable(True)
        self.presetDockAct.setChecked(True)
        subPresetMenu.addAction(self.presetDockAct)
        
        self.visualMenu.addSeparator()
        

        self.selectFontAct = QAction('フォントの選択...', self,
                                         statusTip='フォントの選択',
                                         triggered=self.select_font)        
        self.visualMenu.addAction(self.selectFontAct)
        
        
        
        
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
        

        

        
        # ヘルプメニュー
        self.helpMenu = self.menuBar().addMenu('ヘルプ')


        
        self.aboutAct = QAction('使い方', self, statusTip='使い方',
                                triggered=self.about)
        self.helpMenu.addAction(self.aboutAct)


    def toggle_toolBar(self):
        toolbar = [self.toolBar, self.toolBar2]
        for tb in toolbar:
            tb.setVisible(self.toolBarVisibleAct.isChecked())
            

        
    def set_debug_trail(self):
        self.debug_trail = self.debugTrailAct.isChecked()
    
        

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
            self.set_window_title(self.fname_with_path)

            self.centralWidget.editor.document().setModified(False)
            
            self.setWindowModified(False)
            self.saveFileButton.setEnabled(False)
            self.saveFileAct.setEnabled(False)
            
            self.stopDebugButton.click()
            #self.centralWidget.editor.moveCursor(self.cursor.End)
        
            # デバッグの tableView と実行結果をクリア
            self.envViewer.clear_data()
            self.centralWidget.clear_messages()

            # 検索フィールドを閉じておく
            self.centralWidget.findField.close()

            
    
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
                        
                    except Exception as e:
                        QMessageBox.critical(self, "Error",
                                             "開けませんでした。\n" + str(e))
                        
                        return
                    
                    # エディタにプログラムソースをセットする
                    #self.centralWidget.editor.setPlainText(text)
                    self.centralWidget.editor.setPlainText("")
                    self.centralWidget.editor.insert_as_codes(text)
                    
                    self.fname_with_path = path
                    self.fname = QFileInfo(path).fileName()                
                    self.set_window_title(self.fname_with_path)

                    # 検索フィールドを閉じておく
                    self.centralWidget.findField.close()

                    # デバッグモードは終了しておく
                    self.stop_debug()

                    # デバッグの tableView と実行結果をクリア
                    self.envViewer.clear_data()
                    self.centralWidget.clear_messages()
                    
                    # 変更あり情報（modified）をクリア
                    self.centralWidget.editor.document().setModified(False)
                    self.setWindowModified(False)
                    self.saveFileButton.setEnabled(False)
                    self.saveFileAct.setEnabled(False)
                    
                    
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
            outstr.setCodec("UTF-8")
            
            QApplication.setOverrideCursor(Qt.WaitCursor)
            outstr << self.centralWidget.editor.toPlainText().replace(u'\u301c', u'\uff5e')
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
                                     '設定ファイルを削除することになります。'
                                     +'\n続けても良いでしょうか？',
                                     QMessageBox.Yes, QMessageBox.Cancel)

        if reply == QMessageBox.Yes:
            self.resetConfigFlag = False
            os.remove(CONFIG_FILE)

            QMessageBox.about(self, "設定ファイルを削除しました",
            "設定ファイルを削除しました。アプリを再起動すると、UI の配置が初期化されます")
            
            
            

    # -----------------------------------------------------------------
    # ツールバー関連
    # -----------------------------------------------------------------
    def setup_ToolBar(self):
        self.toolBar = QToolBar()
        self.toolBar.setStyleSheet("QToolBar{spacing:10px; padding: 5px; border:0px}")
        self.toolBar.setObjectName("toolbar")        
        
        
        self.addToolBar(self.toolBar)
        
        # newfile
        self.newFileButton = QToolButton()
        self.newFileButton.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        self.newFileButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.newFileButton.clicked.connect(self.new_file)
        self.toolBar.addWidget(self.newFileButton)        

        
        # openfile
        self.openFileButton = QToolButton()
        self.openFileButton.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.openFileButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.openFileButton.clicked.connect(self.open_file)
        self.toolBar.addWidget(self.openFileButton)        

        
        # savefile
        self.saveFileButton = QToolButton()
        self.saveFileButton.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.saveFileButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.saveFileButton.clicked.connect(self.save_file)
        self.saveFileButton.setEnabled(False)
        self.toolBar.addWidget(self.saveFileButton)        
        


        self.toolBar2 = QToolBar()
        self.toolBar2.setStyleSheet("QToolBar{spacing:10px; padding: 5px; border:0px}")
        self.toolBar2.setObjectName("toolbar2")        
        self.addToolBar(self.toolBar2)
        
        # run program
        self.startButton = QToolButton()
        self.startButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.startButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.startButton.clicked.connect(self.run_program)
        self.toolBar2.addWidget(self.startButton)        

        # stop program
        self.stopButton = QToolButton()
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopButton.clicked.connect(self.stop_program)
        self.stopButton.setEnabled(False)
        self.stopProgramAct.setEnabled(False)
        self.toolBar2.addWidget(self.stopButton)        


        

    # -----------------------------------------------------------------
    # スロット
    # -----------------------------------------------------------------
    def stop_debug(self):
        self.stopDebugButton.setEnabled(False)
        self.startDebugButton.setEnabled(True)
        self.onestepDebugButton.setEnabled(False)
        
        self.presetEnv.set_ReadOnly(False)
        self.presetEnv.setEnabled(True)
        self.addItemButton.setEnabled(True)
        
        self.enable_startButton()
        
        self.centralWidget.set_ReadOnly(False)
        self.centralWidget.clear_HighlightLine()
        self.envViewer.clear_data()

        self.focusWidget.setFocus()
        
        if self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()
            self.thread.stop()
            
        
        
    def prepare_debug_mode(self):        
        textboxValue = self.centralWidget.get_program()        

        preset_env = self.presetEnv.get_data()
        
        evaluatorInfo = self.thread.setup(textboxValue, preset_env)
        first_executable_lineno = evaluatorInfo['lineno']
        
        if evaluatorInfo['noerror']:
            self.centralWidget.clear_messages()

            # history に追加
            self.history.set_elem_as_the1st(evaluatorInfo)
            self.envViewer.set_data(evaluatorInfo['pretty_env'],
                                    level=len(evaluatorInfo['dump']))

            
            # ボタン連動
            self.startDebugButton.setEnabled(False)
            self.stopDebugButton.setEnabled(True)
            self.onestepDebugButton.setEnabled(True)

            self.startButton.setEnabled(False)
            self.startProgramAct.setEnabled(True)
            
            self.presetEnv.clearSelection()
            self.presetEnv.set_ReadOnly(True)
            self.presetEnv.setEnabled(False)
            self.addItemButton.setEnabled(False)

            # 次に実行する行をハイライト
            self.centralWidget.set_HighlightLine(first_executable_lineno,
                                                 self.debug_trail)
            self.centralWidget.set_ReadOnly(True)
            
            # oneStep 実行を有効化
            self.thread.oneStep = True


    def rewind_program(self):
        # ボタン連動：「>>」を有効に
        self.onestepDebugButton.setEnabled(True)

        # 一つ前の実行結果を取得
        self.history.discard_thelatest()        
        #current = self.history.get_elem()
        current = self.history.get_at(-1)
        
        self.centralWidget.set_HighlightLine(current['lineno'],
                                             self.debug_trail)

        
        # rewind のときのみ set_data で previous を指定する
        if not self.history.can_rewind():
            # 巻き戻せない            
            self.envViewer.set_data(current['pretty_env'],
                                    level=len(current['dump']),
                                    previous={})
            self.rewindDebugButton.setEnabled(False)
            
            
        else:
            #previous = self.history.get_elem(-1)
            previous = self.history.get_at(-2)

            if 'lower_level_pretty' in previous.keys():
                lower_level_data = previous['lower_level_pretty']
            else:
                lower_level_data = None

            """
            print("---")
            print(previous)
            print("---")            
            print("current", current['pretty_env'])
            print("lower_current", current['lower_level_pretty'])
            print("previous", previous['pretty_env'])
            print("lower", previous['lower_level_pretty'])
            """
            
            self.envViewer.set_data(current['pretty_env'],
                                    level=len(current['dump']),
                                    previous=previous['pretty_env'],
                                    lower_data=lower_level_data)

    

    def run_program_onestep(self):
        self.startDebugButton.setEnabled(False)

        #current = self.history.get_elem()
        current = self.history.get_at(-1)

        
        
        evalInfo = copy.deepcopy(current)
        self.thread.set_env(evalInfo)

        # onestep 実行が終わるまで onestepDebugButton は無効に
        self.onestepDebugButton.setEnabled(False)
        self.rewindDebugButton.setEnabled(False)
        
        self.thread.start()
        return
    

        
    def run_program(self):
        self.centralWidget.clear_messages()

        preset_env = self.presetEnv.get_data()
        
        
        program = self.centralWidget.get_program()
        self.thread.setup(program, preset_env)
        
        if self.thread.evaluatorInfo['noerror']:
            self.stop_debug()

            self.centralWidget.set_ReadOnly(True)
            
            self.presetEnv.clearSelection()
            self.presetEnv.set_ReadOnly(True)
            self.presetEnv.setEnabled(False)
            self.addItemButton.setEnabled(False)
            
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
        self.centralWidget.add_messages("強制終了されました", error=True);
                


    def eval_finished(self):

        evaluatorInfo = self.thread.evaluatorInfo
        """
        try:
            self.envViewer.set_data(evaluatorInfo['pretty_env'],
                                    len(evaluatorInfo['dump']))
            
        except:
            print("[except in eval_finished]")
            print(evaluatorInfo)
            self.envViewer.clear_data()
        """

        if 'dump' in evaluatorInfo.keys():
            level = len(evaluatorInfo['dump'])
            if 'procedure_finished' in evaluatorInfo.keys():
                procedure_finished = evaluatorInfo['procedure_finished']
            else:
                procedure_finished = False
                
        else:
            level = 0
            procedure_finished = False

        self.envViewer.set_data(evaluatorInfo['pretty_env'],
                                level=level,
                                procedure_finished=procedure_finished)
            
            
        if self.thread.oneStep == False:
            # 通常実行の場合
            self.enable_startButton()
            
        else:
            # oneStep 実行の場合

            if 'empty' not in evaluatorInfo.keys():
                return
                
                
            self.rewindDebugButton.setEnabled(True)


            # history に追加
            self.history.set_elem(evaluatorInfo)
            
            
            if evaluatorInfo['empty']:
                # もう実行するものがない場合

                # ボタン連動：「>>」を無効に
                self.onestepDebugButton.setEnabled(False)
                
                self.centralWidget.clear_HighlightLine()
                QMessageBox.information(self,
                                        "プログラム実行の終了",
                                        "すべてのプログラムが実行されました。",
                                        QMessageBox.Ok)

            else:
                self.onestepDebugButton.setEnabled(True)
                self.centralWidget.set_HighlightLine(evaluatorInfo['lineno'],
                                                     self.debug_trail)
            
            
        
        
    # -----------------------------------------------------------------
    # スタートボタンの依存関連
    # -----------------------------------------------------------------
    def enable_startButton(self):
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)

        self.startProgramAct.setEnabled(True)
        self.stopProgramAct.setEnabled(False)
                
        self.centralWidget.set_ReadOnly(False)
        
        self.presetEnv.set_ReadOnly(False)
        self.presetEnv.setEnabled(True)
        self.addItemButton.setEnabled(True)
        
        #self.centralWidget.editor.highlightCurrentLine()
        

    def disable_startButton(self):
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)

        self.startProgramAct.setEnabled(False)
        self.stopProgramAct.setEnabled(True)
        
        self.centralWidget.set_ReadOnly(True)

        self.presetEnv.clearSelection()
        self.presetEnv.set_ReadOnly(True)
        self.presetEnv.setEnabled(False)
        self.addItemButton.setEnabled(False)
        

    # -----------------------------------------------------------------
    # キー入力時のショートカット
    # -----------------------------------------------------------------        
    def keyPressEvent(self, event):
        # print('keyPressEvent, key = %s.' % event.key())

        # Ctrl と Enter の同時押し
        if event.modifiers() & Qt.ControlModifier and \
           event.key() == Qt.Key_Return:
            self.startButton.click()
            return

        elif not self.startDebugButton.isEnabled():
            # デバッグ中なら
            if event.key() in [Qt.Key_Right, Qt.Key_Down]:
                self.onestepDebugButton.click()
                return
            elif event.key() in [Qt.Key_Left, Qt.Key_Up]:
                self.rewindDebugButton.click()
                return
            elif event.key() == Qt.Key_Escape:
                self.stopDebugButton.click()
                return

            
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
        


    def str_to_bool(self, string):
        if string == "false":
            return False
        else:
            return True
        
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
            print("Error: There is an error to make information about font.")
            #pass
        
        # tableview の第1列の幅
        width = setting.value("tableview_column_width")
        self.envViewer.set_HeaddaColumnWidth(int(width))

        # メニュー->表示->デバッグ のチェック
        checked = self.str_to_bool(setting.value(self.debugDockAct.objectName()))
        self.debugDockAct.setChecked(checked)
        self.show_Dock()

        
        checked = self.str_to_bool(setting.value(self.debugTrailAct.objectName()))
        self.debugTrailAct.setChecked(checked)
        self.debug_trail = checked


        # メニュー->表示->変数の初期値 のチェック
        checked = self.str_to_bool(setting.value(self.presetDockAct.objectName()))
        self.presetDockAct.setChecked(checked)
        self.show_presetDock()



        
        checked = self.str_to_bool(setting.value(self.toolBarVisibleAct.objectName()))
        self.toolBarVisibleAct.setChecked(checked)
        self.toggle_toolBar()

        
                
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
        width = self.envViewer.get_HeaddaColumnWidth()
        setting.setValue("tableview_column_width", width)

        # メニュー->ツール->デバッグ表示 のチェック
        setting.setValue(self.debugDockAct.objectName(),
                         self.debugDockAct.isChecked())        
        setting.setValue(self.debugTrailAct.objectName(),
                         self.debugTrailAct.isChecked())
        setting.setValue(self.toolBarVisibleAct.objectName(),
                         self.toolBarVisibleAct.isChecked())

        setting.setValue(self.presetDockAct.objectName(),
                         self.presetDockAct.isChecked())
        
        
        #program = self.centralWidget.get_program()
        #setting.setValue("program", program)

        
        
    def update_font(self, font):
        self.centralWidget.editor.setFont(font)
        self.centralWidget.messageArea.setFont(font)
        self.envViewer.set_font(font)
        self.presetEnv.set_font(font)
        self.centralWidget.setFont(font)
        

        

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




