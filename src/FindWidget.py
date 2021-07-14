# -*- coding:utf-8 -*-
from PySide2.QtCore import (Qt, QSize, QParallelAnimationGroup,
                            QPropertyAnimation, QPoint, QAbstractAnimation)
from PySide2.QtWidgets import (QWidget, QPushButton, QLineEdit, QLabel,
                               QGridLayout, QStyle, QSpacerItem)


class FindWidget(QWidget):
    def __init__(self, editor, find_action, replace_action, parent=None):
        super().__init__(parent)

        self.editor = editor
        self.find_action = find_action
        self.replace_action = replace_action
        self.mode = "find" # or "replace"
        self.setup_Ui()

        self.find_word = ""
        self.replace_word = ""

        # animation
        self.toggleAnimation = QParallelAnimationGroup()
        self.animMin = QPropertyAnimation(self, b"minimumHeight")
        self.animMin.setDuration(150)
        self.animMax = QPropertyAnimation(self, b"maximumHeight")
        self.animMax.setDuration(150)
        self.toggleAnimation.addAnimation(self.animMin)
        self.toggleAnimation.addAnimation(self.animMax)
        self.animMin.finished.connect(self.animation_finished)
            #QAbstractAnimation.Backward
            #toggleButton.setArrowType(arrow_type)
            #

        
    def setup_Ui(self):

        layoutFind = QGridLayout()
        #layout.setSpacing(0)
        #layout.setContentsMargins(0,0,0,0)

        original_font = self.font()
        current_font = self.font()
        current_font.setPointSize(11)
        
        self.setStyleSheet('border:0px;')
        
        self.label = QLabel("検索")
        
        self.lineEdit = QLineEdit()
        self.lineEdit.textChanged.connect(self.find_text)        
        self.lineEdit.setPlaceholderText("検索する語")
        self.lineEdit.setClearButtonEnabled(True)
        
        self.lineEdit.setFont(current_font)

        lineEdit_style = '''
        QLineEdit:focus {
          border: 1px solid lightblue;
        }
        QLineEdit {
          padding:3px;
          border: 1px solid lightGray;
        }
        '''
        self.lineEdit.setStyleSheet(lineEdit_style)
        
        button_style = '''
        QPushButton {
         padding: 4px;
         color: #333333;
         width: 2.5em;
        }
        QPushButton:hover{
         border: 1px solid lightgray;
         background: lightgray;
        }
        QPushButton:pressed{
         border-top: 1px solid gray;
         border-left: 1px solid gray;
         border-bottom: 0px solid gray;
         border-right: 0px solid gray;
         background: none;
        }
        '''
        self.quitButton = QPushButton()
        self.quitButton.setStyleSheet(button_style)        
        self.quitButton.setIcon(self.style().standardIcon(QStyle.SP_DockWidgetCloseButton))
        self.quitButton.clicked.connect(self.suspend)
        self.quitButton.setCheckable(False)  
        

        self.nextButton = QPushButton()
        self.nextButton.setStyleSheet(button_style)
        self.nextButton.setIcon(self.style().standardIcon(QStyle.SP_TitleBarUnshadeButton))
        self.nextButton.clicked.connect(self.find_next)
        self.nextButton.setCheckable(False)  
        
        self.previousButton = QPushButton()
        self.previousButton.setStyleSheet(button_style)
        self.previousButton.setIcon(self.style().standardIcon(QStyle.SP_TitleBarShadeButton))
        self.previousButton.clicked.connect(self.find_previous)
        self.previousButton.setCheckable(False)  

        
        #spacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
        spacer = QSpacerItem(15, 1)
        
        layoutFind.addWidget(self.label, 0, 0)
        layoutFind.addWidget(self.lineEdit, 0, 1)
        layoutFind.addWidget(self.previousButton, 0, 3)
        layoutFind.addWidget(self.nextButton, 0, 4)
        layoutFind.addItem(spacer, 0, 5)
        layoutFind.addWidget(self.quitButton, 0, 6)


        self.labelReplace = QLabel("置換")
        self.labelReplace.setFont(original_font)

        self.lineEditReplace = QLineEdit()
        self.lineEditReplace.textChanged.connect(self.set_replace_text)        
        self.lineEditReplace.setPlaceholderText("置き換え後")
        self.lineEditReplace.setClearButtonEnabled(True)        
        self.lineEditReplace.setFont(current_font)
        self.lineEditReplace.setStyleSheet(lineEdit_style)

        replaceButton_style = '''
        QPushButton {
         padding: 4px;
         color: #333333;
         width: 2.5em;
        }
        QPushButton:hover{
         border:1px solid lightgray;
         background: lightgray;
        }
        QPushButton:pressed{
         border-top: 1px solid gray;
         border-left: 1px solid gray;
         border-bottom: 0px solid gray;
         border-right: 0px solid gray;
         background: none;
        }
        QPushButton:disabled{
         color: lightgray
        }
        '''

        self.replaceAllButton = QPushButton("すべて")
        self.replaceAllButton.setStyleSheet(replaceButton_style)        
        self.replaceAllButton.setFont(original_font)
        self.replaceAllButton.clicked.connect(self.replace_all)
        self.replaceAllButton.setCheckable(False)  
        self.replaceAllButton.setEnabled(False)        

        self.replaceOneButton = QPushButton("置換")
        self.replaceOneButton.setStyleSheet(replaceButton_style)        
        self.replaceOneButton.setFont(original_font)
        self.replaceOneButton.clicked.connect(self.replace_at)
        self.replaceOneButton.setCheckable(False)  
        self.replaceOneButton.setEnabled(False)        

        
        layoutFind.addWidget(self.labelReplace, 1, 0)
        layoutFind.addWidget(self.lineEditReplace, 1, 1)
        layoutFind.addWidget(self.replaceAllButton, 1, 3)
        layoutFind.addWidget(self.replaceOneButton, 1, 4)

        self.replaceWidgets = [self.labelReplace,
                               self.lineEditReplace,
                               self.replaceAllButton,
                               self.replaceOneButton]
        #for x in self.replaceWidgets: x.hide()
        
        
        self.setLayout(layoutFind)


    def find_text(self, text, addpos=0, keypos_clear=True):
        self.find_word = text
        self.find_action(self.find_word, addpos, keypos_clear)

        if self.replace_word != "" and self.find_word != "":
            self.replaceAllButton.setEnabled(True)
            self.replaceOneButton.setEnabled(True)
        else:
            self.replaceAllButton.setEnabled(False)
            self.replaceOneButton.setEnabled(False)

        

    def find_next(self, text):
        self.find_action(self.find_word, addpos=1, keypos_clear=False)

    def find_previous(self, text):
        self.find_action(self.find_word, addpos=-1, keypos_clear=False)


    def set_replace_text(self, text):
        self.replace_word = text
        
        if self.replace_word != "" and self.find_word != "":
            self.replaceAllButton.setEnabled(True)
            self.replaceOneButton.setEnabled(True)
        else:
            self.replaceAllButton.setEnabled(False)
            self.replaceOneButton.setEnabled(False)


    def replace_at(self):
        if self.find_word != "" and self.replace_word != "":
            self.replace_action(self.find_word, self.replace_word)
        
    def replace_all(self):
        if self.find_word != "" and self.replace_word != "":
            self.replace_action(self.find_word, self.replace_word,
                                all_flag=True)
        
        
    def suspend(self):
        # この widget が有効でないときは何もしない
        
        if self.isVisible():
            # widget が見えている時にクリックされた処理
            
            # 選択領域があるときには再検索
            cursor = self.editor.textCursor()
            selected_text = cursor.selectedText()
            if selected_text != "":
                self.open()
                
            else:
                # 選択領域がないときには閉じる
                self.find_action("")
                self.toggleAnimation.setDirection(QAbstractAnimation.Backward)
                self.after_animation_self_visible = False
                self.toggleAnimation.start()
                

    def close(self):
        self.find_word = ""
        self.suspend()

        
    def open(self, mode=None):
        if mode != None:
            self.mode = mode

        visibled = self.isVisible()
            
        self.setVisible(True)
        
        cursor = self.editor.textCursor()
        selected_text = cursor.selectedText()
        if selected_text != "":
            self.find_word = selected_text
        
        self.lineEdit.setText(self.find_word)
        self.lineEdit.setFocus()
        self.find_text(self.find_word)

        if self.mode == "find":
            for x in self.replaceWidgets: x.hide()
        else:
            for x in self.replaceWidgets: x.show()

            
        #print(self.sizeHint().height(), self.sizeHint().width())

        if visibled:
            # すでに表示されていたなら、アニメーションは行わない
            self.setMinimumHeight(self.sizeHint().height())
            self.setMaximumHeight(self.sizeHint().height())
        else:
            # animation start
            self.animMin.setStartValue(0)
            self.animMin.setEndValue(self.sizeHint().height())

            self.animMax.setStartValue(0)
            self.animMax.setEndValue(self.sizeHint().height())

            self.toggleAnimation.setDirection(QAbstractAnimation.Forward)
            self.after_animation_self_visible = True
            self.toggleAnimation.start()

            
    def animation_finished(self):
        self.setVisible(self.after_animation_self_visible)

