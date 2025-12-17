-- ============================================================
-- NEMIS SAMPLE DATA FOR TESTING
-- Insert this after running schema.sql for immediate testing
-- ============================================================

-- Create some test voters
INSERT INTO User_account (CNIE, name, role, is_active) VALUES
('VT111111', 'Ahmed Hassan', 'Voter', TRUE),
('VT222222', 'Fatima Zahra', 'Voter', TRUE),
('VT333333', 'Youssef Idrissi', 'Voter', TRUE),
('VT444444', 'Salma Bennani', 'Voter', TRUE),
('VT555555', 'Omar Alami', 'Voter', TRUE);

-- Register voters in different regions
INSERT INTO Voter (User_ID, Region_ID, is_eligible) 
SELECT User_ID, 
       CASE 
           WHEN CNIE = 'VT111111' THEN 1  -- Tangier
           WHEN CNIE = 'VT222222' THEN 4  -- Rabat
           WHEN CNIE = 'VT333333' THEN 3  -- Fès
           WHEN CNIE = 'VT444444' THEN 6  -- Casablanca
           WHEN CNIE = 'VT555555' THEN 7  -- Marrakech
       END,
       TRUE
FROM User_account 
WHERE role = 'Voter' AND CNIE LIKE 'VT%';

-- Create test candidates
INSERT INTO User_account (CNIE, name, role, is_active) VALUES
('CD111111', 'Karim El Fassi', 'Candidate', TRUE),
('CD222222', 'Nadia Rbati', 'Candidate', TRUE),
('CD333333', 'Hassan Idrissi', 'Candidate', TRUE),
('CD444444', 'Amina Casawi', 'Candidate', TRUE);

-- Create a sample election
INSERT INTO Election (name, type, start_date, end_date, status, Admin_ID, description)
SELECT 
    'Parliamentary Election 2025',
    'Parliamentary',
    CURRENT_TIMESTAMP + INTERVAL '1 day',  -- Starts tomorrow
    CURRENT_TIMESTAMP + INTERVAL '7 days', -- Ends in 7 days
    'Planned',
    User_ID,
    'National parliamentary elections for 2025'
FROM User_account
WHERE role = 'Admin' AND CNIE = 'AD123456'
LIMIT 1;

-- Associate election with multiple regions
INSERT INTO Election_Region (Election_ID, Region_ID)
SELECT 1, Region_ID
FROM Region
WHERE Region_ID IN (1, 3, 4, 6, 7);  -- Tangier, Fès, Rabat, Casa, Marrakech

-- Register candidates for the election
INSERT INTO Candidate (User_ID, Election_ID, Region_ID, party_name, manifesto, is_approved)
SELECT 
    u.User_ID,
    1,  -- Election ID
    CASE 
        WHEN u.CNIE = 'CD111111' THEN 1  -- Tangier
        WHEN u.CNIE = 'CD222222' THEN 4  -- Rabat
        WHEN u.CNIE = 'CD333333' THEN 3  -- Fès
        WHEN u.CNIE = 'CD444444' THEN 6  -- Casablanca
    END,
    CASE 
        WHEN u.CNIE = 'CD111111' THEN 'Justice Party'
        WHEN u.CNIE = 'CD222222' THEN 'Progress Alliance'
        WHEN u.CNIE = 'CD333333' THEN 'Democratic Union'
        WHEN u.CNIE = 'CD444444' THEN 'People''s Front'
    END,
    'Working for a better future for all Moroccans. Focus on education, healthcare, and economic development.',
    FALSE  -- Not yet approved
FROM User_account u
WHERE u.role = 'Candidate' AND u.CNIE LIKE 'CD%';

-- Create another completed election for testing results
INSERT INTO Election (name, type, start_date, end_date, status, Admin_ID, description)
SELECT 
    'Municipal Election 2024',
    'Municipal',
    CURRENT_TIMESTAMP - INTERVAL '30 days',
    CURRENT_TIMESTAMP - INTERVAL '23 days',
    'Completed',
    User_ID,
    'Local municipal elections 2024'
FROM User_account
WHERE role = 'Admin' AND CNIE = 'AD123456'
LIMIT 1;

-- Associate with regions
INSERT INTO Election_Region (Election_ID, Region_ID)
SELECT 2, Region_ID
FROM Region
WHERE Region_ID IN (1, 4);  -- Tangier, Rabat

