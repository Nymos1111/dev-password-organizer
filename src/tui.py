# src/tui.py

import npyscreen
import os
import string
import random
from core.models import Vault, Project, DatabaseCredential

VAULT_FILE = "vault.encrypted"


class LoginForm(npyscreen.ActionForm):
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


class AddCredentialForm(npyscreen.ActionForm):
    def create(self):
        self.name_w = self.add(npyscreen.TitleText, name="Название (напр. Prod DB):")
        self.host_w = self.add(npyscreen.TitleText, name="Хост/IP:")
        self.user_w = self.add(npyscreen.TitleText, name="Пользователь:")
        self.pass_w = self.add(npyscreen.TitlePassword, name="Пароль:")
        # Кнопка генератора
        self.add(npyscreen.ButtonPress, name="🎲 Сгенерировать пароль", when_pressed_function=self.generate_password)
        self.port_w = self.add(npyscreen.TitleText, name="Порт:", value="3306")

    def generate_password(self):
        # Генерируем случайную строку (буквы + цифры + символы)
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        new_pass = ''.join(random.choice(chars) for _ in range(14))
        self.pass_w.value = new_pass
        self.pass_w.display()
        npyscreen.notify_confirm(f"Сгенерирован пароль: {new_pass}", title="Генератор", editw=1)

    def on_ok(self):
        port_val = 3306
        if self.port_w.value and self.port_w.value.isdigit():
            port_val = int(self.port_w.value)

        new_cred = DatabaseCredential(
            name=self.name_w.value,
            host=self.host_w.value,
            user=self.user_w.value,
            password=self.pass_w.value,
            port=port_val
        )
        if self.parentApp.current_project:
            self.parentApp.current_project.add_credential(new_cred)
            npyscreen.notify_confirm(f"✅ Доступ '{self.name_w.value}' добавлен!", title="Успех")

        self.parentApp.switchForm("PROJECT_MNG")

    def on_cancel(self):
        self.parentApp.switchForm("PROJECT_MNG")


class ProjectManagementForm(npyscreen.FormBaseNew):
    def create(self):
        self.project_label = self.add(npyscreen.TitleFixedText, name="Проект:", value="", editable=False)
        self.add(npyscreen.FixedText, value="--- Доступы ---", editable=False)

        self.access_list = self.add(
            npyscreen.MultiLine,
            name="access_list",
            max_height=10,
            values=[],
            scroll_exit=True
        )

        self.add(npyscreen.FixedText, value="--- Действия ---", editable=False)
        self.add(npyscreen.ButtonPress, name="1. Добавить доступ", when_pressed_function=self.add_access)
        self.add(npyscreen.ButtonPress, name="2. Удалить выбранный", when_pressed_function=self.delete_access)
        self.add(npyscreen.ButtonPress, name="<- Назад в меню", when_pressed_function=self.on_back)

    def beforeEditing(self):
        current_proj = getattr(self.parentApp, 'current_project', None)
        if current_proj:
            self.project_label.value = current_proj.name
            self.creds_objects = list(current_proj.credentials.values())
            if self.creds_objects:
                self.access_list.values = [f"[{c.user}@{c.host}] {c.name}" for c in self.creds_objects]
            else:
                self.access_list.values = ["Доступов пока нет"]
        self.display()

    def add_access(self):
        self.parentApp.switchForm("ADD_CREDENTIAL")

    def delete_access(self):
        selection = self.access_list.value
        if selection is None or not hasattr(self, 'creds_objects') or not self.creds_objects:
            npyscreen.notify_confirm("Сначала выберите доступ в списке!", title="Ошибка")
            return

        index = selection[0] if isinstance(selection, list) else selection
        if index >= len(self.creds_objects):
            return

        cred_to_remove = self.creds_objects[index]
        if npyscreen.notify_yes_no(f"Удалить '{cred_to_remove.name}'?", title="Подтверждение"):
            current_proj = self.parentApp.current_project
            key_to_delete = next((k for k, v in current_proj.credentials.items() if v == cred_to_remove), None)

            if key_to_delete:
                del current_proj.credentials[key_to_delete]
                npyscreen.notify_confirm("Удалено!", title="Успех")
                self.beforeEditing()

    def on_back(self):
        self.parentApp.switchForm("MAIN")


class MainAppForm(npyscreen.FormBaseNew):
    def create(self):
        self.add(npyscreen.TitleFixedText, name="🚀 Dev Password Organizer", editable=False)
        self.project_list = self.add(
            npyscreen.TitleSelectOne,
            name="Проекты (Enter для выбора):",
            values=[],
            max_height=10,
            scroll_exit=True,
            value_changed_callback=self.handle_project_selection
        )
        self.add(npyscreen.ButtonPress, name="1. Добавить новый проект", when_pressed_function=self.add_project)
        self.add(npyscreen.ButtonPress, name="2. Выйти и сохранить", when_pressed_function=self.exit_app)

    def handle_project_selection(self, widget):
        if widget.value and len(widget.value) > 0:
            selected_name = widget.values[widget.value[0]]
            if selected_name == "Нет проектов. Добавьте новый.":
                return
            for p in self.parentApp.vault.list_projects():
                if p.name == selected_name:
                    self.parentApp.current_project = p
                    self.parentApp.switchForm("PROJECT_MNG")

    def beforeEditing(self):
        self.update_list()

    def update_list(self):
        if self.parentApp.vault:
            projects = self.parentApp.vault.list_projects()
            self.project_list.values = [p.name for p in projects] if projects else ["Нет проектов. Добавьте новый."]
        self.project_list.display()

    def add_project(self):
        num = len(self.parentApp.vault.projects) + 1
        new_project = Project(f"Проект {num}", "Описание")
        self.parentApp.vault.add_project(new_project)
        self.update_list()

    def exit_app(self):
        try:
            if self.parentApp.vault:
                self.parentApp.vault.save_to_file(VAULT_FILE)
            npyscreen.notify_wait("💾 Данные сохранены. Выход...", title="Сохранение")
            self.parentApp.setNextForm(None)
            self.editing = False
        except Exception as e:
            npyscreen.notify_critical(f"❌ Ошибка: {e}", title="Ошибка")


class TUIApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.vault = None
        self.current_project = None
        self.addForm("LOGIN", LoginForm, name="Вход")
        self.addForm("MAIN", MainAppForm, name="Главное меню")
        self.addForm("PROJECT_MNG", ProjectManagementForm, name="Управление проектом")
        self.addForm("ADD_CREDENTIAL", AddCredentialForm, name="Новый доступ")
        self.NEXT_ACTIVE_FORM = "LOGIN"