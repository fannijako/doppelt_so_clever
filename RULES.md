# Doppelt so clever — Rules Summary

A summary, in this project's own words, of the rules this simulation implements. Doppelt so clever (*Twice as Clever*) is a roll-and-write dice game designed by Wolfgang Warsch and published by Schmidt Spiele. This repository is an unofficial fan implementation with no affiliation to the publisher; for the official rulebook, see the publisher's product page at <https://www.schmidtspiele.de>.

Terminology: the codebase calls the official *silver* area **grey**, the *return* action **reuse**, and the *extra die* action **plus-one**. This document uses the code's names, with the official term in parentheses on first mention.

## Components

Six dice — blue, green, white, yellow, grey, pink — and a score sheet with five colored scoring sections (blue, green, yellow, grey, pink). The white die is a wildcard: it may stand in for any color.

## Turn Structure

### Active turn

The active player rolls all available dice and picks one, then places its value in the matching colored section. Every die showing a **lower** value than the picked die is discarded to a shared tray (the *Silver Platter*) and is no longer available to the active player this turn. The remaining dice are rerolled and the player picks again — up to **three picks per active turn**. If an early high pick discards everything, the turn simply ends with fewer picks.

### Passive turn

In the solo variant this engine implements, active and passive turns alternate. On a passive turn, all six dice are rolled and the player picks **one of the three lowest** dice to place. (In multiplayer, the non-active players instead pick simultaneously from the tray after the active player finishes.)

### Solo game

The solo game runs **6 rounds**, each an active turn followed by a passive turn. The goal is the highest possible final score.

## The Five Sections

### Blue

Twelve boxes filled strictly left to right, no skipping. The value placed is always the **sum of the blue and white dice** (whichever of the two was picked). Each entry must be **less than or equal to** the previous one. Scoring: a lookup on how many boxes are filled — the more boxes, the more points.

### Green

Twelve boxes filled strictly left to right. The picked green die is **multiplied by the box's printed multiplier** and the product is written in. Scoring works in consecutive pairs: the second value of each pair is subtracted from the first, and the pair results are summed — negative pair results are possible, and a pair whose second box is still empty scores zero.

### Grey (silver)

A grid of 4 rows × 6 columns; each cell names a color and a value 1–6. Picking the grey die lets the player cross matching cells — and dice discarded to the tray **after** the grey die was picked may be crossed as well. Completing a column grants an action. Scoring: per-row points based on how many cells in that row are crossed, summed over the four rows.

### Yellow

Ten values on a 5×4 grid. A yellow die first **circles** its number; a second placement on an already-circled number **crosses** it. Completing a row or column of circles grants a bonus. Scoring: a lookup on the number of **crossed** cells — circles alone score nothing.

### Pink

Twelve boxes filled strictly left to right, each storing the raw value of the picked pink die. Any value may be written, but the box's bonus is only granted if the value **meets or exceeds** the limit printed under the box. Scoring: the sum of all stored values.

## Bonuses (question marks)

Some cells carry a question-mark bonus in a specific color. The moment such a cell is filled, the player immediately makes one free entry in that color's section (the black question mark lets the player choose the color). Bonuses **cannot be banked** — they resolve immediately, and if a bonus entry lands on another bonus cell, the chain continues.

## Stored Actions

Unlike question-mark bonuses, these three actions are saved on the sheet and spent whenever the player chooses:

- **Reroll** — the active player rerolls all currently rolled dice (all of them, not a subset). Not usable on passive turns.
- **Reuse (return)** — the active player retrieves one die from the tray before the next roll.
- **Plus-one (extra die)** — at the end of a round, the player places one additional die of their choice, regardless of where it currently sits. Each die can be taken at most once per round this way.

## Foxes

Fox symbols earned during the game each score, at game end, **the value of the player's lowest-scoring section**. A section worth 0 makes every fox worth 0 — balanced play matters.

## Final Score

The five section scores are summed, then each fox adds the minimum section score. The solo rating table:

| Points  | Rating                 |
|---------|------------------------|
| > 320   | Twice as clever!       |
| 300–319 | Points = IQ!           |
| 280–299 | Respect!               |
| 260–279 | This can't be luck!    |
| 240–259 | People, look at this!  |
| 220–239 | Pretty, pretty clever! |
| 200–219 | You've been training!  |
| 180–199 | You should be happy!   |
| 160–179 | On the right way.      |
| 140–159 | You can do better.     |
| < 140   | Half as clever.        |
