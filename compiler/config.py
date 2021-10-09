import json
import os
import subprocess
import math

from ir_utils import *
from util import *

## Global
__version__ = "0.5" # FIXME add libdash version
GIT_TOP_CMD = [ 'git', 'rev-parse', '--show-toplevel', '--show-superproject-working-tree']
if 'PASH_TOP' in os.environ:
    PASH_TOP = os.environ['PASH_TOP']
else:
    PASH_TOP = subprocess.run(GIT_TOP_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).stdout.rstrip()

PYTHON_VERSION = "python3"
PLANNER_EXECUTABLE = os.path.join(PASH_TOP, "compiler/pash_runtime.py")
RUNTIME_EXECUTABLE = os.path.join(PASH_TOP, "compiler/pash_runtime.sh")

## Ensure that PASH_TMP_PREFIX is set by pa.sh
assert(not os.getenv('PASH_TMP_PREFIX') is None)
PASH_TMP_PREFIX = os.getenv('PASH_TMP_PREFIX')

config = {}
annotations = []
pash_args = None

## Contains a bash subprocess that is used for expanding
bash_mirror = None

def load_config(config_file_path=""):
    global config
    pash_config = {}
    CONFIG_KEY = 'distr_planner'

    if(config_file_path == ""):
      config_file_path = '{}/compiler/config.json'.format(PASH_TOP)
    with open(config_file_path) as config_file:
        pash_config = json.load(config_file)

    if not pash_config:
        raise Exception('No valid configuration could be loaded from {}'.format(config_file_path))

    if CONFIG_KEY not in pash_config:
        raise Exception('Missing `{}` config in {}'.format(CONFIG_KEY, config_file_path))

    config = pash_config

def getWidth():
    cpus = os.cpu_count()
    return math.floor(cpus / 8) if cpus >= 16 else 2

## These are arguments that are common to pash.py and pash_runtime.py
def add_common_arguments(parser):
    parser.add_argument("-w", "--width",
                        type=int,
                        default=getWidth(),
                        help="set data-parallelism factor")
    parser.add_argument("--no_optimize",
                        help="not apply transformations over the DFG",
                        action="store_true")
    parser.add_argument("--dry_run_compiler",
                        help="not execute the compiled script, even if the compiler succeeded",
                        action="store_true")
    parser.add_argument("--assert_compiler_success",
                        help="assert that the compiler succeeded (used to make tests more robust)",
                        action="store_true")
    parser.add_argument("--avoid_pash_runtime_completion",
                        help="avoid the pash_runtime execution completion (only relevant when --debug > 0)",
                        action="store_true")
    ## TODO: Delete that at some point, or make it have a different use (e.g., outputting time even without -d 1).
    parser.add_argument("-t", "--output_time", #FIXME: --time
                        help="(obsolete, time is always logged now) output the time it took for every step",
                        action="store_true")
    parser.add_argument("-p", "--output_optimized", # FIXME: --print
                        help="output the parallel shell script for inspection",
                        action="store_true")
    parser.add_argument("-d", "--debug",
                        type=int,
                        help="configure debug level; defaults to 0",
                        default=0)
    parser.add_argument("--log_file",
                        help="configure where to write the log; defaults to stderr.",
                        default="")
    parser.add_argument("--no_eager",
                        help="(experimental) disable eager nodes before merging nodes",
                        action="store_true")
    parser.add_argument("--no_cat_split_vanish",
                        help="(experimental) disable the optimization that removes cat with N inputs that is followed by a split with N inputs",
                        action="store_true")
    parser.add_argument("--r_split",
                        help="(experimental) use round robin split, merge, wrap, and unwrap",
                        action="store_true")
    parser.add_argument("--r_split_batch_size",
                        type=int,
                        help="(experimental) configure the batch size of r_splti (default: 100KB)",
                        default=100000)
    parser.add_argument("--dgsh_tee",
                        help="(experimental) use dgsh-tee instead of eager",
                        action="store_true")
    parser.add_argument("--speculation",
                        help="(experimental) run the original script during compilation; if compilation succeeds, abort the original and run only the parallel (quick_abort) (Default: no_spec)",
                        choices=['no_spec', 'quick_abort'],
                        default='no_spec')
    parser.add_argument("--termination",
                        help="(experimental) determine the termination behavior of the DFG. Defaults to cleanup after the last process dies, but can drain all streams until depletion",
                        choices=['clean_up_graph', 'drain_stream'],
                        default="clean_up_graph")
    parser.add_argument("--config_path",
                        help="determines the config file path. By default it is 'PASH_TOP/compiler/config.yaml'.",
                        default="")
    parser.add_argument("-v", "--version",
                        action='version',
                        version='%(prog)s {version}'.format(version=__version__))
    return

