// app.js  -- updated with mic button control + robust listening UI

// ---------------- QUESTION FLOW ----------------
const interviewFlow = [
  { text: "Welcome to VoxSketch. I am your forensic assistant. To begin, was the subject male or female?", category: "gender" },
  { text: "Let's start with the face. What was the shape of their face?", category: "face" },
  { text: "What did their eyes look like?", category: "eyes" },
  { text: "Can you describe their eyebrows?", category: "eyebrows" },
  { text: "What about the nose?", category: "nose" },
  { text: "Describe their lips.", category: "lips" },
  { text: "What was the shape of their ears?", category: "ears" },
  { text: "What was their hairstyle?", category: "hair" },
  { text: "Did they have any facial hair, like a mustache", category: "mustache" },
  { text: "Did they have any facial hair, like a beard", category: "beard" }
];

const unsureTriggers = [
  "don't know","do not know","dont know",
  "don't remember","do not remember","dont remember",
  "not sure","unsure","no idea","can't remember","cant remember",
  "confused","not certain","clueless","no guess","not familiar","not aware",
];

const PAUSE_DURATION = 1800;

// map category → question index (for modification step)
const categoryToIndex = {};
interviewFlow.forEach((step, idx) => {
  categoryToIndex[step.category] = idx;
});

// ---------------- GLOBAL STATE ----------------
let currentStep = 0;
let answers = [];
let fullDescription = "";
let currentCategory = "";
let currentGender = "male";

// track which question indexes were actually asked (after auto-skips)
let askedSteps = [];

// conversation mode
let flowMode = "interview";  // "interview" | "review" | "adjust_part" | "done"
let reviewAfterThisAnswer = false;

// visual voice selection state
let visualMode = false;
let currentVisualCategory = null;
let currentVisualOptions = [];

// sketch URL management
let currentImageObjectUrl = null;

// speech recognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let recognitionActive = false; // true when recognition.start() successfully started

// DOM elements
const startButton   = document.getElementById('startButton');
const startButtonLabel = document.getElementById('startButtonLabel');
const undoButton    = document.getElementById('undoButton');
const skipButton    = document.getElementById('skipButton');
const resetButton   = document.getElementById('resetButton');
const micButton     = document.getElementById('micButton');
const promptEl      = document.getElementById('interview-prompt');
const transcriptEl  = document.getElementById('transcript');
const visualOptionsEl = document.getElementById('visual-options');
const optionsGridEl = document.getElementById('options-grid');
const resultImage   = document.getElementById('resultImage');
const previewNote   = document.getElementById('preview-note');
const genderTag     = document.getElementById('genderTag');
const listeningPill = document.getElementById('listening-pill');
const downloadBtn   = document.getElementById('downloadBtn');

// ------------------- small helpers -------------------
function escapeRegExp(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

function containsWord(text, word){
  if (!text || !word) return false;
  const re = new RegExp(`\\b${escapeRegExp(word)}\\b`, 'i');
  return re.test(text);
}

function containsAnyWord(text, arr){
  if (!text) return false;
  for (let w of arr){
    w = (w || "").trim();
    if (!w) continue;
    if (containsWord(text, w)) return true;
  }
  return false;
}

function normalizeLabel(s){
  if (!s) return "";
  return s.toLowerCase()
          .replace(/^\d+\.\s*/, "")
          .replace(/[^\w\s]/g, " ")
          .replace(/\s+/g, " ")
          .trim();
}

function speak(text){
  return new Promise(resolve => {
    const u = new SpeechSynthesisUtterance(text);
    u.onend = resolve;
    try{
      const voices = window.speechSynthesis.getVoices();
      if (voices && voices.length){
        const v = voices.find(v => v.lang && v.lang.startsWith('en')) || voices[0];
        if (v) u.voice = v;
      }
    }catch(e){}
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  });
}

// ------------------- SPEECH SETUP -------------------
if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (e) => {
    const txt = e.results[0][0].transcript;
    transcriptEl.innerText = `You said: "${txt}"`;
    if (visualMode) {
      handleVisualSpokenSelection(txt);
    } else {
      processAnswer(txt);
    }
  };

  recognition.onerror = (ev) => {
    console.error("Speech error:", ev);
    previewNote.innerText = "Speech error: " + (ev && ev.error ? ev.error : "unknown");
    setListening(false);
  };

  recognition.onend = () => {
    recognitionActive = false;
    setListening(false);
  };
} else {
  if (startButton) startButton.disabled = true;
  if (promptEl) promptEl.innerText = "Speech recognition not supported. Please use Chrome / Edge on desktop.";
}

