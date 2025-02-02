from flask import Flask, render_template, send_file, request, redirect, url_for
import os
from pdf2image import convert_from_path
import re
import json

app = Flask(__name__, static_folder="static", template_folder="templates")

# PDFフォルダのパス
IMAGE_FOLDER = "static/images"
SERVER_URL = "http://127.0.0.1:5000"
basedir = "../レポート"
MARKS_FILE = "marks.json"
SAVE_DIR = "../save"

os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)

def extract_number(filename):
    match = re.search(r'第(\d+)回', filename)
    return int(match.group(1)) if match else float('inf')

dirlist = os.listdir(basedir)
sorted_dirlist = sorted(dirlist, key=extract_number)

# PDFを画像に変換
def convert_pdf_to_images(pdf_path_list, savedir, img_name):
    try:
        if os.path.exists( os.path.join(IMAGE_FOLDER, savedir, f"{img_name}_page0.png")):
            n = sum(1 for f in os.listdir(os.path.join(IMAGE_FOLDER, savedir)) if f.startswith(f"{img_name}_page"))
            return [os.path.join(IMAGE_FOLDER, savedir, f"{img_name}_page{i}.png") for i in range(n)]

        page = 0
        for pdf_path in pdf_path_list:
            images = convert_from_path(pdf_path)
            image_paths = []
            for img in images:
                os.makedirs(os.path.join(IMAGE_FOLDER, savedir), exist_ok=True)
                img_path = os.path.join(IMAGE_FOLDER, savedir, f"{img_name}_page{page}.png")
                page += 1
                img.save(img_path, "PNG")
                image_paths.append(img_path)
    except:
        image_paths = [os.path.join(IMAGE_FOLDER, "error.png"),]
    return image_paths

def load_marks(report, author):
    name = author+".json"
    path = os.path.join(SAVE_DIR, report, name)
    if os.path.exists(path):
        with open(path, "r") as f:
            marks = json.load(f)
        return marks
    return []

def load_problem_list(report):
    path = os.path.join(SAVE_DIR, report+".txt")
    if os.path.exists(path):
        with open(path, "r") as f:
            problems = f.read().splitlines()
    else:
        with open(path, "w") as f:
            pass
        problems = load_problem_list(report)
    return problems

@app.route("/")
def index():
    finished = [check_finished_report(report) for report in sorted_dirlist]
    return render_template("dirlist.html", dirlist=sorted_dirlist, finished=finished)


@app.route("/author/<int:report_index>")
def view_author(report_index):
    author_list = os.listdir(os.path.join(basedir, sorted_dirlist[report_index]))
    problem_num = len(load_problem_list(sorted_dirlist[report_index]))
    finished = [check_finished(sorted_dirlist[report_index], author, problem_num) for author in author_list]
    report = sorted_dirlist[report_index]
    return render_template("authorlist.html", author_list=author_list, report_index=report_index, report=report, finished=finished)

@app.route("/pdf/<int:report_index>/<int:author_index>/<int:page_num>")
def view_pdf(report_index, author_index, page_num):
    question = request.args.get("question", default=0, type=int)
    auto_next = request.args.get("auto_next", default="true", type=str)
    auto_next_check = request.args.get("confirm_next", default="true", type=str)
    author_list = os.listdir(os.path.join(basedir, sorted_dirlist[report_index]))
    author = author_list[author_index]
    pdfs = os.listdir(os.path.join(basedir, sorted_dirlist[report_index], author))
    img_name = author
    pdf_path_list = [os.path.join(basedir, sorted_dirlist[report_index], author, pdf) for pdf in pdfs]
    images = convert_pdf_to_images(pdf_path_list, sorted_dirlist[report_index], img_name)
    marks = load_marks(sorted_dirlist[report_index], author)
    problems = load_problem_list(sorted_dirlist[report_index])
    myurl = f"'/pdf/{report_index}/{author_index}/{page_num}?question={question}'"

    if page_num >= len(images):
        return "No more pages."
    

    return render_template(
        "viewer.html",
        image_path=images[page_num],
        report_index=report_index,
        author_index=author_index,
        report=sorted_dirlist[report_index],
        author=author,
        page_num=page_num,
        total_pages=len(images),
        total_pdfs=len(pdfs),
        total_authors=len(author_list),
        marks=marks,
        question=question,
        problems=problems,
        problems_num=len(problems),
        myurl=myurl,
        auto_next=auto_next,
        confirm_next=auto_next_check
    )

@app.route("/edit_problems/<int:report_index>")
def edit_problems(report_index):
    prevpage = request.args.get("prevpage", default=None, type=str)
    report = sorted_dirlist[report_index]
    problems = load_problem_list(report)
    return render_template("edit_problems.html", report=report, problems=problems, report_index=report_index, prevpage=prevpage)


@app.route("/save_marks", methods=["POST"])
def save_marks():
    data = request.get_json()
    author = data["author"]
    report = data["report"]
    marks = data["marks"]

    os.makedirs(os.path.join(SAVE_DIR, report), exist_ok=True)
    name = author+".json"

    # マークデータをファイルに保存
    with open(os.path.join(SAVE_DIR, report, name), "w") as f:
        json.dump(marks, f)

    return {"status": "success"}

@app.route("/save_problems", methods=["POST"])
def save_problems():
    data = request.get_json()
    report_index = data["report_index"]
    names = data["name"]
    index = data["index"]

    report = sorted_dirlist[report_index]
    path = os.path.join(SAVE_DIR, report+".txt")
    with open(path, "w") as f:
        for n in names:
            f.write(n+"\n")
    reflesh_saved_data(report, index)
    return {"status": "success"}

def reflesh_saved_data(report, index):
    os.makedirs(os.path.join(SAVE_DIR, report), exist_ok=True)
    json_list = os.listdir(os.path.join(SAVE_DIR, report))
    marks_new = [None for i in index]
    for j in json_list:
        author = remove_json_suffix(j)
        marks = load_marks(report, author)
        for i, idx in enumerate(index):
            if idx < len(marks) and idx >= 0:
                marks_new[i] = marks[idx]
        with open(os.path.join(SAVE_DIR, report, j), "w") as f:
           json.dump(marks_new, f)

def remove_json_suffix(filename):
    return re.sub(r'\.json$', '', filename)

def check_finished(report, author, problems_num):
    if problems_num == 0:
        return False
    marks = load_marks(report, author)
    if len(marks) < problems_num:
        return False
    return all(mark is not None for mark in marks)

def check_finished_report(report):
    problems_num = len(load_problem_list(report))
    author_list = os.listdir(os.path.join(basedir, report))
    return all(check_finished(report, author, problems_num) for author in author_list)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
