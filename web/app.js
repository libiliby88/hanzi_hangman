import {
  createRound,
  guessStroke,
  MAX_WRONG,
  showHint,
  visibleStrokeIndices,
} from "./game.js";
import { STROKE_GLYPHS } from "./strokes.js";

const TEXT = "#ecf0f1";

const canvas = document.querySelector("#hangman-canvas");
const canvasContext = canvas.getContext("2d");
const characterPanel = document.querySelector("#character-panel");
const characterStrokes = document.querySelector("#character-strokes");
const slotsElement = document.querySelector("#slots");
const wrongCountElement = document.querySelector("#wrong-count");
const strokeCountElement = document.querySelector("#stroke-count");
const hintLineElement = document.querySelector("#hint-line");
const keyboardElement = document.querySelector("#keyboard");
const hintButton = document.querySelector("#hint-button");
const newGameButton = document.querySelector("#new-game-button");
const resultDialog = document.querySelector("#result-dialog");
const resultTitle = document.querySelector("#result-title");
const resultCharacter = document.querySelector("#result-character");
const resultStrokes = document.querySelector("#result-strokes");
const resultSentence = document.querySelector("#result-sentence");
const againButton = document.querySelector("#again-button");
const closeButton = document.querySelector("#close-button");

let data = null;
let graphics = null;
let round = null;
let roundId = 0;
const flashTimers = new Map();
const strokeButtons = new Map();
let strokeFlashTimer = null;
let highlightedStrokeIndex = null;

function drawCanvas() {
  if (!round) {
    return;
  }

  const size = canvas.getBoundingClientRect().width;
  const pixelRatio = window.devicePixelRatio || 1;
  const scale = size / 200;
  canvas.width = Math.max(1, Math.round(size * pixelRatio));
  canvas.height = Math.max(1, Math.round(size * pixelRatio));
  canvasContext.setTransform(pixelRatio * scale, 0, 0, pixelRatio * scale, 0, 0);
  canvasContext.clearRect(0, 0, 200, 200);
  canvasContext.lineWidth = 3;
  canvasContext.strokeStyle = TEXT;
  canvasContext.fillStyle = TEXT;

  canvasContext.beginPath();
  canvasContext.moveTo(20, 180);
  canvasContext.lineTo(100, 180);
  canvasContext.moveTo(60, 180);
  canvasContext.lineTo(60, 20);
  canvasContext.moveTo(60, 20);
  canvasContext.lineTo(120, 20);
  canvasContext.moveTo(120, 20);
  canvasContext.lineTo(120, 40);
  canvasContext.stroke();

  if (round.wrongGuesses >= 1) {
    canvasContext.beginPath();
    canvasContext.arc(120, 55, 15, 0, Math.PI * 2);
    canvasContext.stroke();
  }
  if (round.wrongGuesses >= 2) {
    drawLine(120, 70, 120, 120);
  }
  if (round.wrongGuesses >= 3) {
    drawLine(120, 80, 90, 100);
  }
  if (round.wrongGuesses >= 4) {
    drawLine(120, 80, 150, 100);
  }
  if (round.wrongGuesses >= 5) {
    drawLine(120, 120, 90, 150);
  }
  if (round.wrongGuesses >= 6) {
    drawLine(120, 120, 150, 150);
  }
}

function drawLine(x1, y1, x2, y2) {
  canvasContext.beginPath();
  canvasContext.moveTo(x1, y1);
  canvasContext.lineTo(x2, y2);
  canvasContext.stroke();
}

function renderSlots() {
  slotsElement.replaceChildren();
  round.strokes.forEach((stroke, index) => {
    const slot = document.createElement("div");
    slot.className = `slot ${round.revealed[index] ? "revealed" : "hidden"}`;
    slot.setAttribute("aria-label", `${index + 1}${round.revealed[index] ? stroke : "?"}`);

    const number = document.createElement("span");
    number.className = "slot-number";
    number.textContent = index + 1;
    if (round.revealed[index]) {
      const glyph = document.createElement("span");
      glyph.className = "stroke-glyph slot-glyph";
      glyph.textContent = STROKE_GLYPHS[stroke];
      const strokeName = document.createElement("span");
      strokeName.className = "slot-stroke";
      strokeName.textContent = stroke;
      slot.append(number, glyph, strokeName);
    } else {
      const hiddenStroke = document.createElement("span");
      hiddenStroke.className = "slot-stroke";
      hiddenStroke.textContent = "?";
      slot.append(number, hiddenStroke);
    }
    slotsElement.append(slot);
  });
}

