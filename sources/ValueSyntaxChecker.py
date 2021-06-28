#-*- coding:utf-8 -*-
# -----------------------------------------------------------------------------
# VariableNameChcker.py
#
# A Checker whether given strings are valid as variable names.
# 27 June 2021.
#
# Copyright (c) 2021 Shinya Sato
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php
# -----------------------------------------------------------------------------

Error_mes = ""

        
# tokens
tokens = [
    'NUMBER',
    'ARRAY_L', 'ARRAY_R',
    'CSTR', 'COMMA'
]

t_ARRAY_L = r'\['
t_ARRAY_R = r'\]'
t_COMMA = r','

Error_mes = ""
def t_NUMBER(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        global Error_mes
        Error_mes += "整数値 '%d' が規定より大きすぎます。\n" % t.value
        
        t.value = 0
    return t

def t_CSTR(t):
   r'\"([^\\\n]|(\\.))*?\"'
   return t



# Ignored characters
t_ignore = " \t"

def t_error(t):
    global Error_alised, Error_mes
    Error_alised = True
    Error_mes += "受け入れられない文字がありました： '%s'" % t.value[0]
    t.lexer.skip(1)
    

# Build the lexer
import ply.lex as lex
lexer = lex.lex()
    
# Parsing rules

start = 'value'
def p_value_element(t):
    '''value : NUMBER
                  | CSTR
    '''
    t[0] = ""
    
def p_value_array(t):
    '''value : ARRAY_L ARRAY_R
                  | ARRAY_L array_params ARRAY_R
    '''
    t[0] = ""

def p_array_params(t):
    '''array_params : value
                    | array_params COMMA value
    '''
    if len(t) == 2:
        t[0] = [t[1]]
    else:
        t[0] = t[1] + [t[3]]

    
    
Error_arised = False
def p_error(t):
    
    global Error_alised, Error_mes
    Error_alised = True
    if not(t is None):
        Error_mes += "'%s' は値として正しくありません。\n" % t.value

    else:
        Error_mes += "式が途中で終了しています。\n"


import ply.yacc as yacc
parser = yacc.yacc(write_tables=False, debug=False)

# ----------------------------------------------------------------
class SyntaxChecker:
    def __init__(self, callback=None):

        # callback for print
        global Callback
        Callback = callback

    def is_valid(self, text):
        global parser, Error_alised, Error_mes

        Error_alised = False
        Error_mes = ""
        aNode = parser.parse(text)

        return Error_mes

