#-*- coding:utf-8 -*-
# -----------------------------------------------------------------------------
# while.py
#
# An interpreter of while programs.
# 6th February 2020.
#
# Copyright (c) 2021 Shinya Sato
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php#
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
    def __init__(self, type, leaf=None, children=None):
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
        print("整数値 '%d' が規定より大きすぎます。", t.value)
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
    print("受け入れられない文字がありました： '%s'" % t.value[0])
    t.lexer.skip(1)
    

# Build the lexer
import ply.lex as lex
lexer = lex.lex()
    
# Parsing rules

precedence = (
    ('left','PLUS','MINUS'),
    ('left','TIMES','DIVIDE', 'MOD'),
    ('nonassoc','NE','EQ', 'GE','GT','LE','LT'),
    ('left', 'AND','OR'),
    ('right','UMINUS'),
#    ('nonassoc', 'IFX','ELSE'),
    )

start = 'statement'
def p_statement(t):
    '''statement : NAME SUBST expression
                 | NAME array_nest SUBST expression
                 | NAME INC
                 | NAME DEC
                 | PRINT print_param
                 | WHILE expression DO statement
                 | IF expression THEN statement
                 | IF expression THEN statement ELSE statement
                 | PROCEDURE NAME SUBST NAME procedure_argument COLON statement
                 | BEGIN END
                 | BEGIN statements END
                 | expression
    '''
    if len(t) >= 3:
        if t[2] == ':=':
            t[0] = Node("binop", ":=", [Node("name",t[1]),t[3]])
                
        elif t[1] == 'begin':
            if t[2] == 'end':
                t[0] = Node("nop")
            else:
                t[0] = Node("multi", "", t[2])

            
        elif len(t) >= 4 and t[3] == ':=' and (t[1] != 'procedure'):
            if len(t[2]) == 1:
                t[0] = Node("array_subst", "", [Node("name",t[1]), t[2][0], t[4]])
            else:
                """
                a[1][2][3] := 10
                ==>
                tmp := a
                tmp := tmp[1]
                tmp := tmp[2]
                tmp[3] := 10
                
                
                a[1][2] := 10
                ==>
                tmp := a
                tmp := tmp[1]
                tmp[2] := 10
                
                """
                tmp_name = Node("name", "#tmp")
                subst_codes = [Node("binop", ":=", [tmp_name, Node("name",t[1])])]
                last_exp = t[2].pop()
                for anexp in t[2]:
                    subst_codes += [Node("binop",
                                         ":=",
                                         [tmp_name,
                                          Node("array_element", "",
                                               [tmp_name, anexp])])]
                subst_codes += [Node("array_subst", "", [tmp_name, last_exp, t[4]])]
                t[0] = Node("multi", "", subst_codes)
                
        elif t[2] == '++':
            t[0] = Node('unarrayop', '++', [Node("name",t[1])])
        elif t[2] == '--':
            t[0] = Node('unarrayop', '--', [Node("name",t[1])])
        elif t[1] == 'print':
            t[0] = Node("print", "", t[2])
        elif t[1] == 'while':
            t[0] = Node("while", "", [t[2], t[4]])
        elif t[1] == 'if':
            if len(t) > 5:
                t[0] = Node("if", "with-else", [t[2], t[4], t[6]])
            else:
                t[0] = Node("if", "without-else", [t[2], t[4]])
        elif t[1] == 'procedure':
            t[0] = Node("procedure", t[4], [t[2], t[5], t[7]])

    elif len(t) == 2:
        t[0] = Node("print", "", [t[1]])


        
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
    t[0] = Node("call", t[1], t[2])

    
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

    """
    a[0][100]
    Node("array_element_via_array", "", [Node("array_element", '', [Node('name', t[1]), t[3]]), 100])
    """
    first_element = t[2].pop(0)
    ret = Node("array_element", '', [Node('name', t[1]), first_element])
    for i in t[2]:
        ret = Node("array_element_via_array", "", [ret, i])
    t[0] = ret
        
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
        
def p_error(t):
    #'statement : PRINT error SEMI'
    #print("文法エラー. ")
    #print(t)
    if not(t is None):
        print("%d行目: 文法エラー '%s'\n" % (t.lineno, t.value))
    else:
        global my_lineno
        print("%d行目: 文法エラー\n" % (my_lineno-1))




