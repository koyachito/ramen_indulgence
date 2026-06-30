export function initStatsBars() {
  document.querySelectorAll("[data-width]").forEach((el) => {
    el.style.setProperty("--width", `${el.dataset.width}%`);
  });
}
