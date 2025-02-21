from check_report import convert_pdf_to_images, extract_number
import os

basedir = "../レポート"
dirlist = os.listdir(basedir)
sorted_dirlist = sorted(dirlist, key=extract_number)

for report_index in range(len(sorted_dirlist)):
    author_list = os.listdir(os.path.join(basedir, sorted_dirlist[report_index]))
    for author_index in range(len(author_list)):
        author = author_list[author_index]
        print(sorted_dirlist[report_index], author)
        pdfs = os.listdir(os.path.join(basedir, sorted_dirlist[report_index], author))
        img_name = author
        pdf_path_list = [os.path.join(basedir, sorted_dirlist[report_index], author, pdf) for pdf in pdfs]
        images = convert_pdf_to_images(pdf_path_list, sorted_dirlist[report_index], img_name)