# dictionary of global names and procedures
Procedures = {}

def pretty_print_value(aVal):
    result = ""
    if type(aVal) is int:
        result = "{}".format(aVal)
        return result
    
    elif type(aVal) is str:
        result = "{}".format(aVal)
        return result
    
    elif type(aVal) is dict:
        array_val_list = []
        aVal_key = aVal.keys()
        for i in range(0, max(aVal_key) + 1):
            if i in aVal_key:
                retstr = pretty_print_value(aVal[i])
            else:
                retstr = "0"
                    
            array_val_list += [retstr]
        
        result = "[{}]".format(", ".join(array_val_list))
        return result
        
        
        
def eval_sentence(aNode, env):
    global Procedures
    
    if aNode.type == 'binop':
        if aNode.leaf == ":=":
            target_value = eval_exp(aNode.children[1], env)
            var_name = aNode.children[0].leaf
            if type(target_value) is dict:
                # dict（array） の場合、別のオブジェクトとして代入
                # （もとのオブジェクトに影響が及んでしまう）
                env[var_name] = copy.deepcopy(target_value)
            else:
                env[var_name] = target_value                    
            return

    elif aNode.type == 'array_subst':
        target_value = eval_exp(aNode.children[2], env)
        target_index = eval_exp(aNode.children[1], env)
        var_name = aNode.children[0].leaf

        try:
            env[var_name][target_index] = target_value
        except (TypeError, KeyError):
            env[var_name] = {}
            env[var_name][target_index] = target_value

        return

    elif aNode.type == 'unarrayop':
        if aNode.leaf == '++':
            var_name = aNode.children[0].leaf
            env[var_name] += 1
            return

        elif aNode.leaf == '--':
            var_name = aNode.children[0].leaf
            if env[var_name] > 0:
                env[var_name] -= 1                 
            else:
                env[var_name] = 0
            return

    elif aNode.type == 'print':
        result_vals = []
        for anexp in aNode.children:
            aval = eval_exp(anexp, env)
            #result_vals += [str(aval)]
            result_vals += [pretty_print_value(aval)]

        global my_lineno
        lineno_indent = " " * (len(str(my_lineno-1)) + 5)

        print(lineno_indent + " ".join(result_vals) + "\n")
        return

    
    elif aNode.type == 'while':
        while True:
            target_value = eval_exp(aNode.children[0], env)

            if target_value == 1:
                eval_sentence(aNode.children[1], env)
            else:
                break

        return

    elif aNode.type == 'if':
        target_value = eval_exp(aNode.children[0], env)
        if target_value == 1:            
            eval_sentence(aNode.children[1], env)
        else:
            if aNode.leaf == "with-else":
                eval_sentence(aNode.children[2], env)
        return

    elif aNode.type == 'multi':
        statements = aNode.children
        for statement_node in statements:
            eval_sentence(statement_node, env)
        return

    elif aNode.type == 'procedure':
        Procedures[aNode.leaf] = aNode.children
        return

    
                