function renderStatus() {
  wrongCountElement.textContent = `猜错次数: ${round.wrongGuesses}/${MAX_WRONG}`;
  strokeCountElement.textContent = `共 ${round.strokes.length} 笔`;
  hintLineElement.textContent = `拼音首字母: ${round.hintShown ? round.target.initial : "?"}`;
}

function renderCharacter() {
  const outlines = graphics?.[round.target.character];
  if (!Array.isArray(outlines) || outlines.length !== round.strokes.length) {
    characterPanel.hidden = true;
    characterStrokes.replaceChildren();
    return;
  }

  characterPanel.hidden = false;
  characterStrokes.replaceChildren();
  const visible = new Set(visibleStrokeIndices(round));
  round.strokes.forEach((stroke, index) => {
    if (!visible.has(index) || typeof outlines[index] !== "string" || !outlines[index]) {
      return;
    }
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", outlines[index]);
    path.style.fill = index === highlightedStrokeIndex
      ? "var(--correct)"
      : "var(--text)";
    characterStrokes.append(path);
  });
}

function render() {
  renderSlots();
  renderStatus();
  renderCharacter();
  drawCanvas();
}

function flashButton(name, hit) {
  const button = strokeButtons.get(name);
  if (!button) {
    return;
  }
  const oldTimer = flashTimers.get(name);
  if (oldTimer !== undefined) {
    window.clearTimeout(oldTimer);
  }
  button.classList.remove("flash-correct", "flash-wrong");
  button.classList.add(hit ? "flash-correct" : "flash-wrong");
  const currentRoundId = roundId;
  const timer = window.setTimeout(() => {
    flashTimers.delete(name);
    if (currentRoundId === roundId) {
      button.classList.remove("flash-correct", "flash-wrong");
    }
  }, 250);
  flashTimers.set(name, timer);
}

function cancelFlashes() {
  flashTimers.forEach((timer) => window.clearTimeout(timer));
  flashTimers.clear();
  strokeButtons.forEach((button) => button.classList.remove("flash-correct", "flash-wrong"));
  if (strokeFlashTimer !== null) {
    window.clearTimeout(strokeFlashTimer);
    strokeFlashTimer = null;
  }
  highlightedStrokeIndex = null;
}

function flashStroke(index) {
  if (strokeFlashTimer !== null) {
    window.clearTimeout(strokeFlashTimer);
  }
  highlightedStrokeIndex = index;
  const currentRoundId = roundId;
  strokeFlashTimer = window.setTimeout(() => {
    strokeFlashTimer = null;
    if (currentRoundId === roundId) {
      highlightedStrokeIndex = null;
      renderCharacter();
    }
  }, 250);
}

function startNewGame() {
  cancelFlashes();
  roundId += 1;
  round = createRound(data.characters);
  render();
}

function guess(name) {
  if (!round || round.gameOver) {
    return;
  }
  const result = guessStroke(round, name);
  flashButton(name, result.hit);
  if (result.hit && result.revealedIndex !== null) {
    flashStroke(result.revealedIndex);
  }
  render();
  if (result.finished) {
    showResultDialog(result.finished === "won");
  }
}

function showHintLine() {
  const initial = showHint(round);
  if (initial !== null) {
    renderStatus();
  }
}

function appendHighlightedSentence(sentence, targetCharacter) {
  resultSentence.replaceChildren();
  const pieces = sentence.split(targetCharacter);
  pieces.forEach((piece, index) => {
    if (piece) {
      resultSentence.append(document.createTextNode(piece));
    }
    if (index < pieces.length - 1) {
      const highlighted = document.createElement("strong");
      highlighted.className = "highlight";
      highlighted.textContent = targetCharacter;
      resultSentence.append(highlighted);
    }
  });
}

