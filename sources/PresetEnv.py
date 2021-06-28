# -*- coding: utf-8 -*-
from PySide2.QtGui import QFont
from PySide2.QtCore import (Qt, QModelIndex, QAbstractTableModel)
from PySide2.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                               QWidget, QTableView, QHeaderView)

import re

from ValueSyntaxChecker import SyntaxChecker

class SimpleTableModel(QAbstractTableModel):
    def __init__(self, font=None, parent=None):
        super().__init__(parent)
        
        self.title = ["名前", "値"]
        self.mydata = [["",""],["",""],["",""]]

        self.checker = SyntaxChecker()
        self.reg_variable = re.compile('[a-zA-Z_][a-zA-Z0-9_]*', re.I)
        self.font = font
        self.readonly = False
        
        
    def init_data(self):
        self.mydata = [["",""],["",""],["",""]]


        
    def data(self, index, role):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            #tolist = [[key, value] for (key,value) in self.mydata.items()] 
            #return tolist[index.row()][index.column()]
            return self.mydata[index.row()][index.column()]

        elif index.isValid() and role == Qt.FontRole:
            return self.font

        
    def rowCount(self, parent=QModelIndex()):
        return len(self.mydata)
        
    def columnCount(self, parent=QModelIndex()):
        return len(self.title)
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return
        
        if orientation == Qt.Horizontal:
            return self.title[section]


    def setData(self, index, value, role):
        # Returning true means the value was accepted.
        if index.isValid() and role == Qt.EditRole:
            if index.column() == 0:
                if len(self.reg_variable.findall(value)) == 1:
                    self.mydata[index.row()][0] = value
                    return True
                else:
                    return False
            elif index.column() == 1:
                mes = self.checker.is_valid(value)
                if mes == "":
                    self.mydata[index.row()][1] = value
                    return True
                else:
                    print(mes)
                    return False

            
        return False  # Not Accepted.

    
    def addRow(self, name, value):
        self.beginInsertRows(QModelIndex(), len(self.mydata), len(self.mydata))
        self.mydata.append([name, value])
        self.endInsertRows()

    def removeRows(self, rowIndexes):
        for row in sorted(rowIndexes, reverse=True):
            #self.beginRemoveRows(QModelIndex(), row, row + 1)
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.mydata[row]
            self.endRemoveRows()
            
        
    def flags(self, index):
    
        if index.isValid():
            if not self.readonly:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
            else:
                return Qt.NoItemFlags

        return Qt.NoItemFlags



    
    
class PresetEnv(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        self.table = QTableView()
        self.table.setContentsMargins( 0,0,0,0 )
        self.table.setStyleSheet("padding:0px")

        layout.addWidget(self.table)
        self.setLayout(layout)

        self.model = SimpleTableModel(font=QFont())
        self.table.setModel(self.model)

        # selection 変更の検出用（class 外から見られるように）
        self.selectionModel = self.table.selectionModel()

        
        # ヘッダーの設定
        self.font = QFont()
        vheader = QHeaderView(Qt.Orientation.Vertical)
        vheader.setSectionResizeMode(QHeaderView.ResizeToContents)
         
        self.table.setVerticalHeader(vheader)
        self.table.verticalHeader().hide()
        
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
        self.table.setHorizontalHeader(self.hheader)        



        
    def newItem(self):
        self.model.addRow("","")
        
    
    def selectedRows(self):
        rows = []
        for index in self.table.selectedIndexes():
            #if index.column() == 0:
            #    rows.append(index.row())
            rows.append(index.row())
            
        return list(set(rows))

    def removeItems(self):
        self.model.removeRows(self.selectedRows())


    def set_font(self, font):
        self.model.font=font
        
        self.setStyleSheet('''
        QTableView { font:%dpt %s;}
        ''' % (font.pointSize(), font.family()))

        
    def get_data(self):
        retval = []
        for data in self.model.mydata:
            if data[0] != "" and data[1] != "":
                retval += [data]
                
        return retval
    
    def set_ReadOnly(self, flag):
        self.model.readonly = flag
        
    def clearSelection(self):
        self.selectionModel.clearSelection()
        
