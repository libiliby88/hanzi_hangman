import { createRound, guessStroke, MAX_WRONG, showHint } from "./game.js";

const resultsElement = document.querySelector("#results");
const summaryElement = document.querySelector("#summary");
let passed = 0;
let failed = 0;

function test(name, callback) {
  const item = document.createElement("li");
  try {
    callback();
    passed += 1;
    item.className = "pass";
    item.textContent = `PASS: ${name}`;
    console.log(`PASS: ${name}`);
  } catch (error) {
    failed += 1;
    item.className = "fail";
    item.textContent = `FAIL: ${name} — ${error.message}`;
    console.error(`FAIL: ${name}`, error);
  }
  resultsElement.append(item);
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const singleStroke = { character: "一", strokes: ["横"], initial: "y", sentences: [] };
const tripleStroke = { character: "三", strokes: ["横", "横", "横"], initial: "s", sentences: [] };
const twoStroke = { character: "二", strokes: ["横", "横"], initial: "e", sentences: [] };

test("single-stroke character wins in one guess", () => {
  const round = createRound([singleStroke], () => 0);
  const result = guessStroke(round, "横");
  assert(result.hit && result.revealedIndex === 0, "first stroke should be revealed");
  assert(result.finished === "won" && round.gameOver && round.won, "round should be won");
});

test("三 needs three 横 guesses", () => {
  const round = createRound([tripleStroke], () => 0);
  assert(guessStroke(round, "横").hit && !round.gameOver, "first 横 should reveal one slot");
  assert(guessStroke(round, "横").hit && !round.gameOver, "second 横 should reveal one slot");
  const result = guessStroke(round, "横");
  assert(result.hit && result.finished === "won", "third 横 should win");
  assert(round.revealed.every(Boolean), "all three slots should be revealed");
});

test("guessing a fully revealed present stroke counts as wrong", () => {
  const round = createRound([singleStroke], () => 0);
  guessStroke(round, "横");
  const result = guessStroke(round, "横");
  assert(!result.hit && round.wrongGuesses === 1, "repeated revealed stroke should be wrong");
});

test("guessing an absent stroke is wrong and reveals nothing", () => {
  const round = createRound([singleStroke], () => 0);
  const result = guessStroke(round, "点");
  assert(!result.hit && result.revealedIndex === null, "absent stroke should miss");
  assert(round.wrongGuesses === 1, "absent stroke should increment wrong count");
  assert(round.revealed.every((isRevealed) => !isRevealed), "absent stroke should reveal nothing");
});

test("six wrong guesses lose and reveal every slot", () => {
  const round = createRound([twoStroke], () => 0);
  for (let i = 0; i < MAX_WRONG; i += 1) {
    guessStroke(round, "点");
  }
  assert(round.gameOver && round.won === false, "round should be lost");
  assert(round.wrongGuesses === MAX_WRONG, "wrong count should reach six");
  assert(round.revealed.every(Boolean), "loss should reveal every slot");
});

test("guessing after game over is a no-op", () => {
  const round = createRound([singleStroke], () => 0);
  guessStroke(round, "横");
  const before = JSON.stringify(round);
  const result = guessStroke(round, "点");
  assert(result.hit === false && result.revealedIndex === null && result.finished === null, "result should be a no-op");
  assert(JSON.stringify(round) === before, "round should not change");
});

test("hint returns the initial once, then null", () => {
  const round = createRound([singleStroke], () => 0);
  assert(showHint(round) === "y", "first hint should return initial");
  assert(showHint(round) === null, "second hint should return null");
});

test("hint returns null after game over without a prior hint", () => {
  const round = createRound([singleStroke], () => 0);
  guessStroke(round, "横");
  assert(round.gameOver, "round should be over");
  assert(showHint(round) === null, "hint should be unavailable after game over");
});

summaryElement.textContent = `${passed} passed, ${failed} failed`;
summaryElement.className = failed ? "fail" : "pass";
console.log(`${passed} passed, ${failed} failed`);
