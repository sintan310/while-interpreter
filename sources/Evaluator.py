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
import re


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

def myprint(mes, error=False):
    global GUI_mode, Callback
    
    if GUI_mode:
        Callback(mes, error)
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

    'len': 'LEN',
    'left': 'LEFT',
    'right': 'RIGHT',
    'mid': 'MID',
    'int': 'INT',
    'str': 'STR',
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
    global Error_alised
    Error_alised = True
    myprint("受け入れられない文字がありました： '%s'" % t.value[0], error=True)
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
#    ('nonassoc', 'IFX','ELSE'),
    )

#start = 'statement'
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
    t[0] = Node("binop", t[2], [t[1],t[3]], lineno=t.lineno(2))


def p_expression_builtin(t):
    '''expression : LEN LPAREN expression RPAREN
                  | LEFT LPAREN expression COMMA expression RPAREN
                  | RIGHT LPAREN expression COMMA expression RPAREN
                  | MID LPAREN expression COMMA expression COMMA expression RPAREN
                  | INT LPAREN expression RPAREN
                  | STR LPAREN expression RPAREN

    '''
    if t[1] == 'len':
        t[0] = Node("builtin", 'len', t[3], lineno=t.lineno(1))
    elif t[1] == 'left':
        t[0] = Node("builtin", 'left', [t[3],t[5]], lineno=t.lineno(1))
    elif t[1] == 'right':
        t[0] = Node("builtin", 'right', [t[3],t[5]], lineno=t.lineno(1))
    elif t[1] == 'mid':
        t[0] = Node("builtin", 'mid', [t[3],t[5],t[7]], lineno=t.lineno(1))
    elif t[1] == 'int':
        t[0] = Node("builtin", 'int', t[3], lineno=t.lineno(1))
    else:
        t[0] = Node("builtin", 'str', t[3], lineno=t.lineno(1))
    

def p_expression_call(t):
    'expression : NAME print_param'
    t[0] = Node("call", t[1], t[2], lineno=t.lineno(1))

    
def p_expression_not(t):
    'expression : NOT LPAREN expression RPAREN'
    t[0] = Node("singleop", "not", [t[3]], lineno=t.lineno(1))
    
    
def p_expression_group(t):
    'expression : LPAREN expression RPAREN'
    t[0] = t[2]

def p_expression_number(t):
    'expression : NUMBER'
    t[0] = Node("number", t[1], lineno=t.lineno(1))


def p_expression_array(t):
    '''expression : ARRAY_L ARRAY_R
                  | ARRAY_L print_params ARRAY_R
    '''
    if t[2] == ']':
        t[0] = Node("array", '', [], lineno=t.lineno(1))
    else:
        t[0] = Node("array", '', t[2], lineno=t.lineno(1))


def p_expression_array_element(t):
    '''expression : NAME array_nest
    '''

    t[0] = Node("array_element", "",
                [Node("name",t[1]), t[2]], lineno=t.lineno(1))

    
def p_expression_ccode_string(t):
    '''expression : CSTR
    '''
    t[0] = Node("string", t[1], [], lineno=t.lineno(1))
    
    
def p_expression_name(t):
    'expression : NAME'
    t[0] = Node("name", t[1], [], lineno=t.lineno(1))
    


    

    
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
        myprint("%d行目: 文法エラー '%s'。\n" % (t.lineno, t.value), error=True)

    else:
        myprint("%d行目: 文が途中で終了しています。\n" % (My_lineno-1), error=True)


import ply.yacc as yacc
parser = yacc.yacc(start='statement', write_tables=False, debug=False)
#parser = yacc.yacc(debug=True)

# ----------------------------------------------------------------
My_lineno = 1

class Task:
    def __init__(self, node, cnt=1):
        self.node = node
        self.cnt = cnt
        

class Stack:
    def __init__(self, name=""):
        self.stack = []
        self.name = name

    def __str__(self):
        return self.name+"(%d)" % len(self.stack)
        
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

    def top(self):
        return self.stack[-1]
    
    def push(self, elem):
        #if self.name != "task":
        #    print("---\npush " + self.name + " " + str(elem))
            
        self.stack.append(elem)
        
        #if self.name != "task":
        #    print(self.stack)

    def pop(self):
        val = self.stack.pop()
        
        #if self.name != "task":
        #    print("---\npop " + str(val) + " from " + self.name)
        #    print(self.stack)            
            
        return val
        

