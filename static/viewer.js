let currentMark = 'circle'; // デフォルトマーク
let marks = [];
let currentPage = 0;
const markSize = 0.05;
const big_ratio = 1;
let currentQuestion = 0;
let problemCount = 0;
// マークを選択

const canvas = document.getElementById("canvas");
let ctx = canvas.getContext("2d");
const img = document.getElementById("pdf-image");

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
            let markSize_ = markSize;
            if (i === currentQuestion) {
                markSize_ = markSize * big_ratio;
            }
            if (mark.mark === 'circle') {
                drawCircle(mark.x, mark.y, markSize_);
            } else if (mark.mark === 'cross') {
                drawCross(mark.x, mark.y, markSize_);
            } else if (mark.mark === 'triangle') {
                drawTriangle(mark.x, mark.y, markSize_);
            }
        });

        setTimeout(() => {
            resolve();
        }, 50);
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
        }, 10);
    });
}


// マークの描画関数
function drawCircle(x_ratio, y_ratio, size_rataio) {
    const rect = canvas.getBoundingClientRect();
    const x = x_ratio * rect.width;
    const y = y_ratio * rect.height;
    const size = size_rataio * rect.width / 2 * 1.25;
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
    const size = size_ratio * rect.width / 2
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
    x = x_ratio * rect.width;
    y = y_ratio * rect.height;
    size = size_ratio * rect.width / 2
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
    const x_ratio = x / rect.width;
    const y_ratio = y / rect.height;

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
        const href = link.getAttribute("href").split("?")[0];
        link.setAttribute("href", `${href}?question=${problemIndex}`);
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

    if (isAllMarked && transition) {
        const resultConfirm = confirm('全ての問題にマークがつけられました。次のレポートに移動しますか？');
        if (resultConfirm) {
            location.replace(nextReportLink.href);
        } else {
            changeProblem(0);
        }
    }
}