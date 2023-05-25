import abc
from json import JSONEncoder

from util import make_kv

class AstNode(metaclass=abc.ABCMeta):
    NodeName = 'None'

    @abc.abstractmethod
    def json_serialize(self):
        return

class Command(AstNode):
    pass

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, AstNode):
            return obj.json_serialize()
        # Let the base class default method raise the TypeError
        return JSONEncoder.default(self, obj)

class PipeNode(Command):
    NodeName = 'Pipe'
    is_background: bool
    items: "list[Command]"

    def __init__(self, is_background, items):
        self.is_background = is_background
        self.items = items

    def __repr__(self):
        if (self.is_background):
            return "Background Pipe: {}".format(self.items)    
        else:
            return "Pipe: {}".format(self.items)
        
    def json_serialize(self):
        json_output = make_kv(PipeNode.NodeName,
                              [self.is_background,
                               self.items])
        return json_output

class CommandNode(Command):
    NodeName = 'Command'
    line_number: int
    assignments: list
    arguments: "list[list[ArgChar]]"
    redir_list: list

    def __init__(self, line_number, assignments, arguments, redir_list):
        self.line_number = line_number
        self.assignments = assignments
        self.arguments = arguments
        self.redir_list = redir_list

    def __repr__(self):
        output = "Command: {}".format(self.arguments)
        if(len(self.assignments) > 0):
            output += ", ass[{}]".format(self.assignments)
        if(len(self.redir_list) > 0):
            output += ", reds[{}]".format(self.redir_list)
        return output

    def json_serialize(self):
        json_output = make_kv(CommandNode.NodeName,
                              [self.line_number,
                               self.assignments,
                               self.arguments,
                               self.redir_list])
        return json_output

class SubshellNode(Command):
    NodeName = 'Subshell'
    line_number: int
    body: Command
    redir_list: list

    def __init__(self, line_number, body, redir_list):
        self.line_number = line_number
        self.body = body
        self.redir_list = redir_list

    def json_serialize(self):
        json_output = make_kv(SubshellNode.NodeName,
                              [self.line_number,
                               self.body,
                               self.redir_list])
        return json_output
        
class AndNode(Command):
    NodeName = 'And'
    left_operand: Command
    right_operand: Command

    def __init__(self, left_operand, right_operand):
        self.left_operand = left_operand
        self.right_operand = right_operand

    def __repr__(self):
        output = "{} && {}".format(self.left_operand, self.right_operand)
        return output
    
    def json_serialize(self):
        json_output = make_kv(AndNode.NodeName,
                              [self.left_operand,
                               self.right_operand])
        return json_output

class OrNode(Command):
    NodeName = 'Or'
    left_operand: Command
    right_operand: Command

    def __init__(self, left_operand, right_operand):
        self.left_operand = left_operand
        self.right_operand = right_operand

    def __repr__(self):
        output = "{} || {}".format(self.left_operand, self.right_operand)
        return output
    
    def json_serialize(self):
        json_output = make_kv(OrNode.NodeName,
                              [self.left_operand,
                               self.right_operand])
        return json_output
    
class SemiNode(Command):
    NodeName = 'Semi'
    left_operand: Command
    right_operand: Command

    def __init__(self, left_operand, right_operand):
        self.left_operand = left_operand
        self.right_operand = right_operand

    def __repr__(self):
        output = "{} ; {}".format(self.left_operand, self.right_operand)
        return output
    
    def json_serialize(self):
        json_output = make_kv(SemiNode.NodeName,
                              [self.left_operand,
                               self.right_operand])
        return json_output


class NotNode(Command):
    NodeName = 'Not'
    body: Command

    def __init__(self, body):
        self.body = body

    def json_serialize(self):
        json_output = make_kv(NotNode.NodeName,
                              self.body)
        return json_output

