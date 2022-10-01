import { writable } from "svelte/store";

export const FeedbackStore = writable([
  {
    id: 1,
    rating: 10,
    text: "I cumulus in my pumulus...",
  },
  {
    id: 2,
    rating: 9,
    text: "He she it we me meee.",
  },
  {
    id: 3,
    rating: 7,
    text: "GOOD LORD EVERYTHING IS ON FIRE !",
  },
])