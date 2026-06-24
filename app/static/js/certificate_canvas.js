import { $, $$ } from "./dom.js";

function wrapCanvasText(context, text, maxWidth) {
  const lines = [];
  text.split("\n").forEach((paragraph) => {
    if (!paragraph) {
      lines.push("");
      return;
    }
    let line = "";
    [...paragraph].forEach((character) => {
      const candidate = line + character;
      if (line && context.measureText(candidate).width > maxWidth) {
        lines.push(line);
        line = character;
      } else {
        line = candidate;
      }
    });
    if (line) lines.push(line);
  });
  return lines;
}

function drawCanvasSeal(context, x, y, top, bottom, color = "#a94855") {
  context.save();
  context.strokeStyle = color;
  context.fillStyle = color;
  context.lineWidth = 6;
  context.strokeRect(x - 72, y - 72, 144, 144);
  context.lineWidth = 2;
  context.strokeRect(x - 62, y - 62, 124, 124);
  context.textAlign = "center";
  context.font = '700 27px "Yu Mincho", serif';
  context.fillText(top, x, y - 8);
  context.fillText(bottom, x, y + 30);
  context.restore();
}

export async function createCertificateImage() {
  const certificate = $("#certificate");
  const canvas = document.createElement("canvas");
  canvas.width = 1200;
  canvas.height = 1200;
  const context = canvas.getContext("2d");
  const resultType = certificate.dataset.resultType;
  const isSleep = resultType === "sleep";
  const isBanzai = resultType === "banzai";
  const image = new Image();
  image.src = certificate.dataset.downloadImage;
  try {
    await image.decode();
  } catch (_) {
    await new Promise((resolve, reject) => {
      image.onload = resolve;
      image.onerror = reject;
    });
  }

  if (isSleep || isBanzai) {
    context.fillStyle = "#110b15";
    context.fillRect(0, 0, 1200, 1200);
    context.strokeStyle = isBanzai ? "#c99a46" : "#a94855";
    context.lineWidth = 6;
    context.strokeRect(35, 35, 1130, 1130);
    context.drawImage(image, 330, 120, 540, 540);
    context.fillStyle = isBanzai ? "#e8b84e" : "#e06672";
    context.textAlign = "center";
    context.font = `900 ${isBanzai ? 88 : 112}px "Yu Mincho", serif`;
    context.fillText(isBanzai ? "ラーメンばんざい！" : "今日は寝ろ", 600, 790);
    drawCanvasSeal(
      context,
      960,
      610,
      isBanzai ? "麺愛" : "睡眠",
      isBanzai ? "永遠" : "直行",
      isBanzai ? "#c99a46" : "#a94855",
    );
    context.fillStyle = "#c4b8c7";
    context.font = '600 24px "Yu Gothic", sans-serif';
    context.fillText("ラーメン免罪符　#ラーメン免罪符", 600, 1090);
    return new Promise((resolve, reject) => {
      canvas.toBlob(
        (blob) => blob ? resolve(blob) : reject(new Error("PNG生成に失敗しました")),
        "image/png",
      );
    });
  }

  const title = $("h1", certificate).textContent.trim();
  const verdict = $(".verdict-label", certificate).textContent.trim();
  const text = $(".result-text", certificate).textContent.trim();
  const aruaruElement = $(".ramen-aruaru", certificate);
  const aruaruLabel = $("span", aruaruElement).textContent.trim();
  const aruaruBody = aruaruElement.textContent.replace(aruaruLabel, "").trim();
  const ramen = $$(".result-meta b", certificate)[0].textContent.trim();
  const issuedAt = $$(".result-meta b", certificate)[1].textContent.trim();

  context.fillStyle = "#f7f0df";
  context.fillRect(0, 0, 1200, 1200);
  context.strokeStyle = "#4a2459";
  context.lineWidth = 5;
  context.strokeRect(30, 30, 1140, 1140);
  context.lineWidth = 1;
  context.strokeRect(48, 48, 1104, 1104);
  context.textAlign = "center";
  context.fillStyle = "#9f273a";
  context.font = '700 24px "Yu Gothic", sans-serif';
  context.fillText(verdict, 600, 90);
  context.fillStyle = "#311654";
  context.font = '700 64px "Yu Mincho", serif';
  context.fillText(title, 600, 165);
  context.drawImage(image, 420, 175, 360, 360);

  context.textAlign = "left";
  context.fillStyle = "#20152c";
  context.font = '600 25px "Yu Mincho", serif';
  const lines = wrapCanvasText(context, text, 980);
  let y = 560;
  lines.forEach((line) => {
    if (line === "ラーメン。") {
      context.fillStyle = "#311654";
      context.font = '700 37px "Yu Mincho", serif';
      context.fillText(line, 110, y + 8);
      context.font = '600 25px "Yu Mincho", serif';
      context.fillStyle = "#20152c";
      y += 52;
    } else {
      context.fillText(line, 110, y);
      y += line ? 39 : 18;
    }
  });

  const boxY = Math.max(y + 18, 825);
  context.fillStyle = "#311654";
  context.fillRect(75, boxY, 1050, 112);
  context.fillStyle = "#ffffff";
  context.font = '700 22px "Yu Gothic", sans-serif';
  wrapCanvasText(context, `${aruaruLabel}：${aruaruBody}`, 950)
    .slice(0, 2)
    .forEach((line, index) => {
      context.fillText(line, 120, boxY + 45 + index * 32);
    });
  context.fillStyle = "#665b68";
  context.font = '600 19px "Yu Gothic", sans-serif';
  context.fillText(`発行対象：${ramen}`, 90, 1065);
  context.fillText(`発行日時：${issuedAt}`, 90, 1103);
  drawCanvasSeal(context, 1000, 150, "麺欲", "赦免");
  context.textAlign = "right";
  context.fillText("#ラーメン免罪符", 1110, 1130);

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => blob ? resolve(blob) : reject(new Error("PNG生成に失敗しました")),
      "image/png",
    );
  });
}
