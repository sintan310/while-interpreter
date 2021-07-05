# -*- coding: utf-8 -*-
import copy

from PySide2.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide2.QtGui import QFont, QColor
from PySide2.QtWidgets import (QWidget, QMainWindow, 
                               QTableWidget, QHeaderView, QTableWidgetItem,
                               QHBoxLayout, QAbstractItemView,
                               QGraphicsOpacityEffect)



class EnvViewer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title = ["変数名", "値"]
        #self.data = {'a':20, 'b':10, 'c':2, 'd':'aaa'}
        self.previous_data = {}
        self.data = {}

      
        self.tableWidget = QTableWidget()
        self.tableWidget.setContentsMargins( 0,0,0,0 )
        self.tableWidget.setStyleSheet("padding:0px")

        self.tableWidget.setAlternatingRowColors(True) # 複数行で色を返る

        self.tableWidget.setColumnCount(len(self.title))
        self.tableWidget.setRowCount(len(self.data))

        self.tableWidget.setHorizontalHeaderLabels(self.data)
        
        
        self.font = QFont()
        # self.font.setPointSize(20)

        
        # ヘッダーの設定
        vheader = QHeaderView(Qt.Orientation.Vertical)
        vheader.setSectionResizeMode(QHeaderView.ResizeToContents)
         
        self.tableWidget.setVerticalHeader(vheader)
        self.tableWidget.verticalHeader().hide()
        
        self.hheader = QHeaderView(Qt.Orientation.Horizontal)
        self.hheader.setFont(self.font)
        self.hheader.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.hheader.setStyleSheet('''
          ::section {
            background-color: #e0e0e0;
            padding: 0 5px;
            border: 0px;
          }''')
        self.hheader.setSectionsClickable(False)

        #hheader.setSectionResizeMode(QHeaderView.ResizeToContents)
        #hheader.setSectionResizeMode(1, QHeaderView.Stretch)
        self.hheader.setStretchLastSection(True)        
        self.tableWidget.setHorizontalHeader(self.hheader)        
        self.tableWidget.setHorizontalHeaderLabels(self.title)


        #self.tableWidget.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)


        #self.tableWidget.horizontalHeader().setStyle(QStyleFactory.create('Cleanlooks'))

        # ダブルクリックで編集不可。選択も不可。
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionMode(QAbstractItemView.NoSelection);

        
        # 0列目の長さを 80 にする（Stretch の後で指定する）
        
        
        # レイアウト
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)  # 額縁ぽくてカッコ悪いので 0 にする
        layout.addWidget(self.tableWidget)
        self.setLayout(layout)

        self.set_data(self.data)


        self.effects = []
        self.effect_border = 5
        for i in range(10):
            child = QWidget(self)
            effect = QGraphicsOpacityEffect(child)
            child.setGraphicsEffect(effect)
            child.setStyleSheet("border-width: %dpx; border-style: solid; border-color: yellow; background-color: none; border-radius:10px;" % self.effect_border)
            child.resize(0, 0)
            
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setStartValue(0.6)
            anim.setEndValue(0.3)
            anim.setDuration(400)
            anim.setEasingCurve(QEasingCurve.InCubic)
            anim.finished.connect(self.animation_finished)
            self.effects.append((child, anim, effect))

            
    def animation_finished(self):
        for widget, anim, effect in self.effects:
            widget.resize(0,0)
            widget.move(0,0)
            
            
    def set_HeaddaColumnWidth(self, width):
        self.tableWidget.setColumnWidth(0, width)

    def get_HeaddaColumnWidth(self):
        return self.tableWidget.columnWidth(0)
        

    def set_font(self, font):
        self.font = font
        self.setFont(self.font)
        
        font_size = self.font.pointSize()
        self.setStyleSheet(
            '''QToolTip {
            font-size:%dpt
            }''' % font_size)        
        
        #self.hheader.setFont(self.font)
        
        self.write_data()
        
        
    def set_data(self, data, previous=None):
        if previous == None:
            self.previous_data = copy.deepcopy(self.data)
        else:
            self.previous_data = copy.deepcopy(previous)
            
        self.data = copy.deepcopy(data)

        self.write_data()

        
    def write_data(self):


        self.child1 = QWidget(self)

        
        # self.tableWidget.setHorizontalHeaderLabels(self.title)
        # テーブルの中身作成
        changed_row = []
        
        self.tableWidget.setRowCount(len(self.data))
        
        row = 0
        for key, value in self.data.items():
            item = QTableWidgetItem(key)
            item.setFont(self.font)
            self.tableWidget.setItem(row, 0, item)
            
            
            item = QTableWidgetItem(str(value))
            item.setFont(self.font)

            if key not in self.previous_data.keys():
                self.previous_data[key] = None

            if self.previous_data[key] != self.data[key]:
                item.setBackground(QColor(Qt.yellow).lighter(160))
                
                if self.previous_data[key] == None:
                    self.previous_data[key] = "0"
                    
                item.setToolTip("変更前: " + self.previous_data[key])

                changed_row.append(row)
        

                
                
            self.tableWidget.setItem(row, 1, item)
                        
            row += 1
            
        if changed_row != []:
            width = self.tableWidget.columnWidth(1)
            for i, row in enumerate(changed_row):
                if i>len(self.effects): break
                
                y = 0
                for i in range(row):
                    y += self.tableWidget.rowHeight(i)

                height = self.tableWidget.rowHeight(row)
                
                (widget, anim, effect) = self.effects[i]

                # 12 is the width of the scrollbar
                widget.resize(width + self.effect_border*2 - 12,
                              height +  self.effect_border*2)
                widget.move(self.tableWidget.columnWidth(0) -
                            self.effect_border,
                            self.tableWidget.horizontalHeader().height()+
                            y - 
                            self.effect_border)
                
                anim.start()
            
            

        

if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = TableView()
    widget.show()
    sys.exit(app.exec_())