def eval_exp(aNode, env):

    if aNode.type == 'binop':
        val0 = eval_exp(aNode.children[0], env)
        val1 = eval_exp(aNode.children[1], env)
        if aNode.leaf == "+":
            return val0+val1
        elif aNode.leaf == "-":
            result = val0-val1
            if result < 0: result=0
            return result
        elif aNode.leaf == "*":
            return val0*val1
        elif aNode.leaf == "div":
            return int(val0/val1)
        elif aNode.leaf == "mod":
            return val0%val1
        elif aNode.leaf == "!=":
            if val0 != val1: return 1
            else: return 0
        elif aNode.leaf == "=":
            if val0 == val1: return 1
            else: return 0
        elif aNode.leaf == ">=":
            if val0 >= val1: return 1
            else: return 0
        elif aNode.leaf == ">":
            if val0 > val1: return 1
            else: return 0
        elif aNode.leaf == "<=":
            if val0 <= val1: return 1
            else: return 0
        elif aNode.leaf == "<":
            if val0 < val1: return 1
            else: return 0
        elif aNode.leaf == "and":
            if (val0 ==1) and (val1 == 1): return 1
            else: return 0
        elif aNode.leaf == "or":
            if (val0 ==1) or (val1 == 1): return 1
            else: return 0

    elif aNode.type == 'singleop':
        val0 = eval_exp(aNode.children[0], env)
        if aNode.leaf == "not":
            if val0 ==0: return 1
            else: return 0
            
    elif aNode.type == 'number':
        return aNode.leaf

    elif aNode.type == 'string':
        return aNode.leaf
    
    elif aNode.type == 'name':
        if aNode.leaf in env:
            target_value = env[aNode.leaf]
        else:
            target_value = 0
            
        return(target_value)
    
    elif aNode.type == 'array':
        an_array = {}
        for i, anexp in enumerate(aNode.children):
            here_result = eval_exp(anexp, env)
            an_array[i] = here_result
        
        return an_array
    
    elif aNode.type == 'array_element':
        here_index = eval_exp(aNode.children[1], env)
        name_str = aNode.children[0].leaf
        if name_str in env:
            try:
                target_value = env[name_str][here_index]
            except KeyError:
                env[name_str][here_index] = 0
                target_value = 0
            except TypeError:
                env[name_str] = {}
                env[name_str][here_index] = 0
                target_value = {}
        else:
            target_value = 0

        return(target_value)
    
    
    elif aNode.type == 'array_element_via_array':
        target_value1 = eval_exp(aNode.children[0], env)
        target_value2 = eval_exp(aNode.children[1], env)
        if target_value2 not in target_value1:
            target_value1[target_value2] = 0
        return(target_value1[target_value2])


    elif aNode.type == 'call':
        procedure_name = aNode.leaf

        try:
            # procedure の情報を取得
            procedure_body = Procedures[procedure_name][2]
            procedure_retname = Procedures[procedure_name][0]
            procedure_params = Procedures[procedure_name][1]
        except:
            print("Error: Procedure '{}' が定義されていません。".format(procedure_name))
            return 0

            
        # 呼び出し側の情報を取得
        call_params = aNode.children


        procedure_env = {} 

        # 環境の procedure_params に call_params を代入する
        for procedure_aparam, call_aparam in zip(procedure_params, call_params):
            target_value = eval_exp(call_aparam, env)
            procedure_env[procedure_aparam] = target_value

        # 本体の実行
        eval_sentence(procedure_body, procedure_env)

        for procedure_aparam, call_aparam in zip(procedure_params,
                                                 call_params):
            if call_aparam.type == "name":
                # 変数名で呼び出している時には
                # procedure 内で更新されるものとする
                env[call_aparam.leaf] = procedure_env[procedure_aparam]


        try:
            retval = procedure_env[procedure_retname]
        except KeyError:
            # procedure 内で retval が使われていないときは 0 を返すとする
            retval = 0
                        
        return retval



    
def say_hello():

    message = '''
while言語インタプリタ (6 February 2021 edition)

'''

    print(message)

        
import ply.yacc as yacc
parser = yacc.yacc(write_tables=False, debug=False)


def valid_occurs(aline, keyword):
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


def count_keyword(aline, keyword):
    if '#' not in aline:
        return aline.count(keyword)

    if keyword not in aline:
        return 0
    
    comment_pos = aline.find('#')
    valid_str = aline[:(comment_pos -1)]
    return valid_str.count(keyword)



say_hello()

nest = 0
my_lineno = 1

env = {}

while True:
    try:
        s = input('[%d] $ ' % my_lineno)
        my_lineno += 1
    except EOFError:
        break

    if valid_occurs(s, 'begin'):
        
        nest += count_keyword(s, 'begin')
        nest -= count_keyword(s, 'end')
        
        while nest>0:
            s1 = input('[%d] > ' % my_lineno)
            my_lineno += 1

            s += "\n " + s1
           
            nest += count_keyword(s1, 'begin')
            nest -= count_keyword(s1, 'end')
                
    if not s:
        continue

    if s[0] == "#":
        continue
    
    aNode = parser.parse(s + "\n")
    if not(aNode is None):
        eval_sentence(aNode, env)
        


        
