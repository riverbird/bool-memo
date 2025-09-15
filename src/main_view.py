"""
main_view.py
"""
# coding:utf-8
import json
from datetime import datetime

import httpx
from flet import Column, Row, Icons, Colors
from flet.core import border, border_radius, alignment, padding
from flet.core.alert_dialog import AlertDialog
from flet.core.app_bar import AppBar
from flet.core.border import BorderSide, BorderSideStrokeAlign
from flet.core.bottom_sheet import BottomSheet
from flet.core.box import BoxShadow
from flet.core.buttons import RoundedRectangleBorder
from flet.core.container import Container
from flet.core.divider import Divider
from flet.core.floating_action_button import FloatingActionButton
from flet.core.form_field_control import InputBorder
from flet.core.icon import Icon
from flet.core.icon_button import IconButton
from flet.core.image import Image
from flet.core.list_tile import ListTile
from flet.core.list_view import ListView
from flet.core.markdown import Markdown
from flet.core.navigation_drawer import NavigationDrawer, NavigationDrawerPosition
from flet.core.popup_menu_button import PopupMenuButton, PopupMenuItem
from flet.core.progress_bar import ProgressBar
from flet.core.progress_ring import ProgressRing
from flet.core.safe_area import SafeArea
from flet.core.scrollable_control import OnScrollEvent
from flet.core.snack_bar import SnackBar
from flet.core.text import Text
from flet.core.text_button import TextButton
from flet.core.textfield import TextField
from flet.core.types import MainAxisAlignment, CrossAxisAlignment, ImageFit, FloatingActionButtonLocation