class RedirNode(Command):
    NodeName = 'Redir'
    line_number: int
    node: Command
    redir_list: list

    def __init__(self, line_number, node, redir_list):
        self.line_number = line_number
        self.node = node
        self.redir_list = redir_list

    def json_serialize(self):
        json_output = make_kv(RedirNode.NodeName,
                              [self.line_number,
                               self.node,
                               self.redir_list])
        return json_output

class BackgroundNode(Command):
    NodeName = 'Background'
    line_number: int
    node: Command
    redir_list: list

    def __init__(self, line_number, node, redir_list):
        self.line_number = line_number
        self.node = node
        self.redir_list = redir_list

    def json_serialize(self):
        json_output = make_kv(BackgroundNode.NodeName,
                              [self.line_number,
                               self.node,
                               self.redir_list])
        return json_output

class DefunNode(Command):
    NodeName = 'Defun'
    line_number: int
    name: object
    body: Command

    def __init__(self, line_number, name, body):
        self.line_number = line_number
        self.name = name
        self.body = body

    def json_serialize(self):
        json_output = make_kv(DefunNode.NodeName,
                              [self.line_number,
                               self.name,
                               self.body])
        return json_output

class ForNode(Command):
    NodeName = 'For'
    line_number: int
    argument: "list[list[ArgChar]]"
    body: Command
    variable: object

    def __init__(self, line_number, argument, body, variable):
        self.line_number = line_number
        self.argument = argument
        self.body = body
        self.variable = variable

    def __repr__(self):
        output = "for {} in {}; do ({})".format(self.variable, self.argument, self.body)
        return output
    
    def json_serialize(self):
        json_output = make_kv(ForNode.NodeName,
                              [self.line_number,
                               self.argument,
                               self.body,
                               self.variable])
        return json_output

class WhileNode(Command):
    NodeName = 'While'
    test: Command
    body: Command

    def __init__(self, test, body):
        self.test = test
        self.body = body

    def json_serialize(self):
        json_output = make_kv(WhileNode.NodeName,
                              [self.test,
                               self.body])
        return json_output

class IfNode(Command):
    NodeName = 'If'
    cond: Command
    then_b: Command
    else_b: Command

    def __init__(self, cond, then_b, else_b):
        self.cond = cond
        self.then_b = then_b
        self.else_b = else_b

    def json_serialize(self):
        json_output = make_kv(IfNode.NodeName,
                              [self.cond,
                               self.then_b,
                               self.else_b])
        return json_output

class CaseNode(Command):
    NodeName = 'Case'
    line_number: int
    argument: "list[ArgChar]"
    cases: list

    def __init__(self, line_number, argument, cases):
        self.line_number = line_number
        self.argument = argument
        self.cases = cases

    def json_serialize(self):
        json_output = make_kv(CaseNode.NodeName,
                              [self.line_number,
                               self.argument,
                               self.cases])
        return json_output

class ArgChar(AstNode):
    ## This method formats an arg_char to a string to
    ## the best of its ability
    def format(self) -> str:
        raise NotImplementedError

class CArgChar(ArgChar):
    NodeName = 'C'
    char: int

    def __init__(self, char: int):
        self.char = char

    def __repr__(self):
        return self.format()
    
    def format(self) -> str:
        return str(chr(self.char))

    def json_serialize(self):
        json_output = make_kv(CArgChar.NodeName,
                              self.char)
        return json_output

class EArgChar(ArgChar):
    NodeName = 'E'
    char: int

    def __init__(self, char: int):
        self.char = char

    ## TODO: Implement
    def __repr__(self):
        return f'\\{chr(self.char)}'

    def format(self) -> str:
        ## TODO: This is not right. I think the main reason for the
        ## problems is the differences between bash and the posix
        ## standard.
        non_escape_chars = [92, # \
                            61, # =
                            91, # [
                            93, # ]
                            45, # -
                            58, # :
                            126,# ~
                            42] # *
        if(self.char in non_escape_chars):
            return '{}'.format(chr(self.char))
        else:
            return '\{}'.format(chr(self.char))

    def json_serialize(self):
        json_output = make_kv(EArgChar.NodeName,
                              self.char)
        return json_output

