import { $$ } from "./dom.js";

export function initAutoSubmitForms() {
  $$("form[data-auto-submit]").forEach((form) => {
    setTimeout(() => form.submit(), Number(form.dataset.autoSubmit));
  });
}

export function initCounters() {
  $$("[data-count]").forEach((element) => {
    const target = Number(element.dataset.count);
    const duration = 700;
    const start = performance.now();
    const tick = (time) => {
      const progress = Math.min((time - start) / duration, 1);
      element.textContent = Math.floor(
        target * (1 - (1 - progress) ** 3),
      ).toLocaleString("ja-JP");
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
}

export function initMagneticButtons() {
  if (
    !matchMedia("(pointer: fine)").matches
    || matchMedia("(prefers-reduced-motion: reduce)").matches
  ) {
    return;
  }

  $$(".magnetic").forEach((button) => {
    button.addEventListener("mousemove", (event) => {
      const box = button.getBoundingClientRect();
      button.style.transform = `translate(${(event.clientX - box.left - box.width / 2) * 0.09}px, ${(event.clientY - box.top - box.height / 2) * 0.12}px)`;
    });
    button.addEventListener("mouseleave", () => {
      button.style.transform = "";
    });
  });
}
