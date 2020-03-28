# -*- coding: utf-8 -*-
import os

class Config(object):
    root_dir = 'C:\\Users\\User\\Repos\\baza_zadan'
    tmp_dir = 'C:\\Users\\User\\Repos\\baza_zadan\\tmp'
    task_dir = os.path.join(root_dir, "zadania")
    solv_dir = os.path.join(root_dir, "rozwiązania")
    file_config = {"preamble_len": 4,
                   "preamble_text": [r"\documentclass{article}", 
                                     r"\usepackage{polski}", 
                                     r"\usepackage[utf8]{inputenc}",
                                     r"\usepackage{graphicx}",
                                     r"\usepackage{amsmath}",
                                     r"\usepackage{geometry}",
                                     r"\newgeometry{tmargin=1.5cm, bmargin=1.5cm, lmargin=1.5cm, rmargin=1.5cm}",
                                     r"\begin{document}"],
                    "end_text": [r"\end{document}"]}
    tasks_config_file = os.path.join(root_dir, "tasks_config.json")
    tsk_ext = ".tex"
    sol_ext = ".pdf"
    to_clean_ext = [".aux", ".toc", ".out", ".snm", ".log"]