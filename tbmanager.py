# -*- coding: utf-8 -*-

from copy import deepcopy
import os
import shutil
import json
import codecs
from random import randrange
from tbconfig import Config
import sys
    
class TasksBaseManager(object):
    
    def __init__(self, from_file=False, from_dirs=False, from_dict=False, dct={}):
                
        assert from_file or from_dirs or from_dict
        assert (from_dict == True and dct != {}) or from_dict == False
        if from_file:
            with open(Config.tasks_config_file, "rb") as f:
                a = f.read()
                self.tasks_config = json.loads(a)
        else:
            if from_dirs:
                self.tasks_config = {}
                self.update_config_from_dirs()
            else:
                self.tasks_config = dct
        
    def create_pdf_all(self, fn="zadania_wszystkie", odir=Config.tmp_dir):
        tex_file = deepcopy(Config.file_config["preamble_text"])
        for section, section_tasks in self.tasks_config.items():
            tex_file.append(r"\section{{ {0} }}".format(section))
            for subsection, subsection_tasks in section_tasks.items():
                tex_file.append(r"\subsection{{ {0} }}".format(subsection))
                for i, task in enumerate(subsection_tasks):
                    tex_file.append(r"\textbf{{Zadanie {0}}} \\".format(i+1))
                    tex_file += [x + r"\\" for x in task["treść"]]
        tex_file += Config.file_config["end_text"]
        fn = os.path.join(odir, fn + Config.tsk_ext)
        print("Compiling latex ...")
        with codecs.open(fn, "w", "utf-8") as f:
            f.writelines("\n".join(tex_file))
        res = os.system("pdflatex -output-directory={0} {1}".format(odir, fn))
        if res is not None:
            print("DONE!")
        else:
            print("ERROR! Check logs for details")
        self._clean_files(odir)
    
    def create_pdf(self, tasks, fn="zadania", odir=Config.tmp_dir):
        os.chdir(odir)
        tex_file = deepcopy(Config.file_config["preamble_text"])
        for sec, section_tasks in tasks.items():
            tex_file.append(r"\section{{ {0} }}".format(sec))
            for subsec, subsection_tasks in section_tasks.items():
                tex_file.append(r"\subsection{{ {0} }}".format(subsec))
                for task_num in subsection_tasks:
                    tex_file.append(r"\textbf{{Zadanie {0}}} \\".format(task_num))
                    tex_file += [x + r"\\" for x in self.tasks_config[sec][subsec][task_num-1]["treść"]]
        tex_file += Config.file_config["end_text"]
        if fn == "zadania":
            out_fn = os.path.join(odir, "{0}_{1}{2}".format(fn, randrange(10000), Config.tsk_ext))
        else:
            out_fn = os.path.join(odir, "{0}{1}".format(fn, Config.tsk_ext))
        print("Compiling latex ...")
        with codecs.open(out_fn, "w", "utf-8") as f:
            f.writelines("\n".join(tex_file))
        res = os.system("pdflatex -output-directory={0} {1}".format(odir, out_fn))
        if res is not None:
            print("DONE!")
        else:
            print("ERROR! Check logs for details") 
        self._clean_files(odir)
        
    def create_pdf_sec(self, sec, fn="zadania", odir=Config.tmp_dir):
        os.chdir(odir)
        tex_file = deepcopy(Config.file_config["preamble_text"])
        section_tasks = self.tasks_config.get(sec)
        if section_tasks is not None:
            tex_file.append(r"\section{{ {0} }}".format(sec))
            for subsec, subsection_tasks in section_tasks.items():
                tex_file.append(r"\subsection{{ {0} }}".format(subsec))
                for i, task in enumerate(subsection_tasks):
                    tex_file.append(r"\textbf{{Zadanie {0}}} \\".format(i+1))
                    tex_file += [x + r"\\" for x in task["treść"]]
            tex_file += Config.file_config["end_text"]
            if fn == "zadania":
                out_fn = os.path.join(odir, "{0}_{1}_{2}{3}".format(fn, sec, randrange(10000), Config.tsk_ext))
            else:
                out_fn = os.path.join(odir, "{0}{1}".format(fn, Config.tsk_ext))
            print("Compiling latex ...")
            with codecs.open(out_fn, "w", "utf-8") as f:
                f.writelines("\n".join(tex_file))
            res = os.system("pdflatex -output-directory={0} {1}".format(odir, out_fn))
            if res is not None:
                print("DONE!")
            else:
                print("ERROR! Check logs for details") 
            self._clean_files(odir)
        else:
            print("ERROR! Given section: {0} does not exist!".format(sec))
    
    def add_task(self, sec, subsec, fn, sol_fn, num=None):
        num -= 1
        tfn = os.path.join(Config.root_dir, fn) + Config.tsk_ext
        sfn = os.path.join(Config.root_dir, sol_fn) + Config.sol_ext
        with open(tfn, "r") as f:
            content = f.readlines()
        name = fn.split(os.sep)[-1]
        sol_name = sol_fn.split(os.sep)[-1]
        assert name + "-sol" == sol_name
        sec_dct = self.tasks_config.get(sec)
        if sec_dct is None:
            self._add_section(sec)
        subsec_dct = self.tasks_config[sec].get(subsec)
        if subsec_dct is None:
            self._add_subsection(subsec)
        if num is None:
            self.tasks_config[sec][subsec].append({"treść": content, "nazwa": name})
            n = len(self.tasks_config[sec][subsec])
        else:
            self.tasks_config[sec][subsec][num:num] = [{"treść": content, "nazwa": name}]
            self._rename_files(Config.task_dir, sec, subsec, num)
            self._rename_files(Config.solv_dir, sec, subsec, num)
            n = num+1
        task_fn = os.path.join(Config.task_dir, sec, subsec, "{0}_{1}{2}".format(n, name, Config.tsk_ext))
        shutil.move(tfn, task_fn)
        sol_new_fn = os.path.join(Config.solv_dir, sec, subsec, "{0}_{1}{2}".format(n, sol_name, Config.sol_ext))
        shutil.move(sfn, sol_new_fn)
            
    def update_config_from_dirs(self):
        for sec in os.listdir(Config.task_dir):
            self.tasks_config[sec] = {}
            for subsec in os.listdir(os.path.join(Config.task_dir, sec)):
                self.tasks_config[sec][subsec] = []
                tasks = os.listdir(os.path.join(Config.task_dir, sec, subsec))
                sorted_tasks = sorted(tasks, key=self._sort_files_key)
                for i, task in enumerate(sorted_tasks):
                    task_fn = os.path.join(Config.task_dir, sec, subsec, task)
                    with open(task_fn, "r") as f:
                        content = f.readlines()
                    try:
                        num = int(task.split("_")[0])
                        name = task.split("_")[1].split(".")[0]
                    except Exception as e:
                        name = task.split("_")[0].split(".")[0]
                    self.tasks_config[sec][subsec].append({"treść": content, "nazwa": name})
                    new_fn = os.path.join(Config.task_dir, sec, subsec, "{0}_{1}{2}".format(i+1, name, Config.tsk_ext))
                    os.rename(task_fn, new_fn)
        for sec in os.listdir(Config.solv_dir):
            for subsec in os.listdir(os.path.join(Config.solv_dir, sec)):
                solvs = os.listdir(os.path.join(Config.solv_dir, sec, subsec))
                sorted_solvs = sorted(solvs, key=self._sort_files_key)
                for i, solv in enumerate(sorted_solvs):
                    solv_fn = os.path.join(Config.solv_dir, sec, subsec, solv)
                    try:
                        num = int(solv.split("_")[0])
                        name = solv.split("_")[1].split(".")[0]
                    except Exception as e:
                        name = solv.split("_")[0].split(".")[0]
                    new_fn = os.path.join(Config.solv_dir, sec, subsec, "{0}_{1}{2}".format(i+1, name, Config.sol_ext))
                    os.rename(solv_fn, new_fn)
        self._update_cfg()
                    
    def rename_numbers(self, sec, subsec, old_num, new_num):
        self.tasks_config[sec][subsec].insert(new_num-1, self.tasks_config[sec][subsec].pop(old_num-1))
        if new_num > old_num:
            step=-1
            num = old_num + 1
            max_num = new_num + 1
        else:
            step = 1
            num = new_num
            max_num = old_num
        self._rename_files(Config.task_dir, sec, subsec, num, step=step, max_num=max_num)
        self._rename_files(Config.solv_dir, sec, subsec, num, step=step, max_num=max_num)
        name = self.tasks_config[sec][subsec][new_num-1]["nazwa"]
        old_n = "{0}_{1}".format(old_num, name)
        new_n = "{0}_{1}".format(new_num, name)
        old_fn = os.path.join(Config.task_dir, sec, subsec, old_n + Config.tsk_ext)
        new_fn = os.path.join(Config.task_dir, sec, subsec, new_n + Config.sol_ext)
        print("old: " + old_fn)
        print("new: " + new_fn)
        os.rename(old_fn, new_fn)
        old_fn = os.path.join(Config.solv_dir, sec, subsec, old_n + "-sol" + Config.tsk_ext)
        new_fn = os.path.join(Config.solv_dir, sec, subsec, new_n + "-sol" + Config.sol_ext)
        print("old: " + old_fn)
        print("new: " + new_fn)
        os.rename(old_fn, new_fn)
    
    def _update_cfg(self):
        with open(Config.tasks_config_file, "w", encoding='utf8') as f:
            json.dump(self.tasks_config, f)
            
    def _rename_files(self, tdir, sec, subsec, num, step=1, max_num=None):
        for task in os.listdir(os.path.join(tdir, sec, subsec)):
            tnr = int(task.split("_")[0])
            if tnr >= num:
                if max_num is None or tnr < max_num:
                    new_t = "{0}_{1}".format(tnr+step, task.split("_")[1])
                    old_fn = os.path.join(tdir, sec, subsec, task)
                    new_fn = os.path.join(tdir, sec, subsec, new_t)
                    print("old: " + old_fn)
                    print("new: " + new_fn)
                    os.rename(old_fn, new_fn)
        
    def _clean_files(self, dr):
        print("cleaning ...")
        for fn in os.listdir(dr):
            for ext in Config.to_clean_ext:
                if fn.endswith(ext):
                    out_fn = os.path.join(dr, fn)
                    print("Removing {0} ...".format(fn))
                    os.remove(out_fn)
                    
    def _sort_files_key(self, x):
        name = x.split("_")
        try:
            num = int(x[0])
        except Exception as e:
            num = x[0]
        return num
    
    def _add_section(self, sec):
        os.makedir(os.path.join(Config.tasks_dir, sec))
        self.tasks_config[sec] = {}
        
    def _add_subsection(self, sec, subsec):
        os.makedir(os.path.join(Config.tasks_dir, sec, subsec))
        self.tasks_config[sec][subsec] = []
        
