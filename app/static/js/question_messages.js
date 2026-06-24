import { $ } from "./dom.js";

export function loadQuestionMessages() {
  const questionConfig = $("#diagnosis-question-config");
  return questionConfig ? JSON.parse(questionConfig.textContent) : {};
}
