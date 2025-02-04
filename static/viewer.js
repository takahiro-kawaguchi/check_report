let currentMark = 'circle'; // デフォルトマーク
let marks = [];
let currentPage = 0;
const markSize = 0.05;
const big_ratio = 1.5;
let currentQuestion = 0;
let problemCount = 0;
let auto_next = true;
let auto_next_check = true;
let rotate = 0;
// マークを選択

const canvas = document.getElementById("canvas");
let ctx = canvas.getContext("2d");
const img = document.getElementById("pdf-image");

img.addEventListener('load', redrawCanvas);

canvas.width = img.width;
canvas.height = img.height;

const buttons = {
    circle: document.getElementById("btn-circle"),
    cross: document.getElementById("btn-cross"),
    triangle: document.getElementById("btn-triangle"),
    erace: document.getElementById("btn-erace")
};

const pageLinks = [
    document.getElementById("prev-page-link"),
    document.getElementById("next-page-link"),
    document.getElementById("first-page-link"),
    document.getElementById("last-page-link")
]

const pageNav = document.querySelectorAll(".page-nav"); // すべてのページリンクを取得


const nextReportLink = document.getElementById("next-report-link");

const problemLinks = [];
const markLinks = [];

function setMark(mark) {
    currentMark = mark;
    Object.values(buttons).forEach(btn => {
        btn.classList.remove("btn-primary");
        btn.classList.add("btn-outline-primary");
    });

    // 選択されたボタンを強調
    buttons[mark].classList.remove("btn-outline-primary");
    buttons[mark].classList.add("btn-primary");
}


function redrawCanvas() {
    return new Promise((resolve) => {
        const page_num = currentPage;
        resetCanvasWidth();
        ctx.clearRect(0, 0, canvas.width, canvas.height); // クリア
        marks.forEach((mark, i) => {
            if (!mark) {
                return;
            }
            if (mark.page !== page_num) {
                return;
            }
            let x = mark.x;
            let y = mark.y;
            if (rotate == 1) {
                const x_ = y;
                y = 1 - x;
                x = x_;
            }
            if (rotate == 2) {
                x = 1 - x;
                y = 1 - y;
            }
            if (rotate == 3) {
                const x_ = 1 - y;
                y = x;
                x = x_;
            }
            let markSize_ = markSize;
            if (i === currentQuestion) {
                markSize_ = markSize * big_ratio;
            }
            if (mark.mark === 'circle') {
                drawCircle(x, y, markSize_);
            } else if (mark.mark === 'cross') {
                drawCross(x, y, markSize_);
            } else if (mark.mark === 'triangle') {
                drawTriangle(x, y, markSize_);
            }
        });

        setTimeout(() => {
            resolve();
        }, 100);
    });
}

function updateMarks() {
    return new Promise((resolve) => {
        marks.forEach((mark, i) => {
            if (!mark) {
                markLinks[i].textContent = '';
                return;
            }
            if (mark.mark === 'circle') {
                markLinks[i].textContent = '○';
            } else if (mark.mark === 'cross') {
                markLinks[i].textContent = '×';
            } else if (mark.mark === 'triangle') {
                markLinks[i].textContent = '△';
            }
        });
        setTimeout(() => {
            resolve();
        }, 100);
    });
}


// マークの描画関数
function drawCircle(x_ratio, y_ratio, size_ratio) {
    const rect = canvas.getBoundingClientRect();
    const x = x_ratio * rect.width;
    const y = y_ratio * rect.height;
    const size = size_ratio * rect.width / 2 * 1.25;
    ctx.beginPath();
    ctx.arc(x, y, size, 0, Math.PI * 2);
    // ctx.fillStyle = 'red';
    // ctx.fill();
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 5;
    ctx.stroke();
}

function drawCross(x_ratio, y_ratio, size_ratio) {
    const rect = canvas.getBoundingClientRect();
    const x = x_ratio * rect.width;
    const y = y_ratio * rect.height;
    const size = size_ratio * rect.width / 2;
    ctx.beginPath();
    ctx.moveTo(x - size, y - size);
    ctx.lineTo(x + size, y + size);
    ctx.moveTo(x + size, y - size);
    ctx.lineTo(x - size, y + size);
    ctx.strokeStyle = 'blue';
    ctx.lineWidth = 5;
    ctx.stroke();
}

function drawTriangle(x_ratio, y_ratio, size_ratio) {
    const rect = canvas.getBoundingClientRect();
    const x = x_ratio * rect.width;
    const y = y_ratio * rect.height;
    const size = size_ratio * rect.width / 2
    ctx.beginPath();
    ctx.moveTo(x, y - size);
    ctx.lineTo(x - size, y + size);
    ctx.lineTo(x + size, y + size);
    ctx.closePath();
    ctx.strokeStyle = 'green';
    ctx.lineWidth = 5;
    ctx.stroke();
}

