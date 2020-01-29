from enum import Enum

class AstNodeConstructor(Enum):
    PIPE = 'Pipe'
    COMMAND = 'Command'
    AND = 'And'
    OR = 'Or'
    SEMI = 'Semi'
    REDIR = 'Redir'
    SUBSHELL = 'Subshell'
    BACKGROUND = 'Background'
    DEFUN = 'Defun'
