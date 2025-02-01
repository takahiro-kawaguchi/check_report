let currentMark = 'circle'; // デフォルトマーク
let marks = [];
let currentPage = 0;
const markSize = 0.05;
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

function setMark(mark) {
    currentMark = mark;
    Object.values(buttons).forEach(btn => {
        btn.classList.remove("btn-primary");
        btn.classList.add("btn-secondary");
    });

    // 選択されたボタンを強調
    buttons[mark].classList.remove("btn-secondary");
    buttons[mark].classList.add("btn-primary");
}

const questionDisplay = document.getElementById("current-question");


function updateQuestionNumber(question) {
    pageLinks.forEach(link => {
        const href = link.getAttribute("href").split("?")[0];
        link.setAttribute("href", `${href}?question=${question}`);
    });
    questionDisplay.textContent = `問${currentQuestion}`;
}

function redrawCanvas() {
    const page_num = currentPage;
    resetCanvasWidth();
    ctx.clearRect(0, 0, canvas.width, canvas.height); // クリア
    marks.forEach(mark => {
        if (!mark) {
            return;
        }
        if (mark.page !== page_num) {
            return;
        }
        console.log(mark); 
        if (mark.mark === 'circle') {
            drawCircle(mark.x, mark.y, markSize);
        } else if (mark.mark === 'cross') {
            drawCross(mark.x, mark.y, markSize);
        } else if (mark.mark === 'triangle') {
            drawTriangle(mark.x, mark.y, markSize);
        }
    });
}

// マークの描画関数
function drawCircle(x_ratio, y_ratio, size_rataio) {
    const rect = canvas.getBoundingClientRect();
    const x = x_ratio * rect.width;
    const y = y_ratio * rect.height;
    const size = size_rataio * rect.width/2*1.25;
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
    const size = size_ratio * rect.width/2
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
    size = size_ratio * rect.width/2
    ctx.beginPath();
    ctx.moveTo(x, y - size);
    ctx.lineTo(x - size, y + size);
    ctx.lineTo(x + size, y + size);
    ctx.closePath();
    ctx.strokeStyle = 'green';
    ctx.lineWidth = 5;
    ctx.stroke();
}

function clicked_event(event, report, author, page_num) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const x_ratio = x / rect.width;
    const y_ratio = y / rect.height;

    if (currentMark !== 'erace') {
        marks[currentQuestion] = {page: page_num, x: x_ratio, y: y_ratio, mark: currentMark };
        currentQuestion++;
        updateQuestionNumber(currentQuestion);
    }else{
        const clickedIndex = marks.findIndex(mark => {
            if (!mark) {
                return false;
            }
            return mark.page === page_num && Math.abs(mark.x - x_ratio) < markSize/2 && Math.abs(mark.y - y_ratio) < markSize/2;
        });
        if (clickedIndex >= 0) {
            marks[clickedIndex] = null;
        }
    }
    redrawCanvas();
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

function loadJson(jsonMarks){
    marks_load = JSON.parse(jsonMarks);
    marks_load.forEach((mark, i) => {
        if (!mark) {
            return;
        }
        marks[i] = {x: mark.x, y: mark.y, mark: mark.mark, page: mark.page};
    });
}

function resetCanvasWidth(){
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    ctx = canvas.getContext("2d");
}

window.addEventListener('resize', redrawCanvas);