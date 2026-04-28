COLORS = {
    "background":   (30, 30, 40),
    "panel":        (45, 45, 60),
    "text":         (230, 230, 230),
    "dimmed":       (130, 130, 150),
    "prompt":       (255, 220, 80),
    "button":       (60, 70, 100),
    "button_hover": (80, 95, 140),
    "button_text":  (240, 240, 255),
    "green":        (50, 160, 70),
    "blue":         (50, 100, 200),
    "pink":         (210, 80, 140),
    "yellow":       (220, 200, 50),
    "grey":         (140, 140, 150),
    "white":        (230, 230, 230),
    "box_empty":    (60, 60, 75),
    "crossed":      (200, 60, 60),
    "circled":      (60, 200, 120),
    "score":        (100, 255, 180),
}

DICE_COLORS = {
    "green":  (50, 180, 80),
    "blue":   (60, 120, 220),
    "white":  (230, 230, 230),
    "yellow": (240, 210, 50),
    "grey":   (150, 150, 160),
    "pink":   (230, 90, 150),
}

ACTION_LABELS = {
    "none": "",
    "reroll": "R",
    "reuse": "U",
    "plus_one": "+1",
    "fox": "F",
    "black_question_mark": "?",
    "blue_question_mark": "?",
    "green_question_mark": "?",
    "yellow_question_mark": "?",
    "grey_question_mark": "?",
    "pink_question_mark": "?",
}

ACTION_LABEL_COLORS = {
    "none": (90, 90, 100),
    "reroll": (160, 170, 220),
    "reuse": (140, 210, 150),
    "plus_one": (255, 220, 100),
    "fox": (230, 150, 60),
    "black_question_mark": (200, 200, 200),
    "blue_question_mark": (80, 140, 230),
    "green_question_mark": (70, 190, 90),
    "yellow_question_mark": (220, 200, 60),
    "grey_question_mark": (160, 160, 170),
    "pink_question_mark": (220, 100, 150),
}

FRAMES_PER_SECOND = 30

TITLE_TOP_MARGIN = 10
TITLE_SECTION_HEIGHT = 40
PANEL_LEFT_MARGIN = 10
PANEL_GAP = 15
PANEL_TOTAL_HORIZONTAL_MARGIN = 60
PANEL_BOTTOM_RESERVE = 180
PANEL_MIN_HEIGHT = 80
STATUS_BAR_TOP_MARGIN = 5

PANEL_PADDING_X = 8
PANEL_HEADER_OFFSET_Y = 4
PANEL_CONTENT_OFFSET_Y = 22

PANEL_BORDER_RADIUS = 6
BOX_BORDER_RADIUS = 3
GREY_BOX_BORDER_RADIUS = 2
BUTTON_BORDER_RADIUS = 5
DIE_BORDER_RADIUS = 8
PILL_BORDER_RADIUS = 4

DIE_SIZE = 38
DIE_GAP = 6
DIE_SECTION_LABEL_OFFSET_Y = 2
DIE_SECTION_BOTTOM_PADDING = 4
DIE_TEXT_OFFSET_Y = 10

BOX_ROW_MAX_SIZE = 30
BOX_ROW_GAP = 3
BOX_ROW_CONTENT_OFFSET_Y = 24
BOX_ROW_MARGIN = 20
BOX_ROW_TEXT_OFFSET_Y = 2
BOX_ROW_ACTION_OFFSET_Y = 2

YELLOW_GRID_GAP = 4
YELLOW_GRID_COLS = 4
YELLOW_GRID_ROWS = 5
YELLOW_GRID_MARGIN_H = 60
YELLOW_GRID_MARGIN_V = 50
YELLOW_GRID_ACTION_MARGIN = 40
YELLOW_ROW_ACTION_X_OFFSET = 6
YELLOW_ACTION_Y_OFFSET = 2
YELLOW_CELL_TEXT_OFFSET_Y = 2

GREY_BOX_GAP = 3
GREY_GRID_COLS = 6
GREY_GRID_ROWS = 4
GREY_GRID_MARGIN_H = 20
GREY_GRID_MARGIN_V = 50
GREY_ACTION_Y_OFFSET = 2
GREY_CELL_TEXT_OFFSET_Y = 1

PILL_HEIGHT = 22
PILL_GAP = 4
PILL_TEXT_PADDING = 12
PILL_TEXT_OFFSET_X = 6
PILL_TEXT_OFFSET_Y = 3
PILL_BOTTOM_MARGIN = 4
WON_ACTIONS_EMPTY_OFFSET_Y = 8

BUTTON_HEIGHT = 36
BUTTON_GAP = 10
BUTTON_MAX_WIDTH = 320
BUTTON_AREA_MARGIN = 40
BUTTON_TEXT_OFFSET_Y = 6

STATUS_BAR_HEIGHT = 28
PROMPT_TEXT_HEIGHT = 28
GAME_OVER_BANNER_HEIGHT = 36

POPUP_DURATION_SECONDS = 2.5
POPUP_FADE_SECONDS = 0.5
POPUP_WIDTH = 320
POPUP_HEIGHT = 40
POPUP_GAP = 8
POPUP_MARGIN_RIGHT = 20
POPUP_MARGIN_TOP = 60
POPUP_BORDER_RADIUS = 8
POPUP_TEXT_OFFSET_X = 12
POPUP_TEXT_OFFSET_Y = 10

POPUP_ACTION_NAMES = {
    "none": "",
    "reroll": "Reroll",
    "reuse": "Reuse",
    "plus_one": "+1",
    "fox": "Fox",
    "black_question_mark": "? (any)",
    "blue_question_mark": "? (blue)",
    "green_question_mark": "? (green)",
    "yellow_question_mark": "? (yellow)",
    "grey_question_mark": "? (grey)",
    "pink_question_mark": "? (pink)",
}

POPUP_SOURCE_NAMES = {
    "round_start": "Round Start",
    "pick": "Pick",
    "plus_one": "+1",
    "passive_pick": "Passive Pick",
}