// ------------------- listening control -------------------
function setListening(on){
  if (!listeningPill || !startButton || !startButtonLabel) return;
  if (on){
    listeningPill.style.display = "flex";
    startButton.classList.add('is-listening');
    startButtonLabel.innerText = "Listening…";
    if (micButton) micButton.classList.add('listening');
  } else {
    listeningPill.style.display = "none";
    startButton.classList.remove('is-listening');
    startButtonLabel.innerText = "Start Interview";
    if (micButton) micButton.classList.remove('listening');
  }
}

function startListening(){
  if (!recognition) return;
  try{
    if (recognitionActive) {
      setListening(true);
      return;
    }
    transcriptEl.innerText = "";
    recognition.start();
    recognitionActive = true;
    setListening(true);
  }catch(e){
    console.error("startListening error:", e);
    try{ recognition.stop(); }catch(_){}
    recognitionActive = false;
    setListening(false);
  }
}

function stopListening(){
  if (!recognition) return;
  try{
    recognition.stop();
  }catch(e){
    console.warn("stopListening error:", e);
  } finally {
    recognitionActive = false;
    setListening(false);
  }
}

if (micButton){
  micButton.addEventListener('click', (ev) => {
    ev.preventDefault();
    if (recognitionActive){
      stopListening();
    } else {
      startListening();
    }
  });
}

// ------------------- DESCRIPTION HELPERS -------------------
function recomputeDescription(){
  const parts = [];
  answers.forEach((ans, idx) => {
    if (idx === 0) return; // skip gender
    if (ans) parts.push(ans);
  });
  fullDescription = parts.join(", ");
}

function clearSketch(){
  if (currentImageObjectUrl){
    try { URL.revokeObjectURL(currentImageObjectUrl); } catch(e){}
  }
  currentImageObjectUrl = null;
  resultImage.src = "";
  resultImage.classList.remove('visible');
  previewNote.innerText = "Sketch will appear here as we talk.";
  downloadBtn.disabled = true;
}

// ------------------- INTERVIEW FLOW -------------------
async function startInterview(){
  if (!recognition) return;
  resetButton.disabled = false;
  undoButton.disabled = true;
  skipButton.disabled = true;

  currentStep = 0;
  answers = [];
  recomputeDescription();
  clearSketch();
  visualMode = false;
  currentVisualOptions = [];
  optionsGridEl.innerHTML = "";
  genderTag.textContent = "Gender: not set";
  flowMode = "interview";
  reviewAfterThisAnswer = false;
  askedSteps = [];

  await speak("Starting the interview.");
  askQuestion();
}

async function askQuestion(){
  if (flowMode !== "interview") return;

  // skip beard / mustache automatically for females
  while (
    currentStep < interviewFlow.length &&
    (interviewFlow[currentStep].category === "beard" ||
     interviewFlow[currentStep].category === "mustache") &&
    currentGender === "female"
  ) {
    currentStep++;
  }

  if (currentStep >= interviewFlow.length){
    await enterReviewMode();
    return;
  }

  const step = interviewFlow[currentStep];
  currentCategory = step.category;

  // register that this question was actually asked
  if (!askedSteps.length || askedSteps[askedSteps.length - 1] !== currentStep) {
    askedSteps.push(currentStep);
  }

  visualMode = false;
  visualOptionsEl.style.display = "none";
  optionsGridEl.innerHTML = "";
  transcriptEl.innerText = "";

  promptEl.innerText = step.text;
  undoButton.disabled = currentStep === 0;
  skipButton.disabled = currentStep === 0;

  await speak(step.text);
  startListening();
}

