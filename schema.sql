-- ============================================================
-- NEMIS DATABASE SCHEMA - FINAL OPTIMIZED VERSION
-- National Election Management Information System  
-- Database Course Project - Production Ready
-- ============================================================

-- Drop all objects if they exist (clean slate)
DROP TABLE IF EXISTS Audit_log CASCADE;
DROP TABLE IF EXISTS Vote CASCADE;
DROP TABLE IF EXISTS Candidate CASCADE;
DROP TABLE IF EXISTS Election_Region CASCADE;
DROP TABLE IF EXISTS Election_Phase CASCADE;
DROP TABLE IF EXISTS Election CASCADE;
DROP TABLE IF EXISTS Voter CASCADE;
DROP TABLE IF EXISTS Region CASCADE;
DROP TABLE IF EXISTS User_account CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS validate_candidate_region() CASCADE;
DROP FUNCTION IF EXISTS validate_phase_overlap() CASCADE;
DROP FUNCTION IF EXISTS validate_vote_timing() CASCADE;
DROP FUNCTION IF EXISTS protect_audit_log() CASCADE;
DROP FUNCTION IF EXISTS update_election_status() CASCADE;
DROP FUNCTION IF EXISTS calculate_turnout() CASCADE;
DROP FUNCTION IF EXISTS get_election_winner() CASCADE;
DROP FUNCTION IF EXISTS get_region_statistics() CASCADE;

-- ============================================================
-- CORE TABLES
-- ============================================================

