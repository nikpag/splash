import argparse
import traceback

from annotations import *
import config
import pash_runtime
from util import *

##
# A Daemon responding to requests for compilation
##
# Note: Not an actual daemon with the strict Unix sense
##

# TODO: Rename the pash_runtime to pash_compiler and this to pash_daemon

# TODO: Should we maybe use sockets instead of fifos?

# TODO: Fix the daemon logging.


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input", help="the input fifo from which the daemon will read its input")
    parser.add_argument(
        "output", help="the output fifo to which the daemon will write its output")
    config.add_common_arguments(parser)
    args, unknown_args = parser.parse_known_args()

    return args

# Initialize the daemon


def init():
    args = parse_args()
    config.pash_args = args

    # Load the configuration
    if not config.config:
        config.load_config(args.config_path)

    # Load annotations
    config.annotations = load_annotation_files(
        config.config['distr_planner']['annotations_dir'])

    pash_runtime.runtime_config = config.config['distr_planner']

    return args


def success_response(string):
    return f'OK: {string}\n'


def error_response(string):
    return f'ERROR: {string}\n'


class Scheduler:
    """ Takes care of running processes in parallel if there is no conflict. 
    The scheduler relies on the fact that process will wait for a compilation response.
    This allows it to control wether to allow the next process to run or wait for all other process.
    Flow:
        input cmd -> 
                    |   Compile -> 
                            1- Wait for any unsafe processes to finish
                            2- Compile and check for success and any conficts 
                                - no side effects -> allow to run in parallel by sending a response
                                - failed or conflict -> wait for all process to exit then run this process in unsafe mode

                    |   Exit process_id -> remove process_id from the list of running processes

                    |   Done -> no more pipelines -> wait for all processes to finish and exit
    """

    def __init__(self):
        self.input_fids = set()
        self.output_fids = set()
        self.process_fids = {}  # map process_id -> (input_fids, output_fids)
        self.next_id = 0
        self.running_procs = 0
        self.unsafe_running = False
        self.done = False

    def check_fids_safety(self, process_id):
        proc_input_fids, proc_output_fids = self.process_fids[process_id]
        all_proc_fids = proc_input_fids.union(proc_output_fids)
        if self.output_fids.intersection(all_proc_fids) or self.input_fids.intersection(proc_output_fids):
            return False
        return True

    def compile_and_add(self, compiled_script_file, var_file, input_ir_file):
        self.wait_unsafe()
        process_id = self.get_next_id()
        run_parallel = False
        # Read any shell variables files if present
        config.read_vars_file(var_file)
        ast_or_ir = pash_runtime.compile_ir(
            input_ir_file, compiled_script_file, config.pash_args)

        if ast_or_ir == None:
            response = error_response(f'{process_id} failed to compile')
        else:
            response = success_response(
                f'{process_id} {compiled_script_file} {var_file} {input_ir_file}')

            proc_input_fids = set(map(lambda out: str(out.resource) if str(
                out.resource) != "None" else out, ast_or_ir.all_input_fids()))
            proc_output_fids = set(map(lambda out: str(out.resource) if str(
                out.resource) != "None" else out, ast_or_ir.all_output_fids()))

            self.process_fids[process_id] = (proc_input_fids, proc_output_fids)

            run_parallel = self.check_fids_safety(process_id)
            if run_parallel:
                self.input_fids = self.input_fids.union(proc_input_fids)
                self.output_fids = self.output_fids.union(proc_output_fids)

        if not run_parallel:
            self.wait_for_all()
            self.unsafe_running = True

        self.running_procs += 1
        self.send_output(response)

    def remove_process(self, process_id):
        if process_id in self.process_fids:
            proc_input_fids, proc_output_fids = self.process_fids[process_id]
            self.input_fids -= proc_input_fids
            self.output_fids -= proc_output_fids
            del self.process_fids[process_id]

        self.running_procs -= 1
        if self.running_procs == 0:
            self.unsafe_running = False

    def get_next_id(self):
        self.next_id += 1
        return self.next_id

    def wait_for_all(self):
        while self.running_procs > 0:
            input_cmd = self.wait_input()
            # must be exit command or something is wrong
            if (input_cmd.startswith("Exit:")):
                self.remove_process(int(input_cmd.split(":")[1]))
            else:
                raise Exception(
                    f"Command should be exit but it was {input_cmd}")

    def wait_unsafe(self):
        if self.unsafe_running:
            assert(self.running_procs == 1)
            self.wait_for_all()
            self.unsafe_running = False

    def parse_and_run_cmd(self, input_cmd):
        if(input_cmd.startswith("Compile")):
            compiled_script_file, var_file, input_ir_file = self.__parse_compile_command(
                input_cmd)
            self.compile_and_add(compiled_script_file, var_file, input_ir_file)
        elif (input_cmd.startswith("Exit")):
            self.remove_process(int(input_cmd.split(":")[1]))
        elif (input_cmd.startswith("Done")):
            self.wait_for_all()
            self.send_output("All finished")
            self.done = True
        else:
            self.send_output(error_response(
                f'Unsupported command: {input_cmd}'))

    def wait_input(self):
        input_cmd = ""
        with open(self.in_filename) as fin:
            input_cmd = fin.read()
            input_cmd = input_cmd.rstrip()
        return input_cmd

    def send_output(self, message):
        """ This function should only be called if the output pipe is already opened. It will also close the opened fout pipe """
        assert(not self.fout.closed)
        self.fout.write(message)
        self.fout.flush()
        self.fout.close()

    def __parse_compile_command(self, input):
        try:
            components = input.rstrip().split("|")
            compiled_script_file = components[0].split(":")[1]
            var_file = components[1].split(":")[1]
            input_ir_file = components[2].split(":")[1]
            return compiled_script_file, var_file, input_ir_file
        except:
            raise Exception(f'Parsing failure for line: {input}')

    def run(self, in_filename, out_filename):
        self.in_filename = in_filename
        self.out_filename = out_filename
        while not self.done:
            # Process a single request
            input_cmd = self.wait_input()
            if not input_cmd:
                continue

            # After exit we don't send anything to the client so we don't open the fout pipe
            if (not input_cmd.startswith("Exit:")):
                self.fout = open(out_filename, "w")

            self.parse_and_run_cmd(input_cmd)


def main():
    args = init()
    scheduler = Scheduler()
    scheduler.run(in_filename=args.input, out_filename=args.output)


if __name__ == "__main__":
    main()
