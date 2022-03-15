import pygame as pg
from pygame.color import THECOLORS as COLORS
from time import sleep
from datetime import datetime
from tkinter import *
from tkinter import messagebox
from todolist import ToDoList
from rumpyconfig import RumpyConfig
from config import *

# 尺寸
SCREEN_X = 1000
SCREEN_Y = 800
BOX_Y = 50
LIST_Y = 36
LINE_WEIGHT = 1
NUM = 19  # 单个page所显示的待办数量
VIEW_NUM = 3  # view界面所占用的高度，是3个list高度


def _asku(text=""):
    return messagebox.askokcancel("待办清单 二次确认", f"{text}\n是否完成？")


def _msg(text=""):
    messagebox.showinfo("待办清单 新消息", text)


def draw_lines(screen):
    # 绘制背景色、底框线条
    screen.fill(COLORS["white"])
    # 横向线条
    for i in range(VIEW_NUM, SCREEN_Y // LIST_Y):
        pg.draw.aaline(
            screen, COLORS["grey"], (0, LIST_Y * i), (SCREEN_X, LIST_Y * i), LINE_WEIGHT
        )
    # 纵向线条
    pg.draw.aaline(
        screen,
        COLORS["grey"],
        (BOX_Y, VIEW_NUM * LIST_Y),
        (BOX_Y, SCREEN_Y),
        LINE_WEIGHT,
    )
    pg.draw.aaline(
        screen,
        COLORS["grey"],
        (SCREEN_X - BOX_Y, VIEW_NUM * LIST_Y),
        (SCREEN_X - BOX_Y, SCREEN_Y),
        LINE_WEIGHT,
    )

    # 选中条目
    if y >= (VIEW_NUM - 1) * BOX_Y:
        pg.draw.rect(
            screen,
            COLORS["blue"],
            (BOX_Y, LIST_Y * (y // LIST_Y), SCREEN_X, LIST_Y),
            VIEW_NUM * LINE_WEIGHT,
        )


def draw_view(screen, page, pages, info):
    # 概览
    txt = font32.render("上一页", True, COLORS["brown"])
    screen.blit(txt, (SCREEN_X - 2 * BOX_Y, 0))
    txt = font32.render("下一页", True, COLORS["brown"])
    screen.blit(txt, (SCREEN_X - 2 * BOX_Y, LIST_Y))
    txt = font32.render(f"{page+1}/{pages + 1}页", True, COLORS["black"])
    screen.blit(txt, (SCREEN_X - 2 * BOX_Y, 2 * LIST_Y))
    # 统计
    for i, text in enumerate(info):
        txt = font32.render(text, True, COLORS["black"])
        screen.blit(txt, (0, LIST_Y * i))


def draw_todos(screen, pagedata):
    screendata = []
    for i, k in enumerate(pagedata):
        # 清单文本
        todotext = pagedata[k]["task"].split("\n")[0]
        if len(todotext) > 45:
            todotext = todotext[5:45] + "..."
        txt = font32.render(todotext, True, COLORS["black"])
        screen.blit(txt, (BOX_Y + 5, (i + 3) * LIST_Y + 5))
        # 清单按钮
        txt = font48.render("□", True, COLORS["black"])
        screen.blit(txt, (5, (i + 3) * LIST_Y))
        # 详情
        txt = font32.render("详情", True, COLORS["black"])
        screen.blit(txt, (SCREEN_X - BOX_Y + 2, (i + 3) * LIST_Y + 5))
        screendata.append(k)
    return screendata


def pagedata(alltodo, page):
    data = [alltodo[k] for k in alltodo]
    _pagedata = data[page * NUM : page * NUM + NUM]
    return {i["trx_id"]: i for i in _pagedata}


def todolist_data():

    client = ToDoList(**RumpyConfig.GUI)
    client.group_id = GROUP_ID
    data = client.data(PUBKEYS)
    alltodo, todaytodo = client.todo(PUBKEYS)
    info = [i for i in client.review_daily(data).split("\n") if len(i) > 10][:3]
    pages = len(alltodo) // NUM
    return pages, info, alltodo


pg.init()
font32 = pg.font.SysFont("方正粗黑宋简体", 18)
font48 = pg.font.SysFont("方正粗黑宋简体", 28)
screen = pg.display.set_mode([SCREEN_X, SCREEN_Y])
Tk().wm_withdraw()  # to hide the main window
y, x = 0, 0
page = 0

pages, info, alltodo = todolist_data()
running = True

while running:
    # 检测鼠标事件
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
            break
        # 只判断鼠标点击
        elif event.type == pg.MOUSEBUTTONUP:
            x, y = event.pos[0], event.pos[1]
            if x >= SCREEN_X - 2 * BOX_Y:
                # 翻页
                if y <= LIST_Y:
                    page = max(0, page - 1)
                    print("上页", page)
                elif y <= 2 * LIST_Y:
                    page = min(len(alltodo) // NUM, page + 1)
                    print("下页", page)

            # 检查索引
            _kid = y // LIST_Y - VIEW_NUM
            if _kid < 0:
                continue
            if _kid > len(_pagedata):
                continue

            k = screendata[_kid]
            # 二次弹窗，勾选任务完成
            if x <= BOX_Y:
                if _asku(alltodo[k]["todo"]):
                    # 任务完成，要更新数据。
                    if t.update_todo(alltodo[k]["trx_id"], 1):
                        print(alltodo[k]["todo"], "is done.")
                        sleep(120)
                        pages, info, alltodo = todolist_data()
            # 查看单条任务详情
            if x >= SCREEN_X - BOX_Y and y >= LIST_Y * 3:
                _info = "".join(
                    [f"{alltodo[k][i]}\n" for i in ["create_at", "task", "memo"]]
                )
                _msg(_info)

    draw_lines(screen)  # 背景，线条等
    draw_view(screen, page, pages, info)  # 概览
    _pagedata = pagedata(alltodo, page)  # 获取分页数据
    screendata = draw_todos(screen, _pagedata)  # 当前页数据
    pg.display.flip()


print(datetime.now(), "have a nice try.")
