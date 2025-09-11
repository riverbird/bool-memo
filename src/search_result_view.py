# coding:utf-8
from datetime import datetime

import httpx
from flet import Column, Row, Icons, Colors
from flet.core import border, padding
from flet.core.app_bar import AppBar
from flet.core.border import BorderSide, BorderSideStrokeAlign
from flet.core.box import BoxShadow
from flet.core.container import Container
from flet.core.divider import Divider
from flet.core.icon_button import IconButton
from flet.core.list_view import ListView
from flet.core.popup_menu_button import PopupMenuItem, PopupMenuButton
from flet.core.progress_bar import ProgressBar
from flet.core.safe_area import SafeArea
from flet.core.snack_bar import SnackBar
from flet.core.text import Text
from flet.core.types import MainAxisAlignment, CrossAxisAlignment


class SearchResultView(Column):
    def __init__(self, page, str_keyword):
        super().__init__()
        self.page = page
        self.str_keyword:str = str_keyword

        content = self.build_interface()
        self.controls = [content]
        self.page.appbar = AppBar(
            title=Text(f'搜索结果:{self.str_keyword}'),
            bgcolor=Colors.WHITE,
            color=Colors.BLACK,
            leading=IconButton(
                icon=Icons.ARROW_BACK,
                tooltip='返回',
                on_click=self.on_btn_back_click,
            ),
            actions=[],
        )
        self.page.floating_action_button = None
        self.page.drawer = None
        self.page.run_task(self.search_memo_list, str_keyword)

    async def search_memo_list(self, str_keyword):
        self.progress_bar.visible = True
        self.page.update()
        self.note_list.controls.clear()
        user_id = await self.page.client_storage.get_async('user_id')
        token = await self.page.client_storage.get_async('token')
        req_url = f'https://restapi.10qu.com.cn//memo/?search={str_keyword}&user={user_id}&ordering=-create_time'
        headers = {"Authorization": f'Bearer {token}'}
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(
                    req_url,
                    headers=headers,
                )
                resp.raise_for_status()
                if resp.status_code != 200:
                    snack_bar = SnackBar(Text("搜索用户日记列表请求失败，请刷新重试。"))
                    self.page.overlay.append(snack_bar)
                    snack_bar.open = True
                    self.progress_bar.visible = False
                    self.page.update()
                    return
                data = resp.json()
                memos = data.get('results')
                if not memos:
                    self.progress_bar.visible = False
                    self.page.update()
                    return
                for memo in memos:
                    dt_time = datetime.strptime(memo.get('update_time'), '%Y-%m-%dT%H:%M:%S.%f')
                    str_date = dt_time.strftime("%Y-%m-%d %H:%M:%S")
                    memo_item = Container(
                        data=memo,
                        margin=3,
                        adaptive=True,
                        border_radius=2,
                        bgcolor=Colors.WHITE,
                        padding=padding.only(left=5, top=5, right=5, bottom=5),
                        on_click=self.on_memo_item_click,
                        border=border.only(
                            None, None, None,
                            BorderSide(1, Colors.GREY_200, BorderSideStrokeAlign.OUTSIDE)),
                        shadow=BoxShadow(spread_radius=0, blur_radius=0,
                                         color=Colors.WHITE, offset=(2, 2)),
                        content=Column(
                            expand=True,
                            controls=[
                                Row(
                                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        Text(
                                            value=str_date,
                                            size=12,
                                            color=Colors.GREY,
                                        ),
                                        PopupMenuButton(
                                            icon=Icons.MORE_HORIZ_OUTLINED,
                                            icon_color=Colors.GREY,
                                            items=[
                                                PopupMenuItem(
                                                    icon=Icons.COPY_OUTLINED,
                                                    text='复制全文',
                                                    data=memo,
                                                    on_click=self.on_copy_content
                                                ),
                                                PopupMenuItem(
                                                    icon=Icons.EDIT_OUTLINED,
                                                    text='编辑',
                                                    data=memo,
                                                    on_click=self.on_edit_content
                                                ),
                                                Divider(),
                                                PopupMenuItem(
                                                    icon=Icons.DELETE,
                                                    text='删除',
                                                    data=memo,
                                                    on_click=self.on_delete_memo
                                                )
                                            ],
                                            # icon_color=Colors.WHITE,
                                        )
                                    ]
                                ),
                                Text(
                                    value=memo.get('content'),
                                    size=15,
                                    no_wrap=False,
                                    color=Colors.BLACK87
                                ),
                            ],
                        ),
                    )
                    self.note_list.controls.append(memo_item)
                self.page.update()
        except httpx.HTTPError as e:
            snack_bar = SnackBar(Text(f"查询用户备忘列表请求失败，请刷新重试。{str(e)}"))
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.progress_bar.visible = False
            self.page.update()
            return
        self.progress_bar.visible = False
        self.page.update()

    def on_copy_content(self, e):
        memo_info = e.control.data
        self.page.set_clipboard(memo_info.get('content'))

    def on_delete_memo(self, e):
        memo_info = e.control.data
        self.page.run_task(self.delete_memo, memo_info, e)

    def on_edit_content(self, e):
        memo_data = e.control.data
        self.page.controls.clear()
        from memo_editor_view import MemoEditorView
        page_view = SafeArea(
            MemoEditorView(self.page, memo_data),
            adaptive=True,
            expand=True
        )
        self.page.controls.append(page_view)
        self.page.update()

    async def delete_memo(self, memo_info, e):
        token = await self.page.client_storage.get_async('token')
        memo_id = memo_info.get("id")
        url = f'https://restapi.10qu.com.cn/memo/{memo_id}/'
        headers = {"Authorization": f'Bearer {token}'}
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.delete(
                    url,
                    headers=headers,
                )
                resp.raise_for_status()
                if resp.status_code != 204:
                    snack_bar = SnackBar(Text("删除备忘失败!"))
                    e.control.page.overlay.append(snack_bar)
                    snack_bar.open = True
                    e.control.page.update()
                    return
        except httpx.HTTPError as ex:
            snack_bar = SnackBar(Text(f"删除备忘失败:{str(ex)}"))
            e.control.page.overlay.append(snack_bar)
            snack_bar.open = True
            e.control.page.update()
            return

    async def on_button_refresh_click(self, e):
        await self.search_memo_list(self.str_keyword)

    def on_memo_item_click(self, e):
        memo_data = e.control.data
        self.page.controls.clear()
        from memo_editor_view import MemoEditorView
        page_view = SafeArea(
            MemoEditorView(self.page, memo_data),
            adaptive=True,
            expand=True
        )
        self.page.controls.append(page_view)
        self.page.update()

    def on_btn_back_click(self, e):
        self.page.controls.clear()
        from search_memo_view import SearchMemoView
        page_view = SafeArea(
            SearchMemoView(self.page),
            adaptive=True,
            expand=True
        )
        self.page.controls.append(page_view)
        self.page.update()

    def build_interface(self):
        # 笔记列表
        self.note_list = ListView(
            spacing=10,
            padding=5,
            # height=self.page.height - 120
            expand=True,
        )
        self.progress_bar = ProgressBar(
            value=None,
            bar_height=3,
            bgcolor=Colors.GREY_100,
            color=Colors.GREY_300,
            width=self.page.width,
            visible=False,
        )
        col_notes = Column(
            controls = [
                self.progress_bar,
                self.note_list,
            ],
            alignment=MainAxisAlignment.START,
            horizontal_alignment=CrossAxisAlignment.START,
            adaptive=True,
            width=self.page.width,
        )
        return col_notes
