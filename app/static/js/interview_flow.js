import { $, $$ } from "./dom.js";
import { updateClock } from "./clock.js";
import { loadQuestionMessages } from "./question_messages.js";

export function initInterviewFlow() {
  const diagnosisForm = $("#diagnosis-form");
  if (!diagnosisForm) return;

  const questionMessages = loadQuestionMessages();
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
    const conditional = allSteps.find(
      (step) => step.dataset.question === "ramen_count_today",
    );
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
    if (!preserveIntro) setSister(...questionMessages[questionName].prompt);
    previousButton.disabled = currentStep === 0;
    const isLast = currentStep === visibleSteps.length - 1;
    autoAdvanceNote.textContent = isLast
      ? "回答後、自動で審議を始めます"
      : "回答を選ぶと自動で次へ進みます";
    progressBar.style.width = `${((currentStep + 1) / visibleSteps.length) * 100}%`;
    step.querySelector(
      `input[value="${CSS.escape(String(selectedValue ?? ""))}"]`,
    )?.focus({ preventScroll: true });
  }

  function showSisterReaction(questionName, selectedValue) {
    const reaction = questionMessages[questionName].reactions[selectedValue];
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
