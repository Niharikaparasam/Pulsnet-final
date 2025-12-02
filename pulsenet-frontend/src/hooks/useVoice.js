// src/hooks/useVoice.js
import { useEffect } from "react";

export function useVoice(text, deps = []) {
  useEffect(() => {
    if (!text) return;
    if (!window.speechSynthesis) return;

    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = "en-IN";
    utter.rate = 1;
    utter.pitch = 1;

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
  }, deps);
}
