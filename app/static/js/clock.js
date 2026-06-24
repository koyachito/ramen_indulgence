import { $, $$ } from "./dom.js";

const JAPAN_TIMEZONE = "Asia/Tokyo";

function japanDateParts() {
  const parts = new Intl.DateTimeFormat("ja-JP", {
    timeZone: JAPAN_TIMEZONE,
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "numeric",
    hourCycle: "h23",
  }).formatToParts(new Date());
  return Object.fromEntries(
    parts
      .filter(({ type }) => type !== "literal")
      .map(({ type, value }) => [type, Number(value)]),
  );
}

export function updateClock() {
  const now = new Date();
  const japan = japanDateParts();
  const hour = $("#current-hour");
  const month = $("#current-month");
  const day = $("#current-day");
  if (hour) hour.value = japan.hour;
  if (month) month.value = japan.month;
  if (day) day.value = japan.day;

  const issuedAt = $("#issued-at");
  if (issuedAt) {
    issuedAt.textContent = now.toLocaleString("ja-JP", {
      timeZone: JAPAN_TIMEZONE,
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
    link.href = "/stats";
  });
}
