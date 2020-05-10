#!/usr/bin/python3
# 'conf.py'
# theme.py configuration file parser
# Roch schanen
# created 2020 May 08
# https://github.com/RochSchanen/SimpleConfigurationParser

#####################################################################

# color printing for linux (using bash):

_NORMAL  = 0
_DYELLOW = 33 # dark yellow
_BYELLOW = 93 # bright yellow
_BLUE    = 94
_RED     = 91
_GREEN   = 92
_BOLD    = 1

_LOCATION  = _NORMAL
_TARGET    = _NORMAL
_CONTEXT   = _BOLD
_BLOCK     = _NORMAL
_HCONTEXT  = _NORMAL

def linux_cPrint(Code, *argv):
    COLOR = f'\033[{Code}m'
    ENDC = '\033[0m'
    print(COLOR, *argv, ENDC)
    return

# for windows:

def windows_cPrint(Code, *argv):
    COLOR = ' '
    ENDC  = ' '
    print(COLOR, *argv, ENDC)
    return

from platform import system

if system() == 'Linux': cPrint = linux_cPrint
if system() == 'Darwin': cPrint = linux_cPrint # not tested
if system() == 'Windows': cPrint = windows_cPrint # not tested

#####################################################################
# options

_opt = 1

# verbose options
_V_EEA  = _opt; _opt<<=1 # ENTER/EXIT APLICATION
_V_OCD  = _opt; _opt<<=1 # OPEN/CLOSE FILE - DISPLAY STATUS
_V_BLP  = _opt; _opt<<=1 # BLOCK PARSE
_V_GBL  = _opt; _opt<<=1 # GET BLOCK

# setup verbose option (uncomment to activate)
_VERBOSE = 0
# _VERBOSE |= _V_EEA
# _VERBOSE |= _V_OCD
# _VERBOSE |= _V_BLP
# _VERBOSE |= _V_GBL

def _DEBUG(vCode, cCode, Text):
    # check flags
    if _VERBOSE & vCode:
        # print in color
        cPrint(cCode, Text)
    return

#####################################################################
# imports and constants

from os  import linesep as _EOL
_EOLN = -len(_EOL) 

from sys import argv as argvlist
from sys import exit

_LAST     = -1

_DEBUG(_V_EEA, _NORMAL, '----- ENTER(1)')

######################################################## STATUS

# define keywords
_s_FILE = 'file = '
_s_PATH = 'location = '

# stat
_STATUS = {
    _s_FILE: '',    # configuration filename
    _s_PATH: ''     # current block path
    }

# check configuration file is defined
def _confOpened():
    if _STATUS[_s_FILE]: return 1
    cPrint(_RED, 'closed.')
    return 0

# print path to current block
def _printLocation():
    if _STATUS[_s_FILE]:
        s = f'@ /{_STATUS[_s_PATH]}'
        cPrint(_LOCATION, s)
        return 1
    cPrint(_RED, 'closed.')
    return 0

# print stat
def _printStatus():
    _DEBUG(_V_OCD, _GREEN, '_status()')
    if _STATUS[_s_FILE]:
        cPrint(_NORMAL, f'{_STATUS[_s_FILE]}')
        cPrint(_NORMAL, f'/{_STATUS[_s_PATH]}')
        return 1
    cPrint(_RED, 'closed.')
    return 0

# path to this mddule status file
_PATH = './conf.stat'

# load status from file
def _getstatus():
    _DEBUG(_V_OCD, _GREEN, '_getstatus()')
    # to-do: create file automatically if does not exist
    fh = open(_PATH, 'r')
    for key in _STATUS.keys():
        line = fh.readline()
        value = line[len(key):_EOLN]
        _STATUS[key] = value
        _DEBUG(_V_OCD, _RED, f'|{key}|{_STATUS[key]}|')
    fh.close()
    return

