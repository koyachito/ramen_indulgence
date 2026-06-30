import { initClock } from "./js/clock.js";
import { initRevealAnimations } from "./js/reveal.js";
import {
  initAutoSubmitForms,
  initCounters,
  initMagneticButtons,
} from "./js/page_enhancements.js";
import { initInterviewFlow } from "./js/interview_flow.js?v=16-reaction-total-2300ms";
import { initCertificateDownload } from "./js/download_certificate.js";
import { initStatsBars } from "./js/stats_bars.js";

initClock();
initAutoSubmitForms();
initRevealAnimations();
initCounters();
initInterviewFlow();
initCertificateDownload();
initMagneticButtons();
initStatsBars();
