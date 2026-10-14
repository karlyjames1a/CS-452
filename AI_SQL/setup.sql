CREATE TABLE player (
    player_id INTEGER PRIMARY KEY,
    username VARCHAR(35) NOT NULL
);

CREATE TABLE fighter (
    fighter_id INTEGER PRIMARY KEY,
    fighter_name VARCHAR(35) NOT NULL,
    universe VARCHAR(100) NOT NULL
);

CREATE TABLE stage (
    stage_id INTEGER PRIMARY KEY,
    stage_name VARCHAR(35) NOT NULL,
    universe VARCHAR(100) NOT NULL
);

CREATE TABLE song (
    song_id INTEGER PRIMARY KEY,
    song_name VARCHAR(100) NOT NULL,
    universe VARCHAR(100) NOT NULL
);

CREATE TABLE stock (
    stock_id INTEGER PRIMARY KEY,
    stock_type VARCHAR(35) NOT NULL
);

CREATE TABLE mode (
    mode_id INTEGER PRIMARY KEY,
    mode_type VARCHAR(35) NOT NULL
);

CREATE TABLE item (
    item_id INTEGER PRIMARY KEY,
    item_name VARCHAR(35) NOT NULL,
    item_damage INTEGER NOT NULL,
    item_type VARCHAR(35) NOT NULL
);

CREATE TABLE game_match (
    match_id INTEGER PRIMARY KEY,
    stage_id INTEGER NOT NULL,
    mode_id INTEGER NOT NULL,
    stock_id INTEGER NOT NULL,
    song_id INTEGER NOT NULL,
    match_date DATE NOT NULL,
    FOREIGN KEY (stage_id) REFERENCES stage(stage_id),
    FOREIGN KEY (mode_id) REFERENCES mode(mode_id),
    FOREIGN KEY (stock_id) REFERENCES stock(stock_id),
    FOREIGN KEY (song_id) REFERENCES song(song_id)
);

CREATE TABLE player_match (
    match_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    fighter_id INTEGER NOT NULL,
    ranking INTEGER NOT NULL,
    ko_count INTEGER NOT NULL,
    PRIMARY KEY (match_id, player_id),
    UNIQUE (match_id, ranking),
    FOREIGN KEY (match_id) REFERENCES game_match(match_id),
    FOREIGN KEY (player_id) REFERENCES player(player_id),
    FOREIGN KEY (fighter_id) REFERENCES fighter(fighter_id),
    CHECK (ranking >= 1),
    CHECK (ko_count >= 0)
);

CREATE TABLE match_item (
    item_id INTEGER NOT NULL,
    match_id INTEGER NOT NULL,
    PRIMARY KEY (match_id, item_id),
    FOREIGN KEY (item_id) REFERENCES item(item_id),
    FOREIGN KEY (match_id) REFERENCES game_match(match_id)
);