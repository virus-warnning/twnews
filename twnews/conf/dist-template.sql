CREATE TABLE IF NOT EXISTS "dist_{YYYY}q{Q}" (
	`stock_id`	TEXT NOT NULL,
	`date`	TEXT NOT NULL,
	`level`	INTEGER NOT NULL,
	`numof_holders`	INTEGER NOT NULL,
	`numof_stocks`	INTEGER NOT NULL,
	`percentof_stocks`	REAL NOT NULL,
	PRIMARY KEY(`stock_id`,`date`,`level`)
);
