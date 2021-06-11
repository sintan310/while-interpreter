#-*- coding:utf-8 -*-
# -----------------------------------------------------------------------------
# evaluator.py
#
# An interpreter of while programs.
# 27 May 2021.
#
# Copyright (c) 2021 Shinya Sato
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php
#
# This source is an extension of the following source code:
#
# calc.py
# by David M. Beazley
#
# A simple calculator with variables -- all in one file.
# http://www.dabeaz.com/ply/ply.html
# -----------------------------------------------------------------------------

import copy


class Node:
    def __init__(self, type, leaf=None, children=None, lineno=0):
        """
        Node(type, leaf, children)

         type には "name"、"while" などの識別子
         leaf には int や string などの値
         children には複数 node のための  NodeList （while や if などで使う）
        """
        self.type = type
        
        if children:
            self.children = children
        else:
            self.children = []
            
        self.leaf = leaf
        self.lineno = lineno

    def print(self):            
        print("lineno=%d type=%s leaf=%s" % (self.lineno,self.type, self.leaf))

        
    def toStr(self, aNode=None):

        if aNode == None:
            aNode = self
            
        if aNode.type == "name":
            return aNode.leaf

        elif aNode.type == "number":
            return "%d" % aNode.leaf
        
        elif aNode.type == "binop":
            return "%s%s%s" % (self.toStr(aNode.children[0]),
                               aNode.leaf,
                               self.toStr(aNode.children[1]))

        elif aNode.type == "array_element":
            return "array_element(%s,%s)" % (self.toStr(aNode.children[0]),
                                            self.toStr(aNode.children[1]))

        elif aNode.type == "array_subst":
            return "array_subst(%s,%s,%s)" % (self.toStr(aNode.children[0]),
                                              self.toStr(aNode.children[1]),
                                              self.toStr(aNode.children[2]))

        elif aNode.type == "multi":
            retval = ""
            for anode in aNode.children:
                retval += self.toStr(anode) + " "
                
            return "begin %s end" % (retval)

            

GUI_mode = False
Callback = None

def myprint(mes):
    global GUI_mode, Callback
    
    if GUI_mode:
        Callback(mes)
    else:
        print(mes)
            



# reserved（予約語）
reserved = {
    'print' : 'PRINT',
    'begin': 'BEGIN',
    'end': 'END',
    'while': 'WHILE',
    'do': 'DO',
    'div': 'DIVIDE',
    'mod': 'MOD',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'procedure': 'PROCEDURE',
}

# tokens
tokens = [
    'NAME','NUMBER',
    'PLUS','MINUS','TIMES', 'SEMICOLON', 'COMMA', 'COLON',
    'LPAREN','RPAREN', 'SUBST', 'INC', 'DEC',
    'NE', 'EQ', 'GE', 'GT', 'LE', 'LT',
    'ARRAY_L', 'ARRAY_R',
    'CSTR',
]

tokens += list(reserved.values())


# Tokens

t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_SEMICOLON = r';'
t_COLON = r':'
t_COMMA = r','
t_SUBST = r':='
t_INC = r'\+\+'
t_DEC = r'--'
t_NE = r'!='
t_EQ = r'='
t_GE = r'>='
t_GT = r'>'
t_LE = r'<='
t_LT = r'<'
t_ARRAY_L = r'\['
t_ARRAY_R = r'\]'

#t_NAME    = r'[a-zA-Z_][a-zA-Z0-9_]*'



def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value,'NAME')    # Check for reserved words
    return t    

