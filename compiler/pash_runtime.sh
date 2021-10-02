#!/bin/bash

##
## High level design. 
##
## (1) The `pash_runtime` should behave as a wrapper, saving all the necessary state:
##     - previous exit code
##     - previous set status
##     - previous variables
##     and then reverting to PaSh internal state
##
## (2) Then it should perform pash-internal work.
##
## (3) Then it should make sure to revert the exit code and `set` state to the saved values.
##
## (4) Then it should execute the inside script (either original or parallel)
##     TODO: Figure out what could be different before (1), during (4), and after (7) 
##
## (5) Then it save all necessary state and revert to pash-internal state. 
##     (At the moment this happens automatically because the script is ran in a subshell.)
##
## (6) Then it should do all left pash internal work.
##
## (7) Before exiting it should revert all exit state.
##
## Visually:
##
## -- bash -- | -- pash --
##    ...     |
##      \----(1)----\
##            |     ...
##            |     (2)
##            |     ...
##      /----(3)----/
##    ...     |
##    (4)     |
##    ...     |
##
## (The rest of the steps happen only in debug mode)
##    ...
##      \----(5)----\
##            |     ...
##            |     (6)
##            |     ...
##      /----(7)----/
##    ...     |

## TODO: Make a list/properly define what needs to be saved at (1), (3), (5), (7)
##
## Necessary for pash:
## - PATH important for PaSh but might be changed in bash
## - IFS has to be kept default for PaSh to work
##
## Necessary for bash:
## - Last PID $! (TODO)
## - Last exit code $?
## - set state $-
## - File descriptors (TODO)
## - Loop state (?) Maybe `source` is adequate for this (TODO)
## - Traos (TODO)
##
## (maybe) TODO: After that, maybe we can create cleaner functions for (1), (3), (5), (7). 
##               E.g. we can have a correspondence between variable names and revert them using them 

##
## (1)
##

## Store the previous exit status to propagate to the compiler
## export pash_previous_exit_status=$?
## The assignment now happens outside
export pash_previous_exit_status

## Store the current `set` status to pash to the inside script 
export pash_previous_set_status=$-

##
## temporary (1) -> (2)
##

## Even though this is strictly in (2) it happens here
## because it is necessary for performing the rest of (1)
pash_redir_output()
{
    ## TODO: We should properly allow for different debug levels
    ## TODO: This code is copied in pash_source_declare_vars.sh
    if [ "$PASH_DEBUG_LEVEL" -eq 0 ]; then
        > /dev/null $@
    else
        if [ "$PASH_REDIR" == '&2' ]; then
            >&2 $@
        else
            >>"$PASH_REDIR" $@
        fi
    fi
}

pash_redir_all_output()
{
    if [ "$PASH_DEBUG_LEVEL" -eq 0 ]; then
        > /dev/null 2>&1 $@
    else
        if [ "$PASH_REDIR" == '&2' ]; then
            >&2 $@
        else
            >>"$PASH_REDIR" 2>&1 $@
        fi
    fi
}

export -f pash_redir_output
export -f pash_redir_all_output

## File directory
RUNTIME_DIR=$(dirname "${BASH_SOURCE[0]}")
export PASH_REDIR="&2"
export PASH_DEBUG_LEVEL=0

## Get distro
## TODO: Move that somewhere where it happens once
if type lsb_release >/dev/null 2>&1 ; then
    distro=$(lsb_release -i -s)
elif [ -e /etc/os-release ] ; then
    distro=$(awk -F= '$1 == "ID" {print $2}' /etc/os-release)
fi

# convert to lowercase
distro=$(printf '%s\n' "$distro" | LC_ALL=C tr '[:upper:]' '[:lower:]')

## Check flags
pash_output_time_flag=1
pash_execute_flag=1
pash_speculation_flag=0 # By default there is no speculation
pash_dry_run_compiler_flag=0
pash_assert_compiler_success_flag=0
pash_checking_speculation=0
pash_checking_log_file=0
pash_checking_debug_level=0
pash_avoid_pash_runtime_completion_flag=0
for item in $@
do
    if [ "$pash_checking_speculation" -eq 1 ]; then
        pash_checking_speculation=0
        if [ "no_spec" == "$item" ]; then
            pash_speculation_flag=0
        elif [ "quick_abort" == "$item" ]; then
            ## TODO: Fix how speculation interacts with dry_run, assert_compiler_success
            pash_speculation_flag=1
        else
            pash_redir_output echo "$$: Unknown value for option --speculation"
            exit 1
        fi
    fi

    if [ "$pash_checking_log_file" -eq 1 ]; then
        pash_checking_log_file=0
        export PASH_REDIR="$item"
    fi

    if [ "$pash_checking_debug_level" -eq 1 ]; then
        pash_checking_debug_level=0
        pash_redir_output echo "$$: $item"
        export PASH_DEBUG_LEVEL=$item
    fi

    # We output time always 
    # if [ "--output_time" == "$item" ]; then
    #     pash_output_time_flag=1
    # fi

    if [ "--dry_run_compiler" == "$item" ]; then
        pash_dry_run_compiler_flag=1
    fi

    if [ "--assert_compiler_success" == "$item" ]; then
        pash_assert_compiler_success_flag=1
    fi

    if [ "--speculation" == "$item" ]; then
        pash_checking_speculation=1
    fi

    if [ "--log_file" == "$item" ]; then
        pash_checking_log_file=1
    fi

    if [ "--avoid_pash_runtime_completion" == "$item" ]; then
        pash_avoid_pash_runtime_completion_flag=1
    fi

    if [ "-d" == "$item" ] || [ "--debug" == "$item" ]; then
        pash_checking_debug_level=1
        pash_redir_output echo "$$: $item"
    fi
