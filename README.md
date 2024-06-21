## SPLaSh: Scaling Out Shell Scripts on Serverless Platforms

> _A system for deploying POSIX shell scripts to serverless._

## Running SPLaSh

To parallelize, say, `./evaluation/intro/hello-world.sh` with a parallelization degree of 2× run:

```sh
./pa.sh --serverless_exec -w 2 ./evaluation/intro/hello-world.sh
```

Run `./pa.sh --help` to get more information about the available commands.

## Installation

On Ubuntu, Fedora, and Debian, run the following to set up SPLaSh.
```sh
wget https://raw.githubusercontent.com/binpash/pash/main/scripts/up.sh
sh up.sh
export PASH_TOP="$PWD/pash/"
## Run PaSh with echo hi
"$PASH_TOP/pa.sh" -c "echo hi"
```

For more details, manual installation, or other platforms see [installation instructions](./docs/install).

## Repo Structure

This repo is a frozen version of `splash`. For the most up-to-date version, visit https://github.com/binpash/pash. The structure is as follows:

* [compiler](./compiler): Shell-dataflow translations, associated parallelization transformations, and serverless transformations/primitives.
* [docs](./docs): Design documents, tutorials, installation instructions, etc.
* [evaluation](./evaluation): Shell pipelines and example [scripts](./evaluation/other/more-scripts) used for the evaluation.
* [runtime](./runtime): Runtime components for the shell—e.g., `eager`, `split`—and serverless execution—e.g., `invoke-lambda`,`send-object`.
* [scripts](./scripts): Scripts related to continuous integration, deployment, and testing.

## Community & More

Chat:
* [Discord Server](ttps://discord.com/channels/947328962739187753/) ([Invite](https://discord.gg/6vS9TB97be))

Mailing Lists:
* [pash-devs](https://groups.google.com/g/pash-devs): Join this mailing list for discussing all things `pash`
* [pash-commits](https://groups.google.com/g/pash-commits): Join this mailing list for commit notifications

Development/contributions:
* Contribution guide: [docs/contributing](docs/contributing/contrib.md)
* Continuous Integration Server: [ci.binpa.sh](http://ci.binpa.sh)
