from flask import Flask, render_template, send_file, request, redirect, url_for, jsonify
import os
import re
import json
from concurrent.futures import ThreadPoolExecutor
from run_c_code_safely import run_c_code_safely
import chardet
import shutil
import bs4
import zipfile
from concurrent.futures import ThreadPoolExecutor
import uuid

app = Flask(__name__, static_folder="static", template_folder="templates")

# PDFフォルダのパス
SERVER_URL = "http://127.0.0.1:5000"
basedir = "../レポート"
MARKS_FILE = "marks.json"
SAVE_DIR = "../save"
commentdir = "../コメント"

version = 0
def extract_keys(task_name):
    name = task_name.split("課題")[1]
    split_name = name.split("-")
    numbers = [int(n) for n in split_name if n.isdigit()]
    numbers = numbers[:-1]
    return numbers

def unzip_if_needed_and_list_folders(target_dir):
    # ディレクトリ内のファイルとフォルダを取得
    for item in os.listdir(target_dir):
        if item.lower().endswith('.zip'):
            zip_path = os.path.join(target_dir, item)
            folder_name = os.path.splitext(item)[0]
            folder_path = os.path.join(target_dir, folder_name)

            # 対応するフォルダがない場合は解凍
            if not os.path.exists(folder_path):
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(folder_path)

    # フォルダ一覧を取得（.zipではないディレクトリ）
    folder_list = [
        name for name in os.listdir(target_dir)
        if os.path.isdir(os.path.join(target_dir, name))
    ]
    
    return folder_list

#dirlist = os.listdir(basedir)
dirlist = unzip_if_needed_and_list_folders(basedir)
sorted_dirlist = sorted(dirlist, key=extract_keys)
author_lists = [os.listdir(os.path.join(basedir, report)) for report in sorted_dirlist]

scan_results = {}
executor = ThreadPoolExecutor()


@app.route("/check_finished/<int:report_index>")
def check_finished_report(report_index):
    report = sorted_dirlist[report_index]
    author_list = author_lists[report_index]

    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda author: check_finished(report, author), author_list)
    result = {"finished": all(results)}
    return jsonify(result)


def remove_GDB_comment(code):
    comments = re.findall(r"\/\*[\s\S]*?\*\/|\/\/.*", code)
    for c in comments:
        if "GDB" in c:
            code = code.replace(c, "").strip()
    return code

@app.route("/reload_reports")
def reload_reports():
    global sorted_dirlist
    global author_lists
    #dirlist = os.listdir(basedir)
    dirlist = unzip_if_needed_and_list_folders(basedir)
    sorted_dirlist = sorted(dirlist, key=extract_keys)
    author_lists = [os.listdir(os.path.join(basedir, report)) for report in sorted_dirlist]
    return redirect(url_for("index"))


@app.route("/")
def index():
    return render_template("code_dirlist.html", dirlist=sorted_dirlist)


@app.route("/author/<int:report_index>")
def view_author(report_index):
    author_list = author_lists[report_index]
    #finished = [check_finished(sorted_dirlist[report_index], author) for author in author_list]
    report = sorted_dirlist[report_index]
    return render_template("code_authorlist.html", author_list=author_list, report_index=report_index, report=report)

