const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];

function updateClock() {
  const now = new Date();
  const hour = $("#current-hour");
  const month = $("#current-month");
  const day = $("#current-day");
  if (hour) hour.value = now.getHours();
  if (month) month.value = now.getMonth() + 1;
  if (day) day.value = now.getDate();
  const issuedAt = $("#issued-at");
  if (issuedAt) {
    issuedAt.textContent = now.toLocaleString("ja-JP", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
}
updateClock();
setInterval(updateClock, 30000);

$$("[data-stats-link]").forEach((link) => {
  link.href = `/stats?hour=${new Date().getHours()}`;
});
$$("form[data-auto-submit]").forEach((form) => {
  setTimeout(() => form.submit(), Number(form.dataset.autoSubmit));
});

if ("IntersectionObserver" in window) {
  const revealObserver = new IntersectionObserver(
    (entries) => entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        revealObserver.unobserve(entry.target);
      }
    }),
    { threshold: 0.12 },
  );
  $$(".reveal").forEach((element) => revealObserver.observe(element));
} else {
  $$(".reveal").forEach((element) => element.classList.add("is-visible"));
}

$$("[data-count]").forEach((element) => {
  const target = Number(element.dataset.count);
  const duration = 700;
  const start = performance.now();
  const tick = (time) => {
    const progress = Math.min((time - start) / duration, 1);
    element.textContent = Math.floor(target * (1 - (1 - progress) ** 3)).toLocaleString("ja-JP");
    if (progress < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
});

const questionConfig = $("#diagnosis-question-config");
const QUESTION_MESSAGES = questionConfig ? JSON.parse(questionConfig.textContent) : {};

const diagnosisForm = $("#diagnosis-form");
if (diagnosisForm) {
  const allSteps = $$(".question-step", diagnosisForm);
  const answers = {};
  let visibleSteps = allSteps.filter((step) => !step.hasAttribute("data-conditional"));
  let currentStep = 0;
  let hasAnsweredCurrentStep = false;
  let advanceTimer = null;
  let isReacting = false;
  const sisterImage = $("#sister-image");
  const sisterMessage = $("#sister-message");
  const sisterPanel = $(".sister-panel", diagnosisForm);
  const previousButton = $("#previous-question");
  const autoAdvanceNote = $("#auto-advance-note");
  const progressBar = $("#progress-bar");

  function setSister(image, message, animate = false) {
    sisterImage.src = `${sisterImage.dataset.imageBase}${image}`;
    sisterImage.alt = message;
    sisterMessage.textContent = message;
    if (animate) {
      sisterPanel.classList.remove("is-reacting");
      void sisterPanel.offsetWidth;
      sisterPanel.classList.add("is-reacting");
    }
  }

  function toggleRamenCountQuestion(meals) {
    const conditional = allSteps.find((step) => step.dataset.question === "ramen_count_today");
    const include = Number(meals) >= 3;
    visibleSteps = allSteps.filter((step) => step !== conditional || include);
    conditional.disabled = !include;
    if (!include) {
      delete answers.ramen_count_today;
      $$('input[name="ramen_count_today"]', conditional).forEach((input) => {
        input.checked = false;
      });
    }
  }

  function showQuestion(stepIndex, preserveIntro = false) {
    currentStep = Math.max(0, Math.min(stepIndex, visibleSteps.length - 1));
    allSteps.forEach((step) => step.classList.remove("is-active"));
    const step = visibleSteps[currentStep];
    step.classList.add("is-active");
    const questionName = step.dataset.question;
    const selectedValue = answers[questionName];
    hasAnsweredCurrentStep = selectedValue !== undefined;
    if (!preserveIntro) setSister(...QUESTION_MESSAGES[questionName].prompt);
    previousButton.disabled = currentStep === 0;
    const isLast = currentStep === visibleSteps.length - 1;
    autoAdvanceNote.textContent = isLast
      ? "回答後、自動で審議を始めます"
      : "回答を選ぶと自動で次へ進みます";
    progressBar.style.width = `${((currentStep + 1) / visibleSteps.length) * 100}%`;
    step.querySelector(`input[value="${CSS.escape(String(selectedValue ?? ""))}"]`)?.focus({ preventScroll: true });
  }

  function showSisterReaction(questionName, selectedValue) {
    const reaction = QUESTION_MESSAGES[questionName].reactions[selectedValue];
    if (reaction) setSister(...reaction, true);
  }

  function selectAnswer(questionName, selectedValue) {
    if (isReacting) return;
    answers[questionName] = selectedValue;
    if (questionName === "meals") toggleRamenCountQuestion(selectedValue);
    hasAnsweredCurrentStep = true;
    showSisterReaction(questionName, selectedValue);
    isReacting = true;
    diagnosisForm.classList.add("is-reacting");
    previousButton.disabled = true;
    autoAdvanceNote.textContent = currentStep === visibleSteps.length - 1
      ? "判決をまとめています…"
      : "シスターが確認しています…";
    clearTimeout(advanceTimer);
    advanceTimer = setTimeout(() => {
      isReacting = false;
      diagnosisForm.classList.remove("is-reacting");
      if (currentStep === visibleSteps.length - 1) {
        updateClock();
        diagnosisForm.requestSubmit();
      } else {
        showQuestion(currentStep + 1);
      }
    }, 1250);
  }

  function goToPreviousQuestion() {
    clearTimeout(advanceTimer);
    isReacting = false;
    diagnosisForm.classList.remove("is-reacting");
    showQuestion(currentStep - 1);
  }

  allSteps.forEach((step) => {
    $$("input[type=radio]", step).forEach((input) => {
      input.addEventListener("click", () => selectAnswer(input.name, input.value));
    });
  });
  previousButton.addEventListener("click", goToPreviousQuestion);
  diagnosisForm.addEventListener("submit", (event) => {
    if (!hasAnsweredCurrentStep) {
      event.preventDefault();
      return;
    }
    updateClock();
    diagnosisForm.classList.add("is-submitting");
  });
  showQuestion(0);
}

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

async function createCertificateImage() {
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
  try { await image.decode(); } catch (_) {
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
      canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error("PNG生成に失敗しました")), "image/png");
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
  wrapCanvasText(context, `${aruaruLabel}：${aruaruBody}`, 950).slice(0, 2).forEach((line, index) => {
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
    canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error("PNG生成に失敗しました")), "image/png");
  });
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

const downloadCertificate = $("#download-certificate");
if (downloadCertificate) {
  downloadCertificate.addEventListener("click", async () => {
    const status = $("#share-status");
    downloadCertificate.disabled = true;
    status.textContent = "免罪符画像を生成しています…";
    try {
      const blob = await createCertificateImage();
      const download = document.createElement("a");
      download.href = URL.createObjectURL(blob);
      download.download = downloadCertificate.dataset.filename;
      download.click();
      setTimeout(() => URL.revokeObjectURL(download.href), 1000);
      status.textContent = "免罪符画像をダウンロードしました。";
    } catch (_) {
      status.textContent = "免罪符画像を生成できませんでした。";
    } finally {
      downloadCertificate.disabled = false;
    }
  });
}

if (matchMedia("(pointer: fine)").matches && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
  $$(".magnetic").forEach((button) => {
    button.addEventListener("mousemove", (event) => {
      const box = button.getBoundingClientRect();
      button.style.transform = `translate(${(event.clientX - box.left - box.width / 2) * 0.09}px, ${(event.clientY - box.top - box.height / 2) * 0.12}px)`;
    });
    button.addEventListener("mouseleave", () => { button.style.transform = ""; });
  });
}
