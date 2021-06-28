# -*- coding: utf-8 -*-
#
# QcodeEditor.py
# It is based on the following codes by acbetter:
# https://stackoverflow.com/questions/40386194/create-text-area-textedit-with-line-number-in-pyqt
#
# Others are written by Shinya Sato (15 June 2021)


from PySide2.QtCore import Qt, QRect, QSize, QRegExp, QPoint, QTimer, Signal
from PySide2.QtWidgets import QWidget, QPlainTextEdit, QTextEdit
from PySide2.QtGui import (QColor, QPainter, QTextFormat, QTextBlockFormat,
                           QFont, QTextCursor,
                           QSyntaxHighlighter, QTextCharFormat)

import math

class MyLineTracer:
    def __init__(self, lineno=1, trail=True):
                
        self.trail = trail
        
        self.lineno = lineno
        self.lineno_target = lineno
        self.alpha = 255
        self.count = 0

        self.gap = 0

        self.resolution = 6
        
        
    def set_lineno(self, lineno, trail=True, force=False):
        # lineno は target に設定され、その gap 間はアニメーションになる
        
        if force:
            self.lineno = lineno
        
        self.trail = trail
        
        self.lineno_target = lineno
        self.gap = self.lineno_target - self.lineno
            
        self.alpha = 255
        self.count = 0

        
    def get_lineno(self):
        if not self.trail:
            return 0
        
        if self.gap < 0 and self.lineno < self.lineno_target:
            lineno = self.lineno_target
            self.lineno = lineno
        elif self.gap > 0 and self.lineno > self.lineno_target:
            lineno = self.lineno_target
            self.lineno = lineno

        return math.floor(self.lineno)
        
        
    def update(self):
        self.count += 1
        
        if not (self.count < self.resolution):
            self.alpha = 0
            self.lineno = self.lineno_target
            return
            
        #self.alpha = int(self.alpha - (self.alpha / self.resolution) * 1.1)
        #self.lineno = self.lineno + ((self.lineno_target - self.lineno) / self.resolution)*0.1

        self.alpha = int(self.alpha - (self.alpha / self.resolution) * 3)
        self.lineno = self.lineno + ((self.lineno_target - self.lineno) / self.resolution)*0.2

        
    def is_finished(self):
        if self.count <= self.resolution:
            return False
        else:
            return True
            

        
        

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
                
        keywordFormat = QTextCharFormat()
        # keywordFormat.setFontWeight(QFont.Bold)
        
        keywordFormat.setForeground(QColor(Qt.darkMagenta).lighter(130))
        #keywordPatterns = ["\\bMy[A-Za-z]+\\b"]
        # '\\b' means word boundary
        keywordPatterns = ['\\bprint\\b',
                           '\\bbegin\\b',
                           '\\bend\\b',
                           '\\bwhile\\b',
                           '\\bdo\\b',
                           '\\bdiv\\b',
                           '\\bmod\\b',
                           '\\band\\b',
                           '\\bor\\b',
                           '\\bnot\\b',
                           '\\bif\\b',
                           '\\bthen\\b',
                           '\\belse\\b',
        ]

        self.highlightingRules = [(QRegExp(pattern), keywordFormat)
                                  for pattern in keywordPatterns]


        builtinFormat = QTextCharFormat()
        builtinFormat.setForeground(QColor(Qt.darkYellow).lighter(90))
        patterns = [
                    '\\bprint\\b',

                    '\\blen\\b',
                    '\\bleft\\b',
                    '\\bright\\b',
                    '\\bmid\\b',
                    ]
        for rule in [(QRegExp(pattern), builtinFormat)
                                  for pattern in patterns]:
            self.highlightingRules.append(rule)


        pattern = "\\b[0-9]+"
        digitFormat = QTextCharFormat()
        digitFormat.setForeground(QColor(Qt.darkGreen))
        self.highlightingRules.append((QRegExp(pattern),
                digitFormat))
                
        functionFormat = QTextCharFormat()
        functionFormat.setForeground(QColor(Qt.darkYellow).lighter(90))
        # (?=E) means positive match. foo(a,b): matches,
        # but only foo is selected
        pattern = "\\b[A-Za-z0-9_]+(?=(\\(.*\\):))"
        self.highlightingRules.append((QRegExp(pattern),
                functionFormat))

        patterns = ['\\bprocedure\\b',
                    '\\bdiv\\b',
                    '\\bmod\\b',
                    '\\band\\b',
                    '\\bor\\b',
                    '\\bnot\\b',
                    ]
        operatorFormat = QTextCharFormat()
        operatorFormat.setForeground(QColor(Qt.blue))
        for pat in patterns:
            self.highlightingRules.append((QRegExp(pat),
                                           operatorFormat))

            
        quotationFormat = QTextCharFormat()
        quotationFormat.setForeground(QColor(Qt.darkRed).lighter(120))
        self.highlightingRules.append((QRegExp("\"([^\"]*)\""),
                                       quotationFormat))        

            
        lineCommentFormat = QTextCharFormat()
        lineCommentFormat.setForeground(QColor(Qt.darkGreen).lighter(100))
        self.highlightingRules.append((QRegExp("#[^\n]*"),
                                       lineCommentFormat))

        
        
    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            #expression = QRegExp(pattern)
            expression = pattern
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)


            
                
                


                
class QLineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)


