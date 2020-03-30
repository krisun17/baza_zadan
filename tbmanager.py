# -*- coding: utf-8 -*-

from copy import deepcopy
import os
import shutil
import json
import codecs
from random import randrange
from tbconfig import Config
import sys
from datetime import datetime, date
import argparse

ENCODING = 'utf-8'

def read_tasks_config():
    with open(Config.tasks_config_file, "r") as f:
        config_all = json.loads(f.read())
    return config_all

def write_tasks_config(cfg):
    with open(Config.tasks_config_file, "w") as f:
        f.write(json.dumps(cfg))

def create_pdf(config, outfn, constraints={}):
    # outfn must not contain "."

    operators_dict = {"=": lambda x, y: x == y,
                      ">": lambda x, y: x > y,
                      ">=": lambda x, y: x >= y,
                      "<": lambda x, y: x < y,
                      "<=": lambda x, y: x <= y}

    def is_constraint_fulfilled(task):
        for c_key, c_tup in constraints.items():
            c_val, c_op = c_tup
            t_val = task["atrybuty"].get(c_key)
            if t_val is None or not operators_dict[c_op](t_val, int(c_val)):
                return False
        return True

    def create_tex(tasks_config):

        def is_one_section():
            if len(tasks_config.keys()) == 1:
                return True
            return len(config.keys()) == 1

        def is_el_in_config(cfg, el, el_default={}):
            if type(cfg) == dict:
                return cfg.get(el) is not None or cfg == el_default
            if type(cfg) == list:
                return el in cfg or cfg == el_default

        def add_section(tex_file, sec_name):
            if not is_one_section():
                tex_file.append(r"\section{{ {0} }}".format(sec_name))

        def add_subsection(tex_file, subsec_name):
            if is_one_section():
                tex_file.append(r"\section{{ {0} }}".format(subsec_name))
            else:
                tex_file.append(r"\subsection{{ {0} }}".format(subsec_name))

        def add_task(tex_file, task, sec_i, subs_i, task_num):
            if is_constraint_fulfilled(task):
                if is_one_section():
                    tex_file.append(r"\textbf{{Zadanie {0}.{1}}} \\".format(
                        subs_i+1, task_num))
                else:
                    tex_file.append(r"\textbf{{Zadanie {0}.{1}.{2}}} \\".format(
                        sec_i+1, subs_i+1, task_num))
                tex_file += task["treść"]
                tex_file.append(r"~\\")

        # TODO not print sec if tasks filtered
        tex_file = deepcopy(Config.file_config["preamble_text"])
        for sec_i, (sec_name, sec_tasks) in enumerate(tasks_config.items()):
            if is_el_in_config(config, sec_name):
                add_section(tex_file, sec_name)
                act_sec_cfg = config.get(sec_name, {})
                for subs_i, (subs_name, subs_tasks) in enumerate(sec_tasks.items()):
                    if is_el_in_config(act_sec_cfg, subs_name):
                        add_subsection(tex_file, subs_name)
                        act_subsec_cfg = act_sec_cfg.get(subs_name, [])
                        for task_i, task in enumerate(subs_tasks):
                            task_num = task_i + 1
                            if is_el_in_config(act_subsec_cfg, task_num, []):
                                add_task(tex_file, task, sec_i, subs_i, task_num)
        tex_file += Config.file_config["end_text"]
        return tex_file


    def compile_latex(tex_file):
        fn = os.path.join(Config.tmp_dir, outfn + Config.tsk_ext)
        print("Compiling latex ...")
        with codecs.open(fn, "w", encoding=ENCODING) as f:
            f.writelines("\n".join(tex_file))
        res = os.system("pdflatex -output-directory={0} {1}".format(
            Config.tmp_dir, fn))
        if res is not None:
            print("DONE!")
        else:
            print("ERROR! Check logs for details")

    def clean_files():
        print("cleaning ...")
        for fn in os.listdir(Config.tmp_dir):
            for ext in Config.to_clean_ext:
                if fn.endswith(ext):
                    print("Removing {0} ...".format(fn))
                    os.remove(os.path.join(Config.tmp_dir, fn))

    compile_latex(create_tex(read_tasks_config()))
    clean_files()

