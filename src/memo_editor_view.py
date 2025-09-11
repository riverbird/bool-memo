# coding:utf-8
import json
import httpx
from flet.core.app_bar import AppBar
from flet.core.colors import Colors
from flet.core.column import Column
from flet.core.container import Container
from flet.core.icon_button import IconButton
from flet.core.icons import Icons
from flet.core.popup_menu_button import PopupMenuButton, PopupMenuItem
from flet.core.progress_bar import ProgressBar
from flet.core.row import Row
from flet.core.safe_area import SafeArea
from flet.core.snack_bar import SnackBar
from flet.core.text import Text
from flet.core.types import MainAxisAlignment
from components.custom_text_field import CustomTextField


class MemoEditorView(Column):
    def __init__(self, page, memo_info):
        super().__init__()
        self.page = page
        self.memo_info = memo_info

        self.controls = [
            self.build_interface(),
        ]

        memo_menu_btn = PopupMenuButton(
            items=[
                PopupMenuItem(
                    icon=Icons.COPY_OUTLINED,
                    text='复制全文',
                    on_click=self.on_copy_content
                ),
                PopupMenuItem(
                    icon=Icons.DELETE,
                    text='删除',
                    on_click=self.on_delete_memo
                )
            ],
            # icon_color=Colors.WHITE,
        )
        self.page.appbar = AppBar(
            title=Text(''),
            bgcolor=Colors.WHITE,
            color=Colors.BLACK,
            leading=IconButton(
                icon=Icons.ARROW_BACK,
                tooltip='保存并返回',
                on_click=self.on_button_save_click,
            ),
            actions=[memo_menu_btn],
        )
        self.page.floating_action_button = None
        self.page.drawer = None
        # self.init_diary_type()

    async def get_memo_tag_list(self) -> list|None:
        cached_memo_tag_list_value = await self.page.client_storage.get_async('memo_tag_list')
        cached_memo_tag_list = json.loads(cached_memo_tag_list_value) if cached_memo_tag_list_value else []
        if cached_memo_tag_list:
            return cached_memo_tag_list
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
                    return None
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

    def on_copy_content(self, e):
        content = self.editor.value
        self.page.set_clipboard(content)

    def on_delete_memo(self, e):
        self.page.run_task(self.delete_memo, e)

    async def delete_memo(self, e):
        token = await self.page.client_storage.get_async('token')
        memo_id = self.memo_info.get("id")
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

        # 跳转至主页
        self.page.controls.clear()
        from main_view import MainView
        page_view = SafeArea(
            MainView(self.page),
            adaptive=True,
            expand=True
        )
        self.page.controls.append(page_view)
        self.page.update()

    async def on_button_save_click(self, e):
        str_content = self.editor.value
        self.progress_bar.visible = True
        self.page.update()
        token = await self.page.client_storage.get_async('token')
        user_id = await self.page.client_storage.get_async('user_id')
        user_input = {'user': user_id,
                      'content': str_content}
        headers = {"Authorization": f'Bearer {token}'}
        if self.memo_info is None:
            return
        url = f'https://restapi.10qu.com.cn/memo/{self.memo_info.get("id")}/'
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.put(
                    url,
                    headers=headers,
                    json=user_input,
                )
                resp.raise_for_status()
                if resp.status_code != 200:
                    snack_bar = SnackBar(Text("备忘更新失败!"))
                    e.control.page.overlay.append(snack_bar)
                    snack_bar.open = True
                    e.control.page.update()
                    return
        except httpx.HTTPError as ex:
            snack_bar = SnackBar(Text(f"更新备忘失败:{str(ex)}"))
            e.control.page.overlay.append(snack_bar)
            snack_bar.open = True
            e.control.page.update()
            self.progress_bar.visible = False
            self.page.update()
            return

        self.progress_bar.visible = False
        self.page.update()

        # 跳转至主页面
        self.page.controls.clear()
        from main_view import MainView
        page_view = SafeArea(
            MainView(self.page),
            adaptive=True,
            expand=True
        )
        self.page.controls.append(page_view)
        self.page.update()

    def on_button_undo_click(self, e):
        self.editor.undo()

    def on_button_redo_click(self, e):
        self.editor.redo()

    def on_button_cancel_click(self, e):
        self.page.controls.clear()
        from main_view import MainView
        page_view = SafeArea(
            MainView(self.page),
            adaptive=True,
            expand=True
        )
        self.page.controls.append(page_view)
        self.page.update()

    def build_interface(self):
        # 操作栏
        row_ops = Row(
            alignment=MainAxisAlignment.START,
            spacing=0,
            controls=[
                IconButton(
                    icon=Icons.UNDO,
                    tooltip='撤销',
                    on_click=self.on_button_undo_click
                ),
                IconButton(
                    icon=Icons.REDO,
                    tooltip='重做',
                    on_click=self.on_button_redo_click
                ),
            ]
        )
        self.ops_toolbar = Container(
            content= row_ops,
        )
        self.editor = CustomTextField(
            value='',
            hint_text='正文',
            multiline=True,
            expand=True,
            # suffix=row_ops,
        )
        if self.memo_info is not None:
            self.editor.value = self.memo_info.get('content')

        # 进度条
        self.progress_bar = ProgressBar(
            value=None,
            bar_height=3,
            bgcolor=Colors.GREY_100,
            color=Colors.GREY_300,
            width=self.page.width,
            visible=False
        )

        # 布局
        cols_body = Column(
            controls=[
                self.progress_bar,
                self.editor,
                self.ops_toolbar,
            ],
            expand=True,
            # scroll=ScrollMode.AUTO,
            alignment=MainAxisAlignment.SPACE_BETWEEN
        )
        return cols_body
