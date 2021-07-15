# -*- coding: utf-8 -*-
import copy

from PySide2.QtCore import (Qt, QPropertyAnimation, QEasingCurve,
                            QParallelAnimationGroup)
from PySide2.QtGui import QFont, QColor
from PySide2.QtWidgets import (QWidget, QMainWindow, 
                               QTableWidget, QHeaderView, QTableWidgetItem,
                               QVBoxLayout, QAbstractItemView,
                               QGraphicsOpacityEffect, QScrollArea)



class EnvViewerItem(QWidget):

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

        
        # ヘッダーの設定
        vheader = QHeaderView(Qt.Orientation.Vertical)
        vheader.setSectionResizeMode(QHeaderView.ResizeToContents)
         
        self.tableWidget.setVerticalHeader(vheader)
        self.tableWidget.verticalHeader().hide()
        
        self.hheader = QHeaderView(Qt.Orientation.Horizontal)
        self.hheader.setFont(self.font)
        self.hheader.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.hheader.setStyleSheet('''::section {
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

        
        
        # レイアウト
        self.layout = QVBoxLayout(alignment=Qt.AlignTop)
        self.layout.setContentsMargins(0,0,0,0)  # 額縁ぽくてカッコ悪いので 0 にする
        self.layout.addWidget(self.tableWidget)
        self.setLayout(self.layout)

        self.set_data(self.data)


        # tableWidget close 用のアニメーション        
        self.close_animations = QParallelAnimationGroup()
        
        self.animMin = QPropertyAnimation(self, b"minimumHeight")
        #self.animMin.setEndValue(0)
        self.animMin.setEndValue(2)
        
        #self.animMin.setEasingCurve(QEasingCurve.OutCubic)
        self.animMin.setEasingCurve(QEasingCurve.OutQuad)

        self.animMax = QPropertyAnimation(self, b"maximumHeight")
        #self.animMax.setEndValue(0)
        self.animMax.setEndValue(2)
        
        #self.animMax.setEasingCurve(QEasingCurve.OutCubic)
        self.animMax.setEasingCurve(QEasingCurve.OutQuad)

        self.close_animations.addAnimation(self.animMin)
        self.close_animations.addAnimation(self.animMax)
        

        # tableWidget open 用のアニメーション        
        self.open_animations = QParallelAnimationGroup()
        
        self.animMin_open = QPropertyAnimation(self, b"minimumHeight")
        self.animMin_open.setStartValue(0)
        #self.animMin_open.setEasingCurve(QEasingCurve.OutCubic)
        #self.animMin.setEasingCurve(QEasingCurve.OutQuad)
        #self.animMin_open.setEasingCurve(QEasingCurve.InCubic)
        self.animMin_open.setEasingCurve(QEasingCurve.InQuad)
        
        self.animMax_open = QPropertyAnimation(self, b"maximumHeight")
        self.animMax_open.setStartValue(0)
        #self.animMax_open.setEasingCurve(QEasingCurve.OutCubic)
        #self.animMax.setEasingCurve(QEasingCurve.OutQuad)
        #self.animMax_open.setEasingCurve(QEasingCurve.InCubic)
        self.animMax_open.setEasingCurve(QEasingCurve.InQuad)

        self.open_animations.addAnimation(self.animMin_open)
        self.open_animations.addAnimation(self.animMax_open)
        
            
        # 枠が光るアニメーション用
        # あらかじめ十分な量を用意しておいて対処する方法は Flyweight というらしい
        # https://qiita.com/GRGSIBERIA/items/5d60b520b80457cb00e5
        self.effects = []
        self.effect_border = 5
        for i in range(10):
            child = QWidget(self)
            child.setStyleSheet("""
             border-width: %dpx; 
             border-style: solid; 
             border-color: yellow; 
             background-color: none; border-radius:10px;
            """ % self.effect_border)
            child.resize(0, 0)

            # QWidget は opacity を持たないので下記の様にして加える 
            effect = QGraphicsOpacityEffect(child)            
            child.setGraphicsEffect(effect)

            anim = QPropertyAnimation(effect, b"opacity")
            
            anim.setStartValue(0.6)
            anim.setEndValue(0.3)
            anim.setDuration(400)
            #anim.setEasingCurve(QEasingCurve.InCubic)
            anim.setEasingCurve(QEasingCurve.InQuad)
            anim.finished.connect(self.item_highlight_animation_finished)
            self.effects.append((child, anim, effect))

            

        
        
    def item_highlight_animation_finished(self):
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

        
        # ヘッダも大きくする場合にはコメントアウトを外す
        #self.hheader.setFont(self.font)
        
        self.write_data()



    # 出現時のアニメーション
    def open_animation(self, start=None, duration=200):
        
        height = self.tableWidget_height()
        
        self.animMin_open.setDuration(duration)
        self.animMin_open.setEndValue(height)
        if start != None:
            self.animMin_open.setStartValue(start)
            
        
        self.animMax_open.setDuration(duration)
        self.animMax_open.setEndValue(height)
        if start != None:
            self.animMax_open.setStartValue(start)
        
        self.open_animations.start()

        

    # 閉じるときのアニメーション
    # （deleteLater で destory しないと描画されたままになる）
    def close(self, destroyAction=None, duration=200):

        height = self.tableWidget_height()
        
        self.animMin.setDuration(duration)
        self.animMin.setStartValue(height)

        self.animMax.setDuration(duration)
        self.animMax.setStartValue(height)
        
        
        if destroyAction:
            self.animMin.finished.connect(destroyAction)

        self.close_animations.start()

        
    def tableWidget_height(self):

        #self.tableWidget.setAttribute(Qt.WA_DontShowOnScreen)
        #self.tableWidget.show()

        
        height = self.tableWidget.horizontalHeader().height()

        length = len(self.data)
        if length == 0:
            return height

        
        for i in range(0, length):
            height += self.tableWidget.rowHeight(i)
            
        # 余白分のため +10 しておく
        height += 15

        return height
        
        
    def set_data(self, data, previous=None):
        old_height = self.tableWidget_height()
        
        if previous == None:
            self.previous_data = copy.deepcopy(self.data)
        else:
            self.previous_data = copy.deepcopy(previous)
            
        self.data = copy.deepcopy(data)

        self.write_data()

        
        height = self.tableWidget_height()
        if old_height != height:
            if self.open_animations.state() != QPropertyAnimation.Running:

                # 基底として作られているものには適用しない
                #if self.objectName() == "":
                    self.open_animation(start=old_height, duration=500)
                    
            else:
                height = self.tableWidget_height()
                self.animMin_open.setEndValue(height)
                self.animMax_open.setEndValue(height)
                
                    
        
    def write_data(self):

        # self.tableWidget.setHorizontalHeaderLabels(self.title)
        # テーブルの中身作成

        if self.data == None:
            return

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


        self.tableWidget.resizeColumnToContents(1)
        self.tableWidget.resizeRowsToContents()

        # 枠が光るアニメ効果
        if changed_row != []:
            width = self.tableWidget.columnWidth(1)
            
            for i, row in enumerate(changed_row):

                # 用意していた分のアニメだけ実施
                if i>len(self.effects): break
                
                y = 0
                for i in range(row):
                    y += self.tableWidget.rowHeight(i)

                height = self.tableWidget.rowHeight(row)
                
                (widget, anim, effect) = self.effects[i]

                
                # 12 is an approximate width of the scrollbar
                widget.resize(width + self.effect_border*2 - 12,
                              height +  self.effect_border*2)
                widget.move(self.tableWidget.columnWidth(0) -
                            self.effect_border,
                            self.tableWidget.horizontalHeader().height()+
                            y - 
                            self.effect_border)
                
                anim.start()
            
            

class EnvViewer(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.level = 0

        self.font = QFont()
        self.vsbar_stylesheet = ""
        self.hsbar_stylesheet = '''
        QScrollBar:Horizontal{
         background: white;
         height: 12px;
         }
        QScrollBar::handle:Horizontal{
         background: lightgray;
        }
        QScrollBar::handle:Horizontal:hover{
         background: gray;
        }
        '''

        
        self.setWidgetResizable(True)

        # QScrollArea には Widget を貼り付ける必要がある
        # https://www.wizard-notes.com/entry/python/pyqt-qscrollarea
        self.inner = QWidget()
        self.layout = QVBoxLayout(alignment=Qt.AlignTop)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)
        
        
        # 基底 envViewerItem を作成
        viewer_item = self.make_envViewerItem(base_item=True)
        

        self.headda_column_width = viewer_item.get_HeaddaColumnWidth()

        
        # layout に viewer を入れるが、あくまでも layout のためだけにし、
        # 実際のアクセス管理は配列で行う
        # （連打されると消去が間に合わなく、self.layout.itemAt(0).widget() で
        # 取得できる widget の整合性が取れなくなる）
        self.viewers = [viewer_item]
        self.layout.insertWidget(0, viewer_item)
        
        self.inner.setLayout(self.layout)
        self.setWidget(self.inner)


        viewer_item.open_animation(duration=100)
                                   

    def make_envViewerItem(self, base_item=False):
        viewer_item = EnvViewerItem()
        viewer_item.set_font(self.font)
        #viewer_item.tableWidget.verticalScrollBar().setStyleSheet(self.vsbar_stylesheet)
        viewer_item.tableWidget.verticalScrollBar().setStyleSheet("QScrollBar {height:0px;}")
        viewer_item.tableWidget.horizontalScrollBar().setStyleSheet(self.hsbar_stylesheet)
        #viewer_item.tableWidget.horizontalScrollBar().setStyleSheet("QScrollBar {width:0px;}")
        
        if base_item:
            viewer_item.setObjectName("base_item") # 基底にだけ名前をつける

        return viewer_item
    
        
    def set_font(self, font):
        self.font = font

        for item in self.viewers:
            item.set_font(font)

            

    def vertical_scrollbar_setStyleSheet(self, stylesheet):
        self.vsbar_stylesheet = stylesheet
        self.verticalScrollBar().setStyleSheet(stylesheet)

        #for item in self.viewers:
        #    item.tableWidget.verticalScrollBar().setStyleSheet(stylesheet)
        
                
    def set_data(self, data, level, previous=None,
                 procedure_finished=False,
                 lower_data=None):
        
        if self.level < level:
            # 環境スタック dump が増えた時は viewer を追加
            self.level += 1

            new_item = self.make_envViewerItem()
            new_item.set_data(data, previous)            

            if lower_data != None:
                # いまの top_item を一つ前の状態に戻す
                
                top_item = self.viewers[0]
                top_item_previous = top_item.previous_data
                top_item.set_data(lower_data)
                new_item.setEnabled(False)

            self.layout.insertWidget(0, new_item)
            self.update()
            
            self.viewers.insert(0, new_item)
            new_item.open_animation(duration=500)
            
            
            
        elif self.level > level:
            # 環境スタック dump が減ったときは viewer を削除
            
            delete_item = self.viewers.pop(0)
            self.clear_viewer_chain([delete_item],
                                        duration=600, level_clear=False)
            
            top_item = self.viewers[0]
            top_item.set_data(data)
            self.level -= 1

            
            
            
        else:
            # 通常処理: base_item に set_data する
            top_item = self.viewers[0]
            top_item.set_data(data, previous)

            if procedure_finished:
                top_item.setEnabled(False)
            else:
                top_item.setEnabled(True)
            

        

    def clear_viewer_chain(self, viewer_list, me=None, duration=300,
                           level_clear=True):

        if me:
            me.hide()
            me.deleteLater()

        if viewer_list != []:
            viewer = viewer_list.pop()
            viewer.setEnabled(False)
            viewer.close(lambda:self.clear_viewer_chain(viewer_list,
                                                        me=viewer,
                                                        duration=duration,
                                                        level_clear=level_clear),
                         duration=duration)
                                
        else:
            if level_clear:
                self.level = 0
                
                
        
    def clear_data(self):
        
        count = self.layout.count()
        if count>1:
            widgets = [self.layout.itemAt(i).widget() for i in range(0,count-1)]

            base_widget = self.layout.itemAt(count-1).widget()
            base_widget.set_data({})
            self.viewers = [base_widget]

            self.clear_viewer_chain(widgets)
        else:
        
            base_widget = self.layout.itemAt(0).widget()
            base_widget.set_data({})
            self.viewers = [base_widget]
        
        
    def get_HeaddaColumnWidth(self):
        return self.headda_column_width

    
    def set_HeaddaColumnWidth(self, width):
        self.headda_column_width = width
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.set_HeaddaColumnWidth(width)
        

        
if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            
            widget = EnvViewer()
            self.setCentralWidget(widget)


    
    app = QApplication(sys.argv)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())