class Evaluator:
    def __init__(self, GUI, callback=None):

        # environment
        self.env = {}
        
        # dictionary of global names and procedures
        self.procedures = {}
        
        # stacks for tasks
        self.task = Stack("task")
        self.values = Stack("value")
        self.dump = Stack("dump")
        self.name_ref = Stack("ref")
        
        # callback for print
        global Callback, GUI_mode
        Callback = callback
        GUI_mode = GUI

        # regexp
        self.reg_procedure = re.compile('\\b%s\\b' % 'procedure', re.I)
        self.reg_begin = re.compile('\\b%s\\b' % 'begin', re.I)
        self.reg_end = re.compile('\\b%s\\b' % 'end', re.I)
        
        
        # -------------------------------------------------
        # public
        # -------------------------------------------------
        # line number in one-step evaluation (0 means not running)
        self.onestep_lineno = 0
   

    def set_env(self, param):
        self.env = param['env']
        try:
            self.task = param['task']
            self.values = param['values']
            self.dump = param['dump']
            self.nameref = param['nameref']
        except:
            pass

        
    def clear_stack(self):        
        self.task.clear()
        self.values.clear()
        self.dump.clear()
        self.name_ref.clear()
        self.env = {}
        self.procedures = {}
        
        
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
            if len(value_key) == 0:
                return "[]"
            
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
        

    def pretty_type(self, val):
        if type(val) is int:
            return "整数値"
        elif type(val) is str:
            return "文字列"
        else:
            return "配列"


    def message_err_expression(self, lineno, val0, val1, operator):
        errmes = "%d行目：「%s %s %s」はできません。"
        errmes = errmes % (lineno,
                           self.pretty_type(val0),
                           operator,
                           self.pretty_type(val1))
        return errmes
    
    
    def eval_sentence(self, task):
        global GUI_mode, My_lineno

        aNode = task.node
        cnt = task.cnt
        
        if aNode.type == 'binop':
            if aNode.leaf == ":=":
                if cnt==1:
                    self.task.push(Task(aNode, cnt=2))
                    self.eval_exp(aNode.children[1])
                    
                elif cnt==2:
                    target_value = self.values.pop()
                    var_name = aNode.children[0].leaf
                    
                    if type(target_value) is dict:
                        # dict（array） の場合、別のオブジェクトとして代入
                        # （もとのオブジェクトに影響が及んでしまう）
                        target_value = copy.deepcopy(target_value)
                        
                    self.env[var_name] = target_value

                    """
                    # refname 処理
                    if not self.name_ref.is_empty():
                        refnames = self.name_ref.top()

                        if var_name in refnames.keys():
                            ref = refnames[var_name]                            
                            stacked_env = self.dump.top()
                            stacked_env[ref] = target_value
                    """
                    
                    return
                
            else:
                if cnt==2:
                    #print(aNode.toStr())
                    
                    val1 = self.values.pop()            
                    val0 = self.values.pop()

                    if aNode.leaf not in ['+', '*', '=', '!=',
                                          '<', '>', '<=', '>=']:
                        if not(type(val0) is int) and not(type(val1) is int):
                        
                            errmes = self.message_err_expression(aNode.lineno,
                                                                 val0, val1,
                                                                 aNode.leaf)
                            myprint(errmes, error=True)
                            self.task.push(Task(Node('critical_error')))
                            return
                        

                    if aNode.leaf == "+":
                        if type(val0) is int and type(val1) is int:
                            result = val0+val1

                        elif type(val0) is str and type(val1) is str:
                            # 文字列との連結処理
                            val0 = val0[1:-1]
                            val1 = val1[1:-1]
                            result = '"' + val0 + val1 + '"'
                            

                        elif type(val0) is dict and type(val1) is dict:
                            result = copy.deepcopy(val0)
                            if len(val0) > 0:
                                max_index = max(val0.keys()) + 1
                            else:
                                max_index = 0
                                
                            for key, value in val1.items():
                                result[max_index + key] = value

                            

                        else:
                            errmes = self.message_err_expression(aNode.lineno,
                                                                 val0, val1,
                                                                 aNode.leaf)
                            myprint(errmes, error=True)
                            self.task.push(Task(Node('critical_error')))
                            return

                        
                    elif aNode.leaf == "-":
                        
                        result = val0-val1
                        if result < 0: result=0
                        
                        
                    elif aNode.leaf == "*":
                        if type(val0) is int and type(val1) is int:
                            result = val0*val1

                        elif type(val0) is str and type(val1) is int:
                            val0 = val0[1:-1]
                            result = '"' + val0 * val1 + '"'
                            
                        else:
                            errmes = self.message_err_expression(aNode.lineno,
                                                                 val0, val1,
                                                                 aNode.leaf)
                            myprint(errmes, error=True)
                            self.task.push(Task(Node('critical_error')))
                            return
                            

                    elif aNode.leaf == "div":
                        result = int(val0/val1)

                    elif aNode.leaf == "mod":
                        result = val0%val1

                    elif aNode.leaf == "!=":
                        if val0 != val1:
                            result = 1

                        else:
                            result = 0

                    elif aNode.leaf == "=":
                        if val0 == val1:
                            self.values.push(1)
                            return 
                        else:
                            self.values.push(0)
                            return

                    elif aNode.leaf == ">=":
                        if (type(val0) is int and type(val1) is int) or \
                           (type(val0) is str and type(val1) is str):
                            if val0 >= val1:
                                result = 1
                            else:
                                result = 0
                        else:
                            errmes = self.message_err_expression(aNode.lineno,
                                                                 val0, val1,
                                                                 aNode.leaf)
                            myprint(errmes, error=True)
                            self.task.push(Task(Node('critical_error')))
                            return


                    elif aNode.leaf == ">":
                        if (type(val0) is int and type(val1) is int) or \
                           (type(val0) is str and type(val1) is str):
                            if val0 > val1:
                                result = 1
                            else:
                                result = 0
                        else:
                            errmes = self.message_err_expression(aNode.lineno,
                                                                 val0, val1,
                                                                 aNode.leaf)
                            myprint(errmes, error=True)
                            self.task.push(Task(Node('critical_error')))
                            return
                                

                    elif aNode.leaf == "<=":
                        if (type(val0) is int and type(val1) is int) or \
                           (type(val0) is str and type(val1) is str):
                            if val0 <= val1:
                                result = 1
                            else:
                                result = 0
                        else:
                            errmes = self.message_err_expression(aNode.lineno,
                                                                 val0, val1,
                                                                 aNode.leaf)
                            myprint(errmes, error=True)
                            self.task.push(Task(Node('critical_error')))
                            return
                            

                    elif aNode.leaf == "<":
                        if (type(val0) is int and type(val1) is int) or \
                           (type(val0) is str and type(val1) is str):
                            if val0 < val1:
                                result = 1
                            else:
                                result = 0
                        else:
                            errmes = self.message_err_expression(aNode.lineno,
                                                                 val0, val1,
                                                                 aNode.leaf)
                            myprint(errmes, error=True)
                            self.task.push(Task(Node('critical_error')))
                            return
                                

                    elif aNode.leaf == "and":
                        if (val0 ==1) and (val1 == 1):
                            result = 1
                        else:
                            result = 0


                    elif aNode.leaf == "or":
                        if (val0 ==1) or (val1 == 1):
                            result = 1
                        else:
                            result = 0

                    # 結果を value stack へ push
                    try:
                        self.task.push(Task(Node('push', result)))
                    except:
                        print("error: binop " + aNode.leaf)
                        
                    return

            return
        
        elif aNode.type == 'remove_callparams':
            params = aNode.children[0]
            refname = aNode.children[1]
            
            for aparam in params:
                aval = self.values.pop()
                self.env[aparam] = aval

            remove_target = [x for x in self.env.keys() if x not in params]

            # 今の環境から、引数以外の変数情報を消去
            for param in remove_target:
                self.env.pop(param, None)

            self.name_ref.push(refname)
                
            return
            
        elif aNode.type == 'call':
            if cnt == 2:
                # procedure call の後始末（環境を整える）
                procedure_retname = aNode.children[0]
                procedure_params = aNode.children[1]
                call_params = aNode.children[2]
                orig_env = self.dump.pop()

                refnames = self.name_ref.pop()
                for proc_arg, call_name in refnames.items():
                    orig_env[call_name] = self.env[proc_arg]
                
                
                try:
                    retval = self.env[procedure_retname]
                except:
                    # procedure 内で retval が使われていないときは 0 を返すとする
                    retval = 0

                self.env = orig_env
                self.task.push(Task(Node('push', retval)))
                

        elif aNode.type == 'array_subst':
            if cnt == 1:
                self.task.push(Task(aNode, cnt=2))
                
                exp = aNode.children[2]
                self.eval_exp(exp) # expression
                
                indexes = aNode.children[1]
                for index in indexes:
                    self.eval_exp(index) # index

                    
                return

            elif cnt == 2:

                value = self.values.pop()
                
                indexes = []
                indexes_len = len(aNode.children[1])
               
                for i in range(indexes_len):
                    val = self.values.pop()
                    indexes += [val]

                    
                # 最後までと、最後に分離
                (indexes, last_index) = (indexes[:-1], indexes[-1])

                                
                var_name = aNode.children[0].leaf

                # 環境に存在しないときには 空dict を作成しておく
                if var_name not in self.env.keys():
                    self.env[var_name] = {}

                target = self.env[var_name]
                    
                
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
                    val = self.values.pop()
                    indexes += [val]

                # 最後までと、最後に分離
                (indexes, last_index) = (indexes[:-1], indexes[-1])
                                
                var_name = aNode.children[0].leaf

                # 環境に存在しないときには 0 を返す
                if var_name not in self.env.keys():
                    self.task.push(Task(Node('push', 0)))
                    return

                target = self.env[var_name]
                                    
                for i in indexes:
                    if type(target) is dict and \
                       i in target.keys() and \
                       type(target[i]) is dict:
                            pass
                    else:
                        # 巡れないときには 0 を返して終了
                        self.task.push(Task(Node('push', 0)))
                        return

                    target = target[i]

                try:    
                    self.task.push(Task(Node('push', target[last_index])))
                except:
                    # last_index にアクセスできないときは 0 を返して終了
                    self.task.push(Task(Node('push', 0)))

                    
                return
            

        elif aNode.type == 'unarrayop':
            if aNode.leaf == '++':
                var_name = aNode.children[0].leaf
                try:
                    self.env[var_name] += 1
                    
                except KeyError as e:
                    self.env[var_name] = 1


                # refname 処理
                target_value = self.env[var_name]
                if not self.name_ref.is_empty():
                    refnames = self.name_ref.top()

                    ref = refnames.get(var_name)
                    if ref is not None:
                        stacked_env = self.dump.top()
                        stacked_env[ref] = target_value
                    
                return

            elif aNode.leaf == '--':
                var_name = aNode.children[0].leaf
                if self.env[var_name] > 0:
                    try:
                        self.env[var_name] -= 1
                    except KeyError as e:
                        self.env[var_name] = 0
                        
                else:
                    self.env[var_name] = 0

                # refname 処理
                target_value = self.env[var_name]
                if not self.name_ref.is_empty():
                    refnames = self.name_ref.top()

                    ref = refnames.get(var_name)
                    if ref is not None:
                        stacked_env = self.dump.top()
                        stacked_env[ref] = target_value
                    
                return

            
        elif aNode.type == 'print':

            if cnt == 1:
                self.task.push(Task(aNode, cnt=2))
                for anexp in aNode.children:
                    self.eval_exp(anexp)

                return

            elif cnt == 2:
                result_vals = []
                for i in range(len(aNode.children)):
                    aval = self.values.pop()
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
                self.task.push(Task(aNode, cnt=2))
                self.eval_exp(aNode.children[0])
                return
            
            elif cnt==2:
                aval = self.values.pop()
            
                if aval == 1:
                    # while の繰り返し
                    self.task.push(Task(aNode, cnt=1))
                    self.task.push(Task(aNode.children[1], cnt=1))

                return

        
        elif aNode.type == 'if':
            if cnt==1:
                self.task.push(Task(aNode, cnt=2))
                self.eval_exp(aNode.children[0])
                return
            
            elif cnt==2:
                aval = self.values.pop()
            
                if aval == 1:            
                    self.task.push(Task(aNode.children[1], cnt=1))
                else:
                    if aNode.leaf == "with-else":
                        self.task.push(Task(aNode.children[2], cnt=1))
                return

        
        elif aNode.type == 'multi':
            statements = aNode.children
            for statement_node in statements[::-1]:
                self.task.push(Task(statement_node, cnt=1))
                
            return

        elif aNode.type == 'procedure':
            self.procedures[aNode.leaf] = aNode.children
            return

        elif aNode.type == 'singleop':
            if cnt == 2:
                val0 = self.values.pop()

                if aNode.leaf == "not":
                    if val0 ==0:
                        retval = 1
                    else:
                        retval = 0

                    self.task.push(Task(Node('push', retval)))
                    
            return

        elif aNode.type == 'builtin':
            if aNode.leaf == 'len':
                val0 = self.values.pop()

                if type(val0) is str:
                    self.task.push(Task(Node('push', len(val0)-2)))
                    return
                                        
                if type(val0) is not dict:
                    self.task.push(Task(Node('push', 0)))
                    return
                                    
                if val0 == {}:
                    self.task.push(Task(Node('push', 0)))
                    return
                    
                
                value_keys = val0.keys()

                self.task.push(Task(Node('push', max(value_keys)+1)))

                
            elif aNode.leaf == 'left':
                val1 = self.values.pop()            
                string = self.values.pop()
                raw_string = string[1:-1]  # 両側の " を削除

                if not (type(string) is str):
                    self.task.push(Task(Node('push', '""')))
                    return

                try:
                    self.task.push(Task(Node('push',
                                         '"' + raw_string[:val1] + '"')))
                except:
                    self.task.push(Task(Node('push', string)))

            elif aNode.leaf == 'right':
                val1 = self.values.pop()            
                string = self.values.pop()
                raw_string = string[1:-1]  # 両側の " を削除

                if not (type(string) is str):
                    self.task.push(Task(Node('push', '""')))
                    return

                try:
                    self.task.push(Task(Node('push',
                                         '"' + raw_string[-val1:] + '"')))
                except:
                    self.task.push(Task(Node('push', string)))

            elif aNode.leaf == 'mid':
                num = self.values.pop()
                i = self.values.pop()
                string = self.values.pop()
                raw_string = string[1:-1]  # 両側の " を削除

                if not (type(string) is str):
                    self.task.push(Task(Node('push', '""')))
                    return

                try:
                    self.task.push(Task(Node('push',
                                         '"' + raw_string[i-1:i+num-1] + '"')))
                except:
                    self.task.push(Task(Node('push', string)))

                    
            if aNode.leaf == 'int':
                val0 = self.values.pop()
                
                if type(val0) is int:
                    self.task.push(Task(Node('push', int(val0))))
                    return

                if type(val0) is str:
                    self.task.push(Task(Node('push', int(val0[1:-1]))))
                    return

                self.task.push(Task(Node('push', 0)))


            if aNode.leaf == 'str':
                val0 = self.values.pop()
                
                if type(val0) is str:
                    self.task.push(Task(Node('push', str(val0))))
                    return

                if type(val0) is int:
                    self.task.push(Task(Node('push', '"' + str(val0) + '"')))
                    
                self.task.push(Task(Node('push', 0)))

                

        
        elif aNode.type == 'array':
            if cnt == 2:
                an_array = {}
                for i in range(len(aNode.children)):
                    aval = self.values.pop()
                    an_array[i] = aval

                self.task.push(Task(Node('push', an_array)))
            
            return

                               
        elif aNode.type == 'push':
            self.values.push(aNode.leaf)
            return
        
        elif aNode.type == 'critical_error':
            self.task.clear()
            return



        
    def eval_exp(self, aNode):

        if aNode.type == 'binop':
            self.task.push(Task(aNode, cnt=2))
            self.eval_exp(aNode.children[1])
            self.eval_exp(aNode.children[0])
            return

        elif aNode.type == 'singleop':
            self.task.push(Task(aNode, cnt=2))
            self.eval_exp(aNode.children[0])
            return

        elif aNode.type == 'builtin':
            if aNode.leaf in ['len', 'int', 'str']:
                self.task.push(Task(aNode, cnt=2))
                self.eval_exp(aNode.children)
                
            elif aNode.leaf in ['left', 'right']:
                self.task.push(Task(aNode, cnt=2))
                self.eval_exp(aNode.children[1])
                self.eval_exp(aNode.children[0])
                
            elif aNode.leaf == 'mid':
                self.task.push(Task(aNode, cnt=2))
                self.eval_exp(aNode.children[2])
                self.eval_exp(aNode.children[1])
                self.eval_exp(aNode.children[0])
                
            else:
                print("ERROR: eval_exp " + aNode.leaf)
                
            
        elif aNode.type == 'number':
            self.task.push(Task(Node('push', aNode.leaf)))
            return

        elif aNode.type == 'string':
            '''
            pattern = [('\\n', '\n'),
                       ('\\"', '"'),
                       ('\\t', '\t'),
                       ('\\', '\\'),
                       ]

            string = aNode.leaf
            for key, subst in pattern:
                if key in string:
                    print(key)
                    print("!!")
                    string = string.replace(key, subst)
            '''
            
            self.task.push(Task(Node('push', aNode.leaf)))
            return

        elif aNode.type == 'name':
            if aNode.leaf in self.env:
                target_value = self.env[aNode.leaf]
            else:
                target_value = 0
                self.env[aNode.leaf] = 0
                
            self.task.push(Task(Node('push', target_value)))
            return

        elif aNode.type == 'array':
            self.task.push(Task(aNode, cnt=2))
            for anexp in aNode.children:
                self.eval_exp(anexp)

            return

        elif aNode.type == 'array_element':
            self.task.push(Task(aNode, cnt=2))

            indexes = aNode.children[1]
            for index in indexes:
                self.eval_exp(index) # index
            
            return
        
        
        elif aNode.type == 'call':
            
            procedure_name = aNode.leaf
            
            try:
                # procedure の情報を取得
                procedure_body = self.procedures[procedure_name][2]
                procedure_retname = self.procedures[procedure_name][0]
                procedure_params = self.procedures[procedure_name][1]
            except:
                myprint("実行エラー: 手続き '{}' が定義されていません。".format(procedure_name), error=True)

                self.task.push(Task(Node('critical_error')))
                return


            # 呼び出し側の情報を取得
            call_params = aNode.children


            # 引数の個数のチェック
            if len(procedure_params) > len(call_params):
                myprint("実行エラー: 手続き {} に与えらた引数の個数が少なすぎです（{}個にしてください）。".format(procedure_name, len(procedure_params)))

                self.task.push(Task(Node('critical_error')))
                return

            elif len(procedure_params) < len(call_params):
                myprint("実行エラー: 手続き {} に与えらた引数の個数が多すぎです（{}個にしてください）。".format(procedure_name, len(procedure_params)))

                self.task.push(Task(Node('critical_error')))
                return
                
            
            # 手続き用に環境を完全コピー
            self.dump.push(copy.deepcopy(self.env))

            
            tasks = []
            refname = {}

            
            # 名前呼びのチェック
            for procedure_aparam, call_aparam in zip(procedure_params, call_params):                
                # 名前呼びのとき
                if call_aparam.type == 'name':
                    refname[procedure_aparam] = call_aparam.leaf

                
            # 本体の実行            
            tasks += [Task(Node("remove_callparams", "",
                                [procedure_params, refname]), cnt=1)]
            tasks += [Task(procedure_body, cnt=1)]


            # 後処理（環境を整える）
            tasks += [Task(Node("call", "",
                            [procedure_retname,
                             procedure_params, call_params],
                            lineno=aNode.lineno), cnt=2)]

            # 処理をタスクに積む
            for atask in tasks[::-1]:
                self.task.push(atask)


            # call_params を解釈して、値用のスタックへ積む
            for call_aparam in call_params:
                
                self.eval_exp(call_aparam)

                
            return
        



    def valid_occurs(self, aline, regexp):
        if '#' in aline:
            comment_pos = aline.find('#')
            aline = aline[:comment_pos]

        return len(regexp.findall(aline))


    

    # -------------------------------------------------
    # public 
    # -------------------------------------------------
    def setup(self, s, env=[]):
        """
        evaluator for GUI mode
        """

        global Error_alised
        global lexer, parser
        global My_lineno
        
        lexer.lineno = 1
        My_lineno = 1
        nest = 0

        self.clear_stack()

        if env != []:
            node_list = []
            for aline in env[::-1]:
                sentence = aline[0] + ":=" + aline[1]
                aNode = parser.parse(sentence)
                self.task.push(Task(aNode, cnt=1))
                print(sentence)

            while not self.task.is_empty():            
                task = self.task.pop()
                self.eval_sentence(task)
        

            
        
        ss = s.split('\n')

        sentence_list = []
        sentence = ""

        is_in_multi = False
        is_in_procedure = False
        count_multi = 0

        concat_buf = ""
        
        for s in ss:

            if s.endswith('\\'):
                concat_buf += s[:-1]
                continue
            
            if concat_buf != "":
                s = concat_buf + s
                concat_buf = ""
                
            
            if s=="":
                sentence += s + "\n"
                continue

            if not s:
                continue

            if s[0] == "#":
                sentence += s + "\n"
                continue


            s = s.replace('\t', '')
            
            sentence += s + "\n"
            
            if self.valid_occurs(s, self.reg_procedure):
                if not self.valid_occurs(s, self.reg_begin) \
                   and not self.valid_occurs(s, self.reg_end):
                    is_in_procedure = False
                    sentence_list += [sentence]
                    sentence=""
                    continue
                else:
                    is_in_procedure = True


            if self.valid_occurs(s, self.reg_begin) or \
               self.valid_occurs(s, self.reg_end) or \
               nest>0:

                is_in_multi = True
                
                nest += self.valid_occurs(s, self.reg_begin)
                nest -= self.valid_occurs(s, self.reg_end)
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
                if self.valid_occurs(sentence_list[-1], self.reg_procedure) \
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
            countln = sentence.count("\n")
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
            return {'noerror': False,
                    'lineno': self.onestep_lineno,
                    'env':self.env, 
                    'pretty_env': self.pretty_env(self.env),
                    'task': self.task,
                    'values': self.values,
                    'dump': self.dump,
                    'nameref': self.name_ref}
        
        # はじめに実行される行番号を取得しておく
        if len(node_list) > 0:
            self.onestep_lineno = node_list[0].lineno

        # 逆順にスタックへ積む
        for node in node_list[::-1]:
            self.task.push(Task(node, cnt=1))
            
        return {'noerror': True,
                'lineno': self.onestep_lineno,
                'env':self.env, 
                'pretty_env': self.pretty_env(self.env),
                'task': self.task,
                'values': self.values,
                'dump': self.dump,
                'nameref': self.name_ref}
            

    def eval_onestep(self):
        if self.task.is_empty():
            return {'lineno':0, 'env':{}, 'empty':True,
                    'pretty_env': {},
                    'task': self.task,
                    'values': self.values,
                    'dump': self.dump,
                    'nameref': self.name_ref}

        #print("---")        
        while True:
            
            #(aNode1, cnt1) = self.task.pop()
            task = self.task.pop()

            #aNode1.print()

            self.eval_sentence(task)
                                   

            #print(self.env)
            
            # 次に実行する lineno の取得
            if not self.task.is_empty():
                #(aNode1, cnt1) = self.task.pop()
                task = self.task.pop()
                
                if self.onestep_lineno != 0:
                    old_lineno = self.onestep_lineno
                    
                self.onestep_lineno = task.node.lineno
                self.task.push(task)
                
            else:
                # empty なら終了
                
                return {'lineno':0,
                        'env': self.env,
                        'pretty_env': self.pretty_env(self.env),
                        'empty': True,
                        'task': self.task,
                        'values': self.values,
                        'dump': self.dump,
                        'nameref': self.name_ref}

            
            if self.onestep_lineno == 0:
                # lineno が 0 のときは、行番号に依存しない内部処理なので継続して処理する
                continue
            
            elif old_lineno == self.onestep_lineno:
                # 行番号が同じならば継続
                continue
            
            else:
                break

            
        
        return {'lineno':self.onestep_lineno,
                'env': self.env,
                'pretty_env': self.pretty_env(self.env),
                'empty':self.task.is_empty(),
                'task': self.task,
                'values': self.values,
                'dump': self.dump,
                'nameref': self.name_ref}
        

        
        
    def eval_all(self):
        
        while not self.task.is_empty():
            task  = self.task.pop()
            # task.node.print()
            self.eval_sentence(task)

    
        return {
            'lineno': self.onestep_lineno,
            'env':self.env, 
            'pretty_env': self.pretty_env(self.env),
        }




