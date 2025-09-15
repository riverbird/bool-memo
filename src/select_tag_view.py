# coding:utf-8
import json
from asyncio import Future

import httpx
from flet.core import padding
from flet.core.app_bar import AppBar
from flet.core.checkbox import Checkbox
from flet.core.colors import Colors
from flet.core.column import Column
from flet.core.container import Container
from flet.core.icon import Icon
from flet.core.icon_button import IconButton
from flet.core.icons import Icons
from flet.core.list_view import ListView
from flet.core.progress_bar import ProgressBar
from flet.core.row import Row
from flet.core.safe_area import SafeArea
from flet.core.snack_bar import SnackBar
from flet.core.text import Text
from flet.core.textfield import TextField


class SelectTagView(Column):
    def __init__(self, page, memo_info):
        super().__init__()
        self.page = page
        self.memo_info = memo_info

        self.input_tag = TextField(
            hint_text='请输入标签',
            color=Colors.BLACK,
            border_width=0,
            bgcolor=Colors.WHITE,
            expand=True,
            adaptive=True,
            on_submit=self.on_input_tag_submit,
        )

        self.page.appbar = AppBar(
            title=self.input_tag,
            bgcolor=Colors.WHITE,
            color=Colors.BLACK,
            leading=IconButton(
                icon=Icons.ARROW_BACK,
                tooltip='返回',
                on_click=self.on_button_back_click,
            ),
            actions=[
                IconButton(
                    icon=Icons.DONE,
                    on_click=self.on_selected_button_click
                ),
            ]
        )
        self.page.drawer = None
        self.controls = [self.build_interface()]

    async def on_selected_button_click(self, e):
        ids = []
        self.progress_bar.visible = True
        self.page.update()
        if self.input_tag.value != '':
            new_tag = await self.add_tag(self.input_tag.value)
            if new_tag:
                ids.append(new_tag.get('id'))
        for item in self.list_tags.controls:
            checkbox:Checkbox = item
            if checkbox.value:
                data = checkbox.data
                ids.append(data.get('id'))
        await self.update_memo_tags(ids)

    async def update_memo_tags(self, tags):
        token = await self.page.client_storage.get_async('token')
        user_input = {'tag': tags}
        headers = {"Authorization": f'Bearer {token}'}
        if self.memo_info is None:
            return
        url = f'https://restapi.10qu.com.cn/memo/{self.memo_info.get("id")}/'
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.patch(
                    url,
                    headers=headers,
                    json=user_input,
                )
                resp.raise_for_status()
                if resp.status_code != 200:
                    snack_bar = SnackBar(Text("备忘更新失败!"))
                    self.page.overlay.append(snack_bar)
                    snack_bar.open = True
                    self.progress_bar.visible = False
                    self.page.update()
                    return
                else:
                    self.memo_info = json.loads(resp.text)
        except httpx.HTTPError as ex:
            snack_bar = SnackBar(Text(f"更新备忘失败:{str(ex)}"))
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.progress_bar.visible = False
            self.page.update()
            return
        # 跳转至主页面
        self.page.controls.clear()
        from memo_editor_view import MemoEditorView
        page_view = SafeArea(
            MemoEditorView(self.page, self.memo_info),
            adaptive=True,
            expand=True
        )
        self.page.controls.append(page_view)
        self.page.update()

    def on_input_tag_submit(self, e):
        pass

    async def add_tag(self, tag_str):
        token = await self.page.client_storage.get_async('token')
        user_id = await self.page.client_storage.get_async('user_id')
        url = 'https://restapi.10qu.com.cn/note_tag/'
        headers = {'Authorization': f'Bearer {token}'}
        user_input = {
            'user': user_id,
            'name': tag_str}
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.post(
                    url,
                    headers=headers,
                    json=user_input,
                )
                resp.raise_for_status()
                if resp.status_code != 201:
                    snack_bar = SnackBar(Text("添加标签失败!"))
                    self.page.overlay.append(snack_bar)
                    snack_bar.open = True
                    self.page.update()
                    return None
                else:
                    return json.loads(resp.text)
                # task_query_memo_tag_list = self.page.run_task(self.get_memo_tag_list)
                # task_query_memo_tag_list.add_done_callback(self.handle_memo_tag_list)
        except httpx.HTTPError as ex:
            snack_bar = SnackBar(Text(f"添加标签失败：{str(ex)}"))
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()
            return None

    def on_button_back_click(self, e):
        self.page.controls.clear()
        from memo_editor_view import MemoEditorView
        page_view = SafeArea(
            MemoEditorView(self.page, self.memo_info),
            adaptive=True,
            expand=True
        )
        self.page.controls.append(page_view)
        self.page.update()

    async def get_memo_tag_list(self) -> list | None:
        # cached_memo_tag_list_value = await self.page.client_storage.get_async('memo_tag_list')
        # cached_memo_tag_list = json.loads(cached_memo_tag_list_value) if cached_memo_tag_list_value else []
        # if cached_memo_tag_list:
        #     return cached_memo_tag_list

        self.progress_bar.visible = True
        self.page.update()
        user_id = await self.page.client_storage.get_async('user_id')
        token = await self.page.client_storage.get_async('token')
        url = f'https://restapi.10qu.com.cn/note_tag/?user={user_id}'
        headers = {"Authorization": f'Bearer {token}'}
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers=headers,
                    follow_redirects=True)
                resp.raise_for_status()
                if resp.status_code != 200:
                    return []
                data = resp.json()
                lst_category = data.get('results')
                cached_memo_tag_list_str = json.dumps(lst_category)
                await self.page.client_storage.set_async('memo_tag_list', cached_memo_tag_list_str)
                return lst_category
        except httpx.HTTPError as e:
            snack_bar = SnackBar(Text(f"查询备忘标签请求失败:{str(e)}"))
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.page.update()
        return []

    def handle_memo_tag_list(self, t:Future[list]):
        try:
            res = t.result()
        except Exception as ex:
            snack_bar = SnackBar(Text(f"获取备忘标签请求失败:{str(ex)}"))
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.progress_bar.visible = False
            self.page.update()
        else:
            lst_tags = res
            self.list_tags.controls.clear()
            memo_tags = self.memo_info.get('tag')
            for tag in lst_tags:
                self.list_tags.controls.append(
                    Checkbox(label=tag.get('name'),
                             data=tag,
                             value=tag.get('id') in memo_tags)
                )
            self.list_tags.update()
            self.progress_bar.visible = False
            self.page.update()

    def build_interface(self):
        self.list_tags = ListView(
            spacing=10,
            padding=padding.only(left=2, top=5, right=2, bottom=5),
            expand=True,
        )
        self.progress_bar = ProgressBar(
            value=None,
            bar_height=3,
            bgcolor=Colors.GREY_100,
            color=Colors.GREY_300,
            width=self.page.width
        )
        # 布局
        cols_body = Column(
            controls=[
                self.progress_bar,
                self.list_tags,
            ],
        )
        task_query_memo_tag_list = self.page.run_task(self.get_memo_tag_list)
        task_query_memo_tag_list.add_done_callback(self.handle_memo_tag_list)
        return cols_body