@app.route("/code/<int:report_index>/<int:author_index>/<int:page_num>")
def view_code(report_index, author_index, page_num):
    auto_next = request.args.get("auto_next", default="true", type=str)
    auto_next_check = request.args.get("confirm_next", default="true", type=str)
    # author_list = os.listdir(os.path.join(basedir, sorted_dirlist[report_index]))
    author_list = author_lists[report_index]
    author = author_list[author_index]
    codes = [c for c in os.listdir(os.path.join(basedir, sorted_dirlist[report_index], author)) if c.endswith(".c")]
    if page_num >= len(codes):
        return "Page not found", 404
    code = codes[page_num]
    with open(os.path.join(basedir, sorted_dirlist[report_index], author, code), "rb") as f:
        raw = f.read()
        encoding = chardet.detect(raw)["encoding"] or "utf-8"
        text = raw.decode(encoding)
        code = remove_GDB_comment(text)
    marks = load_marks(sorted_dirlist[report_index], author)
    problems = load_problem_list(sorted_dirlist[report_index])
    marks_common = load_marks("common_"+sorted_dirlist[report_index], author)
    problems_common = load_problem_list("common")
    myurl = f"'/code/{report_index}/{author_index}/{page_num}?v={version}'"
    report = sorted_dirlist[report_index]
    code_sample = load_code_sample(report)
    comment = get_comment(report_index, author_index)
    return render_template("code_viewer.html",
                code=code,
                code_sample = code_sample,
                report_index=report_index,
                total_pages=len(codes), total_authors=len(author_list),
                author_index=author_index, page_num=page_num,
                author=author, report=sorted_dirlist[report_index],
                marks=marks, problems=problems, marks_common=marks_common, problems_common=problems_common,
                problem_num=len(problems),
                problem_num_common=len(problems_common),
                auto_next=auto_next,
                confirm_next=auto_next_check,
                onlinetext = comment,
                myurl=myurl,)


def get_comment(report_index, author_index):
    report = sorted_dirlist[report_index]
    name = report.split("課題")[1]
    split_name = name.split("-")
    numbers = [int(n) for n in split_name if n.isdigit()]
    report_number = numbers[0]
    class_number = report.split("-")[0]
    comment_list = unzip_if_needed_and_list_folders(commentdir)
    #comment_list = os.listdir(commentdir)
    for comment_file in comment_list:
        if f"第{report_number}回" in comment_file and class_number in comment_file:
            #print(comment_file)
            author = author_lists[report_index][author_index]
            author_number = author.split(" ")[0]
            flist = os.listdir(os.path.join(commentdir, comment_file))
            for f in flist:
                if author_number in f:
                    source = os.path.join(commentdir, comment_file, f, "onlinetext.html")
                    soup = bs4.BeautifulSoup(open(source), 'html.parser')
                    #print(soup)
                    return soup.get_text()
            break


# def add_printf_to_scanf(content):
#     pattern = r'(scanf\s*\(\s*"[^"]*"\s*,.*?\))(\s*;)'
#     replacement = r'\1\2\nprintf("\\n");\n'
#     content = re.sub(pattern, replacement, content, flags=re.DOTALL)
#     return content

#def add_printf_to_scanf(content):
#    # scanf の構文全体をキャプチャしつつ、書式文字列と変数名を取り出す
#    pattern = r'(scanf\s*\(\s*"([^"]+)"\s*,\s*&(\w+)\s*\)\s*;)'
#
#    def replacer(match):
#        original_scanf = match.group(1)  # 元の scanf 文全体
#        fmt = match.group(2)             # 書式文字列
#        var = match.group(3)             # 変数名
#        printf_stmt = f'printf("{fmt}\\n", {var});'
#        return f'{original_scanf}\n{printf_stmt}'
#
#    return re.sub(pattern, replacer, content)
#
def add_printf_to_scanf(content):
    # scanf の構文全体をキャプチャしつつ、書式文字列と変数名を取り出す
    pattern = r'(scanf\s*\(\s*"([^"]+)"\s*,\s*&(\w+)\s*\)\s*;)'

    def replacer(match):
        original_scanf = match.group(1)  # 元の scanf 文全体
        fmt = match.group(2)             # 書式文字列（例 "%lf", "%d"）
        var = match.group(3)             # 変数名

        # 出力用にフォーマットを変換（%lfや%fを%gにする）
        fmt_for_printf = re.sub(r'%l?f', '%g', fmt)

        printf_stmt = f'printf("{fmt_for_printf}\\n", {var});'
        return f'{original_scanf}\n{printf_stmt}'

    return re.sub(pattern, replacer, content)


