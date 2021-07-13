# -*- coding:utf-8 -*-

from Evaluator import Evaluator
from PySide2.QtCore import (QThread, QMutex, Signal, QMutexLocker,
                            QCoreApplication)


class MyThread(QThread):
    # Create signals 
    stopped_value = Signal(bool)
    message_value = Signal((str,bool))

    
    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self.stopped = False
        self.mutex = QMutex()
        self.evaluator = Evaluator(GUI=True,
                                   callback=lambda x,y:self.emit_message(x,y))
        
        # ------------------------------------
        # public
        # ------------------------------------
        # onestep 実行フラグ
        self.oneStep = False

        # 実行状態用
        self.evaluatorInfo = None

        

    def setup(self, sentences, pre_env=[]):
        if sentences == "":
            self.evaluatorInfo = {'noerror': False,
                                  'lineno': 0}
        else:
            self.stopped = True
            self.sentences = sentences
            self.evaluatorInfo = self.evaluator.setup(sentences, pre_env)

        return self.evaluatorInfo

    
    def set_env(self, env):
        self.evaluator.set_env(env)

        
    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

        self.stopped_value.emit(self.stopped)

            
    def restart(self):
        with QMutexLocker(self.mutex):
            self.stopped = False
            

    def emit_message(self, mes, error=False):
        # processEvents は、スレッド内で行い、MainWindows に処理を渡す
        # このようにしないと、バッファが溜まってしまう？、らしい？
        QThread.msleep(1)
        self.message_value.emit(mes, error)
        QCoreApplication.processEvents()  

        
    def run(self):
        # evaluation 結果に従って、メンバ変数の self.evaluatorInfo を書き換える        
        # self.evaluatorInfo = None 

        if self.stopped:
            self.restart()
            
            if self.oneStep:
                onestepInfo = self.evaluator.eval_onestep()
                self.evaluatorInfo = onestepInfo
            else:
                self.evaluatorInfo = self.evaluator.eval_all()

            self.stop()

        else:        
            self.evaluatorInfo = {'lineno': 0,
                                  'env': {},
                                  'pretty_env': {},
                                  'empty': True}
            


