-- execute-script の file で流す資源 (UTF-8)。注釈の中の user:name は引数ではない
DROP TABLE IF EXISTS script_file;
CREATE TABLE script_file (id INTEGER PRIMARY KEY, name TEXT, note TEXT);
INSERT INTO script_file VALUES (1, '相沢 美穂', 'a: b');
INSERT INTO script_file VALUES (2, 'Bob', NULL)
