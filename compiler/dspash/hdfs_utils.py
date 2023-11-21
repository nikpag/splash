import json
from collections import namedtuple
from threading import Event, Thread
from typing import List

import requests

# if you are running this outside of the docker container
# you may want to change this to localhost for testing
host = "localhost"
port = "9870"

daemon_quit = Event()


HDFSBlock = namedtuple("HDFSBlock", ["path", "hosts"])


# naming of this class and it's functionality is not ideal ¯\_(ツ)_/¯
# however, this class has hard to miss dependencies so it's hard to modify
# for example I was thinking about removing the dumps() method as I was thinking
# this class is only written but not read. However, it seems there may be go client
# code that reads it. See $DISH_TOP/runtime/dspash/file_reader/dfs_split_reader
class HDFSFileConfig:
    def __init__(self, blocks: List[List[str]]):
        self.blocks: List[HDFSBlock] = []
        for inner in blocks:
            # get_hdfs_block_path is a helper function defined in hdfs_utils.sh
            # it takes two arguments: directory name and block id and returns the path of the block
            # however here, path is not an exact path but a command that will be invoked on workers
            path = f"$(get_hdfs_block_path {inner[0]} {inner[1]})"
            hosts = inner[2:]
            self.blocks.append(HDFSBlock(path, hosts))

    def _serialize(self):
        data = {"blocks": []}
        for path, hosts in self.blocks:
            data["blocks"].append({"path": path, "hosts": hosts})
        return data

    def dumps(self):
        data = self._serialize()
        return json.dumps(data)

    def dump(self, filepath):
        data = self._serialize()
        with open(filepath, "w") as f:
            json.dump(data, f)

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, HDFSFileConfig):
            return False
        return self.blocks == __o.blocks


def file_to_blocks(filepath: str) -> List[List[str]]:
    """
    Takes an hdfs file path as an input and returns a list of inner lists.
    For each inner list, following are true:
        - corresponds to a block
        - first element is the directory name used by hdfs_utils.sh
        - second element is the block id
        - rest of the elements are the ip addresses of the datanodes that have the block

    Example output:
    [['BP-68286741-172.20.0.2-1700503545710', 'blk_1073741830', '172.22.0.3:9866', '172.22.0.4:9866', '172.22.0.7:9866'],
     ['BP-68286741-172.20.0.2-1700503545710', 'blk_1073741831', '172.22.0.3:9866', '172.22.0.5:9866', '172.22.0.7:9866'],
     ['BP-68286741-172.20.0.2-1700503545710', 'blk_1073741832', '172.22.0.3:9866', '172.22.0.5:9866', '172.22.0.4:9866'],
     ['BP-68286741-172.20.0.2-1700503545710', 'blk_1073741833', '172.22.0.5:9866', '172.22.0.6:9866', '172.22.0.7:9866']]
    """
    outer = []

    url = f"http://{host}:{port}/fsck?ugi=root&files=1&blocks=1&locations=1&path={filepath}"
    r = requests.get(url=url)

    save_blocks = False
    for line in r.text.splitlines():
        if line.startswith(filepath):
            size = int(line.split()[1])
            assert size > 0
            save_blocks = True
            continue

        if save_blocks:
            if len(line) == 0:
                break

            space_ix = line.find(" ")
            semi_ix = line.find(":")
            under_ix = line.find("_", semi_ix + 5)

            dir_name = line[space_ix + 1 : semi_ix]
            block_id = line[semi_ix + 1 : under_ix]

            inner = []
            inner.append(dir_name)
            inner.append(block_id)

            after = 0
            while True:
                # len("DatanodeInfoWithStorage") + 1 = 24
                ip_ix = line.find("DatanodeInfoWithStorage", after) + 24

                # -1 + 24 = 23
                if ip_ix == 23:
                    break

                comma_ix = line.find(",", ip_ix)
                ip_addr = line[ip_ix:comma_ix]
                after = comma_ix

                inner.append(ip_addr)

            outer.append(inner)

    return outer


def block_to_nodes(block_id: str) -> List[str]:
    """
    Takes a block id as an input and returns a list.
    First element of the list is the hdfs file path this block belongs to.
    Rest of the elements are the ip addresses of the datanodes that have the block.

    Example:
    input: blk_1073741830
    output: ['/500mib-file', '172.22.0.3:9866', '172.22.0.4:9866', '172.22.0.7:9866']
    """
    res = []

    url = f"http://{host}:{port}/fsck?ugi=root&blockId={block_id}+&path=%2F"
    t = requests.get(url=url).text

    # len("Block belongs to: ") = 18
    file_ix_start = t.find("Block belongs to: ") + 18
    file_ix_end = t.find("\n", file_ix_start)

    filepath = t[file_ix_start:file_ix_end]
    res.append(filepath)

    all_blocks = file_to_blocks(filepath)
    for block in all_blocks:
        if block[1] == block_id:
            for addr in block[2:]:
                res.append(addr)
            break

    return res


def get_live_nodes():
    """
    Returns a dictionary where keys are the ip addresses of the datanodes and values are some related information.
    Please be careful as the keys can contain hostnames.

    Example output:
    {
        "c107c1d2c0f0:9866": {
            "infoAddr": "172.22.0.5:9864",
            "infoSecureAddr": "172.22.0.5:0",
            "xferaddr": "172.22.0.5:9866",
            "lastContact": 0,
            "usedSpace": 393220096,
            "adminState": "In Service",
            "nonDfsUsedSpace": 16368644096,
            "capacity": 1081101176832,
            "numBlocks": 8,
            "version": "3.2.2",
            "used": 393220096,
            "remaining": 1009346957312,
            "blockScheduled": 0,
            "blockPoolUsed": 393220096,
            "blockPoolUsedPercent": 0.03637218,
            "volfails": 0,
            "lastBlockReport": 136
        },
        "15d32bc24bfd:9866": {
            "infoAddr": "172.22.0.3:9864",
            "infoSecureAddr": "172.22.0.3:0",
            "xferaddr": "172.22.0.3:9866",
            ...
        },
        "16489dccb5b2:9866": {
            ...
        },
        "27c75d6187d8:9866": {
            ...
        },
        "5783c1a1a370:9866": {
            ...
        }
    }
    """
    query = "Hadoop:service=NameNode,name=NameNodeInfo"
    url = f"http://{host}:{port}/jmx?qry={query}"
    r = requests.get(url)

    return json.loads(json.loads(r.text)["beans"][0]["LiveNodes"])


def __hdfs_deamon():
    daemon_state = get_live_nodes()
    while not daemon_quit.is_set():
        daemon_quit.wait(3)
        new_deamon_state = get_live_nodes()
        if new_deamon_state.keys() != daemon_state.keys():
            # TODO: notify the scheduler
            print("Notify daemon crashed")

        daemon_state = new_deamon_state


def start_hdfs_deamon():
    Thread(target=__hdfs_deamon).start()


def stop_hdfs_deamon():
    daemon_quit.set()


def get_file_config(filepath: str) -> HDFSFileConfig:
    # Workaround included quotation marks when cat is called with this notation"${IN}"
    # TODO: this should be fixed somewhere higher in the stack
    filepath = filepath.lstrip('"').rstrip('"')
    blocks = file_to_blocks(filepath)
    return HDFSFileConfig(blocks)


# used for testing
if __name__ == "__main__":
    # print(file_to_blocks("/README.md"))
    # print(get_live_nodes())
    # print(file_to_blocks("/500mib-file"))
    print(block_to_nodes("blk_1073741830"))
