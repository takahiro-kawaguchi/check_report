from flask import Flask, render_template, send_file, request, redirect, url_for
import os
from pdf2image import convert_from_path
import re
import json
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import zipfile
from PyPDF2 import PdfReader


app = Flask(__name__, static_folder="static", template_folder="templates")

# PDFフォルダのパス
IMAGE_FOLDER = "static/images"
SERVER_URL = "http://127.0.0.1:5000"
basedir = "../レポート"
MARKS_FILE = "marks.json"
SAVE_DIR = "../save"

version = 0

os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)

def extract_number(filename):
    match = re.search(r'第(\d+)回', filename)
    return int(match.group(1)) if match else float('inf')

def sorted_key(filename):
    is_extra = "遅れ" in filename
    number = extract_number(filename)
    return (is_extra, number)

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


dirlist = unzip_if_needed_and_list_folders(basedir)
sorted_dirlist = sorted(dirlist, key=sorted_key)


def get_total_pdf_pages(pdf_path_list):
    """PDFファイルのリストを受け取り、合計ページ数を返す"""
    total_pages = 0
    for pdf_path in pdf_path_list:
        try:
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                total_pages += len(reader.pages)
        except Exception as e:
            print(f"警告: {pdf_path} のページ数を読み込めませんでした。エラー: {e}")
            # エラーが発生したPDFは0ページとして扱うか、例外を投げるかを選択
            pass
    return total_pages


def convert_pdf_to_images(pdf_path_list, savedir, img_name):
    """
    PDFを画像に変換する。
    期待されるページ数と既存の画像数が一致しない場合は、再生成する。
    """
    # 保存先ディレクトリのフルパス
    save_full_dir = os.path.join(IMAGE_FOLDER, savedir)
    os.makedirs(save_full_dir, exist_ok=True)

    # 1. 期待される総ページ数を計算
    total_expected_pages = get_total_pdf_pages(pdf_path_list)
    if total_expected_pages == 0:
        print("処理するべきPDFページがありません。")
        return []

    # 2. 既存の画像ファイル数をカウント
    pattern = re.compile(rf"^{re.escape(img_name)}_page(\d+)\.png$")
    existing_images = [f for f in os.listdir(save_full_dir) if pattern.match(f)]
    num_existing_images = len(existing_images)

    # 3. ページ数と画像数を比較
    if total_expected_pages == num_existing_images:
        print(f"画像は既に生成済みです ({num_existing_images}枚)。キャッシュを利用します。")
        # ファイル名順にソートしてパスのリストを返す
        existing_images.sort(key=lambda x: int(pattern.match(x).group(1)))
        return [os.path.join(save_full_dir, f) for f in existing_images]

    # 4. 不一致の場合、既存の画像を削除して再生成
    print(f"ページ数/画像数に不一致を検出しました (期待: {total_expected_pages}, 既存: {num_existing_images})。画像を再生成します。")
    for img_file in existing_images:
        os.remove(os.path.join(save_full_dir, img_file))

    # --- 以下、画像の生成処理 ---
    try:
        all_image_paths = []
        page_counter = 0
        for pdf_path in pdf_path_list:
            images = convert_from_path(pdf_path)
            for img in images:
                img_path = os.path.join(save_full_dir, f"{img_name}_page{page_counter}.png")
                img.save(img_path, "PNG")
                all_image_paths.append(img_path)
                page_counter += 1
        
        return all_image_paths

    except Exception as e:
        print(f"エラー: PDFから画像の変換中に問題が発生しました。エラー: {e}")
        # エラー発生時は、専用のエラー画像パスを返す
        return [os.path.join(IMAGE_FOLDER, "error.png")]


def load_marks(report, author):
    name = author+".json"
    path = os.path.join(SAVE_DIR, report, name)
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                marks = json.load(f)
            return marks
        return []
    except:
        print(f"Error loading marks for {author} in report {report}. File may be corrupted or missing.")
        return []