// ------------------- REVIEW MODE -------------------
async function enterReviewMode(){
  flowMode = "review";
  visualMode = false;
  currentVisualOptions = [];
  visualOptionsEl.style.display = "none";
  optionsGridEl.innerHTML = "";

  promptEl.innerText = "Does this sketch look accurate overall? Say 'yes', 'no', or 'somewhat'.";
  transcriptEl.innerText = "";
  await speak("We are done building the sketch. Does this sketch look accurate overall? Say yes, no, or somewhat.");
  startListening();
}

async function handleReviewAnswer(answerRaw){
  const answer = (answerRaw || "").toLowerCase().trim();

  const somewhatTriggers = ["somewhat","some what","little off","bit off","not exactly","kind of","kinda","partly","maybe"];
  const noTriggers = ["no","not accurate","wrong","bad","start again","restart","not good","try again"];
  const yesTriggers = ["yes","yeah","yep","looks good","accurate","perfect","fine","correct","all good"];

  function forceStopListening() {
    if (recognition) {
      try { recognition.stop(); } catch(e){}
    }
    recognitionActive = false;
    setListening(false);
  }

  // SOMEWHAT
  if (containsAnyWord(answer, somewhatTriggers)) {
    downloadBtn.disabled = false;
    transcriptEl.innerText = "Understood — you selected 'somewhat'.";

    forceStopListening();

    setTimeout(async () => {
      await speak("Understood. You selected somewhat. You can refine the sketch or download it as is.");
      flowMode = "adjust_part";
      promptEl.innerText = "Which part do you want to change? Say face, eyes, eyebrows, nose, lips, ears, hair, mustache, or beard.";
      await speak("Which part would you like to change? Say face, eyes, eyebrows, nose, lips, ears, hair, mustache, or beard.");
      startListening();
    }, 300);
    return;
  }

  // NO
  if (containsAnyWord(answer, noTriggers)) {
    transcriptEl.innerText = "Okay — restarting.";

    forceStopListening();

    setTimeout(async () => {
      await speak("Okay, we'll restart the interview and try again.");
      resetInterview();
      setTimeout(startInterview, 500);
    }, 300);
    return;
  }

  // YES
  if (containsAnyWord(answer, yesTriggers)) {
    flowMode = "done";
    transcriptEl.innerText = "Thank you — you can now download the sketch.";
    downloadBtn.disabled = false;

    forceStopListening();

    setTimeout(() => {
      speak("Thank you. You can now download the sketch.");
    }, 300);

    return;
  }

  // Not understood
  transcriptEl.innerText = "I didn't catch that. Say yes, no, or somewhat.";
  forceStopListening();

  setTimeout(async () => {
    await speak("I did not clearly understand. Please say yes, no, or somewhat.");
    startListening();
  }, 300);
}

