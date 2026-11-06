export const MAX_WRONG = 6;

export function createRound(characters, rng = Math.random) {
  const target = characters[Math.floor(rng() * characters.length)];
  const strokes = [...(target.strokes || [])];
  return {
    target,
    strokes,
    revealed: strokes.map(() => false),
    wrongGuesses: 0,
    gameOver: false,
    won: false,
    hintShown: false,
  };
}

export function visibleStrokeIndices(round) {
  return round.revealed.reduce(
    (indices, isRevealed, index) => (isRevealed ? [...indices, index] : indices),
    [],
  );
}

export function guessStroke(round, name) {
  if (round.gameOver) {
    return { hit: false, revealedIndex: null, finished: null };
  }

  const revealedIndex = round.strokes.findIndex(
    (stroke, index) => stroke === name && !round.revealed[index],
  );

  if (revealedIndex !== -1) {
    round.revealed[revealedIndex] = true;
    const won = round.revealed.every(Boolean);
    if (won) {
      round.gameOver = true;
      round.won = true;
    }
    return {
      hit: true,
      revealedIndex,
      finished: won ? "won" : null,
    };
  }

  round.wrongGuesses += 1;
  if (round.wrongGuesses >= MAX_WRONG) {
    round.revealed.fill(true);
    round.gameOver = true;
    round.won = false;
    return { hit: false, revealedIndex: null, finished: "lost" };
  }

  return { hit: false, revealedIndex: null, finished: null };
}

export function showHint(round) {
  if (round.gameOver || round.hintShown) {
    return null;
  }
  round.hintShown = true;
  return round.target.initial;
}
