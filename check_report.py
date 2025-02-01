from flask import Flask, render_template, send_file, request, redirect, url_for
import os
from pdf2image import convert_from_path
import re
import json

app = Flask(__name__, static_folder="static", template_folder="templates")

# PDFフォルダのパス
IMAGE_FOLDER = "static/images"
SERVER_URL = "http://127.0.0.1:5000"
basedir = "レポート"
MARKS_FILE = "marks.json"
SAVE_DIR = "save"

os.makedirs(IMAGE_FOLDER, exist_ok=True)

def extract_number(filename):
    match = re.search(r'第(\d+)回', filename)
    return int(match.group(1)) if match else float('inf')

dirlist = os.listdir(basedir)
sorted_dirlist = sorted(dirlist, key=extract_number)

# PDFを画像に変換
def convert_pdf_to_images(pdf_path_list, pdf_name):
    if os.path.exists( os.path.join(IMAGE_FOLDER, f"{pdf_name}_page0.png")):
        n = sum(1 for f in os.listdir(IMAGE_FOLDER) if f.startswith(f"{pdf_name}_page"))
        return [os.path.join(IMAGE_FOLDER, f"{pdf_name}_page{i}.png") for i in range(n)]

    page = 0
    for pdf_path in pdf_path_list:
        images = convert_from_path(pdf_path)
        image_paths = []
        for img in images:
            img_path = os.path.join(IMAGE_FOLDER, f"{pdf_name}_page{page}.png")
            page += 1
            img.save(img_path, "PNG")
            image_paths.append(img_path)
    return image_paths

def load_marks(report, author):
    name = author+".json"
    path = os.path.join(SAVE_DIR, report, name)
    print(path)
    if os.path.exists(path):
        with open(path, "r") as f:
            marks = json.load(f)
        return marks
    return []

@app.route("/")
def index():
    return render_template("dirlist.html", dirlist=sorted_dirlist)


@app.route("/author/<int:report_index>")
def view_author(report_index):
    author_list = os.listdir(os.path.join(basedir, sorted_dirlist[report_index]))
    return render_template("authorlist.html", author_list=author_list, report_index=report_index)

@app.route("/pdf/<int:report_index>/<int:author_index>/<int:page_num>")
def view_pdf(report_index, author_index, page_num):
    question = request.args.get("question", default=0, type=int)
    author_list = os.listdir(os.path.join(basedir, sorted_dirlist[report_index]))
    author = author_list[author_index]
    pdfs = os.listdir(os.path.join(basedir, sorted_dirlist[report_index], author))
    pdf_name = str(report_index) + "_" + str(author_index)
    pdf_path_list = [os.path.join(basedir, sorted_dirlist[report_index], author, pdf) for pdf in pdfs]
    images = convert_pdf_to_images(pdf_path_list, pdf_name)
    marks = load_marks(sorted_dirlist[report_index], author)
    print(marks)

    if page_num >= len(images):
        return "No more pages."
    
    print("finished")

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
    )

    # pdfs = get_pdf_list()
    # if pdf_index >= len(pdfs):
    #     return "No more PDFs."

    # pdf_name = os.path.splitext(pdfs[pdf_index])[0]
    # pdf_path = os.path.join(PDF_FOLDER, pdfs[pdf_index])
    # images = convert_pdf_to_images(pdf_path, pdf_name)

    # if page_num >= len(images):
    #     return redirect(url_for("view_pdf", pdf_index=pdf_index + 1, page_num=0))

    # return render_template(
    #     "viewer.html",
    #     image_path=images[page_num],
    #     pdf_index=pdf_index,
    #     page_num=page_num,
    #     total_pages=len(images),
    #     total_pdfs=len(pdfs),
    # )

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


if __name__ == "__main__":
    app.run(debug=True)
