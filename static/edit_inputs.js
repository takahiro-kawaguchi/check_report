const inputs_index = [];
const input_names = [];
const input_list = document.getElementById('input-list');
const input_input = [];
let version = 0;
function initialize_input_list(inputs) {
    inputs.forEach((inputs, index) => {
        inputs_index.push(index);
        input_names.push(inputs);
    });
    refresh_input_list();
}

function refresh_input_list() {
    input_list.innerHTML = '';
    input_input.length = 0;
    if (inputs_index.length == 0) {
        const input_item = document.createElement('li');
        input_item.innerHTML = `
            <button class="btn btn-outline-primary" onclick="add_prev(0)">追加</button>
        `;
        input_list.appendChild(input_item);
    }
    input_names.forEach((name, i) => {
        const input_item = document.createElement('li');
        input_item.innerHTML = `
            <div class="input-container">
            <button class="btn btn-outline-primary" onclick="add_prev(${i})">上に追加</button>
            <textarea class="editable" id="input-${i}" rows="3">${name}</textarea>
            <button class="btn btn-outline-primary" onclick="add_next(${i})">下に追加</button>
            <button class="btn btn-outline-secondary" onclick="move_up(${i})">↑</button>
            <button class="btn btn-outline-secondary" onclick="move_down(${i})">↓</button>
            <button class="btn btn-outline-danger" onclick="delete_input(${i})">削除</button>
            </div>
        `;
        input_list.appendChild(input_item);
        input_input[i] = document.getElementById(`input-${i}`);
        input_input[i].addEventListener('input', () => { input_names[i] = input_input[i].value; });
    });
}

function add_next(index) {
    inputs_index.splice(index + 1, 0, -1);
    input_names.splice(index + 1, 0, '');
    refresh_input_list();
}

function add_prev(index) {
    inputs_index.splice(index, 0, -1);
    input_names.splice(index, 0, '');
    refresh_input_list();
}

function move_up(index) {
    if (index > 0) {
        [inputs_index[index - 1], inputs_index[index]] = [inputs_index[index], inputs_index[index - 1]];
        [input_names[index - 1], input_names[index]] = [input_names[index], input_names[index - 1]];
        refresh_input_list();
    }
}
function move_down(index) {
    if (index < inputs_index.length - 1) {
        [inputs_index[index + 1], inputs_index[index]] = [inputs_index[index], inputs_index[index + 1]];
        [input_names[index + 1], input_names[index]] = [input_names[index], input_names[index + 1]];
        refresh_input_list();
    }
}

function delete_input(index) {
    const input_name = input_names[index];
    if (!confirm(`本当に「${input_name}」を削除して良いですか？`)) {
        return;
    }
    inputs_index.splice(index, 1);
    input_names.splice(index, 1);
    refresh_input_list();
}

function save_inputs(report_index, prevurl="#") {
    const input_data = { report_index: report_index, name: input_names, index: inputs_index };
    const input_data_json = JSON.stringify(input_data);
    if (!confirm('変更を保存しますか？')) {
        return;
    }

    fetch('/save_inputs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: input_data_json
    });
    location.replace(prevurl);
}

function cancel_edit_inputs(prevurl="#"){
    if (!confirm('変更を破棄しますか？')) {
        return;
    }
    location.replace(prevurl);
}