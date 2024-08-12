DROP TABLE IF EXISTS defendant_lawyer_assignment;
DROP TABLE IF EXISTS prosecuting_lawyer_assignment;
DROP TABLE IF EXISTS judge_assignment;
DROP TABLE IF EXISTS tag_assignment;
DROP TABLE IF EXISTS case;
DROP TABLE IF EXISTS lawyer;
DROP TABLE IF EXISTS law_firm;
DROP TABLE IF EXISTS verdict;
DROP TABLE IF EXISTS court;
DROP TABLE IF EXISTS judge;
DROP TABLE IF EXISTS tag;


CREATE TABLE tag (
    tag_id INT GENERATED ALWAYS AS IDENTITY,
    tag_name VARCHAR(50) UNIQUE NOT NULL,
    PRIMARY KEY (tag_id)
);

-- Could seed
CREATE TABLE judge (
    judge_id INT GENERATED ALWAYS AS IDENTITY,
    judge_name VARCHAR(50) UNIQUE NOT NULL,
    PRIMARY KEY (judge_id)
);

-- Could seed
CREATE TABLE court (
    court_id INT GENERATED ALWAYS AS IDENTITY,
    court_name VARCHAR(50) UNIQUE NOT NULL,
    PRIMARY KEY (court_id)
);

-- Could seed
CREATE TABLE verdict (
    verdict_id INT GENERATED ALWAYS AS IDENTITY,
    verdict VARCHAR(50) UNIQUE NOT NULL,
    PRIMARY KEY (verdict_id)
);

CREATE TABLE law_firm (
    law_firm_id INT GENERATED ALWAYS AS IDENTITY,
    law_firm_name VARCHAR(50) UNIQUE NOT NULL,
    PRIMARY KEY (law_firm_id)
);

CREATE TABLE lawyer (
    lawyer_id INT GENERATED ALWAYS AS IDENTITY,
    lawyer_name VARCHAR(50) UNIQUE NOT NULL,
    law_firm_id INT,
    PRIMARY KEY (lawyer_id),
    FOREIGN KEY (law_firm_id) REFERENCES law_firm(law_firm_id)
);

CREATE TABLE case (
    case_id VARCHAR(50) UNIQUE NOT NULL,
    summary TEXT,
    defendant VARCHAR(50),
    claimant VARCHAR(50),
    verdict_id INT,
    title VARCHAR(150),
    court_date DATE,
    case_number VARCHAR(50) UNIQUE NOT NULL,
    case_url VARCHAR(50),
    court_id INT,
    verdict_summary TEXT,
    PRIMARY KEY (case_id),
    FOREIGN KEY (verdict_id) REFERENCES verdict(verdict_id),
    FOREIGN KEY (court_id) REFERENCES court(court_id)
);

CREATE TABLE tag_assignment (
    tag_assignment_id INT GENERATED ALWAYS AS IDENTITY,
    case_id VARCHAR(50),
    tag_id INT,
    PRIMARY KEY (tag_assignment_id),
    FOREIGN KEY (case_id) REFERENCES case(case_id),
    FOREIGN KEY (tag_id) REFERENCES tag(tag_id)
);

CREATE TABLE judge_assignment (
    judge_assignment_id INT GENERATED ALWAYS AS IDENTITY,
    case_id VARCHAR(50),
    judge_id INT,
    PRIMARY KEY (judge_assignment_id),
    FOREIGN KEY (case_id) REFERENCES case(case_id),
    FOREIGN KEY (judge_id) REFERENCES judge(judge_id)
);

CREATE TABLE prosecuting_lawyer_assignment (
    prosecuting_lawyer_assignment_id INT GENERATED ALWAYS AS IDENTITY,
    case_id VARCHAR(50),
    lawyer_id INT,
    PRIMARY KEY (prosecuting_lawyer_assignment_id),
    FOREIGN KEY (case_id) REFERENCES case(case_id),
    FOREIGN KEY (lawyer_id) REFERENCES lawyer(lawyer_id)
);

CREATE TABLE defendant_lawyer_assignment (
    defendant_lawyer_assignment_id INT GENERATED ALWAYS AS IDENTITY,
    case_id VARCHAR(50),
    lawyer_id INT,
    PRIMARY KEY (defendant_lawyer_assignment_id),
    FOREIGN KEY (case_id) REFERENCES case(case_id),
    FOREIGN KEY (lawyer_id) REFERENCES lawyer(lawyer_id)
);