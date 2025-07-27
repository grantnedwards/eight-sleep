import { EightSleepBedCard } from "./dist/eight-sleep-bed-card.js";

// Register the custom card
customElements.define("eight-sleep-bed-card", EightSleepBedCard);

// Export for HACS
window.customCards = window.customCards || [];
window.customCards.push({
  type: "eight-sleep-bed-card",
  name: "Eight Sleep Bed Card",
  description: "A beautiful card for controlling Eight Sleep bed temperature and viewing sleep metrics",
  preview: true,
  documentationURL: "https://github.com/lukas-clarke/eight_sleep",
}); 