def update_config():

    def sort_tasks_key(name):
        return int(name.split("_")[0])

    new_config = read_tasks_config()
    for sec in os.listdir(Config.task_dir):
        for subsec in os.listdir(os.path.join(Config.task_dir, sec)):
            sorted_tasks = sorted(os.listdir(os.path.join(Config.task_dir, sec, subsec)),
                                  key=sort_tasks_key)
            for i, task in enumerate(sorted_tasks):
                task_fn = os.path.join(Config.task_dir, sec, subsec, task)
                with open(task_fn, "r", encoding=ENCODING) as f:
                    content = f.readlines()
                new_config[sec][subsec][i]["treść"] = content
                if new_config[sec][subsec][i].get("atrybuty") is None:
                    new_config[sec][subsec][i]["atrybuty"] = {}
    write_tasks_config(new_config)

def update_atrs(new_atrs):
    new_config = read_tasks_config()
    for sec_name, sec_atrs in new_atrs.items():
        for subs_name, subs_atrs in sec_atrs.items():
            for t_num, atrs in subs_atrs.items():
                t_i = int(t_num) - 1
                for c_key, c_val in atrs.items():
                    new_config[sec_name][subs_name][t_i]["atrybuty"][c_key] = c_val
    write_tasks_config(new_config)

def get_task_fname(name, sec, subsec, num, sol=False):
    suf = "-sol" + Config.sol_ext if sol else Config.tsk_ext
    base_dir = Config.solv_dir if sol else Config.task_dir
    tname = "{0}_{1}{2}".format(num, name, suf)
    return os.path.join(base_dir, sec, subsec, tname)

def rename_num(tn, sec, subsec, old_num, new_num):
    os.rename(get_task_fname(tn, sec, subsec, old_num),
              get_task_fname(tn, sec, subsec, new_num))
    os.rename(get_task_fname(tn, sec, subsec, old_num, sol=True),
              get_task_fname(tn, sec, subsec, new_num, sol=True))

def add_task(sec, subsec, tname, num=None, atrs={}):

    def add_sec_and_subsec(new_config):
        if new_config.get(sec) is None:
            new_config[sec] = {}
            os.makedirs(os.path.join(Config.task_dir, sec))
            os.makedirs(os.path.join(Config.solv_dir, sec))
        if new_config[sec].get(subsec) is None:
            os.makedirs(os.path.join(Config.task_dir, sec, subsec))
            os.makedirs(os.path.join(Config.solv_dir, sec, subsec))
            new_config[sec][subsec] = []
        return new_config

    new_config = add_sec_and_subsec(read_tasks_config())
    tfn = os.path.join(Config.root_dir, tname) + Config.tsk_ext
    sfn = os.path.join(Config.root_dir, tname + "-sol") + Config.sol_ext
    tasks_num = len(new_config[sec][subsec])
    with open(tfn, "r", encoding=ENCODING) as f:
        content = f.readlines()
    task_conf = {"treść": content, "nazwa": tname, "atrybuty": atrs}
    if num is None or num > tasks_num:
        new_config[sec][subsec].append(task_conf)
        idx = tasks_num
    else:
        idx = num - 1
        for i in range(idx, task_num):
            rename_num(new_config[sec][subsec][i], sec, subsec, i+1, i+2)
        new_config[sec][subsec][idx:idx] = [task_conf]
    shutil.move(tfn, get_task_fname(tname, sec, subsec, idx+1))
    shutil.move(sfn, get_task_fname(tname, sec, subsec, idx+1, sol=True))
    write_tasks_config(new_config)

def rename_tasks(sec, subsec, old_num, new_num):
    new_config = read_tasks_config()
    idx_new = new_num - 1
    idx_old = old_num - 1
    rename_num(new_config[sec][subsec][idx_old], sec, subsec, old_num, new_num)
    step = 1 if new_num < old_num else -1
    for i in range(idx_new, idx_old, step):
        rename_num(new_config[sec][subsec][i], sec, subsec, i + 1, i + 1 + step)
    new_config[sec][subsec].insert(idx_new, new_config[sec][subsec].pop(idx_old))
    write_tasks_config(new_config)