// ------------------- ADJUST PART -------------------
async function handleAdjustPartAnswer(answerRaw){
  const answer = (answerRaw || "").toLowerCase();

  const partKeywords = {
    face:      ["face"],
    eyes:      ["eye","eyes"],
    eyebrows:  ["eyebrow","eyebrows","brow","brows"],
    nose:      ["nose"],
    lips:      ["lip","lips","mouth"],
    ears:      ["ear","ears"],
    hair:      ["hair","hairstyle","hairstyles","hairstyling"],
    mustache:  ["mustache","moustache"],
    beard:     ["beard","goatee","chin"]
  };

  let chosenCategory = null;

  outer:
  for (const [cat, words] of Object.entries(partKeywords)){
    for (const w of words){
      if (containsWord(answer, w)){
        chosenCategory = cat;
        break outer;
      }
    }
  }

  if (!chosenCategory){
    await speak("I could not understand which part you want to change. Please say face, eyes, eyebrows, nose, lips, ears, hair, mustache, or beard.");
    startListening();
    return;
  }

  if (currentGender === "female" && (chosenCategory === "beard" || chosenCategory === "mustache")){
    await speak("For a female sketch I do not add facial hair. Please choose another part like eyes, eyebrows, nose, lips, ears, or hair.");
    startListening();
    return;
  }

  const idx = categoryToIndex[chosenCategory];
  if (idx === undefined){
    await speak("I cannot modify that part directly. Please choose face, eyes, eyebrows, nose, lips, ears, hair, mustache, or beard.");
    startListening();
    return;
  }

  // Clear old answer for that part
  answers[idx] = null;
  recomputeDescription();
  await buildSketch(fullDescription);

  // jump back to the chosen question; after it's answered we go to review
  currentStep = idx;
  flowMode = "interview";
  reviewAfterThisAnswer = true;

  await speak(`Okay, let's adjust the ${chosenCategory}. Please answer this question again.`);
  askQuestion();
}

// ------------------- MAIN ANSWER HANDLER -------------------
async function processAnswer(answerRaw){
  const answer = (answerRaw || "").trim();
  const lower = answer.toLowerCase();

  if (flowMode === "review"){
    await handleReviewAnswer(answerRaw);
    return;
  }
  if (flowMode === "adjust_part"){
    await handleAdjustPartAnswer(answerRaw);
    return;
  }

  // GENDER
  if (currentCategory === "gender"){
    if (containsAnyWord(lower, ["female","woman","lady"])) currentGender = "female";
    else currentGender = "male";

    answers[0] = currentGender;
    genderTag.textContent = "Gender: " + currentGender;
    await speak(`Okay, I will sketch a ${currentGender}.`);
    currentStep = 1;
    setTimeout(askQuestion, PAUSE_DURATION);
    return;
  }

  // UNSURE -> show visuals
  if (containsAnyWord(lower, unsureTriggers)){
    promptEl.innerText = "I understand. I will show some examples.";
    await speak("I understand. I will show you some options. You can tap a picture, or say 'first one', 'second one', or the name under the picture.");
    await showVisualOptions(currentCategory);
    return;
  }

  // NORMAL ANSWER
  answers[currentStep] = answer;
  recomputeDescription();
  await buildSketch(fullDescription);

  if (reviewAfterThisAnswer){
    reviewAfterThisAnswer = false;
    await enterReviewMode();
  } else {
    currentStep++;
    setTimeout(askQuestion, PAUSE_DURATION);
  }
}

// ------------------- VISUAL OPTIONS -------------------
async function showVisualOptions(category){
  try{
    const res = await fetch('/get_category_options', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ category: category, gender: currentGender })
    });

    if (!res.ok){
      console.error("get_category_options not ok");
      await speak("I am sorry, I cannot show options for this part right now. Let's continue.");
      visualMode = false;
      currentStep++;
      askQuestion();
      return;
    }

    const data = await res.json();
    if (!data.options || !data.options.length){
      await speak("I do not have pictures for this feature yet. Let's continue.");
      visualMode = false;
      currentStep++;
      askQuestion();
      return;
    }

    currentVisualOptions = data.options;
    currentVisualCategory = category;
    visualMode = true;

    optionsGridEl.innerHTML = "";
    data.options.forEach((opt, idx) => {
      const div = document.createElement('div');
      div.className = "option-card";
      div.innerHTML = `
        <img src="${opt.url}" alt="${opt.label}">
        <span>${idx+1}. ${opt.label}</span>
      `;
      div.onclick = () => handleVisualSelection(opt.value, opt.label);
      optionsGridEl.appendChild(div);
    });
    visualOptionsEl.style.display = "block";

    await speak("Please say the option number, like option one or option two, or say the name under the picture. You can also tap it.");
    startListening();
  }catch(e){
    console.error("showVisualOptions error:", e);
    await speak("Something went wrong while loading the options. Let's continue.");
    visualMode = false;
    currentStep++;
    askQuestion();
  }
}