def load_problem_list(report):
    path = os.path.join(SAVE_DIR, report+".txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            problems = f.read().splitlines()
    else:
        with open(path, "w", encoding="utf-8") as f:
            pass
        problems = load_problem_list(report)
    return problems

def rotate_images(images, rotate):
    images_new = []
    for img_path in images:
        rotated_img_path = img_path.replace(".png", f"_rotated{rotate}.png")
        if not os.path.exists(rotated_img_path):
            img = Image.open(img_path)
            img = img.rotate(rotate*90, expand=True)
            img.save(rotated_img_path)
        images_new.append(rotated_img_path)
    return images_new

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
    rotate = request.args.get("rotate", default=0, type=int) % 4
    author_list = os.listdir(os.path.join(basedir, sorted_dirlist[report_index]))
    author = author_list[author_index]
    pdfs = os.listdir(os.path.join(basedir, sorted_dirlist[report_index], author))
    img_name = author
    pdf_path_list = [os.path.join(basedir, sorted_dirlist[report_index], author, pdf) for pdf in pdfs]
    images = convert_pdf_to_images(pdf_path_list, sorted_dirlist[report_index], img_name)
    if rotate != 0:
        images = rotate_images(images, rotate)
    marks = load_marks(sorted_dirlist[report_index], author)
    problems = load_problem_list(sorted_dirlist[report_index])
    myurl = f"'/pdf/{report_index}/{author_index}/{page_num}?question={question}&rotate={rotate}&v={version}'"

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
        confirm_next=auto_next_check,
        rotate=rotate
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
    with open(os.path.join(SAVE_DIR, report, name), "w", encoding="utf-8") as f:
        json.dump(marks, f)

    return {"status": "success"}

@app.route("/save_problems", methods=["POST"])
def save_problems():
    global version
    data = request.get_json()
    report_index = data["report_index"]
    names = data["name"]
    index = data["index"]

    report = sorted_dirlist[report_index]
    path = os.path.join(SAVE_DIR, report+".txt")
    with open(path, "w", encoding="utf-8") as f:
        for n in names:
            f.write(n+"\n")
    refresh_saved_data(report, index)
    version = version + 1
    return {"status": "success"}

@app.route("/next_unfinished_report/<int:report_index>/<int:author_index>")
def next_unfinished_report(report_index, author_index):
    auto_next = request.args.get("auto_next", default="true", type=str)
    auto_next_check = request.args.get("confirm_next", default="true", type=str)
    author_list = os.listdir(os.path.join(basedir, sorted_dirlist[report_index]))
    for i in range(author_index+1, len(author_list)):
        print(author_list[i])
        if not check_finished(sorted_dirlist[report_index], author_list[i], len(load_problem_list(sorted_dirlist[report_index]))):
            return redirect(url_for("view_pdf", report_index=report_index, author_index=i, page_num=0, auto_next=auto_next, confirm_next=auto_next_check))
    for i in range(author_index):
        print(author_list[i])
        if not check_finished(sorted_dirlist[report_index], author_list[i], len(load_problem_list(sorted_dirlist[report_index]))):
            return redirect(url_for("view_pdf", report_index=report_index, author_index=i, page_num=0, auto_next=auto_next, confirm_next=auto_next_check))
    return redirect(url_for("view_author", report_index=report_index))

@app.route("/convert_all_pdfs/")
def convert_all_pdfs():
    for report_idx, report in enumerate(sorted_dirlist):
        author_list = os.listdir(os.path.join(basedir, report))
        for author_idx, author in enumerate(author_list):
            print(report, author)
            view_pdf(report_index=report_idx, author_index=author_idx, page_num=0)
    return "All PDFs converted."


def refresh_saved_data(report, index):
    os.makedirs(os.path.join(SAVE_DIR, report), exist_ok=True)
    json_list = os.listdir(os.path.join(SAVE_DIR, report))
    for j in json_list:
        marks_new = [None for i in index]
        author = remove_json_suffix(j)
        marks = load_marks(report, author)
        for i, idx in enumerate(index):
            if idx < len(marks) and idx >= 0:
                marks_new[i] = marks[idx]
        with open(os.path.join(SAVE_DIR, report, j), "w", encoding="utf-8") as f:
           json.dump(marks_new, f)

def remove_json_suffix(filename):
    return re.sub(r'\.json$', '', filename)

def check_finished(report, author, problems_num):
    print(report, author)
    if problems_num == 0:
        return False
    marks = load_marks(report, author)
    if len(marks) < problems_num:
        return False
    return all(mark is not None for mark in marks)

def check_finished_report_(report):
    problems_num = len(load_problem_list(report))
    author_list = os.listdir(os.path.join(basedir, report))
    return all(check_finished(report, author, problems_num) for author in author_list)

def check_finished_report(report):
    problems_num = len(load_problem_list(report))
    author_list = os.listdir(os.path.join(basedir, report))

    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda author: check_finished(report, author, problems_num), author_list)

    return all(results)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
