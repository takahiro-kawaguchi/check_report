const sample_code = document.getElementById('sample_code');

function initialize_sample(sample_code_text) {
    sample_code.value = sample_code_text;
}


function save_sample(report_index, prevurl="#") {
    let code = sample_code.value;
    const input_data = { report_index: report_index, code: code};
    const input_data_json = JSON.stringify(input_data);
    if (!confirm('変更を保存しますか？')) {
        return;
    }

    fetch('/save_sample', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: input_data_json
    });
    location.replace(prevurl);
}

function cancel_edit(prevurl="#"){
    if (!confirm('変更を破棄しますか？')) {
        return;
    }
    location.replace(prevurl);
}