def t_NUMBER(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        myprint("整数値 '%d' が規定より大きすぎます。" % t.value)
        
        t.value = 0
    return t


# C string
def t_CSTR(t):
   r'\"([^\\\n]|(\\.))*?\"'
   return t


# Ignored characters
t_ignore = " \t"

def t_COMMENT(t):
    r'\#.*'
    pass
    # No return value. Token discarded

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    
def t_error(t):
    myprint("受け入れられない文字がありました： '%s'" % t.value[0])
    t.lexer.skip(1)
    

# Build the lexer
import ply.lex as lex
lexer = lex.lex()
    
# Parsing rules

precedence = (
    ('nonassoc','NE','EQ', 'GE','GT','LE','LT'),
    ('nonassoc','THEN'),
    ('nonassoc','ELSE'),    
    ('left', 'AND','OR'),
    ('left', 'PLUS','MINUS'),
    ('left', 'TIMES','DIVIDE', 'MOD'),
    ('right', 'UMINUS'),
#    ('nonassoc', 'IFX','ELSE'),
    )

start = 'statement'
def p_statement(t):
    '''statement : NAME SUBST expression
                 | NAME array_nest SUBST expression
                 | NAME INC
                 | NAME DEC
                 | PRINT print_param
                 | WHILE expression DO
                 | WHILE expression DO statement
                 | IF expression THEN %prec THEN
                 | IF expression THEN ELSE
                 | IF expression THEN ELSE statement
                 | IF expression THEN statement
                 | IF expression THEN statement ELSE
                 | IF expression THEN statement ELSE statement
                 | PROCEDURE NAME SUBST NAME procedure_argument COLON
                 | PROCEDURE NAME SUBST NAME procedure_argument COLON statement
                 | BEGIN END
                 | BEGIN statements END
    '''
    #            | expression
    if len(t) >= 3:
        if t[2] == ':=':
            # NAME SUBST expression
            t[0] = Node("binop", ":=", [Node("name",t[1]),t[3]],
                        lineno=t.lineno(2))
                
        elif t[1] == 'begin':
            if t[2] == 'end':
                # BEGIN END                
                t[0] = Node("nop", lineno=t.lineno(1))
            else:
                # BEGIN statements END
                dummy_line = Node("nop", lineno=t.lineno(3))
                t[0] = Node("multi", "", t[2] + [dummy_line], lineno=t.lineno(1))
            
        elif len(t) >= 4 and t[3] == ':=' and (t[1] != 'procedure'):
            # NAME array_nest SUBST expression
            t[0] = Node("array_subst", "",
                        [Node("name",t[1]), t[2], t[4]],
                        lineno=t.lineno(3))

                
        elif t[2] == '++':
            # NAME INC
            t[0] = Node('unarrayop', '++', [Node("name",t[1])],
                        lineno=t.lineno(2))
            
        elif t[2] == '--':
            t[0] = Node('unarrayop', '--', [Node("name",t[1])],
                        lineno=t.lineno(2))
            
        elif t[1] == 'print':
            # PRINT print_param
            t[0] = Node("print", "", t[2],
                        lineno=t.lineno(1))
            
        elif t[1] == 'while':
            if len(t) == 5:
                # WHILE expression DO statement
                t[0] = Node("while", "", [t[2], t[4]],
                            lineno=t.lineno(1))
            else:
                # WHILE expression DO
                t[0] = Node("while", "", [t[2], Node("nop")],
                            lineno=t.lineno(1))
                
        elif t[1] == 'if':
            if len(t) == 7:
                # IF expression THEN statement ELSE statement
                t[0] = Node("if", "with-else", [t[2], t[4], t[6]],
                            lineno=t.lineno(1))
                
            elif len(t) == 6:
                if t[4] == 'else':
                    # IF expression THEN ELSE statement
                    t[0] = Node("if", "with-else", [t[2], Node("nop"), t[5]],
                                lineno=t.lineno(1))
                else:
                    # IF expression THEN statement ELSE                    
                    t[0] = Node("if", "with-else", [t[2], t[4], Node("nop")],
                                lineno=t.lineno(1))
                    
            elif len(t) == 5:
                if t[4] == 'else':
                    # IF expression THEN ELSE
                    t[0] = Node("if", "with-else",
                                [t[2], Node("nop"), Node("nop")],
                                lineno=t.lineno(1))
                else:
                    # IF expression THEN statement                    
                    t[0] = Node("if", "without-else", [t[2], t[4]],
                                lineno=t.lineno(1))           
            else:
                # IF expression THEN
                t[0] = Node("if", "without-else", [t[2], Node("nop")],
                            lineno=t.lineno(1))
                
        elif t[1] == 'procedure':
            if len(t) == 8:
                # PROCEDURE NAME SUBST NAME procedure_argument COLON statement
                t[0] = Node("procedure", t[4], [t[2], t[5], t[7]],
                            lineno=t.lineno(1))
            else:
                # PROCEDURE NAME SUBST NAME procedure_argument COLON
                t[0] = Node("procedure", t[4], [t[2], t[5], Node("nop")],
                            lineno=t.lineno(1))

    #elif len(t) == 2:
    #    t[0] = Node("evalexp", "", [t[1]], lineno=t.lineno(1))


        
def p_statements(t):
    '''statements : SEMICOLON
                  | statement 
                  | statements SEMICOLON
                  | statements SEMICOLON statement

    '''
    if t[1] == ';':
        t[0] = [Node("nop")]
    elif len(t) == 2:
        t[0] = [t[1]]
    elif len(t) == 3:
        t[0] = t[1]
    else:
        t[0] = t[1] + [t[3]]

        
        
def p_print_param(t):
    '''print_param : LPAREN RPAREN
                   | LPAREN print_params RPAREN
    '''
    if t[2] == ')':
        t[0] = []
    else:
        t[0] = t[2]

        
def p_print_params(t):
    '''print_params : expression
                    | print_params COMMA expression
    '''
    if len(t) == 2:
        t[0] = [t[1]]
    else:
        t[0] = t[1] + [t[3]]
        
def p_array_nest(t):
    '''array_nest : ARRAY_L expression ARRAY_R
                   | array_nest ARRAY_L expression ARRAY_R
    '''
    if t[3] == ']':
        t[0] = [t[2]]
    else:
        t[0] = t[1] + [t[3]]


        
def p_procedure_argument(t):
    '''procedure_argument : LPAREN RPAREN
                          | LPAREN procedure_arguments RPAREN
    '''
    if t[2] == ')':
        t[0] = []
    else:
        t[0] = t[2]

        
def p_procedure_arguments(t):
    '''procedure_arguments : NAME
                           | procedure_arguments COMMA NAME
    '''
    if len(t) == 2:
        t[0] = [t[1]]
    else:
        t[0] = t[1] + [t[3]]


def p_expression_binop(t):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression MOD expression
                  | expression NE expression
                  | expression EQ expression
                  | expression GE expression
                  | expression GT expression
                  | expression LE expression
                  | expression LT expression
                  | expression AND expression
                  | expression OR expression
    '''
    t[0] = Node("binop", t[2], [t[1],t[3]])




def p_expression_call(t):
    'expression : NAME print_param'
    t[0] = Node("call", t[1], t[2], lineno=t.lineno(1))

    
def p_expression_uminus(t):
    'expression : MINUS expression %prec UMINUS'
    #t[0] = -t[2]
    t[0] = Node("singleop", "-", [t[1]])

    
def p_expression_not(t):
    'expression : NOT LPAREN expression RPAREN'
    t[0] = Node("singleop", "not", [t[3]])
    
    
def p_expression_group(t):
    'expression : LPAREN expression RPAREN'
    t[0] = t[2]

def p_expression_number(t):
    'expression : NUMBER'
    t[0] = Node("number", t[1])


def p_expression_array(t):
    '''expression : ARRAY_L ARRAY_R
                  | ARRAY_L print_params ARRAY_R
    '''
    if t[2] == ']':
        t[0] = Node("array", '', [])
    else:
        t[0] = Node("array", '', t[2])


def p_expression_array_element(t):
    '''expression : NAME array_nest
    '''

    t[0] = Node("array_element", "",
                [Node("name",t[1]), t[2]])

    
def p_expression_ccode_string(t):
    '''expression : CSTR
    '''
    t[0] = Node("string", t[1], [])
        
    
    
def p_expression_name(t):
    'expression : NAME'
    t[0] = Node("name", t[1], [])



    
"""        
def p_multi_statement_error(t):
    '''multi_statement : BEGIN error END
    '''
    print("Syntax error in multi statement. Bad expression")
"""

Error_arised = False
def p_error(t):
    #'statement : PRINT error SEMI'
    #print("文法エラー. ")
    #print(t)
    
    global Error_alised, My_lineno
    Error_alised = True
    if not(t is None):
        myprint("%d行目: 文法エラー '%s'\n" % (t.lineno, t.value))

    else:
        myprint("%d行目: 文が途中で終了しています\n" % (My_lineno-1))


import ply.yacc as yacc
#parser = yacc.yacc(write_tables=False, debug=False)
parser = yacc.yacc(debug=True)

# ----------------------------------------------------------------
My_lineno = 1


class Stack:
    def __init__(self, name=""):
        self.stack = []
        self.name = name
        
    def clear(self):
        self.stack = []

    def print(self):
        for elem in self.stack:
            print(elem)
        
    def is_empty(self):
        if len(self.stack) == 0:
            return True
        else:
            return False
    
    def push(self, elem):
        #if self.name != "task":
        #    print("---\npush " + self.name + "(%d)" % elem)
            
        self.stack.append(elem)
        
        #if self.name != "task":
        #    print(self.stack)

    def pop(self):
        val = self.stack.pop()
        
        #if self.name != "task":
        #    print(("---\npop %d from " % val) + self.name)
        #    print(self.stack)            
            
        return val
        

class Evaluator:
    def __init__(self, GUI, callback=None):

        # dictionary of global names and procedures
        self.procedures = {}

        # stacks for tasks
        self.task = Stack("task")
        self.value = Stack("value")
        self.args = Stack("args")

        # callback for print
        global Callback, GUI_mode
        Callback = callback
        GUI_mode = GUI

        
        # -------------------------------------------------
        # public
        # -------------------------------------------------
        # line number in one-step evaluation (0 means not running)
        self.onestep_lineno = 0
   
    
    def pretty_print_value(self, value):
        result = ""
        if type(value) is int:
            result = "{}".format(value)
            return result

        elif type(value) is str:
            result = "{}".format(value)
            return result

        elif type(value) is dict:
            array_value_list = []
            value_key = value.keys()

            for i in range(0, max(value_key) + 1):
                if i in value_key:
                    retstr = self.pretty_print_value(value[i])
                else:
                    retstr = "0"

                array_value_list += [retstr]

            result = "[{}]".format(", ".join(array_value_list))
            return result
        

    def pretty_env(self, env):
        pretty_env = {}
        for key, value in env.items():
            pretty_env[key] = self.pretty_print_value(value)

        return pretty_env
        
        
    def eval_sentence(self, aNode, cnt, env):
        global GUI_mode, My_lineno
        
        if aNode.type == 'binop':
            if aNode.leaf == ":=":
                if cnt==1:
                    self.task.push((aNode,2, env))
                    self.task.push((Node('args'),2,env))
                    self.eval_exp(aNode.children[1], env)
                    
                elif cnt==2:
                    target_value = self.args.pop()
                    var_name = aNode.children[0].leaf
                    
                    if type(target_value) is dict:
                        # dict（array） の場合、別のオブジェクトとして代入
                        # （もとのオブジェクトに影響が及んでしまう）
                        env[var_name] = copy.deepcopy(target_value)
                    else:
                        env[var_name] = target_value                    
                    return
            else:
                if cnt==2:
                    #print(aNode.toStr())
                    
                    val1 = self.args.pop()            
                    val0 = self.args.pop()

                    if aNode.leaf == "+":
                        if type(val0) is int and type(val1) is int:
                            self.value.push(val0+val1)
                            return

                        else:
                            # 文字列との連結処理
                            if type(val0) is str:
                                val0 = val0[1:-1]
                            else:
                                val0 = str(val0)

                            if type(val1) is str:
                                val1 = val1[1:-1]
                            else:
                                val1 = str(val1)

                            self.value.push('"' + str(val0) + str(val1) + '"')
                            return

                    elif aNode.leaf == "-":
                        
                        result = val0-val1
                        if result < 0: result=0
                        self.value.push(result)
                        return

                    elif aNode.leaf == "*":
                        self.value.push(val0*val1)
                        return

                    elif aNode.leaf == "div":
                        self.value.push(int(val0/val1))
                        return
                    elif aNode.leaf == "mod":
                        self.value.push(val0%val1)
                        return

                    elif aNode.leaf == "!=":
                        if val0 != val1:
                            self.value.push(1)
                            return
                        else:
                            self.value.push(0)
                            return

                    elif aNode.leaf == "=":
                        if val0 == val1:
                            self.value.push(1)
                            return 
                        else:
                            self.value.push(0)
                            return

                    elif aNode.leaf == ">=":
                        if val0 >= val1:
                            self.value.push(1)
                            return
                        else:
                            self.value.push(0)
                            return

                    elif aNode.leaf == ">":
                        if val0 > val1:
                            self.value.push(1)
                            return
                        else:
                            self.value.push(0)
                            return

                    elif aNode.leaf == "<=":
                        if val0 <= val1:
                            self.value.push(1)
                            return
                        else:
                            self.value.push(0)
                            return

                    elif aNode.leaf == "<":
                        if val0 < val1:
                            self.value.push(1)
                            return
                        else:
                            self.value.push(0)
                            return

                    elif aNode.leaf == "and":
                        if (val0 ==1) and (val1 == 1):
                            self.value.push(1)
                            return
                        else:
                            self.value.push(0)
                            return

                    elif aNode.leaf == "or":
                        if (val0 ==1) or (val1 == 1):
                            self.value.push(1)
                            return
                        else:
                            self.value.push(0)
                            return

                
            return
        
        elif aNode.type == 'remove_callparams':
            remove_target = [x for x in env.keys() if x not in aNode.children]
            
            for param in remove_target:
                env.pop(param, None)
                
            return
            
        elif aNode.type == 'call':
            if cnt == 2:
                # procedure call の後始末（環境を整える）
                procedure_retname = aNode.children[0]
                procedure_params = aNode.children[1]
                call_params = aNode.children[2]
                orig_env = aNode.children[3]

                for procedure_aparam, call_aparam in zip(procedure_params,
                                                     call_params):
                    if call_aparam.type == "name":
                        # 変数名で呼び出している時には
                        # procedure 内で更新されるものとする
                        orig_env[call_aparam.leaf] = env[procedure_aparam]
                
                try:
                    retval = env[procedure_retname]
                except:
                    # procedure 内で retval が使われていないときは 0 を返すとする
                    retval = 0
                    
                self.value.push(retval)
                

        elif aNode.type == 'array_subst':
            if cnt == 1:
                self.task.push((aNode, 2, env))
                
                exp = aNode.children[2]
                self.eval_exp(exp, env) # expression
                
                indexes = aNode.children[1]
                for index in indexes:
                    self.task.push((Node('args'),2,env))
                    self.eval_exp(index, env) # index

                    
                return

            elif cnt == 2:
                indexes = []
                indexes_len = len(aNode.children[1])
               
                for i in range(indexes_len):
                    val = self.args.pop()
                    indexes += [val]

                # 最後までと、最後に分離
                (indexes, last_index) = (indexes[:-1], indexes[-1])

                value = self.value.pop()
                                
                var_name = aNode.children[0].leaf

                # 環境に存在しないときには 空dict を作成しておく
                if var_name not in env.keys():
                    env[var_name] = {}

                target = env[var_name]                
                for i in indexes:
                    if type(target) is dict and \
                       i in target.keys() and \
                       type(target[i]) is dict:
                            pass
                    else:
                        target[i] = {}

                    target = target[i]

                target[last_index] = value
                

                return
            
        elif aNode.type == 'array_element':
            if cnt == 2:
                indexes = []
                indexes_len = len(aNode.children[1])
               
                for i in range(indexes_len):
                    val = self.args.pop()
                    indexes += [val]

                # 最後までと、最後に分離
                (indexes, last_index) = (indexes[:-1], indexes[-1])
                                
                var_name = aNode.children[0].leaf

                # 環境に存在しないときには 0 を返す
                if var_name not in env.keys():
                    self.value.push(0)
                    return

                target = env[var_name]                
                for i in indexes:
                    if type(target) is dict and \
                       i in target.keys() and \
                       type(target[i]) is dict:
                            pass
                    else:
                        self.value.push(0)
                        return

                    target = target[i]

                try:    
                    self.value.push(target[last_index])
                except:
                    self.value.push(0)                    
                return
            

        elif aNode.type == 'unarrayop':
            if aNode.leaf == '++':
                var_name = aNode.children[0].leaf
                try:
                    env[var_name] += 1
                except KeyError as e:
                    env[var_name] = 1
                return

            elif aNode.leaf == '--':
                var_name = aNode.children[0].leaf
                if env[var_name] > 0:
                    try:
                        env[var_name] -= 1
                    except KeyError as e:
                        env[var_name] = 0
                        
                else:
                    env[var_name] = 0
                return

            
        elif aNode.type == 'print':

            if cnt == 1:
                self.task.push((aNode, 2, env))
                for anexp in aNode.children:
                    self.task.push((Node('args'),2,env))
                    self.eval_exp(anexp, env)

                return

            elif cnt == 2:
                result_vals = []
                for i in range(len(aNode.children)):
                    aval = self.args.pop()
                    result_vals += [self.pretty_print_value(aval)]
                
                    
                if GUI_mode == False:
                    lineno_indent = " " * (len(str(My_lineno-1)) + 5)
                    print(lineno_indent + " ".join(result_vals) + "\n")
                else:
                    myprint(" ".join(result_vals))

                return


        #elif aNode.type == 'evalexp':
        #    # print ではなく、単なる一つの式を評価するだけ
        #    anexp = aNode.children[0]
        #    aval = self.eval_exp(anexp, env)
        #    return


        elif aNode.type == 'while':
            if cnt==1:
                self.task.push((aNode, 2, env))
                self.eval_exp(aNode.children[0], env)
                return
            
            elif cnt==2:
                aval = self.value.pop()
            
                if aval == 1:
                    self.task.push((aNode, 1, env))
                    self.task.push((aNode.children[1], 1, env))

                return

        
        elif aNode.type == 'if':
            if cnt==1:
                self.task.push((aNode, 2, env))
                self.eval_exp(aNode.children[0], env)
                return
            
            elif cnt==2:
                aval = self.value.pop()
            
                if aval == 1:            
                    self.task.push((aNode.children[1], 1, env))
                else:
                    if aNode.leaf == "with-else":
                        self.task.push((aNode.children[2], 1, env))
                return

        
        elif aNode.type == 'multi':
            statements = aNode.children
            for statement_node in statements[::-1]:
                self.task.push((statement_node, 1, env))
                
            return

        elif aNode.type == 'procedure':
            self.procedures[aNode.leaf] = aNode.children
            return

        elif aNode.type == 'singleop':
            if cnt == 2:
                val0 = self.args.pop()

                if aNode.leaf == "not":
                    if val0 ==0:
                        self.value.push(1)
                        return
                    else:
                        self.value.push(0)
                        return
                
            return
        
        elif aNode.type == 'array':
            if cnt == 2:
                an_array = {}
                for i in range(len(aNode.children)):
                    aval = self.args.pop()
                    an_array[i] = aval

                self.value.push(an_array)
            
            return

        elif aNode.type == 'args':
            aval = self.value.pop()
            self.args.push(aval)
            return
        
        elif aNode.type == 'array_element':
            if cnt==2:
                here_index = self.value.pop()
                name_str = aNode.children[0].leaf
                if name_str in env:
                    try:
                        target_value = env[name_str][here_index]
                    except KeyError:
                        env[name_str][here_index] = 0
                        target_value = 0

                        print("NameError")
                        print(env[name_str])
                    except TypeError:
                        env[name_str] = {}
                        env[name_str][here_index] = 0
                        target_value = {}

                        print("TypeError")
                        print(env[name_str])
                else:
                    target_value = 0

                self.value.push(target_value)
                return




        
    def eval_exp(self, aNode, env):

        if aNode.type == 'binop':
            self.task.push((aNode, 2, env))
            self.task.push((Node('args'),2,env))
            self.eval_exp(aNode.children[1], env)
            self.task.push((Node('args'),2,env))
            self.eval_exp(aNode.children[0], env)
            return

        elif aNode.type == 'singleop':
            self.task.push((aNode, 2, env))
            self.task.push((Node('args'),2,env))
            self.eval_exp(aNode.children[0], env)
            return
            
        elif aNode.type == 'number':
            self.value.push(aNode.leaf)
            return

        elif aNode.type == 'string':
            self.value.push(aNode.leaf)
            return

        elif aNode.type == 'name':
            if aNode.leaf in env:
                target_value = env[aNode.leaf]
            else:
                target_value = 0
                env[aNode.leaf] = 0

            self.value.push(target_value)
            return

        elif aNode.type == 'array':
            self.task.push((aNode, 2, env))
            for anexp in aNode.children:
                self.task.push((Node('args'),2,env))
                self.eval_exp(anexp, env)

            return

        elif aNode.type == 'array_element':
            self.task.push((aNode, 2, env))

            indexes = aNode.children[1]
            for index in indexes:
                self.task.push((Node('args'),2,env))
                self.eval_exp(index, env) # index
            
            return
        
        
        elif aNode.type == 'call':
            
            procedure_name = aNode.leaf
            
            try:
                # procedure の情報を取得
                procedure_body = self.procedures[procedure_name][2]
                procedure_retname = self.procedures[procedure_name][0]
                procedure_params = self.procedures[procedure_name][1]
            except:
                myprint("Error: Procedure '{}' が定義されていません。".format(procedure_name))

                self.value.push(0)
                return


            # 呼び出し側の情報を取得
            call_params = aNode.children


            procedure_env = copy.deepcopy(env)
            #procedure_env = {}

            tasks = []

            # 環境の procedure_params に呼び出し側の値 call_params を代入する
            for procedure_aparam, call_aparam in zip(procedure_params, call_params):
                aNode = Node("binop", ":=",
                             [Node("name", procedure_aparam), call_aparam])
                tasks += [(aNode, 1, procedure_env)]

            # 本体の実行            
            tasks += [(Node("remove_callparams", "", procedure_params),
                       1, procedure_env)]
            tasks += [(procedure_body, 1, procedure_env)]

            # 後処理（環境を整える）
            tasks += [(Node("call", "",
                            [procedure_retname,
                             procedure_params, call_params, env],
                            lineno=aNode.lineno),
                       2,
                       procedure_env)]

            # 処理をタスクに積む
            for atask in tasks[::-1]:
                self.task.push(atask)
                

            return
        



        

    def valid_occurs(self, aline, keyword):
        if keyword not in aline:
            return False

        key_pos = aline.find(keyword)
        if '#' not in aline:
            return True
        else:
            comment_pos = aline.find('#')
            if comment_pos < key_pos:
                return False

        return True


    def count_keyword(self, aline, keyword):
        if '#' not in aline:
            return aline.count(keyword)

        if keyword not in aline:
            return 0

        comment_pos = aline.find('#')
        valid_str = aline[:(comment_pos -1)]
        return valid_str.count(keyword)


    

    # -------------------------------------------------
    # public 
    # -------------------------------------------------
    def setup(self, s):
        """
        evaluator for GUI mode
        """

        global Error_alised
        global lexer, parser
        global My_lineno
        
        env = {}
        lexer.lineno = 1
        My_lineno = 1
        nest = 0

        self.task.clear()
        self.value.clear()
        self.args.clear()

        
        ss = s.split('\n')

        sentence_list = []
        sentence = ""

        is_in_multi = False
        is_in_procedure = False
        count_multi = 0
        
        for s in ss:

            if s=="":
                sentence += s + "\n"
                continue

            if not s:
                continue

            if s[0] == "#":
                sentence += s + "\n"
                continue

            sentence += s + "\n"

            if self.valid_occurs(s, 'procedure'):
                if not self.valid_occurs(s, 'begin') \
                   and not self.valid_occurs(s, 'end'):
                    is_in_procedure = False
                    sentence_list += [sentence]
                    sentence=""
                    continue
                else:
                    is_in_procedure = True


            if self.valid_occurs(s, 'begin') or \
               self.valid_occurs(s, 'end') or \
               nest>0:

                is_in_multi = True

                nest += self.count_keyword(s, 'begin')
                nest -= self.count_keyword(s, 'end')
                #sentence += "\n"

                if nest != 0:                
                    continue


            # nest が 0 のときには sentence に加える
            if count_multi == 0 and is_in_multi and sentence != "":
                # multi は1つまでにする。procedure の multi はカウントしない。
                sentence_list += [sentence]

                is_in_multi = False

                if is_in_procedure:
                    is_in_procedure = False
                else:
                    count_multi += 1
                    #print("sentence=" + sentence)
                    #print("count_multi=%d" % count_multi)

                sentence = ""


        # 加えられなかった sentence があるときには sentence_list に追加する
        if sentence != "":
            try:
                if self.valid_occurs(sentence_list[-1], "procedure") \
                   and count_multi==0:
                    # 最後が procedure で終わってたら、sentence を追加
                    sentence_list += [sentence]
                else:
                    # そうでないときには sentence を前の文の継続とする
                    sentence_list[-1] += sentence
            except:
                sentence_list += [sentence]


        #print(sentence_list)
        

        error_num = 0
        node_list = []
        for sentence in sentence_list:

            #sentence += "\n"
            countln = self.count_keyword(sentence, "\n")
            My_lineno += countln

            # \n だけならば処理しない
            if countln == len(sentence):
                continue


            
            Error_alised = False
            aNode = parser.parse(sentence)

            if Error_alised:
                error_num += 1

            if Error_alised == False and not(aNode is None):
                if aNode.type == "evalexp":
                    aNode.type = "print"

                node_list += [aNode]

                
        # エラーがある場合にはセットアップ終了
        if error_num >0:
            return False
        
        # はじめに実行される行番号を取得しておく
        if len(node_list) > 0:
            self.onestep_lineno = node_list[0].lineno

        # 逆順にスタックへ積む
        for node in node_list[::-1]:
            self.task.push((node,1,env))

        return True
            

    def eval_onestep(self):
        if self.task.is_empty():
            return {'lineno':0, 'env':{}, 'empty':True}

        #print("---")        
        while True:
            
            (aNode1, cnt1, env1) = self.task.pop()

            #aNode1.print()

            self.eval_sentence(aNode1, cnt1, env1)

            #print(env1)
            
            # 次に実行する lineno の取得
            if not self.task.is_empty():
                (aNode1, cnt1, env1) = self.task.pop()
                
                if self.onestep_lineno != 0:
                    old_lineno = self.onestep_lineno
                    
                self.onestep_lineno = aNode1.lineno
                self.task.push((aNode1, cnt1, env1))
                
            else:
                # empty なら終了
                
                return {'lineno':0,
                        'env':self.pretty_env(env1),
                        'empty':True}

            
            if self.onestep_lineno == 0:
                # lineno が 0 のときは、行番号に依存しない内部処理なので継続して処理する
                continue
            
            elif old_lineno == self.onestep_lineno:
                # 行番号が同じならば継続
                continue
            
            else:
                break

            
        
        return {'lineno':self.onestep_lineno,
                'env':self.pretty_env(env1),
                'empty':self.task.is_empty()}
        

        
        
    def eval_all(self):
        env1 = {}
        
        while not self.task.is_empty():
            (aNode1, cnt1, env1) = self.task.pop()
            # aNode1.print()
            self.eval_sentence(aNode1, cnt1, env1)

    
        return self.pretty_env(env1)
