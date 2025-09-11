# coding:utf-8
import flet
import httpx
from flet import Page, Theme
from flet.core.safe_area import SafeArea
from flet.core.theme import DatePickerTheme
from flet.core.types import VisualDensity, MainAxisAlignment, CrossAxisAlignment, ThemeMode, PagePlatform, ScrollMode, \
    Locale

from login_view import LoginControl
from main_view import MainView


def main(page: Page):
    # 页面属性
    page.adaptive = True
    page.title = '布尔备忘'
    page.window.icon = 'assets/icon.png'
    page.scroll = ScrollMode.ADAPTIVE
    page.platform=PagePlatform.ANDROID
    page.vertical_alignment = MainAxisAlignment.CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.theme_mode = ThemeMode.SYSTEM
    page.theme = Theme(
        color_scheme_seed="blue",
        font_family='微软雅黑',
        date_picker_theme=DatePickerTheme(locale=Locale('zh', 'CN')),
        visual_density=VisualDensity.ADAPTIVE_PLATFORM_DENSITY,
        use_material3=True)
    page.dark_theme = Theme(
        color_scheme_seed="green",
        font_family='微软雅黑',
        date_picker_theme=DatePickerTheme(locale=Locale('zh', 'CN')),
        visual_density=VisualDensity.ADAPTIVE_PLATFORM_DENSITY,
        use_material3=True)

    # 初始页面
    def switch_page(page_flag: str):
        page.controls.clear()
        match page_flag:
            case 'login_view':
                page_view = SafeArea(
                    LoginControl(page),
                    adaptive=True,
                    expand=True
                )
            case _:
                page_view = SafeArea(
                    MainView(page),
                    adaptive=True,
                    expand=True
                )
        page.controls.append(page_view)

    # 初始页面
    token = page.client_storage.get('token')
    if token is not None:
        token = token.strip('"')
        url = 'https://restapi.10qu.com.cn/user_info/'
        headers = {'Authorization': f'Bearer {token}'}
        try:
            resp = httpx.get(url, headers=headers, timeout=10.0)
            if resp.status_code != 200:
                switch_page('login_view')
            json_req = resp.json()
            dct_ret = json_req.get('results')
            if dct_ret is not None:
                switch_page('main_view')
            else:
                switch_page('login_view')
        except httpx.HTTPError as e:
            switch_page('login_view')
    else:
        switch_page('login_view')

    page.window.center()


flet.app(
    target=main,
    assets_dir='assets',
    # view=flet.AppView.WEB_BROWSER
)
