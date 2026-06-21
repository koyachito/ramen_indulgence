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
  if ($("#live-clock")) {
    $("#live-clock").textContent = now.toLocaleTimeString("ja-JP", {
      hour: "2-digit",
      minute: "2-digit",
    });
    $("#live-date").textContent = now.toLocaleDateString("ja-JP", {
      year: "numeric",
      month: "long",
      day: "numeric",
      weekday: "short",
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

const revealObserver = new IntersectionObserver(
  (entries) => entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("is-visible");
      revealObserver.unobserve(entry.target);
    }
  }),
  { threshold: 0.12 }
);
$$(".reveal").forEach((element) => revealObserver.observe(element));

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

const form = $("#diagnosis-form");
const progress = $("#progress-bar");
if (form && progress) {
  let currentStep = 0;
  const showStep = (step) => {
    const current = form.querySelector(".wizard-step.is-active");
    const next = form.querySelector(`.wizard-step[data-step="${step}"]`);
    if (!next || current === next) return;
    current?.classList.add("is-leaving");
    setTimeout(() => {
      $$(".wizard-step", form).forEach((item) => {
        item.classList.remove("is-active", "is-leaving");
      });
      next.classList.add("is-active");
      currentStep = step;
      progress.style.width = `${Math.max(0, step - 1) / 3 * 100}%`;
      next.querySelector("input")?.focus({ preventScroll: true });
    }, 280);
  };

  $$(".wizard-next", form).forEach((button) => {
    button.addEventListener("click", () => showStep(Number(button.dataset.nextStep)));
  });

  const activityNext = $("#activity-next", form);
  const activityInputs = $$('input[name="walked"], input[name="worked"]', form);
  const updateActivityNext = () => {
    const selected = activityInputs.some((input) => input.checked);
    $("span", activityNext).textContent = selected ? "この内容で次へ" : "どっちもしてない";
  };
  activityInputs.forEach((input) => input.addEventListener("change", updateActivityNext));
  updateActivityNext();

  $$("[data-auto-next]", form).forEach((input) => {
    input.addEventListener("change", () => {
      setTimeout(() => showStep(Number(input.dataset.autoNext)), 360);
    });
  });

  $$("[data-submit-answer]", form).forEach((input) => {
    input.addEventListener("change", () => {
      progress.style.width = "100%";
      setTimeout(() => {
        updateClock();
        form.classList.add("is-submitting");
        setTimeout(() => form.submit(), 900);
      }, 420);
    });
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (form.classList.contains("is-submitting")) return;
    updateClock();
    form.classList.add("is-submitting");
    setTimeout(() => form.submit(), 850);
  });
}

function wrapCanvasText(context, text, maxWidth) {
  const lines = [];
  let line = "";
  [...text].forEach((character) => {
    const candidate = line + character;
    if (line && context.measureText(candidate).width > maxWidth) {
      lines.push(line);
      line = character;
    } else {
      line = candidate;
    }
  });
  if (line) lines.push(line);
  return lines;
}

function drawWrappedText(context, text, x, y, maxWidth, lineHeight) {
  const lines = wrapCanvasText(context, text, maxWidth);
  lines.forEach((line, index) => context.fillText(line, x, y + index * lineHeight));
  return y + lines.length * lineHeight;
}