-- User Account Table
CREATE TABLE User_account (
    User_ID SERIAL PRIMARY KEY,
    CNIE VARCHAR(20) UNIQUE NOT NULL CHECK (CNIE ~ '^[A-Z]{2}[0-9]{6}$'),
    name VARCHAR(100) NOT NULL CHECK (length(trim(name)) >= 2),
    role VARCHAR(20) NOT NULL CHECK (role IN ('Admin', 'Election Officer', 'Voter', 'Candidate')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Region Table
CREATE TABLE Region (
    Region_ID SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    population INTEGER CHECK (population >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Voter Table
CREATE TABLE Voter (
    Voter_ID SERIAL PRIMARY KEY,
    User_ID INTEGER NOT NULL UNIQUE REFERENCES User_account(User_ID) ON DELETE CASCADE,
    Region_ID INTEGER NOT NULL REFERENCES Region(Region_ID),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_eligible BOOLEAN DEFAULT TRUE NOT NULL,
    date_of_birth DATE,
    CONSTRAINT voter_age_check CHECK (date_of_birth IS NULL OR date_of_birth <= CURRENT_DATE - INTERVAL '18 years')
);

-- Election Table
CREATE TABLE Election (
    Election_ID SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'Planned' CHECK (status IN ('Planned', 'Active', 'Completed', 'Cancelled')),
    Admin_ID INTEGER REFERENCES User_account(User_ID),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    description TEXT,
    CONSTRAINT valid_election_dates CHECK (end_date > start_date)
);

-- Election Phase Table
CREATE TABLE Election_Phase (
    Phase_ID SERIAL PRIMARY KEY,
    Election_ID INTEGER NOT NULL REFERENCES Election(Election_ID) ON DELETE CASCADE,
    phase_name VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    description TEXT,
    CONSTRAINT valid_phase_times CHECK (end_time > start_time)
);

-- Election Region (Many-to-Many)
CREATE TABLE Election_Region (
    Election_Region_ID SERIAL PRIMARY KEY,
    Election_ID INTEGER NOT NULL REFERENCES Election(Election_ID) ON DELETE CASCADE,
    Region_ID INTEGER NOT NULL REFERENCES Region(Region_ID) ON DELETE CASCADE,
    registration_deadline TIMESTAMP,
    voting_centers INTEGER DEFAULT 0,
    UNIQUE(Election_ID, Region_ID)
);

-- Candidate Table
CREATE TABLE Candidate (
    Candidate_ID SERIAL PRIMARY KEY,
    User_ID INTEGER NOT NULL UNIQUE REFERENCES User_account(User_ID) ON DELETE CASCADE,
    Election_ID INTEGER NOT NULL REFERENCES Election(Election_ID) ON DELETE CASCADE,
    Region_ID INTEGER NOT NULL REFERENCES Region(Region_ID),
    party_name VARCHAR(100),
    manifesto TEXT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_approved BOOLEAN DEFAULT FALSE NOT NULL,
    approval_date TIMESTAMP,
    approved_by INTEGER REFERENCES User_account(User_ID)
);

-- Vote Table (Immutable)
CREATE TABLE Vote (
    Vote_ID SERIAL PRIMARY KEY,
    Voter_ID INTEGER NOT NULL REFERENCES Voter(Voter_ID) ON DELETE CASCADE,
    Election_ID INTEGER NOT NULL REFERENCES Election(Election_ID) ON DELETE CASCADE,
    Candidate_ID INTEGER NOT NULL REFERENCES Candidate(Candidate_ID) ON DELETE CASCADE,
    vote_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    verification_code VARCHAR(64) NOT NULL,
    UNIQUE(Voter_ID, Election_ID)
);

-- Audit Log Table (Immutable)
CREATE TABLE Audit_log (
    Log_ID SERIAL PRIMARY KEY,
    User_ID INTEGER REFERENCES User_account(User_ID),
    action VARCHAR(200) NOT NULL,
    table_name VARCHAR(50),
    record_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    details TEXT,
    session_id VARCHAR(100)
);


-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

CREATE INDEX idx_user_role ON User_account(role);
CREATE INDEX idx_user_cnie ON User_account(CNIE);
CREATE INDEX idx_voter_user ON Voter(User_ID);
CREATE INDEX idx_voter_region ON Voter(Region_ID);
CREATE INDEX idx_candidate_election ON Candidate(Election_ID);
CREATE INDEX idx_candidate_region ON Candidate(Region_ID);
CREATE INDEX idx_candidate_approved ON Candidate(is_approved) WHERE is_approved = TRUE;
CREATE INDEX idx_vote_voter ON Vote(Voter_ID);
CREATE INDEX idx_vote_election ON Vote(Election_ID);
CREATE INDEX idx_vote_candidate ON Vote(Candidate_ID);
CREATE INDEX idx_vote_timestamp ON Vote(vote_timestamp);
CREATE INDEX idx_election_status ON Election(status);
CREATE INDEX idx_election_dates ON Election(start_date, end_date);
CREATE INDEX idx_audit_user ON Audit_log(User_ID);
CREATE INDEX idx_audit_timestamp ON Audit_log(timestamp DESC);
CREATE INDEX idx_audit_table ON Audit_log(table_name);

-- ============================================================
-- FUNCTIONS (Advanced SQL Features)
-- ============================================================

-- Calculate turnout by region
CREATE OR REPLACE FUNCTION calculate_turnout(p_election_id INTEGER)
RETURNS TABLE (
    region_name VARCHAR(100),
    eligible_voters BIGINT,
    votes_cast BIGINT,
    turnout_percentage NUMERIC(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.name::VARCHAR(100),
        COUNT(DISTINCT v.Voter_ID) AS eligible_voters,
        COUNT(DISTINCT vt.Vote_ID) AS votes_cast,
        CASE 
            WHEN COUNT(DISTINCT v.Voter_ID) > 0 
            THEN ROUND((COUNT(DISTINCT vt.Vote_ID)::NUMERIC / COUNT(DISTINCT v.Voter_ID)::NUMERIC * 100), 2)
            ELSE 0
        END AS turnout_percentage
    FROM Region r
    LEFT JOIN Voter v ON r.Region_ID = v.Region_ID AND v.is_eligible = TRUE
    LEFT JOIN Vote vt ON v.Voter_ID = vt.Voter_ID AND vt.Election_ID = p_election_id
    JOIN Election_Region er ON r.Region_ID = er.Region_ID AND er.Election_ID = p_election_id
    GROUP BY r.name
    ORDER BY turnout_percentage DESC;
END;
$$ LANGUAGE plpgsql;

-- Get election winner(s)
CREATE OR REPLACE FUNCTION get_election_winner(p_election_id INTEGER)
RETURNS TABLE (
    candidate_name VARCHAR(100),
    party_name VARCHAR(100),
    region_name VARCHAR(100),
    vote_count BIGINT,
    vote_percentage NUMERIC(5,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH RankedCandidates AS (
        SELECT 
            u.name,
            c.party_name,
            r.name AS region,
            COUNT(v.Vote_ID) AS votes,
            ROUND((COUNT(v.Vote_ID)::NUMERIC / 
                NULLIF(SUM(COUNT(v.Vote_ID)) OVER (PARTITION BY c.Region_ID), 0) * 100), 2) AS percentage,
            RANK() OVER (PARTITION BY c.Region_ID ORDER BY COUNT(v.Vote_ID) DESC) AS rank
        FROM Candidate c
        JOIN User_account u ON c.User_ID = u.User_ID
        JOIN Region r ON c.Region_ID = r.Region_ID
        LEFT JOIN Vote v ON c.Candidate_ID = v.Candidate_ID
        WHERE c.Election_ID = p_election_id AND c.is_approved = TRUE
        GROUP BY u.name, c.party_name, r.name, c.Region_ID
    )
    SELECT 
        name::VARCHAR(100),
        party_name::VARCHAR(100),
        region::VARCHAR(100),
        votes,
        percentage
    FROM RankedCandidates
    WHERE rank = 1
    ORDER BY votes DESC;
END;
$$ LANGUAGE plpgsql;

-- Get region statistics
CREATE OR REPLACE FUNCTION get_region_statistics(p_region_id INTEGER DEFAULT NULL)
RETURNS TABLE (
    region_name VARCHAR(100),
    total_voters BIGINT,
    eligible_voters BIGINT,
    total_candidates BIGINT,
    approved_candidates BIGINT,
    active_elections BIGINT,
    total_votes_cast BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.name::VARCHAR(100),
        COUNT(DISTINCT v.Voter_ID) AS total_voters,
        COUNT(DISTINCT v.Voter_ID) FILTER (WHERE v.is_eligible = TRUE) AS eligible_voters,
        COUNT(DISTINCT c.Candidate_ID) AS total_candidates,
        COUNT(DISTINCT c.Candidate_ID) FILTER (WHERE c.is_approved = TRUE) AS approved_candidates,
        COUNT(DISTINCT e.Election_ID) FILTER (WHERE e.status = 'Active') AS active_elections,
        COUNT(DISTINCT vt.Vote_ID) AS total_votes_cast
    FROM Region r
    LEFT JOIN Voter v ON r.Region_ID = v.Region_ID
    LEFT JOIN Candidate c ON r.Region_ID = c.Region_ID
    LEFT JOIN Election_Region er ON r.Region_ID = er.Region_ID
    LEFT JOIN Election e ON er.Election_ID = e.Election_ID
    LEFT JOIN Vote vt ON v.Voter_ID = vt.Voter_ID
    WHERE p_region_id IS NULL OR r.Region_ID = p_region_id
    GROUP BY r.name
    ORDER BY r.name;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- TRIGGERS (Business Rule Enforcement)
-- ============================================================

-- Validate candidate region
CREATE OR REPLACE FUNCTION validate_candidate_region()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM Election_Region 
        WHERE Election_ID = NEW.Election_ID 
        AND Region_ID = NEW.Region_ID
    ) THEN
        RAISE EXCEPTION 'Candidate region must be one of the election regions';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_candidate_region
    BEFORE INSERT OR UPDATE ON Candidate
    FOR EACH ROW
    EXECUTE FUNCTION validate_candidate_region();

-- Prevent phase overlap
CREATE OR REPLACE FUNCTION validate_phase_overlap()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM Election_Phase
        WHERE Election_ID = NEW.Election_ID
        AND Phase_ID != COALESCE(NEW.Phase_ID, -1)
        AND (NEW.start_time, NEW.end_time) OVERLAPS (start_time, end_time)
    ) THEN
        RAISE EXCEPTION 'Election phases cannot overlap';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_phase_overlap
    BEFORE INSERT OR UPDATE ON Election_Phase
    FOR EACH ROW
    EXECUTE FUNCTION validate_phase_overlap();

-- Validate vote timing
CREATE OR REPLACE FUNCTION validate_vote_timing()
RETURNS TRIGGER AS $$
DECLARE
    election_start TIMESTAMP;
    election_end TIMESTAMP;
    election_status VARCHAR(20);
    voter_region INTEGER;
    candidate_region INTEGER;
BEGIN
    SELECT start_date, end_date, status 
    INTO election_start, election_end, election_status
    FROM Election WHERE Election_ID = NEW.Election_ID;
    
    IF election_status != 'Active' THEN
        RAISE EXCEPTION 'Election not active';
    END IF;
    
    IF NEW.vote_timestamp < election_start OR NEW.vote_timestamp > election_end THEN
        RAISE EXCEPTION 'Vote outside election period';
    END IF;
    
    SELECT Region_ID INTO voter_region
    FROM Voter WHERE Voter_ID = NEW.Voter_ID;
    
    SELECT Region_ID INTO candidate_region
    FROM Candidate WHERE Candidate_ID = NEW.Candidate_ID;
    
    IF voter_region != candidate_region THEN
        RAISE EXCEPTION 'Region mismatch';
    END IF;
    
    NEW.verification_code := md5(NEW.Voter_ID::text || NEW.Election_ID::text || NEW.vote_timestamp::text);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_vote_timing
    BEFORE INSERT ON Vote
    FOR EACH ROW
    EXECUTE FUNCTION validate_vote_timing();

-- Protect audit log
CREATE OR REPLACE FUNCTION protect_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log cannot be modified';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_audit_update
    BEFORE UPDATE ON Audit_log
    FOR EACH ROW
    EXECUTE FUNCTION protect_audit_log();

CREATE TRIGGER prevent_audit_delete
    BEFORE DELETE ON Audit_log
    FOR EACH ROW
    EXECUTE FUNCTION protect_audit_log();

-- Auto-update election status
CREATE OR REPLACE FUNCTION update_election_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.start_date <= CURRENT_TIMESTAMP AND NEW.status = 'Planned' THEN
        NEW.status := 'Active';
    END IF;
    
    IF NEW.end_date <= CURRENT_TIMESTAMP AND NEW.status = 'Active' THEN
        NEW.status := 'Completed';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_update_election_status
    BEFORE INSERT OR UPDATE ON Election
    FOR EACH ROW
    EXECUTE FUNCTION update_election_status();

-- Set approval date
CREATE OR REPLACE FUNCTION set_candidate_approval_date()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_approved = TRUE AND (OLD.is_approved IS NULL OR OLD.is_approved = FALSE) THEN
        NEW.approval_date := CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER track_candidate_approval
    BEFORE UPDATE ON Candidate
    FOR EACH ROW
    EXECUTE FUNCTION set_candidate_approval_date();


-- ============================================================
-- VIEWS (Advanced Reporting)
-- ============================================================

-- Election Results View
CREATE OR REPLACE VIEW vw_election_results AS
SELECT 
    e.Election_ID,
    e.name AS election_name,
    e.type,
    e.status,
    c.Candidate_ID,
    u.name AS candidate_name,
    c.party_name,
    r.name AS region_name,
    COUNT(v.Vote_ID) AS vote_count,
    ROUND(COUNT(v.Vote_ID)::NUMERIC * 100.0 / 
        NULLIF(SUM(COUNT(v.Vote_ID)) OVER (PARTITION BY e.Election_ID, c.Region_ID), 0), 2
    ) AS vote_percentage_in_region,
    RANK() OVER (PARTITION BY c.Region_ID, e.Election_ID ORDER BY COUNT(v.Vote_ID) DESC) AS rank_in_region
FROM Election e
LEFT JOIN Candidate c ON e.Election_ID = c.Election_ID AND c.is_approved = TRUE
LEFT JOIN User_account u ON c.User_ID = u.User_ID
LEFT JOIN Region r ON c.Region_ID = r.Region_ID
LEFT JOIN Vote v ON c.Candidate_ID = v.Candidate_ID
GROUP BY e.Election_ID, e.name, e.type, e.status, c.Candidate_ID, u.name, c.party_name, r.name, c.Region_ID
ORDER BY e.Election_ID, vote_count DESC;

-- Voter Turnout View
CREATE OR REPLACE VIEW vw_voter_turnout AS
SELECT 
    e.Election_ID,
    e.name AS election_name,
    r.Region_ID,
    r.name AS region_name,
    COUNT(DISTINCT v.Voter_ID) AS total_eligible_voters,
    COUNT(DISTINCT vt.Vote_ID) AS votes_cast,
    ROUND(
        CASE 
            WHEN COUNT(DISTINCT v.Voter_ID) > 0 
            THEN (COUNT(DISTINCT vt.Vote_ID)::NUMERIC / COUNT(DISTINCT v.Voter_ID)::NUMERIC * 100)
            ELSE 0
        END, 2
    ) AS turnout_percentage
FROM Election e
CROSS JOIN Region r
LEFT JOIN Election_Region er ON e.Election_ID = er.Election_ID AND r.Region_ID = er.Region_ID
LEFT JOIN Voter v ON r.Region_ID = v.Region_ID AND v.is_eligible = TRUE
LEFT JOIN Vote vt ON v.Voter_ID = vt.Voter_ID AND vt.Election_ID = e.Election_ID
WHERE er.Election_Region_ID IS NOT NULL
GROUP BY e.Election_ID, e.name, r.Region_ID, r.name
ORDER BY e.Election_ID, turnout_percentage DESC;

-- Candidate Statistics View
CREATE OR REPLACE VIEW vw_candidate_statistics AS
SELECT 
    c.Candidate_ID,
    u.name AS candidate_name,
    u.CNIE,
    c.party_name,
    r.name AS region_name,
    e.name AS election_name,
    c.is_approved,
    c.registration_date,
    c.approval_date,
    COUNT(v.Vote_ID) AS total_votes,
    RANK() OVER (PARTITION BY c.Election_ID ORDER BY COUNT(v.Vote_ID) DESC) AS overall_rank
FROM Candidate c
JOIN User_account u ON c.User_ID = u.User_ID
JOIN Region r ON c.Region_ID = r.Region_ID
JOIN Election e ON c.Election_ID = e.Election_ID
LEFT JOIN Vote v ON c.Candidate_ID = v.Candidate_ID
GROUP BY c.Candidate_ID, u.name, u.CNIE, c.party_name, r.name, e.name, 
         c.is_approved, c.registration_date, c.approval_date, c.Election_ID
ORDER BY total_votes DESC;

-- Election Overview View
CREATE OR REPLACE VIEW vw_election_overview AS
SELECT 
    e.Election_ID,
    e.name AS election_name,
    e.type,
    e.status,
    e.start_date,
    e.end_date,
    admin.name AS created_by,
    COUNT(DISTINCT er.Region_ID) AS number_of_regions,
    COUNT(DISTINCT c.Candidate_ID) AS total_candidates,
    COUNT(DISTINCT c.Candidate_ID) FILTER (WHERE c.is_approved = TRUE) AS approved_candidates,
    COUNT(DISTINCT v.Vote_ID) AS total_votes,
    CASE 
        WHEN e.start_date > CURRENT_TIMESTAMP THEN 'Upcoming'
        WHEN e.end_date < CURRENT_TIMESTAMP THEN 'Completed'
        ELSE 'In Progress'
    END AS current_phase
FROM Election e
LEFT JOIN User_account admin ON e.Admin_ID = admin.User_ID
LEFT JOIN Election_Region er ON e.Election_ID = er.Election_ID
LEFT JOIN Candidate c ON e.Election_ID = c.Election_ID
LEFT JOIN Vote v ON e.Election_ID = v.Election_ID
GROUP BY e.Election_ID, e.name, e.type, e.status, e.start_date, e.end_date, admin.name
ORDER BY e.start_date DESC;

-- ============================================================
-- SAMPLE DATA
-- ============================================================

-- Moroccan Regions
INSERT INTO Region (name, population) VALUES
('Tangier-Tetouan-Al Hoceima', 3800000),
('Oriental', 2300000),
('Fès-Meknès', 4200000),
('Rabat-Salé-Kénitra', 4600000),
('Béni Mellal-Khénifra', 2500000),
('Casablanca-Settat', 6800000),
('Marrakech-Safi', 4500000),
('Drâa-Tafilalet', 1600000),
('Souss-Massa', 2700000),
('Guelmim-Oued Noun', 450000),
('Laâyoune-Sakia El Hamra', 400000),
('Dakhla-Oued Ed-Dahab', 150000);

-- Admin Users
INSERT INTO User_account (CNIE, name, role, is_active) VALUES
('AD123456', 'Admin User', 'Admin', TRUE),
('EO123456', 'Election Officer', 'Election Officer', TRUE);

-- ============================================================
-- TABLE COMMENTS
-- ============================================================

COMMENT ON TABLE User_account IS 'System users with role-based access control';
COMMENT ON TABLE Voter IS 'Voters assigned to specific regions';
COMMENT ON TABLE Candidate IS 'Candidates requiring approval before elections';
COMMENT ON TABLE Vote IS 'Immutable voting records with verification codes';
COMMENT ON TABLE Audit_log IS 'Immutable audit trail for compliance';
COMMENT ON TABLE Election IS 'Elections with automatic status management';

COMMENT ON FUNCTION calculate_turnout IS 'Calculate voter turnout statistics by region';
COMMENT ON FUNCTION get_election_winner IS 'Get winning candidates by region';
COMMENT ON FUNCTION get_region_statistics IS 'Get comprehensive region statistics';