// ------------------- VISUAL SELECTION -------------------
function handleVisualSelection(value, labelText){
  visualMode = false;
  visualOptionsEl.style.display = "none";
  const usedText = value || labelText || "";
  transcriptEl.innerText = `Selected: ${labelText || value}`;
  answers[currentStep] = usedText;
  recomputeDescription();
  buildSketch(fullDescription);

  if (reviewAfterThisAnswer){
    reviewAfterThisAnswer = false;
    enterReviewMode();
  } else {
    currentStep++;
    setTimeout(askQuestion, 1000);
  }
}

function handleVisualSpokenSelection(answerRaw){
  const answer = (answerRaw || "").toLowerCase();
  if (!visualMode || !currentVisualOptions.length){
    processAnswer(answerRaw);
    return;
  }

  let chosen = null;

  // 1) explicit digits
  const numberMatch = answer.match(/(\d+)/);
  if (numberMatch){
    const n = parseInt(numberMatch[1], 10);
    if (!isNaN(n) && n >= 1 && n <= currentVisualOptions.length){
      chosen = currentVisualOptions[n-1];
    }
  }

  // 2) number words
  if (!chosen){
    const numberWords = {
      "one":1,"first":1,
      "two":2,"second":2,
      "three":3,"third":3,
      "four":4,"fourth":4,
      "five":5,"fifth":5,
      "six":6,"sixth":6,
      "seven":7,"seventh":7,
      "eight":8,"eighth":8,
      "nine":9,"ninth":9,
      "ten":10,"tenth":10,
      "eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,
      "sixteen":16,"seventeen":17,"eighteen":18,"nineteen":19,"twenty":20
    };
    for (const [word, num] of Object.entries(numberWords)){
      if (containsWord(answer, word) && num >= 1 && num <= currentVisualOptions.length){
        chosen = currentVisualOptions[num-1];
        break;
      }
    }
  }

  // 3) match by label/value (normalized)
  if (!chosen){
    const normAnswer = normalizeLabel(answer);
    chosen = currentVisualOptions.find(opt => {
      const cleanLabel = normalizeLabel(opt.label || "");
      const cleanValue = normalizeLabel(opt.value || "");
      if (!normAnswer) return false;
      if (cleanLabel && (normAnswer === cleanLabel || cleanLabel.includes(normAnswer) || normAnswer.includes(cleanLabel))) return true;
      if (cleanValue && (normAnswer === cleanValue || cleanValue.includes(normAnswer) || normAnswer.includes(cleanValue))) return true;
      const ansWords = normAnswer.split(" ").filter(Boolean);
      if (ansWords.length >= 2){
        let matchCount = 0;
        for (const w of ansWords){
          if (cleanLabel.includes(w) || cleanValue.includes(w)) matchCount++;
        }
        if (matchCount >= Math.min(2, ansWords.length)) return true;
      } else if (ansWords.length === 1){
        const w = ansWords[0];
        if (cleanLabel.includes(w) || cleanValue.includes(w)) return true;
      }
      return false;
    });
  }

  if (!chosen){
    speak("I could not understand which picture you meant. Please tap it on the screen.");
    return;
  }

  handleVisualSelection(chosen.value, chosen.label);
}