async function createCertificateImage() {
  const certificate = $("#certificate");
  const canvas = document.createElement("canvas");
  canvas.width = 1200;
  canvas.height = 1200;
  const context = canvas.getContext("2d");
  const reasons = $$(".reason-list p", certificate).map((item) => item.textContent.trim());
  const verdict = $(".verdict-label", certificate).textContent.trim();
  const judgment = $(".judgment-title", certificate).textContent.trim();
  const ramen = $$(".signature b", certificate)[0].textContent.trim();
  const conclusion = $(".conclusion", certificate).textContent.trim();
  const advice = $(".conditions p", certificate).textContent.trim();

  context.fillStyle = "#f7f0df";
  context.fillRect(0, 0, 1200, 1200);
  context.strokeStyle = "#311654";
  context.lineWidth = 5;
  context.strokeRect(30, 30, 1140, 1140);
  context.lineWidth = 1;
  context.strokeRect(48, 48, 1104, 1104);

  context.textAlign = "center";
  context.fillStyle = "#9f273a";
  context.font = '700 24px "Yu Gothic", sans-serif';
  context.fillText(verdict, 600, 105);
  context.fillStyle = "#311654";
  context.font = '700 72px "Yu Mincho", serif';
  context.fillText("ラーメン免罪符", 600, 190);
  context.fillStyle = "#9f273a";
  context.font = '700 38px "Yu Mincho", serif';
  context.fillText(`— ${judgment} —`, 600, 255);

  context.textAlign = "left";
  context.fillStyle = "#20152c";
  context.font = '700 28px "Yu Mincho", serif';
  context.fillText("以下の情状を認定する。", 105, 330);
  context.fillStyle = "#542287";
  context.font = '700 34px "Yu Mincho", serif';
  context.fillText(ramen, 105, 380);

  let y = 445;
  reasons.forEach((reason, index) => {
    context.fillStyle = "#311654";
    context.beginPath();
    context.arc(125, y - 8, 21, 0, Math.PI * 2);
    context.fill();
    context.fillStyle = "#e8b84e";
    context.textAlign = "center";
    context.font = '700 18px "Yu Gothic", sans-serif';
    context.fillText(String(index + 1), 125, y - 1);
    context.textAlign = "left";
    context.fillStyle = "#20152c";
    context.font = '500 23px "Yu Gothic", sans-serif';
    y = drawWrappedText(context, reason, 165, y, 750, 35) + 24;
  });

  const conclusionY = Math.max(y + 10, 770);
  context.fillStyle = "#311654";
  context.fillRect(90, conclusionY, 820, 92);
  context.fillStyle = "#ffffff";
  context.textAlign = "center";
  context.font = '700 30px "Yu Mincho", serif';
  context.fillText(conclusion, 500, conclusionY + 57);

  context.textAlign = "left";
  context.fillStyle = "#9f273a";
  context.font = '700 17px "Yu Gothic", sans-serif';
  context.fillText("付帯条件", 105, conclusionY + 145);
  context.fillStyle = "#20152c";
  context.font = '600 20px "Yu Gothic", sans-serif';
  drawWrappedText(context, advice, 105, conclusionY + 182, 760, 31);

  const image = $(".judge img", certificate);
  try {
    await image.decode();
  } catch (_) {
    // The image may already be decoded.
  }
  const imageSize = 315;
  context.drawImage(image, 830, 650, imageSize, imageSize);

  context.strokeStyle = "#9f273a";
  context.lineWidth = 7;
  context.beginPath();
  context.arc(1000, 1015, 76, 0, Math.PI * 2);
  context.stroke();
  context.textAlign = "center";
  context.fillStyle = "#9f273a";
  context.font = '700 25px "Yu Mincho", serif';
  context.fillText("麺 欲", 1000, 1005);
  context.fillText("赦 免", 1000, 1042);

  context.fillStyle = "#756c7c";
  context.font = '500 16px "Yu Gothic", sans-serif';
  context.fillText("ラーメン免罪符　#ラーメン免罪符", 600, 1130);

  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error("PNG生成に失敗しました")), "image/png");
  });
}