-- Add more candidates for completed election
INSERT INTO User_account (CNIE, name, role, is_active) VALUES
('CD555555', 'Mohammed Tanjaoui', 'Candidate', TRUE),
('CD666666', 'Leila Rbatia', 'Candidate', TRUE);

INSERT INTO Candidate (User_ID, Election_ID, Region_ID, party_name, manifesto, is_approved, approved_by)
SELECT 
    u.User_ID,
    2,  -- Completed election
    CASE 
        WHEN u.CNIE = 'CD555555' THEN 1  -- Tangier
        WHEN u.CNIE = 'CD666666' THEN 4  -- Rabat
    END,
    CASE 
        WHEN u.CNIE = 'CD555555' THEN 'Unity Party'
        WHEN u.CNIE = 'CD666666' THEN 'Reform Movement'
    END,
    'Focus on local infrastructure and services.',
    TRUE,  -- Approved
    (SELECT User_ID FROM User_account WHERE CNIE = 'EO123456')
FROM User_account u
WHERE u.role = 'Candidate' AND u.CNIE IN ('CD555555', 'CD666666');

-- Add some votes to completed election
INSERT INTO Vote (Voter_ID, Election_ID, Candidate_ID, vote_timestamp)
SELECT 
    v.Voter_ID,
    2,
    (SELECT Candidate_ID FROM Candidate c 
     WHERE c.Election_ID = 2 AND c.Region_ID = v.Region_ID 
     ORDER BY RANDOM() LIMIT 1),
    CURRENT_TIMESTAMP - INTERVAL '25 days'
FROM Voter v
WHERE v.Region_ID IN (1, 4)  -- Voters from Tangier and Rabat
LIMIT 3;

-- Add audit log entries
INSERT INTO Audit_log (User_ID, action, table_name, details)
SELECT 
    User_ID,
    'Sample data loaded',
    'Multiple tables',
    'Initial test data inserted for demonstration purposes'
FROM User_account
WHERE CNIE = 'AD123456';

-- Add election phases for upcoming election
INSERT INTO Election_Phase (Election_ID, phase_name, start_time, end_time, description)
VALUES
(1, 'Registration', CURRENT_TIMESTAMP + INTERVAL '1 day', CURRENT_TIMESTAMP + INTERVAL '3 days', 'Voter registration period'),
(1, 'Campaigning', CURRENT_TIMESTAMP + INTERVAL '3 days', CURRENT_TIMESTAMP + INTERVAL '6 days', 'Campaign period'),
(1, 'Voting', CURRENT_TIMESTAMP + INTERVAL '6 days', CURRENT_TIMESTAMP + INTERVAL '7 days', 'Voting day');

-- Verification queries
SELECT '=== SAMPLE DATA LOADED SUCCESSFULLY ===' AS status;

SELECT 'Total Users: ' || COUNT(*) AS info FROM User_account;
SELECT 'Total Voters: ' || COUNT(*) AS info FROM Voter;
SELECT 'Total Candidates: ' || COUNT(*) AS info FROM Candidate;
SELECT 'Total Elections: ' || COUNT(*) AS info FROM Election;
SELECT 'Total Votes: ' || COUNT(*) AS info FROM Vote;

-- Show elections
SELECT 
    Election_ID,
    name,
    status,
    start_date,
    end_date,
    (SELECT COUNT(*) FROM Candidate WHERE Candidate.Election_ID = Election.Election_ID) AS candidates,
    (SELECT COUNT(*) FROM Vote WHERE Vote.Election_ID = Election.Election_ID) AS votes
FROM Election;

-- Show regions with voters
SELECT 
    r.name AS region,
    COUNT(DISTINCT v.Voter_ID) AS voters,
    COUNT(DISTINCT c.Candidate_ID) AS candidates
FROM Region r
LEFT JOIN Voter v ON r.Region_ID = v.Region_ID
LEFT JOIN Candidate c ON r.Region_ID = c.Region_ID
GROUP BY r.name
HAVING COUNT(DISTINCT v.Voter_ID) > 0 OR COUNT(DISTINCT c.Candidate_ID) > 0
ORDER BY voters DESC;

-- Show candidates by election
SELECT 
    e.name AS election,
    u.name AS candidate,
    c.party_name,
    r.name AS region,
    c.is_approved
FROM Candidate c
JOIN User_account u ON c.User_ID = u.User_ID
JOIN Election e ON c.Election_ID = e.Election_ID
JOIN Region r ON c.Region_ID = r.Region_ID
ORDER BY e.Election_ID, c.is_approved DESC, u.name;