// ------------------- BUILD SKETCH -------------------
async function buildSketch(desc){
  if (!desc){
    clearSketch();
    return;
  }

  previewNote.innerText = "Updating composite…";
  try{
    const res = await fetch('/build_sketch', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ description: desc, gender: currentGender })
    });

    if (!res.ok){
      let err = "Unknown error";
      try{ const data = await res.json(); err = data.error || err; }catch(_){}
      console.error("build_sketch error:", err);
      previewNote.innerText = "Error rendering sketch.";
      return;
    }

    const blob = await res.blob();
    if (currentImageObjectUrl){
      try { URL.revokeObjectURL(currentImageObjectUrl); } catch(e){}
    }
    const url = URL.createObjectURL(blob);
    currentImageObjectUrl = url;
    resultImage.src = url;
    resultImage.onload = () => {
      resultImage.classList.add('visible');
      previewNote.innerText = "Live composite preview.";
      downloadBtn.disabled = false;
    };
  }catch(e){
    console.error("build_sketch exception:", e);
    previewNote.innerText = "Error rendering sketch.";
  }
}

// ------------------- UNDO, SKIP, RESET, DOWNLOAD -------------------
function undoLast(){
  if (!askedSteps.length) return;

  // If we are currently on the final review question ("yes / no / somewhat"),
  // undo should go back to the *last asked* feature question and ask it again.
  if (flowMode === "review") {
    const lastIdx = askedSteps[askedSteps.length - 1];
    if (lastIdx > 0) {
      answers[lastIdx] = null;
    }

    currentStep = lastIdx;
    recomputeDescription();
    if (fullDescription) buildSketch(fullDescription);
    else clearSketch();

    flowMode = "interview";
    reviewAfterThisAnswer = true;   // after answering, return to review
    askQuestion();
    return;
  }

  if (visualMode){
    visualMode = false;
    visualOptionsEl.style.display = "none";
    optionsGridEl.innerHTML = "";
  }

  // pop the current question index from the stack
  const lastIdx = askedSteps.pop();
  if (lastIdx === undefined) return;

  if (lastIdx > 0) {
    answers[lastIdx] = null;  // clear that answer (gender kept if lastIdx == 0)
  }

  // new target = previous asked question, or 0 if none
  if (askedSteps.length) {
    currentStep = askedSteps[askedSteps.length - 1];
  } else {
    currentStep = 0;
  }

  if (currentStep === 0){
    currentGender = "male";
    genderTag.textContent = "Gender: not set";
  }

  recomputeDescription();
  if (fullDescription) buildSketch(fullDescription);
  else clearSketch();

  flowMode = "interview";
  reviewAfterThisAnswer = false;
  askQuestion();
}

function skipQuestion(){
  if (currentStep === 0) return;
  if (visualMode){
    visualMode = false;
    visualOptionsEl.style.display = "none";
    optionsGridEl.innerHTML = "";
  }
  currentStep++;
  flowMode = "interview";
  reviewAfterThisAnswer = false;
  askQuestion();
}

function resetInterview(){
  try{ recognition && recognition.stop(); }catch(e){}
  window.speechSynthesis.cancel();
  setListening(false);

  currentStep = 0;
  answers = [];
  fullDescription = "";
  currentGender = "male";
  genderTag.textContent = "Gender: not set";
  askedSteps = [];

  visualMode = false;
  currentVisualOptions = [];
  optionsGridEl.innerHTML = "";
  visualOptionsEl.style.display = "none";

  promptEl.innerText = 'Click “Start Interview” to begin.';
  transcriptEl.innerText = "";
  clearSketch();

  startButton.disabled = false;
  undoButton.disabled = true;
  skipButton.disabled = true;
  resetButton.disabled = false;

  flowMode = "interview";
  reviewAfterThisAnswer = false;
}

function downloadSketch(){
  if (!currentImageObjectUrl) return;
  const a = document.createElement('a');
  a.href = currentImageObjectUrl;
  a.download = 'voxsketch.png';
  document.body.appendChild(a);
  a.click();
  a.remove();
}

// --------- BUTTON WIRING ---------
startButton.addEventListener('click', startInterview);
undoButton.addEventListener('click', undoLast);
skipButton.addEventListener('click', skipQuestion);
resetButton.addEventListener('click', resetInterview);
downloadBtn.addEventListener('click', downloadSketch);

document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && currentStep === 0 && !startButton.disabled){
    startInterview();
  }
});
