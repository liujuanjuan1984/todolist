import os
import sys
import datetime
import pandas as pd
import re
from typing import List, Dict
from rumpy import RumClient
from officepy import Stime
import dataclasses


@dataclasses.dataclass
class TodoOne:
    """a todo"""

    trx_id: str
    task: str
    create_at: str
    update_at: str = None
    status: int = 0
    memo: str = ""

    def __post_init__(self):
        self.update_at = self.update_at or self.create_at


class ToDoList(RumClient):
    """RUM 应用想法：待办清单"""

    def data(self, pubkeys) -> Dict:
        """
        init todolist data
        pubkeys: list of pubkey 某个人可能有多个pubkey参与待办清单数据更新，比如多设备，或自己更换了账号
        """

        data = {}
        _info = {"like": 1, "dislike": -1}

        for trx in self.group.trxs_by(pubkeys):  # 特定的人发布的信息才算数
            if trx["Publisher"] not in pubkeys:
                continue

            trxtype = self.group.trx_type(trx)
            ts = str(Stime.ts2datetime(trx.get("TimeStamp")))

            if trxtype in _info:
                todoid = trx["Content"]["id"]
                if todoid in data:
                    data[todoid]["status"] += _info[trxtype]  # 点赞行为更新 todo 状态
                    data[todoid]["update_at"] = ts

            try:
                note = trx["Content"]["content"]
            except:
                continue

            if trxtype in ["text_only", "image_text"]:  # 以 todo: 开头的文本推送，视为一条待办
                if note[:5].lower() in ["todo:", "todo："]:
                    data[trx["TrxId"]] = TodoOne(
                        **{"trx_id": trx["TrxId"], "create_at": ts, "task": note}
                    ).__dict__

            elif trxtype in ["reply"]:  # 对待办添加评论，视为 memo
                todoid = trx["Content"]["inreplyto"]["trxid"]
                if todoid in data:
                    data[todoid]["memo"] += f"\n### {ts}\n{note}\n"
        data = self._remove_repeat(data)  # 移除被标记为重复的任务
        return data

    def todo_pd(self, pubkeys, today=None, data=None):
        """
        return dataframe type data of todos
        today:str 2021-11-21
        """
        data = data or self.data(pubkeys)

        df = pd.DataFrame(data).T
        # all todos
        alltodo = df[df["status"] == 0]
        # todos for today
        today = today or f"{datetime.date.today()}"
        todaytodo = alltodo[alltodo["task"].str.find(today) >= 0]
        return alltodo, todaytodo

    def todo(self, pubkeys, today=None, data=None):
        """return dict type data of todos"""
        data = data or self.data(pubkeys)

        # all todos
        alltodo = {}
        for tid in data:
            # 只有数值为 0 才是待办
            if data[tid]["status"] == 0:
                alltodo[tid] = data[tid]
        # todos for today

        todaytodo = {}
        for tid in alltodo:
            if alltodo[tid]["task"].find(today or f"{datetime.date.today()}") >= 0:
                todaytodo[tid] = data[tid]

        return alltodo, todaytodo

    def _remove_repeat(self, data):
        """如果某条待办的描述中包含：REPEAT:trx_id，或 ::REPEAT:: 表示此条 todo 与 指定 trx_id 的数据重复，则该条数据舍弃。"""
        newdata = {}
        for i in data:
            flag = True
            pttn = r"REPEAT:([\w\d]{8}\-[\w\d]{4}-[\w\d]{4}-[\w\d]{4}-[\w\d]{12})"
            irlt = re.findall(pttn, data[i]["memo"])
            jrlt = re.findall("::REPEAT::", data[i]["memo"])
            if len(irlt) > 0 or len(jrlt) > 0:
                continue
            newdata[i] = data[i]
        return newdata

    def review_daily(self, data=None, is_post=False):
        data = data or self.data()
        info = {}
        for trx_id in data:
            i = data[trx_id]
            create = i["create_at"][:10]
            if create not in info:
                info[create] = {"create": [trx_id], "update": []}
            else:
                info[create]["create"].append(trx_id)
            if i["status"] >= 1:
                info[create]["update"].append(trx_id)

        sn = sd = 0
        note = ""
        for day in info:
            n = len(info[day]["create"])
            d = len(info[day]["update"])
            view = Stime.view_percent(f"{day} ", d / n, wide=20)
            note = f"{view} {d}/{n}\n{note}"
            sd += d
            sn += n
        view = Stime.view_percent("待办清单整体", sd / sn, wide=20)
        note = f"{view} {sd}/{sn}\n\n{note}"
        if is_post:
            return self.post_text(note)
        return note
