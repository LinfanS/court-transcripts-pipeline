source .env

export PGPASSWORD=${DB_PASSWORD}

psql -h ${DB_HOST} -p ${DB_PORT} -d ${DB_NAME} -U ${DB_USER} <<EOF
DROP TABLE IF EXISTS participant_assignment;
DROP TABLE IF EXISTS judge_assignment;
DROP TABLE IF EXISTS tag_assignment;
DROP TABLE IF EXISTS court_case;
DROP TABLE IF EXISTS lawyer;
DROP TABLE IF EXISTS law_firm;
DROP TABLE IF EXISTS verdict;
DROP TABLE IF EXISTS participant;
DROP TABLE IF EXISTS court;
DROP TABLE IF EXISTS judge;
DROP TABLE IF EXISTS tag;


CREATE TABLE tag (
    tag_id INT GENERATED ALWAYS AS IDENTITY,
    tag_name VARCHAR(50) UNIQUE NOT NULL,
    PRIMARY KEY (tag_id)
);

CREATE TABLE judge (
    judge_id INT GENERATED ALWAYS AS IDENTITY,
    judge_name VARCHAR(200) UNIQUE NOT NULL,
    PRIMARY KEY (judge_id)
);

CREATE TABLE court (
    court_id INT GENERATED ALWAYS AS IDENTITY,
    court_name VARCHAR(100) UNIQUE NOT NULL,
    PRIMARY KEY (court_id)
);

CREATE TABLE participant (
    participant_id INT GENERATED ALWAYS AS IDENTITY,
    participant_name VARCHAR(150) UNIQUE NOT NULL,
    PRIMARY KEY (participant_id)
);

CREATE TABLE verdict (
    verdict_id INT GENERATED ALWAYS AS IDENTITY,
    verdict VARCHAR(50) UNIQUE NOT NULL,
    PRIMARY KEY (verdict_id)
);

CREATE TABLE law_firm (
    law_firm_id INT GENERATED ALWAYS AS IDENTITY,
    law_firm_name VARCHAR(100) UNIQUE,
    PRIMARY KEY (law_firm_id)
);

CREATE TABLE lawyer (
    lawyer_id INT GENERATED ALWAYS AS IDENTITY,
    lawyer_name VARCHAR(200),
    law_firm_id INT,
    UNIQUE(lawyer_name, law_firm_id),
    PRIMARY KEY (lawyer_id),
    FOREIGN KEY (law_firm_id) REFERENCES law_firm(law_firm_id)
);

CREATE TABLE court_case (
    court_case_id VARCHAR(50) UNIQUE NOT NULL,
    summary TEXT,
    verdict_id INT,
    title VARCHAR(150),
    court_date DATE,
    case_number VARCHAR(50) UNIQUE NOT NULL,
    case_url VARCHAR(200),
    court_id INT,
    verdict_summary TEXT,
    PRIMARY KEY (court_case_id),
    FOREIGN KEY (verdict_id) REFERENCES verdict(verdict_id),
    FOREIGN KEY (court_id) REFERENCES court(court_id)
);

CREATE TABLE tag_assignment (
    court_case_id VARCHAR(50),
    tag_id INT,
    PRIMARY KEY (court_case_id, tag_id),
    FOREIGN KEY (court_case_id) REFERENCES court_case(court_case_id),
    FOREIGN KEY (tag_id) REFERENCES tag(tag_id)
);

CREATE TABLE judge_assignment (
    court_case_id VARCHAR(50),
    judge_id INT,
    PRIMARY KEY (court_case_id, judge_id),
    FOREIGN KEY (court_case_id) REFERENCES court_case(court_case_id),
    FOREIGN KEY (judge_id) REFERENCES judge(judge_id)
);

CREATE TABLE participant_assignment (
    court_case_id VARCHAR(50),
    participant_id INT,
    lawyer_id INT,
    is_defendant BOOLEAN,
    PRIMARY KEY (court_case_id, participant_id),
    FOREIGN KEY (court_case_id) REFERENCES court_case(court_case_id),
    FOREIGN KEY (participant_id) REFERENCES participant(participant_id),
    FOREIGN KEY (lawyer_id) REFERENCES lawyer(lawyer_id)
);


INSERT INTO court(court_name) 
VALUES ('United Kingdom Supreme Court'), ('Privy Council'), ('Court of Appeal (Civil Division)'),
('Court of Appeal (Criminal Division)'), ('High Court (Administrative Court)'), ('High Court (Chancery Division)'),
('High Court (Admiralty Court)'), ('High Court (Commercial Court)'), ('High Court (Family Division)'),
('High Court (Intellectual Property Enterprise Court)'), ('High Court (King''s Bench Division)'), ('High Court (Queen''s Bench Division)'),
('High Court (Mercantile Court)'), ('High Court (Patents Court)'), ('High Court (Senior Courts Costs Office)'),
('High Court (Technology and Construction Court)'), ('Court of Protection'), ('Family Court');

INSERT INTO verdict(verdict)
VALUES ('Guilty'), ('Not Guilty'), ('Dismissed'), ('Acquitted'), ('Hung Jury'), ('Claimant Wins'), ('Defendant Wins'),
('Settlement'), ('Struck Out'), ('Appeal Dismissed'), ('Appeal Allowed'), ('Other');
\dt
EOF

echo "Successfully reset the transactions table"
unset PGPASSWORD