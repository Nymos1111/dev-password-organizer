# src/tui.py

import npyscreen
import os
# ✅ ИСПРАВЛЕНИЕ: Теперь достаточно простого абсолютного импорта
from core.models import Vault, Project

VAULT_FILE = "vault.encrypted"
# ... (Остальной код tui.py остается прежним)


class LoginForm(npyscreen.ActionForm):
    # ... (Остальной код формы остался без изменений)

    def create(self):
        self.password_widget = self.add(
            npyscreen.TitlePassword,
            name="🔒 Мастер-пароль:",
            when_editing=True
        )

    def on_ok(self):
        master_password = self.password_widget.value

        try:
            if not os.path.exists(VAULT_FILE):
                self.parentApp.vault = Vault(master_password)
                self.parentApp.vault.save_to_file(VAULT_FILE)
                npyscreen.notify_wait("✅ Новый Vault создан и сохранен!", title="Успех")
            else:
                self.parentApp.vault = Vault.load_from_file(VAULT_FILE, master_password)
                npyscreen.notify_wait("✅ Данные успешно загружены!", title="Успех")

            self.parentApp.setNextForm("MAIN")
            self.editing = False

        except Exception as e:
            npyscreen.notify_critical(f"Ошибка загрузки: {str(e)}", title="Ошибка")

    def on_cancel(self):
        self.parentApp.setNextForm(None)


class MainAppForm(npyscreen.FormBaseNew):

    def create(self):
        self.name = "Главное меню"
        self.add(npyscreen.TitleFixedText, name="🚀 Dev Password Organizer", editable=False)
        self.add(npyscreen.FixedText, value="--- Управление Vault ---", editable=False)

        self.project_list = self.add(
            npyscreen.TitleSelectOne,
            name="Проекты:",
            values=["(Загрузка...)"],
            max_height=10,
            scroll_exit=True
        )

        self.add(npyscreen.FixedText, value="--- Действия ---", editable=False)
        self.add(npyscreen.ButtonPress, name="1. Добавить новый проект", when_pressed_function=self.add_project)
        self.add(npyscreen.ButtonPress, name="2. Выйти и сохранить", when_pressed_function=self.exit_app)

        self.update_list()

    def update_list(self):
        if self.parentApp.vault:
            projects = self.parentApp.vault.list_projects()
            self.project_list.values = [p.name for p in projects]
        else:
            self.project_list.values = ["Нет данных (ошибка загрузки)"]
        self.project_list.display()

    def add_project(self):
        new_project_name = f"Новый проект {len(self.parentApp.vault.projects) + 1}"
        new_project = Project(new_project_name, "Описание проекта")
        self.parentApp.vault.add_project(new_project)

        npyscreen.notify_wait(f"✅ Проект '{new_project_name}' добавлен.", title="Успех")
        self.update_list()

    def exit_app(self):
        try:
            self.parentApp.vault.save_to_file(VAULT_FILE)
            npyscreen.notify_wait("💾 Данные сохранены. Выход...", title="Сохранение")
            self.parentApp.setNextForm(None)
        except Exception as e:
            npyscreen.notify_critical(f"❌ Ошибка сохранения: {e}", title="Ошибка")


class TUIApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.vault = None

        # ✅ ДОБАВЛЯЕМ ЭТУ СТРОЧКУ:
        self.NEXT_ACTIVE_FORM = 'LOGIN'

        self.addForm("LOGIN", LoginForm, name="Вход")
        self.addForm("MAIN", MainAppForm, name="Главное меню")