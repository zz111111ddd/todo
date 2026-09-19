#!/usr/bin/env python3
"""Простой менеджер задач для командной строки (данные хранятся в JSON)."""
import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

DEFAULT_DB = Path.home() / ".todo_cli.json"


@dataclass
class Task:
    id: int
    title: str
    done: bool = False
    created: str = ""


class TodoStore:
    def __init__(self, path=DEFAULT_DB):
        self.path = Path(path)
        self.tasks = self._load()

    def _load(self):
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as f:
            return [Task(**item) for item in json.load(f)]

    def _save(self):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump([asdict(t) for t in self.tasks], f, ensure_ascii=False, indent=2)

    def _get(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"Задача #{task_id} не найдена")

    def add(self, title):
        title = title.strip()
        if not title:
            raise ValueError("Название задачи не может быть пустым")
        next_id = max((t.id for t in self.tasks), default=0) + 1
        task = Task(next_id, title, False, datetime.now().isoformat(timespec="seconds"))
        self.tasks.append(task)
        self._save()
        return task

    def complete(self, task_id):
        task = self._get(task_id)
        task.done = True
        self._save()
        return task

    def remove(self, task_id):
        task = self._get(task_id)
        self.tasks.remove(task)
        self._save()
        return task

    def list(self, show_all=True):
        return [t for t in self.tasks if show_all or not t.done]


def build_parser():
    parser = argparse.ArgumentParser(description="Менеджер задач")
    parser.add_argument("--db", default=DEFAULT_DB, help="путь к файлу с данными")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="добавить задачу")
    p_add.add_argument("title", nargs="+", help="текст задачи")

    p_list = sub.add_parser("list", help="показать задачи")
    p_list.add_argument("--pending", action="store_true", help="только невыполненные")

    p_done = sub.add_parser("done", help="отметить задачу выполненной")
    p_done.add_argument("id", type=int)

    p_rm = sub.add_parser("remove", help="удалить задачу")
    p_rm.add_argument("id", type=int)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    store = TodoStore(args.db)
    try:
        if args.command == "add":
            task = store.add(" ".join(args.title))
            print(f"Добавлена задача #{task.id}: {task.title}")
        elif args.command == "list":
            tasks = store.list(show_all=not args.pending)
            if not tasks:
                print("Задач нет.")
            for t in tasks:
                mark = "x" if t.done else " "
                print(f"[{mark}] #{t.id} {t.title}")
        elif args.command == "done":
            task = store.complete(args.id)
            print(f"Выполнено: #{task.id} {task.title}")
        elif args.command == "remove":
            task = store.remove(args.id)
            print(f"Удалено: #{task.id} {task.title}")
    except (KeyError, ValueError) as err:
        print(f"Ошибка: {err.args[0]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
