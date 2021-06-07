# -*- coding: utf-8 -*-
#
# QcodeEditor.py by acbetter.
# https://stackoverflow.com/questions/40386194/create-text-area-textedit-with-line-number-in-pyqt
#
# Editted by Shinya Sato (3 June 2021)
# - to fit it in PySide2
# - to fix the lineNumberAreaWidth
# - to add another highlightLine for one-step execution
#   in hightlightLine and highlightCurrentLine functions


from PySide2.QtCore import Qt, QRect, QSize
from PySide2.QtWidgets import QWidget, QPlainTextEdit, QTextEdit
from PySide2.QtGui import (QColor, QPainter, QTextFormat, QTextBlockFormat,
                           QFont, QTextCursor)


class QLineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class QCodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = QLineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        
        self.hlineno = 0

        self.format_normal = QTextBlockFormat()
        self.format_normal.setBackground(Qt.white)

        self.format_onestep = QTextBlockFormat()
        self.format_onestep.setBackground(QColor(Qt.green).lighter(160))
        

        
    def lineNumberAreaWidth(self):
        """
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        """
        space = 3 + self.fontMetrics().width('9') * 3
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))


    def clearHighlightLine(self):
        #cursor = self.textCursor()
        #cursor.movePosition(QTextCursor.Start)
        #cursor.movePosition(QTextCursor.NextBlock,
        #                    QTextCursor.MoveAnchor,
        #                    self.hlineno - 1)

        if self.hlineno > 0:
            cursor = QTextCursor(self.document().findBlockByNumber(self.hlineno -1))
            self.setTextCursor(cursor)                
            self.hlineno = 0
            
        self.highlightLine()
        self.highlightCurrentLine()
        
        
    def setHighlightLineno(self, lineno):            
        self.hlineno = lineno
        self.highlightLine()
        

    def highlightLine(self):

        # 全画面を選択しておき、白の背景色にする
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.setBlockFormat(self.format_normal)
        
        # current cursor を移動させて、画面を自動的にスクロールさせる
        if self.hlineno > 0:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.NextBlock,
                                QTextCursor.MoveAnchor,
                                self.hlineno - 1)
            self.setTextCursor(cursor)


            # hlineno をハイライト表示
            cursor = QTextCursor(self.document().findBlockByNumber(self.hlineno -1))
            cursor.setBlockFormat(self.format_onestep)
                             
        return
        

        
    def highlightCurrentLine(self):
        extraSelections = []

        if self.hlineno > 0:
            pass
            
        else:
            if not self.isReadOnly():

                selection = QTextEdit.ExtraSelection()
                lineColor = QColor(Qt.yellow).lighter(160)
                selection.format.setBackground(lineColor)
                selection.format.setProperty(QTextFormat.FullWidthSelection,
                                             True)
                selection.cursor = self.textCursor()
                selection.cursor.clearSelection()
                extraSelections.append(selection)
                self.setExtraSelections(extraSelections)

        


            

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)

        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # Just to make sure I use the right font
        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width(), height, Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1



if __name__ == '__main__':
    import sys
    from PySide2.QtWidgets import QApplication

    app = QApplication(sys.argv)
    codeEditor = QCodeEditor()
    codeEditor.show()
    sys.exit(app.exec_())
    
