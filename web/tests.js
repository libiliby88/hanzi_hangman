import {
  createRound,
  guessStroke,
  MAX_WRONG,
  showHint,
  visibleStrokeIndices,
} from "./game.js";
import { STROKE_GLYPHS } from "./strokes.js";

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
const twoDifferentStrokes = { character: "十", strokes: ["横", "竖"], initial: "s", sentences: [] };

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
  const round = createRound([twoDifferentStrokes], () => 0);
  guessStroke(round, "横");
  const result = guessStroke(round, "横");
  assert(!result.hit, "repeated revealed stroke should be wrong");
  assert(result.revealedIndex === null, "repeated revealed stroke should reveal nothing");
  assert(round.wrongGuesses === 1, "repeated revealed stroke should increment wrong count");
  assert(!round.gameOver, "round should still be in progress");
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

test("visible stroke indices follow the reveal state", () => {
  const round = createRound([tripleStroke], () => 0);
  assert(visibleStrokeIndices(round).length === 0, "nothing should be visible initially");
  guessStroke(round, "横");
  assert(
    JSON.stringify(visibleStrokeIndices(round)) === "[0]",
    "the first guessed stroke should be visible",
  );
  guessStroke(round, "横");
  assert(
    JSON.stringify(visibleStrokeIndices(round)) === "[0,1]",
    "the first two guessed strokes should be visible",
  );
});

function updateSummary() {
  summaryElement.textContent = `${passed} passed, ${failed} failed`;
  summaryElement.className = failed ? "fail" : "pass";
  console.log(`${passed} passed, ${failed} failed`);
}

async function testRealData() {
  try {
    const [dataResponse, graphicsResponse] = await Promise.all([
      fetch("../hanzi_data.json"),
      fetch("../hanzi_graphics.json"),
    ]);
    if (!dataResponse.ok || !graphicsResponse.ok) {
      throw new Error(`HTTP ${dataResponse.status}/${graphicsResponse.status}`);
    }
    const [data, graphics] = await Promise.all([
      dataResponse.json(),
      graphicsResponse.json(),
    ]);

    test("every palette name and alias has a glyph", () => {
      data.stroke_palette.forEach((entry) => {
        assert(STROKE_GLYPHS[entry.name], `${entry.name} is missing`);
        if (entry.alt) {
          assert(STROKE_GLYPHS[entry.alt], `${entry.alt} is missing`);
        }
      });
    });

    test("every mapped glyph is one CJK Strokes codepoint", () => {
      Object.entries(STROKE_GLYPHS).forEach(([name, glyph]) => {
        assert([...glyph].length === 1, `${name} is not one codepoint`);
        const codepoint = glyph.codePointAt(0);
        assert(codepoint >= 0x31c0 && codepoint <= 0x31e3, `${name} is outside CJK Strokes`);
      });
    });

    test("different strokes do not share glyphs except the known alias pair", () => {
      const seen = new Map();
      Object.entries(STROKE_GLYPHS).forEach(([name, glyph]) => {
        const previous = seen.get(glyph);
        if (previous) {
          const expected = new Set(["竖折撇", "竖折折"]);
          assert(
            expected.has(name) && expected.has(previous),
            `${name} unexpectedly shares ${glyph} with ${previous}`,
          );
        }
        seen.set(glyph, name);
      });
    });

    test("every character has matching non-empty stroke outlines", () => {
      data.characters.forEach((entry) => {
        assert(graphics[entry.character], `${entry.character} is missing graphics`);
        assert(
          graphics[entry.character].length === entry.strokes.length,
          `${entry.character} has mismatched outline count`,
        );
        graphics[entry.character].forEach((path, index) => {
          assert(typeof path === "string" && path.length > 0, `${entry.character}[${index}] is empty`);
        });
      });
    });
  } catch (error) {
    test("real data loads", () => {
      throw error;
    });
  }
  updateSummary();
}

updateSummary();
testRealData();