@app.route("/generate/<int:report_index>/<int:author_index>/<int:page_num>")
def generate_result(report_index, author_index, page_num):
    # author_list = os.listdir(os.path.join(basedir, sorted_dirlist[report_index]))
    author_list = author_lists[report_index]
    author = author_list[author_index]
    codes = [c for c in os.listdir(os.path.join(basedir, sorted_dirlist[report_index], author)) if c.endswith(".c")]
    if page_num >= len(codes):
        return "Page not found", 404
    code = codes[page_num]
    with open(os.path.join(basedir, sorted_dirlist[report_index], author, code), "rb") as f:
        raw = f.read()
        encoding = chardet.detect(raw)["encoding"] or "utf-8"
        text = raw.decode(encoding)
        code = remove_GDB_comment(text)
    inputs = load_input_list(sorted_dirlist[report_index])
    result = run_c_code_safely(add_printf_to_scanf(code), input_data_list = inputs)
    html = render_template("program_output.html",
                result = result, code=code, sccess=result["success"],
                report_index=report_index,
                total_pages=len(codes), total_authors=len(author_list), author_index=author_index, page_num=page_num,
                author=author, report=sorted_dirlist[report_index], name="report")
    return jsonify({'html': html})


@app.route("/generate_sample/<int:report_index>")
def generate_result_sample(report_index):
    code = load_code_sample(sorted_dirlist[report_index])
    inputs = load_input_list(sorted_dirlist[report_index])
    result = run_c_code_safely(add_printf_to_scanf(code), input_data_list = inputs)
    html = render_template("program_output.html",
                result = result, code=code, sccess=result["success"],
                report_index=report_index,
                total_pages=1, total_authors=1, author_index=0, page_num=0,
                author="sample", report=sorted_dirlist[report_index], name="sample")
    return jsonify({'html': html})



@app.route("/next_unfinished_report/<int:report_index>/<int:author_index>")
def next_unfinished_report(report_index, author_index):
    auto_next = request.args.get("auto_next", default="true", type=str)
    auto_next_check = request.args.get("confirm_next", default="true", type=str)
    # author_list = os.listdir(os.path.join(basedir, sorted_dirlist[report_index]))
    author_list = author_lists[report_index]
    for i in range(author_index+1, len(author_list)):
        #print(author_list[i])
        if not check_finished(sorted_dirlist[report_index], author_list[i]):
            return redirect(url_for("view_code", report_index=report_index, author_index=i, page_num=0, auto_next=auto_next, confirm_next=auto_next_check))
    for i in range(author_index):
        #print(author_list[i])
        if not check_finished(sorted_dirlist[report_index], author_list[i]):
            return redirect(url_for("view_code", report_index=report_index, author_index=i, page_num=0, auto_next=auto_next, confirm_next=auto_next_check))
    return redirect(url_for("view_author", report_index=report_index))

@app.route("/edit_problems/<report_index>")
def edit_problems(report_index):
    prevpage = request.args.get("prevpage", default="'/'", type=str)
    if report_index == "common":
        report = "common"
        report_index = -1
    else:
        report_index = int(report_index)
        report = sorted_dirlist[report_index]
    problems = load_problem_list(report)
    return render_template("edit_problems.html", report=report, problems=problems, report_index=report_index, prevpage=prevpage)

@app.route("/edit_inputs/<report_index>")
def edit_inputs(report_index):
    prevpage = request.args.get("prevpage", default="'/'", type=str)
    if report_index == "common":
        report = "common"
        report_index = -1
    else:
        report_index = int(report_index)
        report = sorted_dirlist[report_index]
    inputs = load_input_list(report)
    return render_template("edit_inputs.html", report=report, inputs=inputs, report_index=report_index, prevpage=prevpage)