const shareCertificate = $("#share-certificate");
if (shareCertificate) {
  const shareButtonLabel = $("#share-button-label");
  const shareGuide = $("#share-guide");
  const supportsNativeFileShare =
    Boolean(navigator.share && navigator.canShare) &&
    navigator.canShare({
      files: [new File(["test"], "test.png", { type: "image/png" })],
    });
  const supportsImageClipboard = Boolean(window.ClipboardItem && navigator.clipboard?.write);

  if (supportsNativeFileShare) {
    shareButtonLabel.textContent = "画像つきで共有する";
    shareGuide.textContent = "タップ後、共有先の一覧から「X」を選んでください。画像も一緒に渡されます。";
  } else if (supportsImageClipboard) {
    shareButtonLabel.textContent = "画像をコピーしてXを開く";
    shareGuide.textContent = "Xが開いたらCtrl+V（Macは⌘V）で画像を貼り付けます";
  } else {
    shareButtonLabel.textContent = "画像を保存してXを開く";
    shareGuide.textContent = "保存されたPNGを、開いたXの投稿画面で画像追加してください。";
  }

  shareCertificate.addEventListener("click", async () => {
    const status = $("#share-status");
    const originalText = shareButtonLabel.textContent;
    shareCertificate.disabled = true;
    shareButtonLabel.textContent = "免罪符画像を生成中…";
    status.textContent = "";
    try {
      const blobPromise = createCertificateImage();
      let clipboardPromise = null;
      let xWindow = null;

      if (!supportsNativeFileShare && supportsImageClipboard) {
        clipboardPromise = navigator.clipboard.write([
          new ClipboardItem({ "image/png": blobPromise }),
        ]);
        xWindow = window.open(shareCertificate.dataset.shareUrl, "_blank");
      }

      const blob = await blobPromise;
      const file = new File([blob], shareCertificate.dataset.filename, { type: "image/png" });
      const shareData = {
        files: [file],
        title: "ラーメン免罪符",
        text: "本日のラーメン欲は赦されました。 #ラーメン免罪符",
      };
      if (supportsNativeFileShare && navigator.canShare(shareData)) {
        await navigator.share(shareData);
        status.textContent = "免罪符画像を共有しました。";
      } else if (clipboardPromise) {
        try {
          await clipboardPromise;
          status.textContent = "画像をコピーしました。Xの投稿欄で Ctrl+V（Macは⌘V）を押してください。";
          if (!xWindow) window.open(shareCertificate.dataset.shareUrl, "_blank", "noopener");
        } catch (_) {
          if (xWindow) xWindow.close();
          throw new Error("clipboard-failed");
        }
      } else {
        const download = document.createElement("a");
        download.href = URL.createObjectURL(blob);
        download.download = shareCertificate.dataset.filename;
        download.click();
        setTimeout(() => URL.revokeObjectURL(download.href), 1000);
        window.open(shareCertificate.dataset.shareUrl, "_blank", "noopener");
        status.textContent = "PNGを保存しました。Xの投稿画面へ画像を添付してください。";
      }
    } catch (error) {
      if (error.name !== "AbortError" && error.message === "clipboard-failed") {
        try {
          const blob = await createCertificateImage();
          const download = document.createElement("a");
          download.href = URL.createObjectURL(blob);
          download.download = shareCertificate.dataset.filename;
          download.click();
          setTimeout(() => URL.revokeObjectURL(download.href), 1000);
          window.open(shareCertificate.dataset.shareUrl, "_blank", "noopener");
          status.textContent = "画像コピーが許可されなかったため、PNGを保存しました。";
        } catch (_) {
          status.textContent = "画像を生成できませんでした。もう一度お試しください。";
        }
      } else if (error.name !== "AbortError") {
        status.textContent = "画像を生成できませんでした。もう一度お試しください。";
      }
    } finally {
      shareCertificate.disabled = false;
      shareButtonLabel.textContent = originalText;
    }
  });
}

if (matchMedia("(pointer: fine)").matches && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
  $$(".magnetic").forEach((button) => {
    button.addEventListener("mousemove", (event) => {
      const box = button.getBoundingClientRect();
      const x = (event.clientX - box.left - box.width / 2) * 0.09;
      const y = (event.clientY - box.top - box.height / 2) * 0.12;
      button.style.transform = `translate(${x}px, ${y}px)`;
    });
    button.addEventListener("mouseleave", () => {
      button.style.transform = "";
    });
  });
}