def pass_common_arguments(pash_arguments):
    arguments = []
    if (pash_arguments.no_optimize):
        arguments.append(string_to_argument("--no_optimize"))
    if (pash_arguments.dry_run_compiler):
        arguments.append(string_to_argument("--dry_run_compiler"))
    if (pash_arguments.assert_compiler_success):
        arguments.append(string_to_argument("--assert_compiler_success"))
    if (pash_arguments.avoid_pash_runtime_completion):
        arguments.append(string_to_argument("--avoid_pash_runtime_completion"))
    if (pash_arguments.output_time):
        arguments.append(string_to_argument("--output_time"))
    if (pash_arguments.output_optimized):
        arguments.append(string_to_argument("--output_optimized"))
    if(not pash_arguments.log_file == ""):
        arguments.append(string_to_argument("--log_file"))
        arguments.append(string_to_argument(pash_arguments.log_file))
    if (pash_arguments.no_eager):
        arguments.append(string_to_argument("--no_eager"))
    if (pash_arguments.r_split):
        arguments.append(string_to_argument("--r_split"))
    if (pash_arguments.dgsh_tee):
        arguments.append(string_to_argument("--dgsh_tee"))
    arguments.append(string_to_argument("--r_split_batch_size"))
    arguments.append(string_to_argument(str(pash_arguments.r_split_batch_size)))
    if (pash_arguments.no_cat_split_vanish):
        arguments.append(string_to_argument("--no_cat_split_vanish"))
    arguments.append(string_to_argument("--debug"))
    arguments.append(string_to_argument(str(pash_arguments.debug)))
    arguments.append(string_to_argument("--termination"))
    arguments.append(string_to_argument(pash_arguments.termination))
    arguments.append(string_to_argument("--speculation"))
    arguments.append(string_to_argument(pash_arguments.speculation))
    arguments.append(string_to_argument("--width"))
    arguments.append(string_to_argument(str(pash_arguments.width)))
    if(not pash_arguments.config_path == ""):
        arguments.append(string_to_argument("--config_path"))
        arguments.append(string_to_argument(pash_arguments.config_path))
    return arguments

def init_log_file():
    global pash_args
    if(not pash_args.log_file == ""):
        with open(pash_args.log_file, "w") as f:
            pass

def wait_bash_mirror(bash_mirror):
    r = bash_mirror.expect(r'EXPECT\$ ')
    assert(r == 0)
    # log(bash_mirror.before)

def query_expand_bash_mirror(bash_mirror, string):
    _, file_to_save_output = ptempfile()
    bash_mirror.sendline(f'echo -n {string} > {file_to_save_output}')
    
    wait_bash_mirror(bash_mirror)
    log("mirror done!")

    with open(file_to_save_output) as f:
        log("Ready to print output")
        data = f.read()
        log(data)
    return data

def update_bash_mirror_vars(var_file_path):
    global bash_mirror

    assert(var_file_path != ""  and not var_file_path is None)

    ## TODO: There is unnecessary write/read to this var file now.
    bash_mirror.sendline(f'PS1="EXPECT\$ "')
    wait_bash_mirror(bash_mirror)
    log("PS1 set!")

    bash_mirror.sendline(f'source {var_file_path}')
    log("sent source to mirror")
    # bash_mirror.stdin.write(f'source {var_file_path}\n')
    # bash_mirror.stdin.flush()
    wait_bash_mirror(bash_mirror)
    log("mirror done!")

    ## This is just for debugging
    query_expand_bash_mirror(bash_mirror, "$-")
    

##
## Read a shell variables file
##

def read_vars_file(var_file_path):
    global config


    config['shell_variables'] = None
    config['shell_variables_file_path'] = var_file_path
    if(not var_file_path is None):
        vars_dict = {}
        with open(var_file_path) as f:
            lines = [line.rstrip() for line in f.readlines()]

        # MMG 2021-03-09 definitively breaking on newlines (e.g., IFS) and function outputs (i.e., `declare -f`)
        for line in lines:
            words = line.split(' ')
            # FIXME is this assignment needed?
            _export_or_typeset = words[0]
            rest = " ".join(words[1:])

            space_index = rest.find(' ')
            eq_index = rest.find('=')
            var_type = None

            ## Declared but unset?
            if eq_index == -1:
                if space_index != -1:
                    var_name = rest[(space_index+1):]
                    var_type = rest[:space_index]
                else:
                    var_name = rest
                var_value = ""
            ## Set, with type
            elif(space_index < eq_index and not space_index == -1):
                var_type = rest[:space_index]

                if var_type == "--":
                    var_type = None
                
                var_name = rest[(space_index+1):eq_index]
                var_value = rest[(eq_index+1):]
            ## Set, without type
            else:
                var_name = rest[:eq_index]
                var_value = rest[(eq_index+1):]

            ## Strip quotes
            if var_value is not None and len(var_value) >= 2 and \
               var_value[0] == "\"" and var_value[-1] == "\"":
                var_value = var_value[1:-1]                
                
            vars_dict[var_name] = (var_type, var_value)

        config['shell_variables'] = vars_dict