function showResultDialog(won) {
  const sentences = round.target.sentences || [];
  const sentence = sentences.length
    ? sentences[Math.floor(Math.random() * sentences.length)]
    : "(暂无例句)";
  resultTitle.textContent = won ? "恭喜!" : "游戏结束";
  resultCharacter.textContent = round.target.character;
  resultStrokes.replaceChildren(document.createTextNode("笔顺: "));
  round.strokes.forEach((stroke, index) => {
    if (index > 0) {
      resultStrokes.append(document.createTextNode("  "));
    }
    const glyph = document.createElement("span");
    glyph.className = "stroke-glyph result-stroke-glyph";
    glyph.textContent = STROKE_GLYPHS[stroke];
    resultStrokes.append(glyph, document.createTextNode(` ${stroke}`));
  });
  appendHighlightedSentence(sentence, round.target.character);
  if (typeof resultDialog.showModal === "function") {
    resultDialog.showModal();
  } else {
    resultDialog.setAttribute("open", "");
  }
}

function closeResultDialog() {
  if (resultDialog.open && typeof resultDialog.close === "function") {
    resultDialog.close();
  } else {
    resultDialog.removeAttribute("open");
  }
}

function createKeyboard() {
  keyboardElement.replaceChildren();
  strokeButtons.clear();
  data.stroke_palette.forEach((entry) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "stroke-button";
    const glyphs = [entry.name, entry.alt]
      .filter(Boolean)
      .map((name) => STROKE_GLYPHS[name]);
    const glyph = document.createElement("span");
    glyph.className = "stroke-glyph stroke-button-glyph";
    glyph.textContent = [...new Set(glyphs)].join(" / ");
    const names = document.createElement("span");
    names.className = "stroke-button-name";
    names.textContent = entry.alt ? `${entry.name}\n${entry.alt}` : entry.name;
    button.append(glyph, names);
    button.setAttribute("aria-label", entry.alt ? `${entry.name}、${entry.alt}` : entry.name);
    button.addEventListener("click", () => guess(entry.name));
    keyboardElement.append(button);
    strokeButtons.set(entry.name, button);
  });
}

async function loadData() {
  try {
    const dataResponse = await fetch("../hanzi_data.json");
    if (!dataResponse.ok) {
      throw new Error(`HTTP ${dataResponse.status}`);
    }
    data = await dataResponse.json();
    createKeyboard();
    startNewGame();

    fetch("../hanzi_graphics.json")
      .then((graphicsResponse) => {
        if (!graphicsResponse.ok) {
          throw new Error(`HTTP ${graphicsResponse.status}`);
        }
        return graphicsResponse.json();
      })
      .then((loadedGraphics) => {
        graphics = loadedGraphics;
        renderCharacter();
      })
      .catch((error) => {
        console.warn("Optional hanzi_graphics.json unavailable", error);
      });
  } catch (error) {
    document.querySelector("#app").replaceChildren(
      Object.assign(document.createElement("p"), {
        className: "wrong-text",
        textContent: `数据加载失败: ${error.message}`,
      }),
    );
    console.error("Failed to load hanzi_data.json", error);
  }
}

hintButton.addEventListener("click", showHintLine);
newGameButton.addEventListener("click", () => {
  closeResultDialog();
  startNewGame();
});
againButton.addEventListener("click", () => {
  closeResultDialog();
  startNewGame();
});
closeButton.addEventListener("click", closeResultDialog);
window.addEventListener("resize", drawCanvas);
if (typeof ResizeObserver === "function") {
  new ResizeObserver(drawCanvas).observe(canvas);
}

if ("serviceWorker" in navigator &&
    (window.isSecureContext || location.hostname === "localhost" || location.hostname === "127.0.0.1")) {
  navigator.serviceWorker.register("sw.js").catch(() => {
    // A plain HTTP LAN origin can still use the online game without a service worker.
  });
}

loadData();
