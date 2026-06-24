import { $ } from "./dom.js";
import { createCertificateImage } from "./certificate_canvas.js";

export function initCertificateDownload() {
  const downloadCertificate = $("#download-certificate");
  if (!downloadCertificate) return;

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
