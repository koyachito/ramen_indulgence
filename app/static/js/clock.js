import { $, $$ } from "./dom.js";

export function updateClock() {
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

export function initClock() {
  updateClock();
  setInterval(updateClock, 30000);
  $$("[data-stats-link]").forEach((link) => {
    link.href = `/stats?hour=${new Date().getHours()}`;
  });
}
