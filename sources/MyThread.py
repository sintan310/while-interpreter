# -*- coding:utf-8 -*-

from Evaluator import Evaluator
from PySide2.QtCore import (QThread, QMutex, Signal, QMutexLocker,
                            QCoreApplication)


class MyThread(QThread):
    # Create signals 
    stopped_value = Signal(bool)
    message_value = Signal(str)

    
    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self.stopped = False
        self.mutex = QMutex()
        self.evaluator = Evaluator(GUI=True,
                                   callback=self.emit_message)
        
        # ------------------------------------
        # public
        # ------------------------------------
        # onestep 実行フラグ
        self.oneStep = False

        # 実行状態用
        self.evaluatorInfo = None

        

    def setup(self, sentences):
        if sentences == "":
            self.evaluatorInfo = {'noerror': False}
            return 0

        self.stopped = True
        self.sentences = sentences
        valid = self.evaluator.setup(sentences)

        self.evaluatorInfo = {'noerror': valid}

        return self.evaluator.onestep_lineno

            
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
        # evaluation 結果に従って、メンバ変数の self.evaluatorInfo を書き換える
        # self.evaluatorInfo = None
        
        if self.stopped:
            self.restart()
            
            if self.oneStep:
                onestepInfo = self.evaluator.eval_onestep()
                self.evaluatorInfo = {'lineno': onestepInfo['lineno'],
                                 'env': onestepInfo['env'],
                                 'empty': onestepInfo['empty']}
            else:
                env = self.evaluator.eval_all()
                self.evaluatorInfo = {'lineno': 0,
                                 'env': env,
                                 'empty': True}

            self.stop()

        else:        
            self.evaluatorInfo = {'lineno': 0, 'env': {}, 'empty': True}
            