async function clicked_event(event, report, author, page_num) {
    if (problemCount === 0) {
        return;
    }
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    let x_ratio = x / rect.width;
    let y_ratio = y / rect.height;
    if (rotate == 1) {
        const x_ = 1 - y_ratio;
        y_ratio = x_ratio;
        x_ratio = x_;
    }
    if (rotate == 2) {
        x_ratio = 1 - x_ratio;
        y_ratio = 1 - y_ratio;
    }
    if (rotate == 3) {
        const x_ = y_ratio;
        y_ratio = 1 - x_ratio;
        x_ratio = x_;
    }

    if (currentMark !== 'erace') {
        marks[currentQuestion] = { page: page_num, x: x_ratio, y: y_ratio, mark: currentMark };
        await redrawCanvas(page_num);
        await updateMarks();
        findNextProblem();
    } else {
        const clickedIndex = marks.findIndex(mark => {
            if (!mark) {
                return false;
            }
            return mark.page === page_num && Math.abs(mark.x - x_ratio) < markSize / 2 && Math.abs(mark.y - y_ratio) < markSize / 2;
        });
        if (clickedIndex >= 0) {
            marks[clickedIndex] = null;
        }
    }
    redrawCanvas();
    updateMarks();
    saveMarks(report, author, page_num, marks);
}

function saveMarks(report, author, page_num, marks) {
    fetch('/save_marks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            report: report,
            author: author,
            page_num: page_num,
            marks: marks
        }),
    });
}

function loadJson(jsonMarks) {
    marks_load = JSON.parse(jsonMarks);
    marks_load.forEach((mark, i) => {
        if (!mark) {
            return;
        }
        marks[i] = { x: mark.x, y: mark.y, mark: mark.mark, page: mark.page };
    });
}

function resetCanvasWidth() {
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    ctx = canvas.getContext("2d");
}

window.addEventListener('resize', redrawCanvas);

function changeProblem(problemIndex) {
    currentQuestion = problemIndex;
    problemLinks.forEach(btn => {
        btn.classList.remove("btn-primary");
        btn.classList.add("btn-outline-primary");
    });

    // 選択されたボタンを強調
    problemLinks[problemIndex].classList.remove("btn-outline-primary");
    problemLinks[problemIndex].classList.add("btn-primary");

    pageLinks.forEach(link => {
        // const url = new URL(link.getAttribute("href"));
        // url.searchParams.set('question', problemIndex);
        // const href = url.toString();
        link.setAttribute("href", updateQueryParameter(link.getAttribute("href"), 'question', problemIndex));
        //const href = link.getAttribute("href").split("?")[0];
        //link.setAttribute("href", `${href}?question=${problemIndex}`);
    });
    pageNav.forEach(link => {
        link.setAttribute("href", updateQueryParameter(link.getAttribute("href"), 'question', problemIndex));
    });
    redrawCanvas();
}

function getProblemLinks(problemCount) {
    for (let i = 0; i < problemCount; i++) {
        problemLinks.push(document.getElementById(`problem${i}`));
        markLinks.push(document.getElementById(`mark${i}`));
    }
}

function removeMark_(index, report, author, page_num) {
    marks[index] = null;
    redrawCanvas();
    updateMarks();
    saveMarks(report, author, page_num, marks);
}

function findNextProblem(transition = true) {
    let isAllMarked = true;
    for (let i = currentQuestion; i < problemCount; i++) {
        if (!marks[i]) {
            isAllMarked = false;
            changeProblem(i);
            break;
        }
    }
    if (isAllMarked) {
        for (let i = 0; i < currentQuestion; i++) {
            if (!marks[i]) {
                isAllMarked = false;
                changeProblem(i);
                break;
            }
        }
    }

    if (isAllMarked && transition && auto_next) {
        if (!auto_next_check) {
            const autoNext = document.getElementById("auto-next");
            auto_next = autoNext.checked;
            let nexturl = updateQueryParameter(nextReportLink.href, 'auto_next', auto_next);
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
            let nexturl = updateQueryParameter(nextReportLink.href, 'auto_next', auto_next);
            const autoNextcheck = document.getElementById("confirm-next");
            auto_next_check = autoNextcheck.checked;
            nexturl = updateQueryParameter(nexturl, 'confirm_next', auto_next_check);
            location.replace(nexturl);
        } else {
            changeProblem(0);
        }
    }
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

function updateQueryParameter(url, param, newValue) {
    if (url == "#") {
        return url;
    }
    let urlObj = new URL(url, window.location.origin);
    urlObj.searchParams.set(param, newValue);
    return urlObj.pathname + "?" + urlObj.searchParams.toString();
}

function rotate_image(i_rotate) {
    rotate = (rotate + i_rotate) % 4;
    let url = location.href;
    url = updateQueryParameter(url, 'rotate', rotate);
    url = updateQueryParameter(url, 'question', currentQuestion);
    url = updateQueryParameter(url, 'auto_next', auto_next);
    url = updateQueryParameter(url, 'confirm_next', auto_next_check);
    location.replace(url);
}

function move_up(index, report, author, page_num) {
    if (index > 0) {
        [marks[index - 1], marks[index]] = [marks[index], marks[index - 1]];
        redrawCanvas();
        updateMarks();
        saveMarks(report, author, page_num, marks);
    }
}
function move_down(index, report, author, page_num) {
    if (index < problemCount - 1) {
        [marks[index + 1], marks[index]] = [marks[index], marks[index + 1]];
        redrawCanvas();
        updateMarks();
        saveMarks(report, author, page_num, marks);
    }
}