# save status to file
def _setstatus():
    _DEBUG(_V_OCD, _GREEN, '_setstatus()')
    fh = open(_PATH, 'w')
    for key in _STATUS.keys():
        _DEBUG(_V_OCD, _RED, f'|{key}|{_STATUS[key]}|')
        fh.write(f'{key}{_STATUS[key]}\n')
    fh.close()
    return

######################################################## OPEN CLOSE

# define configuration file name
def _open():
    _DEBUG(_V_OCD, _GREEN, '_open()')
    file = _STATUS[_s_FILE]
    if file:
        cPrint(_RED, f'"{file}" already opened.')
        return 0
    else:
        file = argvlist[0]
        print(f'opening configuration file "{file}".')
        fh = open(file); fh.close()
        _STATUS[_s_FILE] = file 
    return 1

# clear configuration file name
def _close():
    _DEBUG(_V_OCD, _GREEN, '_close()')
    file = _STATUS[_s_FILE]
    if file:
        print(f'closing Configuration file "{file}".')
        _STATUS[_s_FILE] = ""
        _STATUS[_s_PATH] = ""
        return 1
    else:
        cPrint(_RED, f'already closed.')
    return 0

######################################################## PARSER

_FH = None  # file handle
_LINE = ''  # current line (string to be parsed)

def _openFile():
    global _FH
    _FH = open(_STATUS[_s_FILE], 'r')
    return

def _readLine():
    global _LINE
    _LINE = _FH.readline()
    return

def _closeFile():
    _FH.close()
    return

# configuration file parser
class _block():

    def __init__(self, level, name, hcontext):
        # enter block
        _DEBUG(_V_BLP, _GREEN, f'enter _block({level}, {name})')
        # LOCAL
        self.name     = name  # this block's name
        self.blocks   = {}    # sub blocks
        self.lcontext = {}    # local context variables
        self.hcontext = {}    # inherited context variables
        self.target   = {}    # targets list
        self.lv  = level      # this block level (indentation)
        self.tab = level*'\t' # indentation string
        # explicitely copy inherited context variable (improve)
        for i in hcontext: self.hcontext[i]=hcontext[i]
        # parse block
        while _LINE:
            # skip empty line
            if self._skipComment(): continue
            # check line indent (end block)
            if _LINE.find(self.tab) < 0: break
            # check new block
            if self._newBlock(): continue
            # check context
            if self._captureContext(): continue
            # check target
            if self._captureTarget(): continue
            # ignore and carry on
            _readLine() # read next line to parse
        # exit block
        _DEBUG(_V_BLP, _GREEN, f'exit _block({level}, {name})')
        # done
        return

    # to-do: add # comments !!!
    def _skipComment(self):
        if _LINE[0] == _EOL:
            _readLine()
            return 1
        return 0

    def _captureTarget(self):
        line = _LINE[self.lv:_EOLN]
        _DEBUG(_V_BLP, _NORMAL, line)
        front, flag, value = line.partition(' = ')
        if flag:
            key = front.strip()            
            _DEBUG(_V_BLP, _RED, f'<{key}>=<{value}>')
            self.target[key] = value
            _readLine() 
            return 1
        return 0
    
    def _captureContext(self):
        line = _LINE[self.lv:_EOLN]
        if line[0] == '[':
            _DEBUG(_V_BLP, _NORMAL, line)
            key, flag, value = line.partition(' = ')
            ns, ne = key.find('['), key.find(']')
            name = line[ns+1:ne]
            self.lcontext[name] = value
            self.hcontext[name] = value
            _DEBUG(_V_BLP, _RED, f'<{name}>=<{value}>')
            _readLine()
            return 1
        return 0

    def _newBlock(self):
        line = _LINE[self.lv:_EOLN]
        if line[0] == '/':
            _DEBUG(_V_BLP, _NORMAL, line)
            name = line[1:].strip()
            _DEBUG(_V_BLP, _RED, f'<{name}>')
            _readLine()
            self.blocks[name] = _block(
                self.lv+1, name, self.hcontext)
            return 1
        return 0

######################################################## TEST