class QCodeEditor(QPlainTextEdit):
    myclicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = QLineNumberArea(self)
        
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
       
        self.updateLineNumberAreaWidth(0)


        #self.clicked.connect(self.field_clicked)
        
        self.hlineno = 0
        self.tabStop = 4
        
        
        self.setAcceptDrops(False)

        self.syntax_highlighter = SyntaxHighlighter(self.document())
        
        self.bracket_list = {
            '(' : ')',
            '[' : ']',
            '"' : '"',
        }
        

        # linetracer
        self.line_tracer = MyLineTracer()
        self.timer_lt = QTimer()


        # find word
        self.keypos = 0
        self.keyword = ""

        
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.myclicked.emit()

        
    # paste のイベント
    def insertFromMimeData(self, source):
        if source.hasText():
            text = source.text()
            self.insert_as_codes(text)



            
    def get_tabspace_size(self, pos):
        return self.tabStop - (pos % self.tabStop)
            
    def insert_as_codes(self, text):
        cursor = self.textCursor()

        replaced_text = ""
        pos = cursor.positionInBlock()
        for x in list(text):
            if x == '\t':
                space_size = self.get_tabspace_size(pos)
                replaced_text += ' ' * space_size

                pos += self.tabStop

            elif x == '\n':
                replaced_text += '\n'
                pos = 0
            else:
                replaced_text += x
                pos+=1

        cursor.insertText(replaced_text)
        cursor.movePosition(QTextCursor.Start)
        self.setTextCursor(cursor)
        
        

    def indent_tab(self, cursor):
        # カーソルがスペース上ならば、右側のワード前まで移動
        block_text = cursor.block().text()
        pos = cursor.positionInBlock()
        try:
            if block_text[pos] == " ":
                cursor.movePosition(QTextCursor.NextWord)
        except:
            pass

        tabsize = self.get_tabspace_size(cursor.positionInBlock())
        cursor.insertText(' ' * tabsize)
        
        
    def indent_shifttab(self, cursor):
        # 1行選択
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.NextWord,
                            QTextCursor.KeepAnchor)

        selected_text = cursor.selectedText()
        cursor.clearSelection()

        if selected_text.startswith(' '):
            # shifttab 操作可
            
            block_text = cursor.block().text()
            pos = cursor.positionInBlock()
            try:
                if block_text[pos] == " ":
                    cursor.movePosition(QTextCursor.NextWord)
            except:
                pass
                    
            tabsize = self.get_tabspace_size(cursor.positionInBlock())

            delete_size = self.tabStop - tabsize
            if pos > 0 and delete_size == 0:
                delete_size = self.tabStop

            for i in range(delete_size):
                cursor.deletePreviousChar()
                        
        
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backtab:
            cursor = self.textCursor()

            if not cursor.hasSelection():
            
                cursor.clearSelection()

                self.indent_shifttab(cursor)
                
                    
            else:
                # selection があるとき
                epos = cursor.anchor()
                spos = cursor.position()
                if epos < spos:
                    epos, spos = spos, epos
                    
                cursor.clearSelection()
                cursor.setPosition(spos)
                cursor.setPosition(epos, QTextCursor.KeepAnchor)
                selected_text = cursor.selectedText().replace(u'\u2029', '\n')
                cursor.clearSelection()

                countln = selected_text.count('\n')
                #print(countln)
                
                cursor.setPosition(spos)
                for i in range(countln+1):
                    self.indent_shifttab(cursor)
                    cursor.movePosition(QTextCursor.NextBlock)

                
                

        elif event.key() == Qt.Key_Return:

            if event.modifiers() & Qt.ControlModifier:
                super().keyPressEvent(event)
                return

                        
            cursor = self.textCursor()
            
            cursor.clearSelection()

            # 行頭から現在場所までを選択
            start_pos = cursor.position()
            cursor.movePosition(QTextCursor.StartOfBlock,
                                    QTextCursor.KeepAnchor)
            selected_left_text = cursor.selectedText()
            cursor.clearSelection()

            indent_chars = ""            
            for char in list(selected_left_text):
                if char == "":
                    break

                if char != " ":
                    break

                indent_chars += char

                

            if not selected_left_text.endswith("begin"):
                # begin 以外では、行の先頭のインデントを受け継いで終わり
                cursor.setPosition(start_pos)
                cursor.insertBlock()
                cursor.insertText(indent_chars)
                return
                


            # 同レベルの end までを取得
            cursor.setPosition(start_pos)
            cursor.movePosition(QTextCursor.End,
                                    QTextCursor.KeepAnchor)
            selected_text = cursor.selectedText().replace(u'\u2029', '\n')

            if selected_left_text.startswith("procedure"):
                # procedure 行の begin は、indent 0 として探す
                pattern = "\\nend\\b"
                indent_depth = 0
            else:
                pattern = indent_chars + "end\\b"
                indent_depth = len(indent_chars)
                
                
            rx = QRegExp(pattern)
            pos = rx.indexIn(selected_text, 0)

            if pos == -1:
                # 同レベルが出現しないなら、ペア end が必要
                end_required = True
                
            else:
                # 同レベルが出現するので、ペア end はいらない。
                # ただし、そこまでに begin が同レベル以下で出現していれば
                # ペアの end は必要。
                rx1 = QRegExp('\\b(begin|procedure)\\b')
                rx2 = QRegExp('(\\b(if|while|else)\\b).*\\bbegin\\b')
                #rx2 = QRegExp('\\bprocedure\\b')

                end_required = False
                
                selected_text = selected_text[:pos]
                for line in selected_text.split('\n'):
                    pos = rx1.indexIn(line, 0)
                    #print("line:[%s] pos=%d" % (line, pos))
                    if pos != -1 and pos <= indent_depth:
                        end_required = True
                        break
                    
                    pos = rx2.indexIn(line, 0)
                    #print("line:[%s] pos=%d" % (line, pos))
                    if pos != -1 and pos <= indent_depth:
                        end_required = True
                        break
                    

                    
            if not end_required:
                # 不要なら、単なるインデント
                cursor.setPosition(start_pos)
                cursor.insertBlock()
                cursor.insertText(indent_chars + ' ' * self.tabStop)
                return
                                

            # ペア end を挿入
            cursor.setPosition(start_pos)
            cursor.movePosition(QTextCursor.EndOfBlock,
                                    QTextCursor.KeepAnchor)
            selected_right_text = cursor.selectedText()
            
            #cursor.clearSelection() せずに、選択領域を上書き
            text = '\n'
            text+= selected_right_text + '\n'
            text+= indent_chars + "end"
            cursor.insertText(text)

            cursor.setPosition(start_pos)
            cursor.movePosition(QTextCursor.NextBlock)
            self.setTextCursor(cursor)            
            cursor.insertText(indent_chars + ' ' * self.tabStop)
                            
            return
            
            

        elif event.key() == Qt.Key_Tab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                epos = cursor.anchor()
                spos = cursor.position()
                if epos < spos:
                    epos, spos = spos, epos

                    
                cursor.clearSelection()
                cursor.setPosition(spos)
                cursor.setPosition(epos, QTextCursor.KeepAnchor)
                selected_text = cursor.selectedText().replace(u'\u2029', '\n')
                cursor.clearSelection()

                countln = selected_text.count('\n')
                
                cursor.setPosition(spos)

                for i in range(countln+1):
                    cursor.movePosition(QTextCursor.StartOfLine)
                    self.indent_tab(cursor)                    
                    cursor.movePosition(QTextCursor.NextBlock)

                    
                    
            else:
                self.indent_tab(cursor)
                #super().keyPressEvent(event)

                
        else:
            closing_char = self.bracket_list.get(event.text())
            if closing_char:
                char_cursor = self.textCursor()
                char_position = char_cursor.position()

                char_cursor.movePosition(QTextCursor.EndOfBlock,
                                         QTextCursor.KeepAnchor)
                selected_text = char_cursor.selectedText()
                if selected_text == "":
                    self.insertPlainText(closing_char)
                    char_cursor.setPosition(char_position)
                    self.setTextCursor(char_cursor)

                    
            super().keyPressEvent(event)
        
        
    def lineNumberAreaWidth(self):
        """
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        """
        space = 10 + self.fontMetrics().width('9') * 3
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





    def set_find_word(self, keyword, addpos=0, initflag=True):
        # addpos
        # 1 or -1: self.keypos += addpos
        #
        # initflag:
        # True : 初期状態（self.keypos = 0）にし、カレントへ移動しない
        # False: self.keypos に従い、カレントも移動
        
        if keyword:
            self.findWordPattern = QRegExp(keyword)
        else:
            self.findWordPattern = None
            self.keypos = 0

            self.setExtraSelections([])
            cursor = self.textCursor()
            cursor.clearSelection()
            self.setTextCursor(cursor)                
            
            return

        if initflag:
            self.keypos = 0
        else:
            if addpos > 0:
                self.keypos += 1
            else:
                self.keypos -= 1
                if self.keypos < 0:
                    # -1 は最後の該当箇所という意味で使う
                    self.keypos = -1


        # for keyword finding
        self.findWordFormat = QTextCharFormat()
        self.findWordFormat.setBackground(QColor(Qt.yellow).lighter(130))
        
        self.findWordPosFormat = QTextCharFormat()
        self.findWordPosFormat.setBackground(QColor(Qt.darkYellow).lighter(130))
        
        

        # Find Keyword
        if self.findWordPattern:
            extraSelections = []

            # match した場所の記憶用
            matched_positions = []

            text = self.toPlainText()

            expression = self.findWordPattern
            
            index = expression.indexIn(text)
            length = expression.matchedLength()
            while index >= 0:
                selection = QTextEdit.ExtraSelection()
                selection.format.setBackground(QColor(Qt.yellow))
                selection.cursor = self.textCursor()
                selection.cursor.setPosition(index)
                selection.cursor.movePosition(QTextCursor.NextCharacter,
                                              QTextCursor.KeepAnchor, length)
                
                matched_positions += [index]
                extraSelections += [selection]
                
                index = expression.indexIn(text, index + length)


            if matched_positions == []:
                return

            if initflag:
                self.setExtraSelections(extraSelections)
                return

            
            # 現在 match 場所のハイライト処理
            try:
                if self.keypos >= 0:
                    index = matched_positions[self.keypos]
                    
                else:
                    # 最後に match した場所
                    self.keypos = len(matched_positions)-1
                    index = matched_positions[self.keypos]

            except:
                self.keypos = 0
                index = matched_positions[self.keypos]

                
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(Qt.darkYellow))
            selection.cursor = self.textCursor()
            selection.cursor.setPosition(index)
            selection.cursor.movePosition(QTextCursor.NextCharacter,
                                          QTextCursor.KeepAnchor, length)
            self.setTextCursor(selection.cursor)                

            extraSelections += [selection]
                

            self.setExtraSelections(extraSelections)
            
        

    def clearHighlightLine(self):

        if self.hlineno > 0:
            # 緑色背景になっている行へカーソルを移動させる
            cursor = QTextCursor(self.document().findBlockByNumber(self.hlineno -1))
            #cursor = self.textCursor()
            #cursor.movePosition(QTextCursor.Start)
            #cursor.movePosition(QTextCursor.NextBlock,
            #                    QTextCursor.MoveAnchor,
            #                    self.hlineno - 1)

            self.setTextCursor(cursor)                
            self.hlineno = 0
            self.line_tracer.set_lineno(0)
            
        self.highlightLine()

        
        
    def setHighlightLineno(self, lineno, trail=True):
        if trail != self.line_tracer.trail:
            # line tracer がトレースしていないかもしれないので、現在地をセット
            self.line_tracer.set_lineno(self.hlineno, force=True)

        
        self.line_tracer.set_lineno(lineno, trail)
        
        self.hlineno = lineno
        self.highlightLine()
        

        
            
    def highlightLine(self):

        if self.hlineno == 0:
            self.setExtraSelections([])
            
        else:
            extraSelections = []



            # line tracer 用
            if self.line_tracer.get_lineno() > 0:
                self.line_tracer.update()
                
                selection_lt = QTextEdit.ExtraSelection()

                lineColor_lt = QColor(Qt.green).lighter(160)
                alpha = self.line_tracer.alpha
                lineColor_lt.setAlpha(alpha)
                
                selection_lt.format.setBackground(lineColor_lt)
                selection_lt.format.setProperty(QTextFormat.FullWidthSelection,
                                             True)
                selection_lt.cursor = self.textCursor()

                hlineno_lt = self.line_tracer.get_lineno()
                selection_lt.cursor = QTextCursor(self.document().findBlockByNumber(hlineno_lt -1))
                #self.setTextCursor(selection_lt.cursor)
                #selection_lt.cursor.clearSelection()
                extraSelections.append(selection_lt)

                if not self.line_tracer.is_finished():
                    self.timer_lt.singleShot(50, self.highlightLine)
                else:
                    self.setTextCursor(selection_lt.cursor)


            # hightline 用
            selection = QTextEdit.ExtraSelection()
            
            lineColor = QColor(Qt.green).lighter(160)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection,
                                         True)
            selection.cursor = self.textCursor()

            selection.cursor = QTextCursor(self.document().findBlockByNumber(self.hlineno -1))
            if self.line_tracer.get_lineno() == 0:
                self.setTextCursor(selection.cursor)
                
            selection.cursor.clearSelection()
            extraSelections.append(selection)


                    
            self.setExtraSelections(extraSelections)
                

            return
            


    def highlightCurrentLine(self):
        self.lineNumberArea.repaint()
        

    def field_clicked(self):
        self.set_find_word("")
        

    def lineNumberAreaPaintEvent(self, event):

        cursor = self.textCursor()
        current_lineno = cursor.block().blockNumber() + 1
        
        
        painter = QPainter(self.lineNumberArea)
        painter.setFont(self.font())        
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

                if number == str(current_lineno):
                    painter.setPen(Qt.black)
                else:
                    painter.setPen(Qt.darkGray)

                painter.drawText(0, top,
                                 self.lineNumberArea.width()-3, height,
                                 Qt.AlignRight, number)
                
                

                
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
    
