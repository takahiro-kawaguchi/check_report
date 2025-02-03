const magnifier = document.getElementById("magnifier");
const image_magnified = img;
const toggleCheckbox = document.getElementById("toggleMagnifier");

// === 設定（虫眼鏡のサイズ & 拡大倍率） ===
const MAGNIFIER_SIZE = 400;  // 虫眼鏡の直径
const ZOOM_LEVEL = 2;         // 拡大倍率

// 虫眼鏡の大きさを設定
magnifier.style.width = `${MAGNIFIER_SIZE}px`;
magnifier.style.height = `${MAGNIFIER_SIZE}px`;

document.querySelector(".container").addEventListener("mousemove", (e) => {

    if (!toggleCheckbox.checked) {
        magnifier.style.display = "none"; // 無効なら表示しない
        return;
    }

    let { left, top, width, height } = image_magnified.getBoundingClientRect();
    let x = e.clientX - left;
    let y = e.clientY - top;

    if (x > 0 && x < width && y > 0 && y < height) {
        magnifier.style.left = `${x - MAGNIFIER_SIZE / 2}px`;
        magnifier.style.top = `${y - MAGNIFIER_SIZE / 2}px`;
        magnifier.style.backgroundImage = `url(${image_magnified.src})`;
        magnifier.style.backgroundSize = `${width * ZOOM_LEVEL}px ${height * ZOOM_LEVEL}px`;
        magnifier.style.backgroundPosition = `-${x * ZOOM_LEVEL - MAGNIFIER_SIZE / 2}px -${y * ZOOM_LEVEL - MAGNIFIER_SIZE / 2}px`;
        magnifier.style.display = "block";
    } else {
        magnifier.style.display = "none";
    }
});