def _test():
    # allow to modify global variable
    global _VERBOSE
    # check conf.stat
    if not _confOpened(): return 0
    # select verbose all
    _VERBOSE = -1
    # open file
    _openFile()
    # read first line
    _readLine()
    # parse file
    _block(0,'root',{})
    # done
    _closeFile()
    # done
    return 1

######################################################## GET BLOCK

def _getBlock(Block, Path):
    # find next name: split path
    name, flag, path = Path.partition('/')
    # verbose
    _DEBUG(_V_GBL, _DYELLOW, f'<{name}><{flag}><{path}>')
    # get next block
    if name:
        # get next block
        if name in Block.blocks:
            # continue recursion
            return _getBlock(Block.blocks[name], path)
        else:
            # block name is missing
            cPrint(_RED, f'{name} not found in {Block.name}')
            return None
    # recursion ends: found last matching block
    return Block

######################################################## STD LIST

def _stdList(b):
    # show location
    _printLocation()
    # list context variables
    for i in b.hcontext:
        if i in b.lcontext:
            # this is a locally defined context variable
            cPrint(_CONTEXT, f'[{i}] = {b.lcontext[i]}')
        # this is a context variable inherited
        else: cPrint(_HCONTEXT, f'[{i}] = {b.hcontext[i]}')        
    # show sub blocks
    for i in b.blocks: cPrint(_BLOCK, f'/{i}') 
    # show local targets
    for i in b.target: cPrint(_TARGET, f'<{i}> = < {b.target[i]}>')
    # done
    return    

######################################################## LIST

def _list():
    # check state
    if not _confOpened(): return 0
    # open file
    _openFile()
    _readLine()
    root = _block(0,'root',{})
    _closeFile()
    # get block from path
    b = _getBlock(root, _STATUS[_s_PATH])
    # list
    if b: _stdList(b)
    return 1

######################################################## FORWARD

def _forwardBlock():
    global _STATUS
    # check state
    if not _confOpened(): return 0
    # open file
    _openFile()
    _readLine()
    root = _block(0,'root',{})
    b = _getBlock(root, _STATUS[_s_PATH])
    _closeFile()
    # get requested block name
    name = argvlist[0]
    # check name
    if name in b.blocks:
        # add name to the path
        if _STATUS[_s_PATH]: _STATUS[_s_PATH] += '/'
        _STATUS[_s_PATH] += f'{name}'
        # get block
        b = b.blocks[name] 
        # list
        _stdList(b)
    else:
        cPrint(_RED, 'block name undefined')
    return 1

######################################################## BACK

def _stepBack():
    global _STATUS
    # check state
    if not _confOpened(): return 0
    # open file
    _openFile()
    _readLine()
    root = _block(0,'root',{})
    _closeFile()
    # split path
    path, flag, name = _STATUS[_s_PATH].rpartition('/')
    # update
    _STATUS[_s_PATH] = path
    # get block
    b = _getBlock(root, path)
    # list
    _stdList(b)
    # done
    return 1

######################################################## COMMANDS

cmdlist = {
    'parse' : _test,
    's' : _printStatus, 
    'o' : _open,
    'c' : _close,
    'l' : _list,
    'f' : _forwardBlock,
    'b' : _stepBack
}

if len(argvlist) > 1 :
    argvlist.pop(0)
    if argvlist[0] in cmdlist.keys():
        _getstatus()
        if cmdlist[argvlist.pop(0)](): _setstatus()
        _DEBUG(_V_EEA, _NORMAL, '----- EXIT(1)')
        exit()

######################################################## USAGE

print('USAGE: conf "option" <argument>')
print('options:')
print('\t"s" prints state')
print('\t"o" <filename> opens filenname')
print('\t"c" closes file')
print('\t"l" lists the current block')
print('\t"f" <blockname> forwards to next block')
print('\t"b" step back to parent block')
print('\t"parse" only displays the full parsing process')

#####################################################################

_DEBUG(_V_EEA, _NORMAL, '----- EXIT(2)')