class BaseRunner(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Wiersz poleceń bazy zadań Anulki',
            usage='''python tbmanager.py <command> [<args>]

            Dopuszczalne komendy:
               generuj        Generuje zadania na podstawie konfiguracji
               sekcja         Generuje zadania tylko z danej sekcji
               dodaj          Dodaje zadania
               dodaj_atrybuty Dodaj atrybuty do zadań
               przenumeruj    Przenumerowuje zadanie
            ''')
        parser.add_argument('command', help='Subcommand to run')
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def generuj(self):

        def get_date():
            return datetime.now().strftime("%Y%m%d%H%M")

        parser = argparse.ArgumentParser(
            description='Generuje zadania na podstawie konfiguracji')
        parser.add_argument('--zadania', help='plik z konfiguracją zadań, domyślnie wszystko')
        parser.add_argument('--atrybuty', help='plik z atrybutami, domyślnie wszystko')
        parser.add_argument('--output', help='nazwa pliku wyjściowego, nie może zawierać kropki')
        args = parser.parse_args(sys.argv[2:])
        out = "zadania_{0}".format(get_date()) if  args.output is None else args.output
        zad = {} if args.zadania is None else self._load_config(args.zadania)
        atrs = {} if args.atrybuty is None else self._load_atrs(args.atrybuty)
        print('Running generuj zadania={0} atrybuty={1} output={2}'.format(zad, atrs, out))
        create_pdf(zad, out, constraints=atrs)

    def sekcja(self):
        parser = argparse.ArgumentParser(
            description='Generuje zadania tylko z danej sekcji')

        parser.add_argument('rozdzial', help='nazwa rozdziału, obowiązkowa')
        parser.add_argument('--atrybuty', help='plik z atrybutami, domyślnie wszystko')
        parser.add_argument('--output', help='nazwa pliku wyjściowego, nie może zawierać kropki')
        args = parser.parse_args(sys.argv[2:])
        out = "zadania_{0}".format(args.rozdzial) if  args.output is None else args.output
        atrs = {} if args.atrybuty is None else self._load_atrs(args.atrybuty)
        print('Running sekcja sekcja={0} atrybuty={1} output={2}'.format(args.rozdzial, atrs, out))
        create_pdf({args.rozdzial: {}}, out, constraints=atrs)

    def dodaj(self):
        parser = argparse.ArgumentParser(
            description='Dodaje zadania do bazy')

        parser.add_argument('rozdzial', help='nazwa rozdzialu, obowiązkowa')
        parser.add_argument('podrozdzial', help='nazwa podrozdziału, obowiązkowa')
        parser.add_argument('plik', help='nazwa pliku do dodania')
        parser.add_argument('--numer', help='numer zadania')
        parser.add_argument('--atrybuty', help='atrybuty zadania', type=str)
        parser.add_argument('--atrybuty_plik', help='plik do atrybutów zadania')
        args = parser.parse_args(sys.argv[2:])
        if args.atrybuty is None:
            if args.atrybuty_plik is None:
                atrs = {}
            else:
                atrs = self._load_atrs(args.atrybuty_plik)
        else:
            atrs = json.loads(args.atrybuty)
        print('Running dodaj rozdzial={0} podrozdzial={1} plik={2} numer={3} atrybuty={4}'.format(
            args.rozdzial, args.podrozdzial, args.plik, args.numer, atrs))
        add_task(args.rozdzial, args.podrozdzial, args.plik, num=args.numer, atrs=atrs)

    def dodaj_atrybuty(self):
        parser = argparse.ArgumentParser(
            description='Dodaje atrybuty do zadań')

        parser.add_argument('plik', help='plik .json z nowymi atrybutami')
        args = parser.parse_args(sys.argv[2:])
        atrs = self._load_atrs(args.plik)
        print('Running dodaj_atrybuty {0}'.format(args.plik))
        update_atrs(atrs)

    def przenumeruj(self):
        parser = argparse.ArgumentParser(
            description='Przenumerowuje zadania')

        parser.add_argument('rozdzial', help='nazwa rozdzialu, obowiązkowa')
        parser.add_argument('podrozdzial', help='nazwa podrozdziału, obowiązkowa')
        parser.add_argument('stary_numer', help='stary numer zadania')
        parser.add_argument('nowy_numer', help='nowy numer zadania')
        print('Running dodaj rozdzial={0} podrozdzial={1} stary_numer={2} nowy_numer={3}'.format(
            args.rozdzial, args.podrozdzial, args.stary_numer, args.nowy_numer))
        rename_tasks(args.rozdzial, args.podrozdzial, int(args.stary_numer), int(args.nowy_numer))

    def _load_config(self, path="zadania.json"):
        with open(path, "r", encoding=ENCODING) as f:
            cfg = json.loads(f.read())
        return cfg

    def _load_atrs(self, path="atrybuty.json"):
        return self._load_config(path)

# TODO by mozna bylo zmienic nazwe katalogow i plikow
if __name__ == "__main__":
    update_config()
    BaseRunner()
