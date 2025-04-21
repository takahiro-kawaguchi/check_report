let radios = document.querySelectorAll('input[type="radio"]');
let n_problems;
let n_problems_common;
let author;
let report;
let auto_next = true;
let auto_next_check = true;


const pageLinks = [
    document.getElementById("prev-page-link"),
    document.getElementById("next-page-link"),
    document.getElementById("first-page-link"),
    document.getElementById("last-page-link")
]

const pageNav = document.querySelectorAll(".page-nav"); // すべてのページリンクを取得


radios.forEach(radio => {
    radio.addEventListener('change', submitForm); // 状態が変更されたらsubmitFormを呼び出し
});

const form = document.getElementById('problems-form');

function submitForm(){
    // フォームのデータを取得
    let values = [];
    for(let i = 0; i<n_problems; i++){
        value = form.elements[`problem${i}`].value;
        values.push(value);
    }
    let values_common = [];
    for(let i = 0; i<n_problems_common; i++){
        value = form.elements[`common${i}`].value;
        values_common.push(value);
    }
    const data_json = JSON.stringify({
        author: author,
        report: report,
        problems: values,
        common: values_common
    });
    fetch('/save_marks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: data_json
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        if (data.message === 'finished'){
            if (auto_next) {
                if (!auto_next_check) {
                    const autoNext = document.getElementById("auto-next");
                    auto_next = autoNext.checked;
                    //let nexturl = updateQueryParameter(nextReportLink.href, 'auto_next', auto_next);
                    const unfinished = document.getElementById("next-unfinished-report-link");
                    let nexturl = unfinished.href;
                    nexturl = updateQueryParameter(nexturl, 'auto_next', auto_next);
                    const autoNextcheck = document.getElementById("confirm-next");
                    auto_next_check = autoNextcheck.checked;
                    nexturl = updateQueryParameter(nexturl, 'confirm_next', auto_next_check);
                    location.replace(nexturl);
                    return;
                }
                const resultConfirm = confirm('全ての問題にマークがつけられました。次のレポートに移動しますか？');
                if (resultConfirm) {
                    const autoNext = document.getElementById("auto-next");
                    auto_next = autoNext.checked;
                    //let nexturl = updateQueryParameter(nextReportLink.href, 'auto_next', auto_next);
                    const unfinished = document.getElementById("next-unfinished-report-link");
                    let nexturl = unfinished.href;
                    nexturl = updateQueryParameter(nexturl, 'auto_next', auto_next);
                    const autoNextcheck = document.getElementById("confirm-next");
                    auto_next_check = autoNextcheck.checked;
                    nexturl = updateQueryParameter(nexturl, 'confirm_next', auto_next_check);
                    location.replace(nexturl);
                } else {
                }
            }
        }
    });


}

function resetOption(optionName) {
    // 指定したnameのラジオボタンをすべて取得して、チェックを外す
    let radios = document.getElementsByName(optionName);
    radios.forEach(radio => {
        radio.checked = false;
    });
    submitForm();
}



function toggleAutoNext() {
    const autoNext = document.getElementById("auto-next");
    auto_next = autoNext.checked;
    pageLinks.forEach(link => {
        link.setAttribute("href", updateQueryParameter(link.getAttribute("href"), 'auto_next', auto_next));
    });
    pageNav.forEach(link => {
        link.setAttribute("href", updateQueryParameter(link.getAttribute("href"), 'auto_next', auto_next));
    });
    const nextreport = document.getElementById("next-report-link");
    nextreport.setAttribute("href", updateQueryParameter(nextreport.getAttribute("href"), 'auto_next', auto_next));
    const prevreport = document.getElementById("prev-report-link");
    prevreport.setAttribute("href", updateQueryParameter(prevreport.getAttribute("href"), 'auto_next', auto_next));
    const unfinished = document.getElementById("next-unfinished-report-link");
    unfinished.setAttribute("href", updateQueryParameter(unfinished.getAttribute("href"), 'auto_next', auto_next));
}

function toggleConfirmNext() {
    const autoNextcheck = document.getElementById("confirm-next");
    auto_next_check = autoNextcheck.checked;
    pageLinks.forEach(link => {
        link.setAttribute("href", updateQueryParameter(link.getAttribute("href"), 'confirm_next', auto_next_check));
    });
    pageNav.forEach(link => {
        link.setAttribute("href", updateQueryParameter(link.getAttribute("href"), 'confirm_next', auto_next_check));
    });
    const nextreport = document.getElementById("next-report-link");
    nextreport.setAttribute("href", updateQueryParameter(nextreport.getAttribute("href"), 'confirm_next', auto_next_check));
    const prevreport = document.getElementById("prev-report-link");
    prevreport.setAttribute("href", updateQueryParameter(prevreport.getAttribute("href"), 'confirm_next', auto_next_check));
    const unfinished = document.getElementById("next-unfinished-report-link");
    unfinished.setAttribute("href", updateQueryParameter(unfinished.getAttribute("href"), 'confirm_next', auto_next_check));
}

