import argparse
import os
import argparse
import os
import getpass
import sys
# Принудительно добавляем корневую папку (dev-password-organizer)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))


from core.models import Vault, Project, DatabaseCredential
from tui import TUIApp
# ...

VAULT_FILE = "vault.encrypted"
# ... (Остальной код main.py остается прежним)
GLOBAL_MASTER_PASSWORD = None


def get_vault(file_path: str) -> Vault:
    """Управляет загрузкой и созданием Vault, запрашивая пароль один раз."""
    global GLOBAL_MASTER_PASSWORD

    # 1. Запрос пароля (если еще не введен)
    if GLOBAL_MASTER_PASSWORD is None:
        if os.path.exists(file_path):
            prompt = "🔒 Введите мастер-пароль: "
        else:
            prompt = "🔒 Введите НОВЫЙ мастер-пароль (создаем базу): "

        # Ввод "вслепую" (символы не отображаются)
        master_password = getpass.getpass(prompt)
        GLOBAL_MASTER_PASSWORD = master_password
    else:
        master_password = GLOBAL_MASTER_PASSWORD

    # 2. Логика загрузки/создания
    if not os.path.exists(file_path):
        print(f"⭐ Файл {file_path} не найден. Создается новый Vault.")
        return Vault(master_password)

    try:
        return Vault.load_from_file(file_path, master_password)
    except ValueError as e:
        print(f"\n{str(e)}")
        GLOBAL_MASTER_PASSWORD = None
        exit(1)


def main():
    parser = argparse.ArgumentParser(description="Dev Password Organizer CLI")
    parser.add_argument("action", choices=["add-project", "list-projects", "add-credential", "save", "load", "tui"],
                        help="Действие")
    parser.add_argument("--name", type=str, help="Название")
    parser.add_argument("--description", type=str, default="", help="Описание")
    parser.add_argument("--host", type=str, default="", help="Хост")
    parser.add_argument("--user", type=str, default="", help="Юзер")
    parser.add_argument("--password", type=str, default="", help="Пароль БД")
    parser.add_argument("--port", type=int, default=3306, help="Порт")
    parser.add_argument("--file", type=str, default="vault.encrypted", help="Файл хранилища")

    args = parser.parse_args()
    is_dirty = False

    if args.action == "tui":
        app = TUIApp()
        app.run()
        return

    # --- Команды CLI (остальная логика) ---
    # ... (логика CLI не менялась, кроме исправления импортов)

    if args.action == "load":
        get_vault(args.file)
        print("✅ Данные успешно загружены и расшифрованы!")
        return

    if args.action == "save":
        vault = get_vault(args.file)
        vault.save_to_file(args.file)
        print(f"💾 Принудительно сохранено в {args.file}")
        return

    vault = get_vault(args.file)

    if args.action == "add-project":
        if not args.name:
            print("❌ Ошибка: укажите --name")
            return
        vault.add_project(Project(args.name, args.description))
        print(f"✅ Проект '{args.name}' создан.")
        is_dirty = True

    elif args.action == "list-projects":
        projects = vault.list_projects()
        if not projects:
            print("📂 Список пуст.")
        else:
            print("📋 Проекты:")
            for p in projects:
                print(f" - {p.name}: {p.description}")
                for cred in p.credentials.values():
                    print(f"   └── {cred}")

    elif args.action == "add-credential":
        if not all([args.name, args.host, args.user, args.password]):
            print("❌ Ошибка: укажите --name, --host, --user, --password")
            return

        if not vault.projects:
            print("❌ Сначала создайте проект (add-project).")
            return

        target_project = next(iter(vault.projects.values()))

        cred = DatabaseCredential(args.name, args.host, args.user, args.password, args.port)
        target_project.add_credential(cred)
        print(f"✅ Доступ '{args.name}' добавлен в проект '{target_project.name}'.")
        is_dirty = True

    if is_dirty:
        try:
            vault.save_to_file(args.file)
            print(f"💾 Изменения автоматически сохранены в {args.file}")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")


if __name__ == "__main__":
    main()