if __name__ == "__main__":
    tm = TasksBaseManager(from_dirs=True)
    typ = sys.argv[1]
    #print(typ)
    if typ == "wszystko":
        tm.create_pdf_all()
    if typ == "generuj":
        with open("zadania.json", "rb") as f:
            a = f.read()
            config = json.loads(a)
        if len(sys.argv) > 2:
            tm.create_pdf(config, fn=sys.argv[2])
        tm.create_pdf(config)
    if typ == "sekcja":
        tm.create_pdf_sec(sys.argv[2])
    if typ == "dodaj":
        if len(sys.argv) < 6:
            print("ERROR! Podaj sekcję, podsekcję, plik z zadaniem i plik z rozwiązaniem")
        else:
            sec = sys.argv[2]
            subsec = sys.argv[3]
            zad = sys.argv[4]
            rozw = sys.argv[5]
            if len(sys.argv) > 6:
                num=int(sys.argv[6])
                print(num)
                tm.add_task(sec, subsec, zad, rozw, num)
            tm.add_task(sec, subsec, zad, rozw)
    if typ == "przenumeruj":
        if len(sys.argv) < 6:
            print("ERROR! Podaj sekcję, podsekcję, numer stary i numer nowy")
        else:
            sec = sys.argv[2]
            subsec = sys.argv[3]
            num1 = int(sys.argv[4])
            num2 = int(sys.argv[5])
            tm.rename_numbers(sec, subsec, num1, num2)
        
        