class TArgChar(ArgChar):
    NodeName = 'T'
    string: str

    def __init__(self, string: str):
        self.string = string

    ## TODO: Implement
    # def __repr__(self):
    #     return f''

    def json_serialize(self):
        json_output = make_kv(TArgChar.NodeName,
                              self.string)
        return json_output

class AArgChar(ArgChar):
    NodeName = 'A'
    arg: "list[ArgChar]"

    def __init__(self, arg: "list[ArgChar]"):
        self.arg = arg

    ## TODO: Implement
    # def __repr__(self):
    #     return f''

    def json_serialize(self):
        json_output = make_kv(AArgChar.NodeName,
                              self.arg)
        return json_output

class VArgChar(ArgChar):
    NodeName = 'V'
    fmt: object
    null: bool
    var: str
    arg: "list[ArgChar]"

    def __init__(self, fmt, null: bool, var: str, arg: "list[ArgChar]"):
        self.fmt = fmt
        self.null = null
        self.var = var
        self.arg = arg

    def __repr__(self):
        return f'V({self.fmt},{self.null},{self.var},{self.arg})'

    def format(self) -> str:
        return '${{{}}}'.format(self.var)

    def json_serialize(self):
        json_output = make_kv(VArgChar.NodeName,
                              [self.fmt,
                               self.null,
                               self.var,
                               self.arg])
        return json_output

class QArgChar(ArgChar):
    NodeName = 'Q'
    arg: "list[ArgChar]"

    def __init__(self, arg: "list[ArgChar]"):
        self.arg = arg

    def __repr__(self):
        return f'Q({self.arg})'
    
    def format(self) -> str:
        chars = [arg_char.format() for arg_char in self.arg]
        joined_chars = "".join(chars)
        return '"{}"'.format(joined_chars)

    def json_serialize(self):
        json_output = make_kv(QArgChar.NodeName,
                              self.arg)
        return json_output

class BArgChar(ArgChar):
    NodeName = 'B'
    node: Command

    def __init__(self, node: Command):
        self.node = node

    ## TODO: Implement
    # def __repr__(self):
    #     return f''

    def format(self) -> str:
        return '$({})'.format(self.node)

    def json_serialize(self):
        json_output = make_kv(BArgChar.NodeName,
                              self.node)
        return json_output


## This function takes an object that contains a mix of untyped and typed AstNodes (yuck) 
## and turns it into untyped json-like object. It is required atm because the infrastructure that
## we have does not translate everything to its typed form at once before compiling, and therefore
## we end up with these abomination objects.
##
## Very important TODO: 
##    We need to fix this by properly defining types (based on `compiler/parser/ast_atd.atd`)
##    and creating a bidirectional transformation from these types to the untyped json object.
##    Then we can have all ast_to_ir infrastructure work on these objects, and only in the end
##    requiring to go to the untyped form to interface with printing and parsing 
##    (which ATM does not interface with the typed form).
def ast_node_to_untyped_deep(node):
    if(isinstance(node, AstNode)):
        json_key, json_val = node.json_serialize()
        return [json_key, ast_node_to_untyped_deep(json_val)]
    elif(isinstance(node, list)):
        return [ast_node_to_untyped_deep(obj) for obj in node]
    elif(isinstance(node, tuple)):
        return [ast_node_to_untyped_deep(obj) for obj in node]
    elif(isinstance(node, dict)):
        return {k: ast_node_to_untyped_deep(v) for k, v in node.items()}
    else:
        return node

def make_typed_semi_sequence(asts: "list[AstNode]") -> SemiNode:
    assert(len(asts) > 0)

    if(len(asts) == 1):
        return asts[0]
    else:
        acc = asts[-1]
        ## Remove the last ast
        iter_asts = asts[:-1]
        for ast in iter_asts[::-1]:
            acc = SemiNode(ast, acc)
        return acc