@app.route("/edit_sample/<report_index>")
def edit_sample(report_index):
    prevpage = request.args.get("prevpage", default="'/'", type=str)
    report_index = int(report_index)
    report = sorted_dirlist[report_index]
    code = load_code_sample(report)
    return render_template("edit_sample.html", code_sample=code, report_index=report_index, prevpage=prevpage)



def load_problem_list(report):
    if not report.startswith("common"):
        report = "-".join(report.split("-")[1:-1])
    path = os.path.join(SAVE_DIR, report+".txt")
    if os.path.exists(path):
        with open(path, "r") as f:
            problems = f.read().splitlines()
    else:
        with open(path, "w") as f:
            pass
        problems = load_problem_list(report)
    return problems

def load_input_list(report):
    report = "-".join(report.split("-")[1:-1])
    path = os.path.join(SAVE_DIR, report+"_input.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            inputs = json.load(f)
    else:
        with open(path, "w") as f:
            json.dump([], f)
        inputs = load_input_list(report)
    return inputs

@app.route("/save_problems", methods=["POST"])
def save_problems():
    global version
    data = request.get_json()
    report_index = data["report_index"]
    names = data["name"]
    index = data["index"]
    if report_index < 0:
        report = "common"
    else:
        report = sorted_dirlist[report_index]
        report = "-".join(report.split("-")[1:-1])
    path = os.path.join(SAVE_DIR, report+".txt")
    with open(path, "w") as f:
        for n in names:
            f.write(n+"\n")
    refresh_saved_data(report, index)
    version = version + 1
    return {"status": "success"}


@app.route("/save_inputs", methods=["POST"])
def save_inputs():
    global version
    data = request.get_json()
    report_index = data["report_index"]
    names = data["name"]
    index = data["index"]
    report = sorted_dirlist[report_index]
    report = "-".join(report.split("-")[1:-1])
    path = os.path.join(SAVE_DIR, report+"_input.json")
    with open(path, "w") as f:
        json.dump(names, f)
    refresh_saved_data(report, index)
    version = version + 1
    return {"status": "success"}

@app.route("/save_sample", methods=["POST"])
def save_sample():
    data = request.get_json()
    report_index = data["report_index"]
    code = data["code"]
    report = sorted_dirlist[report_index]
    report = "-".join(report.split("-")[1:-1])
    path = os.path.join(SAVE_DIR, report+"_sample.c")
    with open(path, "w") as f:
        f.write(code)
    return {"status": "success"}


@app.route("/save_marks", methods=["POST"])
def save_marks():
    data = request.get_json()
    author = data["author"]
    report = data["report"]
    marks = data["problems"]

    os.makedirs(os.path.join(SAVE_DIR, report), exist_ok=True)
    name = author+".json"
    # マークデータをファイルに保存
    with open(os.path.join(SAVE_DIR, report, name), "w") as f:
        json.dump(marks, f)

    marks = data["common"]
    os.makedirs(os.path.join(SAVE_DIR, "common_"+report), exist_ok=True)
    name = author+".json"
    # マークデータをファイルに保存
    with open(os.path.join(SAVE_DIR, "common_"+report, name), "w") as f:
        json.dump(marks, f)
    if check_finished(report, author):
        message = "finished"
    else:
        message = "not finished"
    return jsonify({"status": "success", 'message': message}), 200

def refresh_saved_data(report, index):
    if report == "common":
        flist = os.listdir(SAVE_DIR)
        for f in flist:
            if f.startswith("common"):
                if os.path.isdir(os.path.join(SAVE_DIR, f)):
                    refresh_saved_data(f, index)
        return
    os.makedirs(os.path.join(SAVE_DIR, report), exist_ok=True)
    json_list = os.listdir(os.path.join(SAVE_DIR, report))
    for j in json_list:
        marks_new = [None for i in index]
        author = remove_json_suffix(j)
        marks = load_marks(report, author)
        for i, idx in enumerate(index):
            if idx < len(marks) and idx >= 0:
                marks_new[i] = marks[idx]
        with open(os.path.join(SAVE_DIR, report, j), "w") as f:
           json.dump(marks_new, f)

def remove_json_suffix(filename):
    return re.sub(r'\.json$', '', filename)

def load_marks(report, author):
    name = author+".json"
    path = os.path.join(SAVE_DIR, report, name)
    if os.path.exists(path):
        with open(path, "r") as f:
            marks = json.load(f)
        return marks
    return []

@app.route("/check_finished/<int:report_index>/<int:author_index>")
def check_finished_index(report_index, author_index):
    # author_list = os.listdir(os.path.join(basedir, sorted_dirlist[report_index]))
    author_list = author_lists[report_index]
    author = author_list[author_index]
    report = sorted_dirlist[report_index]
    result = check_finished(report, author)
    return jsonify({"finished": result})


def check_finished(report, author):
    if not report.startswith("common"):
        if not check_finished("common_"+report, author):
            #print("common not finished")
            return False
        #print("common finished")
        problems_num = len(load_problem_list(report))
    else:
        problems_num = len(load_problem_list("common"))
        #print("common", problems_num)
    if problems_num == 0:
        return False
    marks = load_marks(report, author)
    #print(marks)
    if len(marks) < problems_num:
        return False
    return all(mark for mark in marks)


def load_code_sample(report):
    report = "-".join(report.split("-")[1:-1])
    path = os.path.join(SAVE_DIR, report+"_sample.c")
    if os.path.exists(path):
        with open(path, "r") as f:
            code = f.read()
    else:
        shutil.copyfile("sample.c", path)
        code = load_code_sample(report)
    return code

@app.route("/get_scan_result/<scan_id>")
def get_scan_result(scan_id):
    return jsonify(scan_results.get(scan_id, {"status": "not found"}))

@app.route("/start_scan")
def start_scan():
    scan_id = str(uuid.uuid4())
    scan_results[scan_id] = {
    "status": "running",
    "errors": [],
    "log": [],
    "total": 0,
    "checked": 0,
    }
    
    def task():
        total = 0
        for report_index, report in enumerate(sorted_dirlist):
            author_list = author_lists[report_index]
            for author in author_list:
                code_dir = os.path.join(basedir, report, author)
                total += len([c for c in os.listdir(code_dir) if c.endswith(".c")])
        scan_results[scan_id]["total"] = total
        scan_results[scan_id]["checked"] = 0

        for report_index, report in enumerate(sorted_dirlist):
            author_list = author_lists[report_index]
            for author_index, author in enumerate(author_list):
                logline = f"checking {report} / {author}"
                scan_results[scan_id]["log"].append(logline)
                code_dir = os.path.join(basedir, report, author)
                codes = [c for c in os.listdir(code_dir) if c.endswith(".c")]
                for page_num, code_file in enumerate(codes):
                    code_path = os.path.join(code_dir, code_file)
                    with open(code_path, "rb") as f:
                        raw = f.read()
                        encoding = chardet.detect(raw)["encoding"] or "utf-8"
                        text = raw.decode(encoding)
                        clean_code = remove_GDB_comment(text)
                        inputs = load_input_list(report)
                        result = run_c_code_safely(add_printf_to_scanf(clean_code), input_data_list=inputs)
                        if not result["success"]:
                            scan_results[scan_id]["errors"].append({
                                "report_index": report_index,
                                "author_index": author_index,
                                "page_num": page_num,
                                "author": author,
                                "report": report,
                                "filename": code_file,
                                "error": result.get("error", "unknown error")
                            })
                    scan_results[scan_id]["checked"] += 1
        scan_results[scan_id]["status"] = "done"

    executor.submit(task)
    return jsonify({"scan_id": scan_id})


@app.route("/compile_errors_live")
def compile_errors_live():
    return render_template("compile_errors_live.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0')