function updateQueryParameter(url, param, newValue) {
    if (url == "#") {
        return url;
    }
    let urlObj = new URL(url, window.location.origin);
    urlObj.searchParams.set(param, newValue);
    return urlObj.pathname + "?" + urlObj.searchParams.toString();
}


function updateCheckboxes(auto_next_, auto_next_check_) {
    pageLinks.forEach(link => {
        link.setAttribute("href", updateQueryParameter(link.getAttribute("href"), 'auto_next', auto_next_));
        link.setAttribute("href", updateQueryParameter(link.getAttribute("href"), 'confirm_next', auto_next_check_));
    });
    pageNav.forEach(link => {
        link.setAttribute("href", updateQueryParameter(link.getAttribute("href"), 'auto_next', auto_next_));
        link.setAttribute("href", updateQueryParameter(link.getAttribute("href"), 'confirm_next', auto_next_check_));
    });
    const nextreport = document.getElementById("next-report-link");
    nextreport.setAttribute("href", updateQueryParameter(nextreport.getAttribute("href"), 'auto_next', auto_next_));
    nextreport.setAttribute("href", updateQueryParameter(nextreport.getAttribute("href"), 'confirm_next', auto_next_check_));
    const prevreport = document.getElementById("prev-report-link");
    prevreport.setAttribute("href", updateQueryParameter(prevreport.getAttribute("href"), 'auto_next', auto_next_));
    prevreport.setAttribute("href", updateQueryParameter(prevreport.getAttribute("href"), 'confirm_next', auto_next_check_));
    auto_next = auto_next_;
    auto_next_check = auto_next_check_;
    const autoNext = document.getElementById("auto-next");
    autoNext.checked = auto_next;
    const autoNextcheck = document.getElementById("confirm-next");
    autoNextcheck.checked = auto_next_check;
}


function loadMark(marks, marks_common) {
    let marks_load = JSON.parse(marks);
    marks_load.forEach((mark, i) => {
        console.log(i, mark);
        nodelist = form.elements[`problem${i}`];
        nodelist.forEach((node) => {
            if (node.value === mark) {
                node.checked = true;
            }
        });
    });
    let marks_load_common = JSON.parse(marks_common);
    marks_load_common.forEach((mark, i) => {
        console.log(i, mark);
        nodelist = form.elements[`common${i}`];
        nodelist.forEach((node) => {
            if (node.value === mark) {
                node.checked = true;
            }
        });
    });
}


document.addEventListener('DOMContentLoaded', () => {
    const rows = document.querySelectorAll('#problems-form tbody tr');
    let currentRowIndex = 0;

    const focusRow = (index) => {
        const row = rows[index];
        if (!row) return;
        const checkedRadio = row.querySelector('input[type=radio]:checked'); // チェックされたラジオボタンを探す
        if (checkedRadio) {
            checkedRadio.focus();  // チェックされたラジオボタンにフォーカスを当てる
        } else {
            const firstRadio = row.querySelector('input[type=radio]'); // まだ選択されていない場合は最初のラジオボタンにフォーカス
            if (firstRadio) firstRadio.focus();
        }
            rows.forEach(row => row.classList.remove('table-active'));
            row.classList.add('table-active');

    };

    const selectRadio = (rowIndex, value) => {
        const radios = rows[rowIndex].querySelectorAll('input[type=radio]');
        radios.forEach(radio => {
            if (radio.value === value) {
                radio.checked = true;
            }
        });
        if (currentRowIndex < rows.length - 1) {
            currentRowIndex++;
            focusRow(currentRowIndex);
        }
        submitForm();
    };

    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown') {
            currentRowIndex = Math.min(currentRowIndex + 1, rows.length - 1);
            focusRow(currentRowIndex);
            e.preventDefault();
        } else if (e.key === 'ArrowUp') {
            currentRowIndex = Math.max(currentRowIndex - 1, 0);
            focusRow(currentRowIndex);
            e.preventDefault();
        } else if (e.key === '1') {
            selectRadio(currentRowIndex, 'circle');
        } else if (e.key === '2') {
            selectRadio(currentRowIndex, 'triangle');
        } else if (e.key === '3') {
            selectRadio(currentRowIndex, 'cross');
        } else if (e.key === '0') {
            // クリア（選択解除）
            const name = rows[currentRowIndex].querySelector('input[type=radio]').name;
            resetOption(name);
        }
    });

    // 最初の行にフォーカス
    focusRow(currentRowIndex);
});