class MainView(Column):
    def __init__(self, page):
        super().__init__()
        self.page = page

        self.selected_idx = -1
        self.page_idx = 1
        self.loading = False
        self.diary_type_list = None
        self.dct_tag = {}

        self.alignment = MainAxisAlignment.SPACE_BETWEEN,
        self.spacing = 0
        self.tight = True

        self.dlg_about = AlertDialog(
            modal=True,
            title=Text('关于'),
            content=Column(
                controls=[Divider(height=1, color='gray'),
                          Text('布尔备忘v0.2.0'),
                          Text('一个快速的备忘记录软件，支持Markdown。'),
                          Text('浙江舒博特网络科技有限公司 出品'),
                          Text('官网: http://https://www.zjsbt.cn/service/derivatives'),
                          ],
                alignment=MainAxisAlignment.START,
                width=300,
                height=90,
            ),
            actions=[TextButton("确定", on_click=self.on_about_ok_click), ],
            actions_alignment=MainAxisAlignment.END,
        )

        # 抽屉
        self.page.run_task(self.build_drawer)

        # 浮动按钮
        self.page.floating_action_button = FloatingActionButton(
            icon=Icons.CREATE,
            bgcolor=Colors.BLUE,
            foreground_color=Colors.WHITE,
            shape=RoundedRectangleBorder(radius=50),
            data=0,
            on_click=self.on_fab_pressed,
        )
        # self.page.floating_action_button_location = FloatingActionButtonLocation.CENTER_FLOAT
        self.page.appbar = AppBar(
            title=Text('布尔备忘', color=Colors.BLACK),
            bgcolor=Colors.WHITE,
            color=Colors.BLACK,
            actions=[
                IconButton(
                    icon=Icons.SEARCH,
                    on_click=self.on_button_search_click
                ),
                IconButton(
                    icon=Icons.REFRESH,
                    on_click=self.on_button_refresh_click
                ),
            ],
        )

        content = self.build_interface()

        self.page.bottom_appbar = None
        self.controls = [content, self.dlg_about]
        self.page.run_task(self.query_memos_list)

    async def query_memos_list(self, append_mode='restart', tag_id=None):
        def on_btn_expand_click(e):
            markdown_value = e.control.data
            col = e.control.parent
            markdown_control = col.controls[1]
            markdown_control.value = markdown_value
            e.control.visible = False
            retract_btn = col.controls[4]
            retract_btn.visible = True
            self.note_list.update()

        def on_btn_retract_click(e):
            markdown_value = e.control.data
            col = e.control.parent
            markdown_control = col.controls[1]
            markdown_control.value = markdown_value
            e.control.visible = False
            expand_btn = col.controls[3]
            expand_btn.visible = True
            self.note_list.update()

        self.progress_bar.visible = True
        self.page.update()
        if append_mode == 'restart':
            self.note_list.controls.clear()
        token = await self.page.client_storage.get_async('token')
        user_id = await self.page.client_storage.get_async('user_id')
        if tag_id == 'star':
            url = f'https://restapi.10qu.com.cn/memo/?user={user_id}&star=true&ordering=-create_time'
        elif isinstance(tag_id, int):
            url = f'https://restapi.10qu.com.cn/memo/?user={user_id}&tag={tag_id}'
        else:
            url = f'https://restapi.10qu.com.cn/memo/?user={user_id}&ordering=-create_time&page={self.page_idx}&size=30'
        headers = {"Authorization": f'Bearer {token}'}
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                lst_memo = data.get('results')
                for memo in lst_memo:
                    dt_time = datetime.strptime(memo.get('update_time'), '%Y-%m-%dT%H:%M:%S.%f')
                    str_date = dt_time.strftime("%Y-%m-%d %H:%M:%S")
                    # 标签
                    row_tags = Row()
                    for tag in memo.get('tag', []):
                        row_tags.controls.append(
                            Text(f'#{self.dct_tag.get(tag)}',
                                 color=Colors.BLUE
                            )
                        )
                    # 展开按钮
                    markdown_value = memo.get('content')[:500]
                    btn_expand = TextButton(
                        '展开',
                        data=memo.get('content'),
                        on_click=on_btn_expand_click
                    )
                    btn_retract = TextButton(
                        '收起',
                        data=memo.get('content')[:500],
                        on_click=on_btn_retract_click
                    )
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
                            alignment=MainAxisAlignment.START,
                            spacing=0,
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
                                                    icon=Icons.STAR,
                                                    text='收藏',
                                                    data=memo,
                                                    on_click=self.on_star_memo
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
                                        )
                                    ]
                                ),
                                # Text(
                                #     value=memo.get('content'),
                                #     size=15,
                                #     no_wrap=False,
                                #     color=Colors.BLACK87
                                # ),
                                Markdown(
                                    value=markdown_value,
                                ),
                                row_tags,
                                btn_expand,
                                btn_retract,
                            ],
                        ),
                    )
                    if len(memo.get('content')) > 500:
                        btn_expand.visible = True
                    else:
                        btn_expand.visible = False
                    btn_retract.visible = False
                    self.note_list.controls.append(memo_item)
                if len(lst_memo) == 30:
                    self.btn_load_more.visible = True
                else:
                    self.btn_load_more.visible = False
                self.progress_bar.visible = False
                self.page.update()
        except httpx.HTTPError as e:
            snack_bar = SnackBar(Text(f"查询用户备忘列表请求失败，请刷新重试。{str(e)}"))
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
            self.progress_bar.visible = False
            self.page.update()

    def on_copy_content(self, e):
        memo_info = e.control.data
        self.page.set_clipboard(memo_info.get('content'))

    async def on_star_memo(self, e):
        memo_info = e.control.data
        token = await self.page.client_storage.get_async('token')
        headers = {"Authorization": f'Bearer {token}'}
        user_input = {'star': True}
        url = f'https://restapi.10qu.com.cn/memo/{memo_info.get("id")}/'
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.patch(
                    url,
                    headers=headers,
                    json=user_input,
                )
                resp.raise_for_status()
                if resp.status_code != 200:
                    snack_bar = SnackBar(Text(f"修改备忘收藏状态失败."))
                    e.control.page.overlay.append(snack_bar)
                    snack_bar.open = True
                    e.control.page.update()
                    return
                update_result = resp.json()
        except httpx.HTTPError as ex:
            snack_bar = SnackBar(Text(f"修改备忘收藏状态失败:{str(ex)}"))
            e.control.page.overlay.append(snack_bar)
            snack_bar.open = True
            e.control.page.update()
            return
        update_result_text = '成功' if update_result else '失败'
        snack_bar = SnackBar(Text(f"修改备忘收藏状态{update_result_text}!"))
        e.control.page.overlay.append(snack_bar)
        snack_bar.open = True
        e.control.page.update()

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

    async def on_fab_pressed(self, e):
        async def on_btn_post_clicked(ex):
            # 关闭BottomSheet
            bs.open = False
            # ex.page.overlay.clear()
            # ex.control.update()
            # ex.control.page.update()
            self.page.overlay.clear()
            self.page.update()

            # 提交任务
            content = input_memo.value
            if len(content) == 0:
                snack_bar = SnackBar(Text("备忘信息不允许为空!"))
                e.control.page.overlay.append(snack_bar)
                snack_bar.open = True
                e.control.page.update()
                return
            token = await self.page.client_storage.get_async('token')
            user_id = await self.page.client_storage.get_async('user_id')
            url = 'https://restapi.10qu.com.cn/memo/'
            headers = {'Authorization': f'Bearer {token}'}
            user_input = {'user': user_id,
                          'content': content,
                          'tag': selected_tag_list}
            progress_ring = ProgressRing(width=32, height=32, stroke_width=2)
            progress_ring.top = self.page.height / 2 - progress_ring.height / 2
            progress_ring.left = self.page.width / 2 - progress_ring.width / 2
            e.control.page.overlay.append(progress_ring)
            e.control.page.update()
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    resp = await client.post(
                        url,
                        headers=headers,
                        json=user_input,
                    )
                    resp.raise_for_status()
                    if resp.status_code != 201:
                        snack_bar = SnackBar(Text("添加备忘失败!"))
                        e.control.page.overlay.append(snack_bar)
                        snack_bar.open = True
                        progress_ring.visible = False
                        e.control.page.update()
                        return
                    snack_bar = SnackBar(Text("备忘添加成功!"))
                    e.control.page.overlay.append(snack_bar)
                    snack_bar.open = True
                    e.control.update()
                    e.control.page.update()

                    # 更新列表
                    await self.query_memos_list()
            except httpx.HTTPError as ex:
                snack_bar = SnackBar(Text(f"任务添加异常：{str(ex)}"))
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
            progress_ring.visible = False
            e.control.page.update()
            self.page.update()

        def on_select_memo_tag(ex):
            select_id = ex.data
            select_text = ''
            for item in ex.control.items:
                if select_id == item.uid:
                    select_text = item.text
                    tag_id = item.data.get('id')
                    selected_tag_list.append(tag_id)
                    break
            src_value = input_memo.value
            input_memo.value = f"{src_value}\r\n#{select_text}"
            input_memo.update()

        def on_btn_task_clicked(ex):
            src_value = input_memo.value
            insert_str = "- [] "
            input_memo.value = f"{src_value}\r\n{insert_str}"
            input_memo.update()

        selected_tag_list = []
        input_memo = TextField(
            hint_text='现在您的想法是...',
            label='任何想法',
            expand=True,
            # filled=True,
            multiline=True,
            border=InputBorder.OUTLINE,
            # border_radius=5,
            # height=120,
            # autofocus=True,
            adaptive=True,
            min_lines=14,
        )
        # input_container = Container(
        #     content=input_memo,
        #     expand=True,
        #     # height=240,
        # )
        tag_list_items = []
        tag_list = await self.get_memo_tag_list()
        for tag in tag_list:
            tag_list_items.append(
                PopupMenuItem(
                    text=tag.get('name'),
                    icon=Icons.TAG_OUTLINED,
                    data=tag,
                )
            )

        btn_tag = PopupMenuButton(
            icon=Icons.TAG_OUTLINED,
            content=Row([
                Icon(name=Icons.TAG_OUTLINED),
                # Text('截止日期')
            ]),
            items=tag_list_items,
            on_select=on_select_memo_tag
        )
        btn_post = IconButton(
            icon=Icons.SEND_OUTLINED,
            on_click=on_btn_post_clicked
        )
        btn_task_box = IconButton(
            icon=Icons.CHECK_BOX_OUTLINED,
            on_click=on_btn_task_clicked
        )
        row_extra = Row(
            controls=[
                btn_tag,
                btn_task_box,
                Container(expand=True),
                btn_post
            ],
            alignment=MainAxisAlignment.SPACE_BETWEEN
        )

        bs = BottomSheet(
            Container(
                Column(
                    [
                        row_extra,
                        input_memo,
                    ],
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                    tight=True,
                ),
                adaptive=True,
                border_radius=2,
                padding=10,
                # expand=True,
            ),
            # use_safe_area=True,
            maintain_bottom_view_insets_padding=True,
            open=True,
        )
        # e.page.overlay.append(bs)
        # e.control.update()
        # e.control.page.update()
        self.page.overlay.append(bs)
        self.page.update()

    async def on_button_refresh_click(self, e):
        # self.page.run_task(self.query_diary_list)
        self.page_idx = 1
        await self.query_memos_list(append_mode='restart', tag_id=None)

    def on_button_search_click(self, e):
        self.page.controls.clear()
        from search_memo_view import SearchMemoView
        page_view = SafeArea(
            SearchMemoView(self.page),
            adaptive=True,
            expand=True
        )
        self.page.controls.append(page_view)
        self.page.update()

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

    def on_about_click(self, e):
        self.page.dialog = self.dlg_about
        self.dlg_about.open = True
        self.page.update()

    def on_about_ok_click(self, e):
        self.dlg_about.open = False
        self.page.update()

    async def on_logout(self, e):
        url = 'https://restapi.10qu.com.cn/logout/'
        token = await self.page.client_storage.get_async('token')
        headers = {"Authorization": f'Bearer {token}'}
        progress_ring = ProgressRing(width=32, height=32, stroke_width=2)
        progress_ring.top = self.page.height / 2 - progress_ring.height / 2
        progress_ring.left = self.page.width / 2 - progress_ring.width / 2
        e.control.page.overlay.append(progress_ring)
        e.control.page.update()
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers=headers,
                )
                resp.raise_for_status()
                if resp.status_code != 200:
                    snack_bar = SnackBar(Text("退出登录失败，请稍后重新再试。"))
                    e.control.page.overlay.append(snack_bar)
                    snack_bar.open = True
                    progress_ring.visible = False
                    e.control.page.update()
                    return
                data = resp.json()
                if data.get('code') != '0':
                    snack_bar = SnackBar(Text("退出登录失败，请稍后重新再试。"))
                    e.control.page.overlay.append(snack_bar)
                    snack_bar.open = True
                    progress_ring.visible = False
                    e.control.page.update()
                    return
        except httpx.HTTPError as ex:
            snack_bar = SnackBar(Text(f"退出登录失败:{str(ex)}"))
            e.control.page.overlay.append(snack_bar)
            snack_bar.open = True
            progress_ring.visible = False
            e.control.page.update()
        progress_ring.visible = False
        # 跳转至登录界面
        await self.page.client_storage.clear_async()
        from login_view import LoginControl
        page_view = SafeArea(
            LoginControl(self.page),
            adaptive=True,
            expand=True
        )
        self.page.controls.clear()
        self.page.controls.append(page_view)
        self.page.update()

    async def on_query_all_memo_click(self, e):
        self.page.drawer.open = False
        self.page.update()
        await self.query_memos_list(append_mode='restart', tag_id=None)

    async def on_query_star_memo_click(self, e):
        self.page.drawer.open = False
        self.page.update()
        await self.query_memos_list(append_mode='restart', tag_id='star')

    async def on_query_memo_tag_click(self, e):
        tag_info = e.control.data
        tag_id = tag_info.get('id')
        self.page.drawer.open = False
        self.page.update()
        await self.query_memos_list(append_mode='restart', tag_id=tag_id)

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

    def load_next_page(self, e):
        self.page.run_task(self.load_more)

    async def load_more(self):
        self.loading = True
        self.progress_bar.visible = True
        self.btn_load_more.visible = False
        self.progress_ring.visible = True

        self.page_idx += 1
        await self.query_memos_list(append_mode='append', tag_id=None)

        snack_bar = SnackBar(Text(f"第{self.page_idx}页加载完成。"))
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.progress_bar.visible = False
        self.btn_load_more.visible = True
        self.progress_ring.visible = False
        self.loading = False
        self.page.update()

    def on_list_view_scroll(self, e: OnScrollEvent):
        # e.pixels: 当前滚动条位置
        # e.max_scroll_extent: 最大滚动位置
        if e.pixels >= e.max_scroll_extent - 50 and not self.loading:
            # 距离底部小于50像素时触发加载
            self.page.run_task(self.load_more)

    def on_manage_tags_click(self, e):
        self.page.controls.clear()
        from tag_manage_view import TagManageView
        page_view = SafeArea(
            TagManageView(self.page),
            adaptive=True,
            expand=True
        )
        self.page.controls.append(page_view)
        self.page.update()

    async def build_drawer(self):
        cached_user_info_value = await self.page.client_storage.get_async('diary_user_info')
        cached_user_info = json.loads(cached_user_info_value) if cached_user_info_value else {}
        if cached_user_info:
            avatar_url = cached_user_info.get('avatar_url', 'assets/default_avatar.png')
            nick_name = cached_user_info.get('nick_name', '用户名')
        else:
            token = await self.page.client_storage.get_async('token')
            url='https://restapi.10qu.com.cn/user_info/'
            headers = {'Authorization': f'Bearer {token}'}
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    resp = await client.get(
                        url,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    if resp.status_code != 200:
                        snack_bar = SnackBar(Text("获取用户信息失败."))
                        self.page.overlay.append(snack_bar)
                        snack_bar.open = True
                        avatar_url = 'assets/default_avatar.png'
                        nick_name = '未知'
                        self.page.update()
                    else:
                        data = resp.json()
                        user_info = data.get('results')
                        avatar_url = user_info.get('avatar_url', 'assets/default_avatar.png')
                        nick_name = user_info.get('nick_name', '')
                        cached_user_info_str = json.dumps(user_info)
                        await self.page.client_storage.set_async('dairy_user_info', cached_user_info_str)
            except httpx.HTTPError as ex:
                snack_bar = SnackBar(Text(f"获取用户信息失败：{str(ex)}"))
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                avatar_url = 'assets/default_avatar.png'
                nick_name = '未知'
                self.page.update()

        text_user = Text(
            nick_name,
            size=14,
            color=Colors.WHITE
        )
        img_avatar = Image(
            src=avatar_url,
            width=32,
            height=32,
            fit=ImageFit.CONTAIN,
            border_radius=border_radius.all(30)
        )

        head = Container(
            content=Row(
                controls=[img_avatar,
                          text_user],
                alignment=MainAxisAlignment.SPACE_AROUND,
                # vertical_alignment=CrossAxisAlignment.CENTER,
                # spacing=10
            ),
            bgcolor=Colors.BLUE_600,
            height=100,
            alignment=alignment.center_left,
            adaptive=True,
        )
        # 获得日记类型列表
        lst_category = await self.get_memo_tag_list()
        for tag in lst_category:
            self.dct_tag[tag.get('id')] = tag.get('name')

        cate_list_tiles = [
            head,
            ListTile(
                title=Text('全部备忘'),
                selected=self.selected_idx == 0,
                selected_tile_color=Colors.BLUE_100,
                hover_color=Colors.BLUE_50,
                leading=Icon(Icons.ALL_INBOX),
                on_click=self.on_query_all_memo_click,
            ),
            ListTile(
                title=Text('已收藏'),
                selected=self.selected_idx == 0,
                selected_tile_color=Colors.BLUE_100,
                hover_color=Colors.BLUE_50,
                leading=Icon(Icons.STAR),
                on_click=self.on_query_star_memo_click,
            ),
        ]
        col_drawer = Column(
            controls=cate_list_tiles
            # alignment=MainAxisAlignment.START,
        )
        col_drawer.controls.append(
            Divider(),
        )
        col_drawer.controls.append(
            ListTile(
                title=Text('管理标签'),
                selected=self.selected_idx == 0,
                selected_tile_color=Colors.BLUE_100,
                hover_color=Colors.BLUE_50,
                leading=Icon(Icons.SETTINGS),
                on_click=self.on_manage_tags_click,
            ),
        )
        for cate in lst_category:
            col_drawer.controls.append(
                ListTile(
                    title=Text(cate.get('name')),
                    leading=Icon(Icons.TAG_OUTLINED),
                    selected_tile_color=Colors.BLUE_100,
                    hover_color=Colors.BLUE_50,
                    data=cate,
                    on_click=self.on_query_memo_tag_click,
                )
            )
        col_drawer.controls.append(Container(expand=True))
        col_drawer.controls.append(
            Divider(
                # thickness=1,
                # color=Colors.GREY_200,
            )
        )
        col_drawer.controls.append(ListTile(title=Text('关于我们'),
                         leading=Icon(Icons.HELP),
                         on_click=self.on_about_click,
                         ))
        col_drawer.controls.append(
            ListTile(
                title=Text('退出登录'),
                leading=Icon(Icons.EXIT_TO_APP),
                on_click=self.on_logout,
            )
        )
        # return col_drawer
        self.drawer = NavigationDrawer(
            position=NavigationDrawerPosition.START,
            open=False,
            controls=[
                Container(
                    content=col_drawer,
                    expand=1,
                    padding=0,
                    margin=0,
                )
            ]
        )
        self.page.drawer = self.drawer
        self.page.update()

    def build_interface(self):
        # 笔记列表
        self.note_list = ListView(
            spacing=10,
            padding=padding.only(left=2, top=5, right=2, bottom=5),
            expand=True,
            # height=self.page.height - 10,
            # on_scroll= self.on_list_view_scroll,
        )

        self.progress_bar = ProgressBar(
            value=None,
            bar_height=3,
            bgcolor=Colors.GREY_100,
            color=Colors.GREY_300,
            width=self.page.width
        )
        self.btn_load_more = IconButton(
            icon=Icons.ARROW_DOWNWARD_OUTLINED,
            on_click=self.load_next_page,
            visible=False,
        )
        self.progress_ring = ProgressRing(
            width=28,
            height=28,
            visible=False,
        )

        col_notes = Column(
            controls = [
                self.progress_bar,
                self.note_list,
                Row([self.btn_load_more, self.progress_ring],
                    alignment=MainAxisAlignment.CENTER)
            ],
            alignment=MainAxisAlignment.SPACE_BETWEEN,
            horizontal_alignment=CrossAxisAlignment.CENTER,
            adaptive=True,
            width=self.page.width,
            spacing=0,
            tight=True,
        )
        return col_notes