done

##
## temporary (2) -> (1)
##

pash_redir_output echo "$$: (1) Previous exit status: $pash_previous_exit_status"
pash_redir_output echo "$$: (1) Previous set state: $pash_previous_set_status"

## Prepare a file with all shell variables
##
## This is only needed by PaSh to expand.
##
## TODO: Maybe we can get rid of it since PaSh has access to the environment anyway?
pash_runtime_shell_variables_file="$($RUNTIME_DIR/pash_ptempfile_name.sh $distro)"
source "$RUNTIME_DIR/pash_declare_vars.sh" "$pash_runtime_shell_variables_file"
pash_redir_output echo "$$: (1) Bash variables saved in: $pash_runtime_shell_variables_file"

## Abort script if variable is unset
pash_default_set_state="huB"

## Revert the `set` state to not have spurious failures 
pash_redir_output echo "$$: (1) Bash set state at start of execution: $pash_previous_set_status"
source "$RUNTIME_DIR/pash_set_from_to.sh" "$pash_previous_set_status" "$pash_default_set_state"
pash_redir_output echo "$$: (1) Set state reverted to PaSh-internal set state: $pash_previous_set_status"

##
## (2)
##

## The first argument contains the sequential script. Just running it should work for all tests.
pash_sequential_script_file=$1

## The parallel script will be saved in the following file if compilation is successful.
pash_compiled_script_file="$($RUNTIME_DIR/pash_ptempfile_name.sh $distro)"


if [ "$pash_speculation_flag" -eq 1 ]; then
    ## Count the execution time
    pash_exec_time_start=$(date +"%s%N")
    source "$RUNTIME_DIR/pash_runtime_quick_abort.sh"
    pash_runtime_final_status=$?
    ## For now this will fail!!!
    exit 1
else
    ## TODO: Have a more proper communication protocol
    echo "Compile:${pash_compiled_script_file}| Variable File:${pash_runtime_shell_variables_file}" > "$RUNTIME_IN_FIFO"
    pash_redir_output echo "$$: (1) Daemon responds:"
    pash_redir_output cat "$RUNTIME_OUT_FIFO"
    
    pash_redir_all_output python3 "$RUNTIME_DIR/pash_runtime.py" ${pash_compiled_script_file} --var_file "${pash_runtime_shell_variables_file}" "${@:2}"
    pash_runtime_return_code=$?
    pash_redir_output echo "$$: Compiler exited with code: $pash_runtime_return_code"
    if [ "$pash_runtime_return_code" -ne 0 ] && [ "$pash_assert_compiler_success_flag" -eq 1 ]; then
        pash_redir_output echo "$$: ERROR: Compiler failed with error code: $pash_runtime_return_code"
        exit 1
    fi

    ##
    ## (3)
    ##

    ## Count the execution time
    pash_exec_time_start=$(date +"%s%N")

    ## If the compiler failed or if we dry_run the compiler, we have to run the sequential
    if [ "$pash_runtime_return_code" -ne 0 ] || [ "$pash_dry_run_compiler_flag" -eq 1 ]; then
        pash_script_to_execute="${pash_sequential_script_file}"
    else
        pash_script_to_execute="${pash_compiled_script_file}"
    fi

    ##
    ## (4)
    ##
    source "$RUNTIME_DIR/pash_wrap_vars.sh" ${pash_script_to_execute}
    pash_runtime_final_status=$?

    ## We only want to execute (5) and (6) if we are in debug mode and it is not explicitly avoided
    if [ "$PASH_DEBUG_LEVEL" -ne 0 ] && [ "$pash_avoid_pash_runtime_completion_flag" -ne 1 ]; then
        ##
        ## (5)
        ##

        ## Prepare a file for the output shell variables to be saved in
        pash_output_variables_file="$($RUNTIME_DIR/pash_ptempfile_name.sh $distro)"
        # pash_redir_output echo "$$: Output vars: $pash_output_variables_file"

        ## Prepare a file for the `set` state of the inner shell to be output
        pash_output_set_file="$($RUNTIME_DIR/pash_ptempfile_name.sh $distro)"

        source "$RUNTIME_DIR/pash_runtime_shell_to_pash.sh" ${pash_output_variables_file} ${pash_output_set_file}

        ##
        ## (6)
        ##
        source "$RUNTIME_DIR/pash_runtime_complete_execution.sh"
    fi
fi

