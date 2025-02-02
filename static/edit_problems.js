const problems_index = [];
const problem_names = [];
const problem_list = document.getElementById('problem-list');
const problem_input = [];
function initialize_problem_list(problems) {
    problems.forEach((problem, index) => {
        problems_index.push(index);
        problem_names.push(problem);
    }
    );
    reflesh_problem_list();
}

function reflesh_problem_list() {
    problem_list.innerHTML = '';
    problem_input.length = 0;
    if (problems_index.length == 0) {
        const problem_item = document.createElement('li');
        problem_item.innerHTML = `
            <button class="btn btn-outline-primary" onclick="add_prev(0)">追加</button>
        `;
        problem_list.appendChild(problem_item);
        problem_input[i] = document.getElementById(`problem-${i}`);
        addEventListener('input', () => { problem_names[i] = problem_input[i].value; });
    }
    problem_names.forEach((name, i) => {
        const problem_item = document.createElement('li');
        problem_item.innerHTML = `
            <button class="btn btn-outline-primary" onclick="add_prev(${i})">上に追加</button>
            <input type="text" class="editable" id="problem-${i}" value="${name}">
            <button class="btn btn-outline-primary" onclick="add_next(${i})">下に追加</button>
            <button class="btn btn-outline-secondary" onclick="move_up(${i})">↑</button>
            <button class="btn btn-outline-secondary" onclick="move_down(${i})">↓</button>
            <button class="btn btn-outline-danger" onclick="delete_problem(${i})">削除</button>
        `;
        problem_list.appendChild(problem_item);
        problem_input[i] = document.getElementById(`problem-${i}`);
        addEventListener('input', () => { problem_names[i] = problem_input[i].value; });
    });
}

function add_next(index) {
    problems_index.splice(index + 1, 0, -1);
    problem_names.splice(index + 1, 0, '');
    reflesh_problem_list();
}

function add_prev(index) {
    problems_index.splice(index, 0, -1);
    problem_names.splice(index, 0, '');
    reflesh_problem_list();
}

function move_up(index) {
    if (index > 0) {
        [problems_index[index - 1], problems_index[index]] = [problems_index[index], problems_index[index - 1]];
        [problem_names[index - 1], problem_names[index]] = [problem_names[index], problem_names[index - 1]];
        reflesh_problem_list();
    }
}
function move_down(index) {
    if (index < problems_index.length - 1) {
        [problems_index[index + 1], problems_index[index]] = [problems_index[index], problems_index[index + 1]];
        [problem_names[index + 1], problem_names[index]] = [problem_names[index], problem_names[index + 1]];
        reflesh_problem_list();
    }
}

function delete_problem(index) {
    const problem_name = problem_names[index];
    if (!confirm(`本当に「${problem_name}」を削除して良いですか？`)) {
        return;
    }
    problems_index.splice(index, 1);
    problem_names.splice(index, 1);
    reflesh_problem_list();
}

function save_problems(report_index, prevurl="#") {
    console.log(prevurl);
    const problem_data = { report_index: report_index, name: problem_names, index: problems_index };
    const problem_data_json = JSON.stringify(problem_data);
    if (!confirm('変更を保存しますか？')) {
        return;
    }

    fetch('/save_problems', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: problem_data_json
    });
    location.replace(prevurl);
}

function cancel_edit_problems(prevurl="#"){
    if (!confirm('変更を破棄しますか？')) {
        return;
    }
    location.replace(prevurl);
}